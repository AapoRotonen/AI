"""
main.py - FastAPI backend

ENDPOINTIT:
GET  /health        - Palvelimen tila
POST /chat          - AI-asiakaspalveluagentti
POST /human-chat    - "Ihmis"-asiakaspalvelija (toinen botti eri persoonalla)
POST /setup         - Lataa tuotekatalogi RAG-tietokantaan
GET  /products/count - Kuinka monta tuotetietoa on ladattu

KÄYNNISTYS:
uvicorn main:app --reload --port 8000

FRONTEND kutsuu tätä osoitteesta:
http://localhost:8000
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Literal
from pathlib import Path

from agent.graph import get_agent
from agent.state import AgentState
from core.retrieval import get_retriever
from core.config import get_settings

settings = get_settings()

app = FastAPI(title="Koivu Store AI API", version="1.0.0")

# Kehityskäytössä salli vain omat paikalliset frontend-osoitteet.
# Julkaisuympäristössä aseta CORS_ALLOWED_ORIGINS täsmälliseen frontend-osoitteeseen.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in settings.cors_allowed_origins.split(",") if origin.strip()],
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


class ChatTurn(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(max_length=4000)


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    history: list[ChatTurn] = Field(default_factory=list, max_length=12)


class ChatResponse(BaseModel):
    answer: str
    path: str
    should_escalate: bool


@app.get("/health")
def health():
    retriever = get_retriever()
    return {
        "status": "ok",
        "products_loaded": retriever.get_count()
    }


@app.post("/setup")
def setup_knowledge_base():
    """
    Lataa tuotekatalogi RAG-tietokantaan.
    Tätä kutsutaan kerran ennen kuin chattiä voi käyttää.
    """
    retriever = get_retriever()

    # Jos jo ladattu, ei ladata uudelleen
    if retriever.get_count() > 0:
        return {"message": "Tuotekatalogi jo ladattu", "chunks": retriever.get_count()}

    products_file = Path("data/products.txt")
    if not products_file.exists():
        return {"error": "data/products.txt ei löydy"}

    text = products_file.read_text(encoding="utf-8")
    count = retriever.add_text(text, source="products.txt")
    return {"message": f"Ladattu {count} tuotetietoa", "chunks": count}


@app.get("/products/count")
def products_count():
    return {"count": get_retriever().get_count()}


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    """
    AI-asiakaspalveluagentti.
    Hakee ensin tuotekatalogista, sitten webistä, lopuksi eskaloi.
    """
    agent = get_agent()

    initial_state: AgentState = {
        "question": request.message,
        "rag_results": [],
        "web_results": [],
        "answer": "",
        "path_taken": "RAG",
        "should_escalate": False,
        "needs_human": False,
        "human_mode": False,
        "iteration_count": 0,
        "rag_was_sufficient": False,
        "history": [turn.model_dump() for turn in request.history[-12:]],
    }

    result = agent.invoke(initial_state)

    return ChatResponse(
        answer=result.get("answer", "Jokin meni pieleen."),
        path=result.get("path_taken", "RAG"),
        should_escalate=result.get("should_escalate", False)
    )


@app.post("/human-chat", response_model=ChatResponse)
def human_chat(request: ChatRequest):
    """
    "Ihmis"-asiakaspalvelija - sama GPT-4o mutta eri persoona.
    Frontend kutsuu tätä kun käyttäjä klikkaa "Yhdistä ihmiseen".
    """
    agent = get_agent()

    initial_state: AgentState = {
        "question": request.message,
        "rag_results": [],
        "web_results": [],
        "answer": "",
        "path_taken": "Ihminen",
        "should_escalate": False,
        "needs_human": False,
        "human_mode": True,   # Tämä aktivoi Maija-demon persoonan
        "iteration_count": 0,
        "rag_was_sufficient": False,
        "history": [turn.model_dump() for turn in request.history[-12:]],
    }

    result = agent.invoke(initial_state)

    return ChatResponse(
        answer=result.get("answer", "Jokin meni pieleen."),
        path="Ihminen",
        should_escalate=False
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
