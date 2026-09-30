# Security

Koivu Store is a local portfolio demo, not a production commerce service. Do not send real customer information or deploy the API publicly without a separate security review.

## Current controls

- Authentication uses salted password hashes and revocable HttpOnly sessions.
- Backend queries enforce ownership for orders and support cases.
- The order tool is read-only and receives the authenticated user identity from FastAPI.
- Support review and paid catalog initialization use separate server-side API keys.
- Intent/evidence/answer model responses are structured and validated; graph routes are allowlisted in Python.
- Retrieved catalogue and web content are treated as untrusted input.
- Application logs exclude prompts, passwords, cookies, and API-key values.

## Before deployment

The demo does not yet have rate limits, account lockout, MFA, per-operator staff identity, automated retention, encrypted database storage, backups, email verification, or a staff dashboard. Deploy only behind HTTPS, set COOKIE_SECURE=true, use exact CORS origins and a secrets manager, protect costly endpoints, and connect a real order service only after its authorization contract is reviewed.

For detailed controls, API access rules, limitations, and reporting guidance, see [docs/security.md](docs/security.md).
