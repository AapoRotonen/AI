"""FastAPI API for the Koivu Store demo."""

from __future__ import annotations

import hmac
import re
import sqlite3
import time
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Literal

from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict, Field

from agent.graph import get_agent
from agent.state import AgentState
from core.config import Settings, get_settings
from core.database import Database
from core.observability import log_event
from core.orders import OrderStatusService, price_demo_order_items
from core.security import (
    hash_password,
    new_case_id,
    new_order_reference,
    new_session_token,
    new_user_id,
    sanitize_support_text,
    token_digest,
    verify_password,
)
from core.retrieval import get_retriever

settings = get_settings()
SESSION_COOKIE = "koivu_session"
_EMAIL_PATTERN = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
_INVALID_LOGIN_HASH = hash_password("fixed-placeholder-password-never-used")


class ChatTurn(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(max_length=1500)


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    history: list[ChatTurn] = Field(default_factory=list, max_length=12)


class ChatResponse(BaseModel):
    answer: str
    path: str
    should_escalate: bool
    support_case_id: str | None = None
    auth_required: bool = False


class Credentials(BaseModel):
    email: str = Field(min_length=5, max_length=254)
    password: str = Field(min_length=12, max_length=128)


class OrderItemRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    product_id: str = Field(min_length=1, max_length=32)
    color: str = Field(min_length=1, max_length=40)
    size: str = Field(min_length=1, max_length=32)
    quantity: int = Field(ge=1, le=20, strict=True)


class CreateDemoOrderRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[OrderItemRequest] = Field(min_length=1, max_length=24)


class SupportReply(BaseModel):
    response: str = Field(min_length=1, max_length=4000)


class SupportCaseResponse(BaseModel):
    id: str
    status: str
    human_response: str | None = None
    demo_response: bool = False


class DemoOrderResponse(BaseModel):
    id: str
    status: str
    tracking_code: str | None
    created_at: str
    items: list[dict] = Field(default_factory=list)
    total_cents: int = 0


def _normalise_email(email: str) -> str:
    value = email.strip().lower()
    if not _EMAIL_PATTERN.fullmatch(value):
        raise HTTPException(status_code=422, detail="Anna kelvollinen sähköpostiosoite.")
    return value


def _issue_session(response: Response, db: Database, user_id: str, config: Settings) -> None:
    token = new_session_token()
    expires_at = datetime.now(timezone.utc) + timedelta(hours=config.session_ttl_hours)
    db.create_session(token_digest(token), user_id, expires_at.isoformat())
    response.set_cookie(
        key=SESSION_COOKIE,
        value=token,
        max_age=config.session_ttl_hours * 60 * 60,
        httponly=True,
        secure=config.cookie_secure,
        samesite="strict",
        path="/",
    )


def _is_generic_human_request(message: str) -> bool:
    text = message.casefold()
    asks_for_person = any(term in text for term in ("ihmi", "asiakaspalvel", "henkilö", "agent", "ihminen"))
    mentions_issue = any(
        term in text
        for term in ("tilaus", "paket", "toimit", "palaut", "vaiht", "reklamaa", "maksu", "lasku", "hyvity", "peruut", "rikki", "virhe", "väär", "koko", "tuote")
    )
    return asks_for_person and not mentions_issue


def _create_support_case(
    db: Database, user_id: str, question: str, result: dict, original_message: str = ""
) -> dict:
    if result.get("intent") == "personal_support":
        reason = result.get("escalation_reason") or "order_support"
    elif result.get("intent") == "external_info":
        reason = result.get("escalation_reason") or "external_lookup_failed"
    else:
        reason = result.get("escalation_reason") or "no_grounded_answer"
    allowed_reasons = {
        "order_support_requires_review",
        "order_service_unavailable",
        "order_not_found_or_not_owned",
        "no_supported_automatic_answer",
        "web_search_empty",
        "web_search_failed",
        "no_grounded_sources",
        "answer_generation_or_validation_failed",
    }
    if reason not in allowed_reasons:
        reason = "no_supported_automatic_answer"
    safe_context = {
        "route": str(result.get("path_taken", ""))[:160],
        "intent": str(result.get("intent", "ambiguous"))[:40],
        "source_ids": list(result.get("source_ids", []))[:8],
        "request_id": str(result.get("request_id", ""))[:64],
    }
    safe_question = sanitize_support_text(question)
    existing = db.find_open_support_case(user_id, safe_question, reason)
    if existing:
        return existing
    if result.get("human_requested") and _is_generic_human_request(original_message):
        existing = db.find_latest_open_support_case(user_id, reason)
        if existing:
            return existing
    return db.create_support_case(
        case_id=new_case_id(),
        user_id=user_id,
        question=safe_question,
        reason=reason,
        safe_context=safe_context,
    )


def create_app(database: Database | None = None, config: Settings | None = None) -> FastAPI:
    active_settings = config or get_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        app.state.database = database or Database(active_settings.database_path)
        app.state.database.initialize()
        yield

    app = FastAPI(title="Koivu Store AI API", version="2.0.0", lifespan=lifespan)
    origins = [origin.strip() for origin in active_settings.cors_allowed_origins.split(",") if origin.strip()]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "DELETE"],
        allow_headers=["Content-Type", "X-Support-Agent-Key", "X-Catalog-Setup-Key"],
    )

    @app.middleware("http")
    async def request_observability(request: Request, call_next):
        request_id = uuid.uuid4().hex
        request.state.request_id = request_id
        start = time.perf_counter()
        status_code = 500
        error_type = None
        try:
            response = await call_next(request)
            status_code = response.status_code
            response.headers["X-Request-ID"] = request_id
            if request.url.path.startswith(("/auth/", "/orders", "/support/", "/chat", "/human-chat")):
                response.headers["Cache-Control"] = "no-store"
            return response
        except Exception as exc:
            error_type = type(exc).__name__
            raise
        finally:
            log_event(
                "http_request",
                request_id=request_id,
                method=request.method,
                path=request.url.path,
                status_code=status_code,
                duration_ms=round((time.perf_counter() - start) * 1000, 2),
                error_type=error_type,
            )

    def get_db(request: Request) -> Database:
        return request.app.state.database

    def get_current_user(
        request: Request,
        db: Database = Depends(get_db),
    ) -> dict | None:
        token = request.cookies.get(SESSION_COOKIE)
        if not token:
            return None
        return db.get_session_user(token_digest(token))

    def require_user(user: dict | None = Depends(get_current_user)) -> dict:
        if user is None:
            raise HTTPException(status_code=401, detail="Kirjaudu sisään jatkaaksesi.")
        return user

    def require_support_agent(
        support_key: str | None = Header(default=None, alias="X-Support-Agent-Key"),
    ) -> None:
        expected = active_settings.support_agent_api_key
        if not expected:
            raise HTTPException(status_code=503, detail="Tukihenkilön rajapintaa ei ole määritetty.")
        if not support_key or not hmac.compare_digest(support_key.encode("utf-8"), expected.encode("utf-8")):
            raise HTTPException(status_code=401, detail="Tukihenkilön tunniste ei kelpaa.")

    def require_catalog_admin(
        setup_key: str | None = Header(default=None, alias="X-Catalog-Setup-Key"),
    ) -> None:
        expected = active_settings.catalog_setup_api_key
        if not expected:
            raise HTTPException(status_code=503, detail="Katalogin alustusta ei ole määritetty.")
        if not setup_key or not hmac.compare_digest(setup_key.encode("utf-8"), expected.encode("utf-8")):
            raise HTTPException(status_code=401, detail="Katalogin ylläpitotunniste ei kelpaa.")

    @app.get("/health")
    def health():
        return {"status": "ok", "products_loaded": get_retriever().get_count()}

    @app.post("/setup")
    def setup_knowledge_base(_: None = Depends(require_catalog_admin)):
        if not active_settings.openai_api_key:
            raise HTTPException(status_code=503, detail="OpenAI-embeddingien avainta ei ole määritetty.")
        retriever = get_retriever()
        if retriever.get_count() > 0:
            return {"message": "Tuotekatalogi jo ladattu", "chunks": retriever.get_count()}
        products_file = Path(__file__).parent / "data" / "products.txt"
        count = retriever.add_text(products_file.read_text(encoding="utf-8"), source="products.txt")
        return {"message": f"Ladattu {count} tuotetietoa", "chunks": count}

    @app.get("/products/count")
    def products_count():
        return {"count": get_retriever().get_count()}

    @app.post("/auth/register", status_code=201)
    def register(
        payload: Credentials,
        response: Response,
        http_request: Request,
        db: Database = Depends(get_db),
    ):
        email = _normalise_email(payload.email)
        user_id = new_user_id()
        try:
            db.create_user(user_id, email, hash_password(payload.password))
        except sqlite3.IntegrityError:
            raise HTTPException(status_code=409, detail="Tälle sähköpostiosoitteelle on jo tili.")
        _issue_session(response, db, user_id, active_settings)
        log_event("auth_register", request_id=http_request.state.request_id, user_id=user_id)
        return {"id": user_id, "email": email}

    @app.post("/auth/login")
    def login(payload: Credentials, response: Response, db: Database = Depends(get_db)):
        email = _normalise_email(payload.email)
        user = db.get_user_by_email(email)
        valid = verify_password(payload.password, user["password_hash"] if user else _INVALID_LOGIN_HASH)
        if not user or not valid:
            raise HTTPException(status_code=401, detail="Sähköposti tai salasana ei kelpaa.")
        _issue_session(response, db, user["id"], active_settings)
        return {"id": user["id"], "email": user["email"]}

    @app.post("/auth/logout")
    def logout(request: Request, response: Response, db: Database = Depends(get_db)):
        token = request.cookies.get(SESSION_COOKIE)
        if token:
            db.delete_session(token_digest(token))
        response.delete_cookie(SESSION_COOKIE, path="/", httponly=True, secure=active_settings.cookie_secure, samesite="strict")
        return {"logged_out": True}

    @app.get("/auth/me")
    def auth_me(user: dict | None = Depends(get_current_user)):
        return {"authenticated": user is not None, "user": user}

    @app.get("/orders", response_model=list[DemoOrderResponse])
    def list_orders(user: dict = Depends(require_user), db: Database = Depends(get_db)):
        return db.list_owned_orders(user["id"])

    @app.post("/orders", response_model=DemoOrderResponse, status_code=201)
    def create_order(
        payload: CreateDemoOrderRequest,
        user: dict = Depends(require_user),
        db: Database = Depends(get_db),
    ):
        try:
            items, total_cents = price_demo_order_items([item.model_dump() for item in payload.items])
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        return db.create_order(new_order_reference(), user["id"], items, total_cents)

    @app.delete("/orders/{order_id}", status_code=204)
    def cancel_demo_order(
        order_id: str,
        user: dict = Depends(require_user),
        db: Database = Depends(get_db),
    ):
        if not db.delete_owned_order(order_id, user["id"]):
            raise HTTPException(status_code=404, detail="Demotilausta ei löydy tältä tililtä.")
        return Response(status_code=204)

    @app.get("/support/cases/{case_id}", response_model=SupportCaseResponse)
    def get_my_support_case(
        case_id: str,
        user: dict = Depends(require_user),
        db: Database = Depends(get_db),
    ):
        case = db.get_support_case(case_id, user["id"])
        if case is None:
            raise HTTPException(status_code=404, detail="Tukipyyntöä ei löydy.")
        return case

    @app.post("/support/my-cases/{case_id}/demo-reply", response_model=SupportCaseResponse)
    def demo_reply_to_my_case(
        case_id: str,
        user: dict = Depends(require_user),
        db: Database = Depends(get_db),
    ):
        """Add a canned, explicitly marked staff-response demo to the user's own open case."""
        reply = (
            "Hei! Olen Koivun asiakaspalvelun demokäsittelijä. Näen tukipyyntösi. "
            "Kerro rauhassa, mihin tarvitset apua, niin jatketaan tästä."
        )
        case = db.demo_reply_to_user_support_case(case_id, user["id"], reply)
        if case is None:
            raise HTTPException(status_code=404, detail="Avoinna olevaa tukipyyntöä ei löydy tältä tililtä.")
        return case

    @app.get("/support/cases", dependencies=[Depends(require_support_agent)])
    def list_support_cases(status: Literal["open", "answered", "closed"] | None = Query(default=None), db: Database = Depends(get_db)):
        return db.list_support_cases(status)

    @app.get("/support/my-cases")
    def list_my_support_cases(user: dict = Depends(require_user), db: Database = Depends(get_db)):
        return db.list_user_support_cases(user["id"])

    @app.post("/support/my-cases/reset")
    def reset_my_support_cases(user: dict = Depends(require_user), db: Database = Depends(get_db)):
        """Delete only this signed-in customer's demo support cases."""
        return {"deleted": db.delete_user_support_cases(user["id"])}

    @app.post("/support/cases/{case_id}/reply", dependencies=[Depends(require_support_agent)])
    def reply_to_case(case_id: str, payload: SupportReply, db: Database = Depends(get_db)):
        case = db.reply_to_support_case(case_id, sanitize_support_text(payload.response))
        if case is None:
            raise HTTPException(status_code=404, detail="Avoinna olevaa tukipyyntöä ei löydy.")
        return case

    @app.post("/support/cases/{case_id}/close", dependencies=[Depends(require_support_agent)])
    def close_case(case_id: str, db: Database = Depends(get_db)):
        case = db.close_support_case(case_id)
        if case is None:
            raise HTTPException(status_code=404, detail="Tukipyyntöä ei löydy tai se on jo suljettu.")
        return case

    @app.post("/chat", response_model=ChatResponse)
    def chat(
        request: ChatRequest,
        http_request: Request,
        db: Database = Depends(get_db),
        user: dict | None = Depends(get_current_user),
    ):
        order_tool = OrderStatusService(db).as_agent_tool(user["id"]) if user else None
        initial_state: AgentState = {
            "question": request.message,
            "intent": "ambiguous",
            "rag_results": [],
            "web_results": [],
            "answer": "",
            "path_taken": "",
            "should_escalate": False,
            "needs_human": False,
            "iteration_count": 0,
            "rag_was_sufficient": False,
            "history": [turn.model_dump() for turn in request.history[-12:]],
            "user_id": user["id"] if user else None,
            "order_tool": order_tool,
            "request_id": http_request.state.request_id,
            "llm_calls": 0,
            "input_tokens": 0,
            "output_tokens": 0,
        }
        result = get_agent().invoke(initial_state)
        support_case_id = None
        answer = result.get("answer", "En saanut muodostettua vastausta.")
        auth_required = bool(result.get("auth_required", False))
        if result.get("create_support_case"):
            if user:
                case_question = result.get("standalone_question") or request.message
                case = _create_support_case(db, user["id"], case_question, result, request.message)
                support_case_id = case["id"]
                answer = "Selvä, asiakaspalvelun demokäsittelijä liittyy nyt tähän chattiin."
            else:
                auth_required = True
                answer = "Kirjaudu sisään, niin voin liittää tukipyynnön tiliisi."
        log_event(
            "agent_completed",
            request_id=http_request.state.request_id,
            user_id=user["id"] if user else None,
            intent=result.get("intent", "ambiguous"),
            route=result.get("path_taken", ""),
            tool="get_order_status" if result.get("order_status_checked") else None,
            fallback=bool(result.get("should_escalate")),
            support_case_created=bool(support_case_id),
            llm_calls=result.get("llm_calls", 0),
            input_tokens=result.get("input_tokens", 0),
            output_tokens=result.get("output_tokens", 0),
        )
        return ChatResponse(
            answer=answer,
            path=result.get("path_taken", "Selvennys"),
            should_escalate=bool(result.get("should_escalate", False)),
            support_case_id=support_case_id,
            auth_required=auth_required,
        )

    @app.post("/human-chat", response_model=ChatResponse)
    def create_support_request(
        request: ChatRequest,
        http_request: Request,
        user: dict = Depends(require_user),
        db: Database = Depends(get_db),
    ):
        """Compatibility endpoint: create a real case; it never simulates a human with an LLM."""
        case = _create_support_case(
            db,
            user["id"],
            request.message,
            {
                "intent": "personal_support",
                "path_taken": "Tukipyyntö",
                "escalation_reason": "order_support_requires_review",
                "request_id": http_request.state.request_id,
                "source_ids": [],
            },
        )
        return ChatResponse(
            answer="Tukipyyntösi on kirjattu asiakaspalvelun käsittelyjonoon. Käsittelijän vastaus näkyy tililläsi.",
            path="Tukipyyntö",
            should_escalate=True,
            support_case_id=case["id"],
        )

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
