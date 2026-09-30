# Koivu Store AI Agent

Koivu Store is a Finnish fashion-store demo with a product catalogue, hybrid retrieval, account-scoped demo orders, and a persisted human-support case workflow. LangGraph orchestrates the request; backend code controls which capabilities are available.

## What the demo does

- Classifies requests into product, order support, external information, or ambiguous intent using a Pydantic structured LLM response. A fixed Python allowlist selects the route.
- Answers product questions with Chroma vector retrieval, BM25, reciprocal-rank fusion, an evidence assessment, and a structured response whose source IDs are checked against retrieved documents.
- Routes public, current-information questions to Tavily when configured. Retrieved catalogue and web content are treated as untrusted data.
- Registers users with salted PBKDF2 password hashes and revocable server-side sessions in HttpOnly, SameSite cookies. Customers can see only their own demo orders and support cases.
- Customers can select an available product, colour, and size, submit the cart as a local demo order, and see its items and total under their account. The backend validates variants and calculates prices; no payment is collected.
- Exposes a narrow `get_order_status(order_id)` tool whose user identity is bound by the backend and whose database query checks order ownership.
- Offers staff review for personal or exceptional support requests and creates a case only after the signed-in customer confirms. A fixed, clearly labelled demo reply can make the human route visible in chat; a real operator can answer from the protected console using the server-side `SUPPORT_AGENT_API_KEY`. Customers can reset their own demo-case history.
- Logs request IDs, routes, durations, tool failures, and provider-reported token counts without logging prompt or response content.

The cart and favourites remain in browser storage. Checkout stores a synthetic order, selected items, colour/size variants, and server-calculated total in local SQLite for the signed-in account. It does not represent a paid purchase. The customer can see the order details and status in the account panel.

## Run locally

Use Python 3.12 and the dependencies in `backend/requirements.txt`. Create `backend/.env` from `.env.example` only if it does not already exist, then set the server-side OpenAI key. The Tavily key is optional. Keep support and catalog setup keys on the backend only.

On a new environment, create the virtual environment and install runtime plus test dependencies:

~~~powershell
Set-Location backend
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
~~~

From the repository root, start the API:

```powershell
Set-Location backend
..\backend\.venv\Scripts\python.exe -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

In another PowerShell window, start the static frontend:

```powershell
Set-Location frontend
..\backend\.venv\Scripts\python.exe -m http.server 5500 --bind 127.0.0.1
```

Open <http://127.0.0.1:5500/>. The API health endpoint is <http://127.0.0.1:8000/health>. If port 8000 is already occupied, run the API on port 8001 and open <http://127.0.0.1:5500/?apiPort=8001>.

The local Chroma catalogue is stored in `backend/chroma_db`. Catalog setup is an authenticated administrative operation because it can call the paid embeddings API. It requires `CATALOG_SETUP_API_KEY` and `OPENAI_API_KEY`; the browser does not call it. Do not reset or replace an existing Chroma directory casually.

Choose a product, colour, and size, add it to the cart, then select **Tilaa (demo)** to save an unpaid demo order to the signed-in account. To try the human branch, ask the assistant for staff help while signed in. The demo customer-service agent joins the same chat with a clearly labelled fixed reply; the request is also saved to the account case history. The protected operator console can review and answer persisted cases. See [security documentation](docs/security.md) for access boundaries and deployment limits.

## Tests and evaluations

From `backend/`, run the no-network unit and security suite:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -p "test_*.py" -v
```

From the repository root, check frontend JavaScript syntax:

```powershell
node --check frontend/store.js
```

The retrieval evaluation dataset and Recall@K, Precision@K, and MRR runner are documented in [docs/rag-evaluation.md](docs/rag-evaluation.md). Running vector or hybrid evaluation uses the configured embeddings provider and may incur API costs; the normal tests mock model/tool calls and do not make those requests.

## Documentation

- [Architecture overview](docs/architecture.md)
- [Detailed architecture design and request sequences](docs/architecture-design.md)
- [Security model and limitations](docs/security.md)
- [Privacy and data flows](docs/privacy.md)
- [Retrieval evaluation](docs/rag-evaluation.md)
- [Agent evaluation](docs/agent-evaluation.md)
- [Current system summary (Finnish)](docs/current-system.md)
- [Implementation summary and verification status](docs/implementation-summary.md)
- [Coding-agent instructions](AGENTS.md)

This remains a portfolio/demo system, not a production commerce service. Before real customer use, add abuse controls and rate limits, staff identities and audit attribution, operational alerting, secure deployment configuration, formal retention rules, and a real order-service integration.
