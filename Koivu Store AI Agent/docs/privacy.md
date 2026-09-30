# Privacy and data flows

This is a technical description of the current demo, not a legal privacy notice. Do not enter real customer information until the controller, legal basis, retention schedule, processor agreements, data transfers, and user notice have been reviewed and documented.

## Data inventory

| Data | Destination | Current handling |
| --- | --- | --- |
| Registration email and password | FastAPI → local SQLite | Email is stored for the account; password is stored only as a salted PBKDF2 hash. The password is not sent to an LLM. |
| Session cookie | Browser → FastAPI | Random opaque token in an HttpOnly, SameSite cookie; the backend stores only its SHA-256 digest and expiry. It is not included in chat prompts or logs. |
| Chat message and up to 12 prior turns | Browser → FastAPI → OpenAI | Sent for semantic intent/evidence/answer calls. History is bounded and remains in the browser during the current page session; the app does not persist it as a conversation. A user can still type personal information into chat, so the UI discourages that. |
| Product retrieval query and catalogue | Backend → OpenAI embeddings; catalogue also in local Chroma | The query is embedded for vector search. The local catalogue is embedded when an authorized operator initializes it. |
| Order reference | Chat classifier, then backend order service | The reference can be part of the user message sent to the classifier. The order lookup result is read locally and returned directly; customer/order records are not added to the answer-generation context. |
| Tavily query/results | Backend → Tavily, only on external-information route | Current question is included in the web search request. Web results are untrusted context for the answer model. |
| Support case | Local SQLite; visible to owner and support-key holders | The question is redacted for common email, phone, long numeric card-like, and token-like values. A minimal route/intent/source-ID context is stored. An operator reply is persisted for the customer. Cases remain until manually managed; there is no automatic retention/deletion job. |
| Demo orders | Browser cart → FastAPI → local SQLite | Synthetic `ORD-...` reference, status, selected product/colour/size/quantity lines, and server-calculated total; orders are scoped to the account. No payment is taken and this is not a real purchase. |
| Cart and favourites | Browser `localStorage` | Stored locally by the existing storefront, independent of backend accounts. |
| Operational logs | Backend process logs | Request ID, method/path, status, duration, route, tool outcome, and provider-reported token counts. Chat text, model response text, passwords, cookies, and API keys are not logged by application events. Infrastructure/hosting logs may differ. |
| Product images | Unsplash URLs | The browser requests image URLs from Unsplash, which receives ordinary network request metadata. |

## Access and retention

Backend code performs authentication and ownership checks before order or case reads. Customer queries are owner-scoped in parameterized SQL. The support operator API can read sanitized case content using `SUPPORT_AGENT_API_KEY`. Accounts, sessions, orders, and cases live in the local SQLite file configured by `DATABASE_PATH`; there is no automatic purge policy. Operators must currently manage the local database and its retention themselves.

OpenAI and Tavily retention, processing location, and account terms depend on the configured provider accounts and settings. They are not inferred from this repository. Confirm provider terms and data-processing arrangements before processing real customer data.

## Privacy limitations

- User messages and bounded conversation history are sent to OpenAI; input redaction is not performed before those calls.
- Support redaction is pattern-based and can miss or over-redact information. It is a minimization aid, not a complete PII detector.
- No retention/deletion UI, export workflow, account deletion endpoint, or privacy-request process exists yet.
- The browser store does not implement payment, customer accounts for purchases, or real orders.
- The frontend notice and this document are demo disclosures; they do not replace a legally reviewed privacy notice.
