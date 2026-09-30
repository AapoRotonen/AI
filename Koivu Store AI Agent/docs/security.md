# Security model

This is a local portfolio demo. Its security controls demonstrate boundaries in application code; they do not make the service ready for public deployment.

## Threat model

Assume a caller can send arbitrary chat text, forge browser conversation history, ask the model to reveal instructions, submit prompt-injection text, and guess another customer's order or case identifier. Catalogue documents and Tavily pages may also contain hostile instructions. The LLM can misclassify, misunderstand, or generate invalid content.

## Implemented controls

- **Authentication:** email/password registration; minimum 12-character password; salted PBKDF2-HMAC-SHA256 password hashes; generic login failures. Successful login creates a random, revocable server-side session. Only a digest of the cookie token is stored.
- **Cookie and browser boundary:** session cookie is `HttpOnly`, `SameSite=Strict`, and `Secure` is configurable for HTTPS deployments. CORS permits only configured exact origins and credentialed requests.
- **Authorization:** order listing, support-case status, and ticket creation require a valid session. Repository methods scope order queries by both the requested ID and authenticated owner ID. Missing and foreign orders produce the same result. Customers can read only their own cases.
- **Least-privilege tool:** `get_order_status` accepts only a validated order reference. The API binds the authenticated user ID to the tool before graph execution. The tool cannot list orders, execute SQL, or mutate order state.
- **Support operations:** case review/reply/close endpoints require `X-Support-Agent-Key`; when no key is configured, they return `503`. The catalog setup endpoint similarly requires `X-Catalog-Setup-Key` because initialization may incur embedding costs.
- **Structured model output:** intent, evidence assessment, and answer use Pydantic schemas. Python performs route allowlisting and checks answer source IDs against retrieved IDs. Invalid outputs fail to clarification or escalation.
- **Prompt injection:** system prompts identify user history, retrieved catalogue text, and web content as untrusted data. More importantly, those sources cannot grant database access or alter the backend's user identity or SQL ownership checks.
- **Validation and privacy:** API fields and lengths are bounded. Support text is redacted for common email, phone, long card-number, and token-like values before persistence. HTTP/event logs omit message bodies, credentials, and model reasoning.

## Protected API surface

| Route | Access |
| --- | --- |
| `POST /auth/register`, `POST /auth/login`, `POST /auth/logout`, `GET /auth/me` | Public login operations; logout invalidates the current session |
| `GET /orders`, `POST /orders`, `DELETE /orders/{id}` | Authenticated customer; order creation validates server-side product/variant/price data; listing and cancellation are owner-scoped |
| `POST /chat` | Public product chat; order lookup is available only with a valid session |
| `POST /human-chat`, `GET /support/my-cases`, `GET /support/cases/{id}`, `POST /support/my-cases/{id}/demo-reply` | Authenticated customer; creates or reads only own cases. Demo replies are fixed text and marked as simulated. |
| `GET /support/cases`, `POST /support/cases/{id}/reply`, `POST /support/cases/{id}/close` | `X-Support-Agent-Key` |
| `POST /setup` | `X-Catalog-Setup-Key` and configured OpenAI key |

## Known limits before deployment

- There is no rate limit, account lockout, email verification, password reset, MFA, CSRF token, or abuse/cost quota. SameSite cookies and exact CORS origins reduce browser cross-site exposure but are not a substitute for a full deployment review.
- `SUPPORT_AGENT_API_KEY` is a shared operator credential, so the demo cannot attribute actions to individual staff members. It must be random, server-side, and rotated if exposed.
- SQLite is local single-service persistence without encryption-at-rest, managed backups, retention automation, or multi-instance coordination.
- API keys must not be exposed to the browser. Set `COOKIE_SECURE=true` behind HTTPS, use a secrets manager, configure exact frontend origins, rate-limit costly endpoints, and review provider agreements before real customer data is used.
- Source-ID validation proves only that an answer cited a retrieved source. It does not prove every semantic claim is entailed by that source. Model-backed factual quality still needs human-reviewed evaluations.
- The demo order store is not connected to payment, fulfillment, or a real commerce system.
