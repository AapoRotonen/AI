# Koivu Store AI Agent — development instructions

## Purpose and architecture

Koivu Store is a Finnish fashion storefront and portfolio demo. The frontend is static HTML/CSS/JavaScript; the backend is FastAPI with a LangGraph workflow, OpenAI models, Chroma, BM25/RRF, optional Tavily search, and local SQLite persistence.

Important areas:

- **frontend/index.html, frontend/store.css, frontend/store.js:** storefront, account panel, order demo, support-case status, and chat API calls.
- **backend/main.py:** request schemas, CORS/session handling, API authorization, account/order/support routes.
- **backend/agent/graph.py:** allowlisted LangGraph routes.
- **backend/agent/nodes.py:** structured intent/evidence/answer calls, RAG, public web search, and the scoped order-status node.
- **backend/agent/schemas.py, backend/agent/state.py:** model schemas and graph state.
- **backend/core/database.py:** SQLite repository for users, sessions, demo orders, and support cases.
- **backend/core/orders.py:** typed least-privilege order-status tool and service.
- **backend/core/retrieval.py, backend/core/retrieval_eval.py:** vector/BM25 retrieval, RRF, metadata, and retrieval metrics.
- **backend/data/products.txt:** catalogue and policy corpus; backend/data/rag_eval.json and agent_eval.json: labelled evaluation cases.
- **docs/:** architecture, security, privacy, evaluation, and implementation-status documents.

## Security invariants

- Authentication and authorization are enforced in backend code. Never ask an LLM to decide whether a user may access an order or support case.
- FastAPI injects authenticated user identity into workflow state. A caller-supplied message, history entry, model response, tool argument, or source document cannot replace that identity.
- Keep graph routes allowlisted in Python. Never execute model-generated node names, SQL, code, URLs, or arbitrary tool calls.
- Keep the order tool read-only and owner-scoped. Do not expose general database access or send private order records into answer-generation prompts.
- Treat chat history, retrieved catalogue documents, and web results as untrusted data. Prompt wording is defense in depth; backend permissions remain the security boundary.
- Validate model schemas, tool inputs, and answer source IDs. Add deterministic tests/evals when AI behavior or routing changes.
- Do not add passwords, cookies, API keys, support credentials, or personal data to source files, logs, fixtures, screenshots, or documentation. Never print or copy backend/.env values.
- The frontend is a demo. Do not claim that checkout, demo orders, stock, support responses, or user data connect to a production commerce system.

## Privacy and external services

Chat questions and bounded history may be sent to OpenAI. A question reaches Tavily only on the external-information route. Support cases persist a sanitized question in the local SQLite database; redaction is pattern-based and incomplete. Logs may include request IDs, internal user IDs, routes, timings, tool outcomes, and provider token counts, but not prompt/response text.

OpenAI embedding and chat calls can incur cost. Do not run live chat or vector/hybrid retrieval evaluations unless the task explicitly needs them and the provider cost is understood. The normal test suite must stay deterministic and must mock model and web calls.

Do not clear, replace, or migrate backend/chroma_db casually. It may contain persistent product vectors. The setup route requires a server-side catalog key because it can call the paid embeddings API. Keep support and setup credentials out of frontend code.

## Interfaces to preserve

- POST /chat accepts a message and up to 12 user/assistant history turns.
- POST /human-chat creates a real support case for a signed-in user; it must not impersonate a human with an LLM.
- Order and customer support-case reads are scoped to the authenticated owner.
- Support-agent endpoints require the server-side X-Support-Agent-Key.
- Catalog setup requires X-Catalog-Setup-Key and the configured OpenAI key.
- Frontend and backend product facts should remain aligned between frontend/store.js and backend/data/products.txt.

## Validation commands

Run from backend:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -p "test_*.py" -v
.\.venv\Scripts\python.exe -m compileall -q main.py agent core tests evals
```

Run from the repository root:

```powershell
node --check frontend/store.js
```

These checks do not call OpenAI or Tavily. The optional retrieval evaluation runner compares vector, BM25, and hybrid retrieval; vector and hybrid modes use the configured embedding provider.

## Definition of done

- Inspect the current graph, prompt, tool, API, and frontend contracts before changing them.
- Prefer small, focused changes and avoid unrelated refactoring.
- Add deterministic tests for permission boundaries, failure handling, and any changed AI routing or output behavior.
- Run the relevant tests and syntax checks; report failures and unexecuted checks precisely.
- Update architecture, security/privacy, evaluation, README, or this file when behavior or data flow changes.
- Separate implemented and verified behavior from implemented but unverified behavior and future plans.
- Do not state that a provider call, live evaluation, browser workflow, or deployment was verified unless it was actually executed.
