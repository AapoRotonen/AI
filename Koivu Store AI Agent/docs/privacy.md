# Privacy and data flows

This is a technical description of the current demo, not a legal privacy notice. Do not enter real customer information until the controller, legal basis, retention schedule, processor agreements, data transfers, and user notice have been reviewed and documented.

## Data inventory

| Data | Destination | Current handling |
| --- | --- | --- |
| Registration email and password | FastAPI → local SQLite locally; prepared Azure mode uses Cosmos DB for NoSQL | Email is stored for the account; password is stored only as a salted PBKDF2 hash. The password is not sent to an LLM. The Azure database starts empty; local records are not migrated. |
| Session cookie | Browser → FastAPI | Random opaque token in an HttpOnly, SameSite cookie; the backend stores only its SHA-256 digest and expiry. Local mode uses SQLite. Prepared Azure mode stores the digest/expiry in Cosmos DB with TTL. Production cookie is `Secure` over the same HTTPS origin. The token is not included in chat prompts or logs. |
| Chat message and up to 12 prior turns | Browser → FastAPI → OpenAI | Sent for semantic intent/evidence/answer calls. History is bounded and remains in the browser during the current page session; the app does not persist it as a conversation. A user can still type personal information into chat, so the UI discourages that. |
| Product retrieval query and catalogue | Backend → OpenAI embeddings; catalogue also in local Chroma | The query is embedded for vector search. The local catalogue is embedded when an authorized operator initializes it. |
| Order reference | Chat classifier, then backend order service | The reference can be part of the user message sent to the classifier. The order lookup result is read locally and returned directly; customer/order records are not added to the answer-generation context. |
| Tavily query/results | Backend → Tavily, only on external-information route | Current question is included in the web search request. Web results are untrusted context for the answer model. |
| Support case | Local SQLite; prepared Azure mode uses Cosmos DB | The question is redacted for common email, phone, long numeric card-like, and token-like values. A minimal route/intent/source-ID context is stored. An operator reply is persisted for the customer. Reads are owner-scoped for customers. The public demo operator console is protected by one shared server-side key, not per-person accounts; there is no operator attribution/audit history. Cases remain until manually managed; there is no automatic retention/deletion job. |
| Demo orders and optional Stripe test checkout | Browser cart → FastAPI → local SQLite; prepared Azure mode uses Cosmos DB; optionally FastAPI → Stripe-hosted Checkout in test mode | Synthetic order reference, status, selected product/colour/size/quantity lines, server-calculated total, and test Checkout session ID are stored on the account-scoped order. Product names, quantities, amounts, and synthetic order/account references are sent to Stripe. Card details are entered on Stripe's hosted page and are not handled or stored by this application. Only a verified test webhook can mark an order `paid`; this is not a real purchase or fulfillment. |
| Cart and favourites | Browser `localStorage` | Stored locally by the existing storefront, independent of backend accounts. |
| Operational logs | Backend process logs; prepared Azure target forwards container logs to Log Analytics | Request ID, method/path, status, duration, route, tool outcome, and provider-reported token counts. Chat text, model response text, passwords, cookies, and API keys are not logged by application events. The proposed workspace retention is 30 days. Azure platform logs can contain additional operational metadata and may be subject to separate settings. |
| Chroma index snapshot | Local Chroma; prepared Azure mode stores a private ZIP in Azure Blob Storage and restores it into ephemeral container storage | The current corpus is the versioned product/policy file. The deployment snapshot contains Chroma index files and a SHA-256 manifest; it should not contain customer records. Older versioned ZIPs remain until an operator removes them. |
| Product images | Unsplash URLs | The browser requests image URLs from Unsplash, which receives ordinary network request metadata. |

## Access and retention

Backend code performs authentication and ownership checks before order or case reads. Local customer queries are owner-scoped in parameterized SQL; the Cosmos implementation partitions the same operations by the authenticated owner ID. The support operator API can read sanitized case content using `SUPPORT_AGENT_API_KEY`. Local accounts, sessions, orders, and cases live in SQLite configured by `DATABASE_PATH`; Azure mode stores them in a Cosmos account in the selected region. The Azure configuration uses single-region Cosmos serverless and private Blob storage; the current resource and deployment state is specific to the target subscription. The operator manages case/order retention; sessions expire after the configured TTL. A customer can reset only their own demo support cases. There is no account deletion endpoint.

OpenAI and Tavily retention, processing location, and account terms depend on the configured provider accounts and settings. They are not inferred from this repository. Confirm provider terms and data-processing arrangements before processing real customer data.

For an Azure deployment, the selected Azure region determines the primary region for Cosmos data and Blob snapshot storage. The app also sends chat messages/history and product queries to OpenAI, and routes selected current/public questions to Tavily. Their processing locations and retention are controlled by those provider accounts and are not guaranteed by the Azure region. Azure Container Apps receives the inbound HTTPS request, and operational logs are sent to the configured Log Analytics workspace. Review the actual portal settings and provider terms before entering personal data.

## Privacy limitations

- User messages and bounded conversation history are sent to OpenAI; input redaction is not performed before those calls.
- Support redaction is pattern-based and can miss or over-redact information. It is a minimization aid, not a complete PII detector.
- No retention/deletion UI, export workflow, account deletion endpoint, or privacy-request process exists yet.
- The browser store has an optional Stripe test-mode checkout, but no live payment capability, inventory reservation, fulfillment, or production commerce integration. Test checkout is disabled unless test-only server settings are provided.
- The frontend notice and this document are demo disclosures; they do not replace a legally reviewed privacy notice.
