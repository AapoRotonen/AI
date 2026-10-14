# Koivu Store AI Agent

Koivu Store is a Finnish fashion-store demo with a product catalogue, hybrid retrieval, account-scoped demo orders, and a persisted human-support case workflow. LangGraph orchestrates the request; backend code controls which capabilities are available.

The catalogue has 18 sample products across knitwear, clothing, accessories, bags, and shoes. `frontend/catalog.json` is the single public product-data source for the storefront, product detail pages, backend order validation, and the deterministic BM25 catalogue corpus. The site includes separate category, product, about, shipping, and returns pages.

## What the demo does

- Classifies requests into product, order support, external information, or ambiguous intent using a Pydantic structured LLM response. A fixed Python allowlist selects the route.
- Answers product questions with Chroma vector retrieval, BM25, reciprocal-rank fusion, an evidence assessment, and a structured response whose source IDs are checked against retrieved documents.
- Adds the current sample catalogue to local BM25 on startup, so product details and new catalogue entries are searchable without embedding calls. The persisted Chroma index may still contain an older product corpus until it is deliberately refreshed.
- Routes public, current-information questions to Tavily when configured. Retrieved catalogue and web content are treated as untrusted data.
- Registers users with salted PBKDF2 password hashes and revocable server-side sessions in HttpOnly, SameSite cookies. Customers can see only their own demo orders and support cases.
- Customers can select an available product, colour, and size, save an unpaid demo order, or use the optional Stripe-hosted test checkout. The backend validates variants and calculates prices; only a signed test-mode webhook can mark a test order paid.
- Exposes a narrow `get_order_status(order_id)` tool whose user identity is bound by the backend and whose database query checks order ownership.
- Offers staff review for personal or exceptional support requests and creates a case only after the signed-in customer confirms. A fixed, clearly labelled demo reply can make the human route visible in chat; a real operator can answer from the protected console using the server-side `SUPPORT_AGENT_API_KEY`. Customers can reset their own demo-case history.
- Logs request IDs, routes, durations, tool failures, and provider-reported token counts without logging prompt or response content.

The cart and favourites remain in browser storage. The free demo-order path stores a synthetic order in local SQLite for the signed-in account. Optionally, a configured `sk_test_...` Stripe key opens Stripe-hosted test checkout; an HMAC-verified webhook updates the synthetic order status. Test checkout is disabled unless all three server settings (`STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`, `PUBLIC_APP_URL`) are configured, and live Stripe keys are rejected. This only exercises a payment flow in Stripe test mode; it does not charge real money, reserve live inventory, fulfill orders, or represent a real purchase. Product prices and availability are portfolio sample data.

## Run locally

Use Python 3.12 and the dependencies in `backend/requirements.txt`. Create `backend/.env` from `.env.example` only if it does not already exist, then set the server-side OpenAI key. The Tavily key is optional. Keep support, catalog setup, and Stripe test keys on the backend only. For Stripe test checkout, also set the webhook signing secret from a Stripe test-mode webhook endpoint and the public browser origin; never set a live Stripe key.

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

Open `http://127.0.0.1:5500/shop.html` for categories and search. Each item has a shareable `product.html?id=...` page. The about, shipping, and returns pages describe this prototype; their example terms are not real purchase or delivery promises.

The local Chroma index is stored in `backend/chroma_db`. The public catalogue is available to BM25 directly from `frontend/catalog.json`; this does not require an embedding call. The authenticated catalog setup operation can embed the demo-scope corpus and therefore requires `CATALOG_SETUP_API_KEY` and `OPENAI_API_KEY`. The browser does not call it. Do not reset or replace an existing Chroma directory casually.

Choose a product, colour, and size, add it to the cart, then save a free demo order or (when configured) open the Stripe test checkout. Stripe test mode simulates the payment flow without moving real money; use only Stripe's published test card numbers. To try the human branch, ask the assistant for staff help while signed in. The demo customer-service agent joins the same chat with a clearly labelled fixed reply; the request is also saved to the account case history. The protected operator console can review and answer persisted cases. See [security documentation](docs/security.md) for access boundaries and deployment limits.

## Tests and evaluations

From `backend/`, run the no-network unit and security suite:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -p "test_*.py" -v
```

From the repository root, check frontend JavaScript syntax:

```powershell
node --check frontend/store.js
node --check frontend/catalog-pages.js
node --check frontend/support-console.js
node --check frontend/app-config.js
```

For a local container smoke test when Docker is installed, build from the repository root with `docker build -t koivu-store:local .` and run `docker run --rm -p 8000:8000 --env-file backend/.env koivu-store:local`.

The retrieval evaluation dataset and Recall@K, Precision@K, and MRR runner are documented in [docs/rag-evaluation.md](docs/rag-evaluation.md). Running vector or hybrid evaluation uses the configured embeddings provider and may incur API costs; the normal tests mock model/tool calls and do not make those requests.

The optional checkout sends product names, quantities, euro amounts, and synthetic order/account references to Stripe's hosted Checkout in test mode. The application does not receive or store card details. Its local signature-verified webhook tests the order-state transition; it does not trigger real fulfillment.

For local setup and Stripe CLI webhook forwarding, see [Stripe test checkout](docs/stripe-test-checkout.md). The Azure workflow does not configure the Stripe settings, so the deployed test checkout remains disabled.

## Azure deployment

The repository includes a prepared Azure Container Apps deployment path. The app serves both the static storefront and FastAPI from one HTTPS origin so the existing HttpOnly/SameSite session cookie remains same-origin. Local development still defaults to SQLite and Chroma; the Azure target uses Cosmos DB serverless for durable demo accounts, sessions, orders and support cases, and a private Blob snapshot for Chroma.

Azure resources are **not** created on push or pull request. The separate GitHub Actions workflow is manual, has a `no`-by-default confirmation gate, and splits foundation provisioning from application deployment. Check each run's health and readiness results before sharing the app. Cosmos requests/storage, ACR Basic, Blob, logs, active container usage, and provider APIs can cost money.

- [Azure architecture and cost model](docs/azure/ARCHITECTURE.md)
- [Technical deployment and operations](docs/azure/DEPLOYMENT.md)
- [Azure deployment checklist](docs/azure/CHECKLIST.md)

Do not dispatch the `foundation` stage until you accept the possible Cosmos DB/registry charges and configure a Cost Management budget. Alerts do not stop billing. Review the architecture and deployment documents before provisioning.

## Documentation

- [Architecture overview](docs/architecture.md)
- [Detailed architecture design and request sequences](docs/architecture-design.md)
- [Security model and limitations](docs/security.md)
- [Privacy and data flows](docs/privacy.md)
- [Retrieval evaluation](docs/rag-evaluation.md)
- [Agent evaluation](docs/agent-evaluation.md)
- [Current system summary (Finnish)](docs/current-system.md)
- [Implementation summary and verification status](docs/implementation-summary.md)
- [Azure architecture](docs/azure/ARCHITECTURE.md)
- [Azure operations](docs/azure/DEPLOYMENT.md)
- [Azure deployment checklist](docs/azure/CHECKLIST.md)
- [Coding-agent instructions](AGENTS.md)

This remains a portfolio/demo system, not a production commerce service. Before real customer use, add abuse controls and rate limits, staff identities and audit attribution, operational alerting, secure deployment configuration, formal retention rules, and a real order-service integration.
