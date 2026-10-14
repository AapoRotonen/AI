# Architecture overview

Koivu Store is a local portfolio demo: a static Finnish storefront calls a FastAPI service that orchestrates LLM interpretation, catalogue retrieval, public web search, account-scoped demo-order lookup, and human support cases.

## Components

- `frontend/catalog.json` is the canonical public sample catalogue. `shop.html` and `product.html?id=...` render searchable categories and shareable product details; `about.html`, `shipping.html`, and `returns.html` explain the demo boundary. Account credentials are sent only to the backend; the browser receives an HttpOnly session cookie. Cart and favourites remain in browser storage.
- `backend/main.py` validates requests, resolves the session, injects authenticated identity into the workflow, owns API permissions, and persists user/order/support data.
- `backend/agent/` contains the typed intent and evidence schemas, LangGraph state, nodes, and hard-coded conditional routing.
- `backend/core/retrieval.py` combines persisted Chroma vector rankings with BM25 rankings built from both Chroma chunks and the current shared JSON catalogue, then fuses them with reciprocal-rank fusion (RRF). The JSON catalogue enters BM25 without paid embedding calls; old Chroma snapshots are not silently replaced.
- `backend/core/database.py` uses parameterized SQLite operations for local accounts, sessions, product-line demo orders, and support cases. `backend/core/catalog.py` loads the shared catalogue and `backend/core/orders.py` validates cart variants and server-side prices from it.
- `backend/core/payments.py` optionally creates Stripe-hosted Checkout Sessions using test-mode keys only, verifies webhook signatures against raw bodies, and supports idempotent order-state transitions. Azure deployment does not configure these optional secrets, so the hosted demo keeps test checkout disabled.
- `backend/evals/` and `backend/tests/` provide retrieval metrics, routing cases, API/security tests, and no-network unit tests.

## Request routes

| Intent | Application route | Permission boundary |
| --- | --- | --- |
| Product | Hybrid RAG → evidence assessment → cited structured answer | Catalogue content only |
| Style advice | RAG identifies the discussed Koivu item → Web search for outside-catalogue shoe/accessory suggestions when configured → stylist | Never claims an accessory is sold unless the catalogue confirms it |
| Order support | Login check → latest owned order (or referenced owned order); personal or exceptional issues can be offered human review, then create a case after confirmation | Tool receives the authenticated user ID; SQL filters by both order ID and owner ID |
| External | Tavily search → cited structured answer | Public search only; no order tool or customer data |
| Greeting | Deterministic greeting without a model call | No retrieval or tools |
| Ambiguous | Deterministic clarification | No retrieval or tools |

The classifier returns a Pydantic `Intent`; Python maps only known values to graph nodes. Invalid output and provider failures become clarification. No LLM-selected graph node or SQL statement is executed.

## Human review

The API stores a sanitized case only after a signed-in customer asks for or confirms human review. The chat polls the owner's case for a reply. A separate authenticated operator console can list, answer, and close cases using `SUPPORT_AGENT_API_KEY`. For local presentations, a signed-in customer asking for a person gets a fixed, clearly labelled canned demo reply automatically in the chat; it is not an LLM impersonating a real operator. The account view lets the owner cancel a local demo order, which deletes only that owner-scoped order. There is no notification service, SLA tracking, or per-operator identity.

## Local data boundaries

OpenAI receives chat messages/history for intent/evidence/answer calls and retrieval queries for embeddings. Tavily receives a question only on the external-search route. Passwords are stored as salted PBKDF2 hashes; session tokens are opaque, HttpOnly cookies while only their SHA-256 digests are stored. The order result is returned directly from the backend and is not passed back to the answer LLM. Request logs contain operational metadata, not chat content.

See [architecture-design.md](architecture-design.md) for detailed request sequences and diagrams, [security.md](security.md) for safeguards and limits, and [privacy.md](privacy.md) for the data-flow inventory.
