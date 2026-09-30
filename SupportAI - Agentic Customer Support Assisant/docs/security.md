# Security notes

This is a proof of concept, not a security-certified or production-ready system.

## Assets

- Customer and ticket details (synthetic in this repository).
- Support account credentials and bearer tokens.
- Internal knowledge and service status.
- Ticket state and human approval records.
- Database credentials and model API key supplied through environment variables.

## Actors and trust boundaries

| Actor/component | Trust level | Main authority |
|---|---|---|
| Support agent | Authenticated, limited | Assigned tickets; create proposals |
| Senior support | Authenticated, broader | Read tickets; approve/reject another person's proposal |
| Admin | Authenticated, administrative | Broad access and protected Actuator endpoints |
| Browser/user message | Untrusted input | No authority by itself |
| LLM and tool arguments | Untrusted | May request a tool; cannot authorize access |
| Ticket/knowledge text | Untrusted data | Evidence only, never executable instructions |
| Domain services/database | Trusted enforcement point | Apply access and state rules |

## Authentication and authorization

Passwords are hashed with BCrypt. Login returns a signed HMAC JWT with an eight-hour expiry; `JWT_SECRET` must be at least 32 bytes. Spring Security validates JWT issuer, signature, and expiry. Regular support agents see only assigned tickets. Customer and order lookup requires a ticket ID and passes through the ticket authorization service. Unauthorized ticket IDs return a generic not-found response. Review decisions require a senior/admin role and a reviewer distinct from the proposal author.

Both REST and AI call the same service methods. Controller role annotations are defense in depth, not the sole authorization boundary.

## Least privilege and AI tools

Seven tools expose specific reads and one review proposal. No arbitrary customer enumerator, repository, SQL, shell, filesystem, generic HTTP, refund, credit, or direct ticket-write tool exists. The request budget is eight tool executions. `proposeTicketAction` accepts only `CLOSE_TICKET`; Java creates a pending review. The model has no approval tool.

## Prompt injection and indirect injection

User prompts, ticket descriptions/history, and retrieved documents can contain malicious instructions. The system prompt says to treat those strings as data, but prompts are not a security control. Every ticket read is authorized in Java. The knowledge tool returns policy text only and cannot alter role checks, expose repositories, or execute instructions. The regression dataset contains direct and indirect injection cases; live-model refusal behavior is not measured here.

## Data leakage and privacy controls

Only a ticket the current user may access can be returned. The customer tool returns name/ID only. Order lookups are ticket-scoped. Logs/audit omit prompts, tool output bodies, credentials, and reasoning. The assistant uses a generic model-failure message. Spring AI tool arguments/results are not explicitly enabled for logs.

## Secret handling

`.env` and private key files are ignored. `OPENAI_API_KEY`, database password, and JWT secret are environment configuration. The checked-in `.env.example` values are placeholders/local demo settings only; `supportai-disabled` is a sentinel, not a credential, and disables actual model/embedding calls. The included demo passwords are intentionally convenient defaults and must be overridden before sharing a running instance. Never send secrets to the model.

Docker Compose requires non-empty database and JWT secrets, binds host ports to loopback only, and runs the app container read-only as an unprivileged user with all Linux capabilities dropped, a bounded temporary filesystem, and `no-new-privileges`. These are local PoC safeguards; do not expose the application or database to an untrusted network.

## Dependency scan triage

Trivy 0.74.0 scanned both rebuilt images on 2026-09-30:

- The application image has one high report for `io.modelcontextprotocol.sdk:mcp-core` 0.18.3 (CVE-2026-35568). The [upstream advisory](https://github.com/modelcontextprotocol/java-sdk/security/advisories/GHSA-8jxr-pr72-r468) says Spring AI is not affected because it validates `Origin`, and this app does not expose MCP server endpoints. Reassess this when changing Spring AI or adding MCP endpoints.
- The PostgreSQL image still has 2 critical and 82 high reports after upgrading all Debian Trixie packages available during the build. The critical libxml2 report, CVE-2026-6653, has no fix in Debian Trixie at scan time; the [Debian tracker](https://security-tracker.debian.org/tracker/CVE-2026-6653) classifies it as a minor issue. Trivy also flags Go standard-library CVEs embedded in `gosu`; its [upstream security policy](https://github.com/tianon/gosu/blob/master/SECURITY.md) says to check whether the vulnerable Go functionality is actually used.

The database is bound to loopback and this PoC uses synthetic data. These remaining image findings make the database image unsuitable for production or an untrusted network. Re-scan and review them before deploying or using real data.

## Human approval

Only a distinct senior/admin user can approve or reject a pending proposal. The policy and supported action are determined in Java. Approval and ticket close occur in a service transaction. AI cannot approve itself or write ticket state directly.

## Lightweight threat model

| Threat | PoC mitigation | Residual limitation |
|---|---|---|
| Agent asks model to enumerate records | No enumeration tool; scoped service checks | Other agent endpoints need future coverage/tests |
| Model calls another agent's ticket ID | Ticket service authorization; generic 404 | Requests may still reveal response timing |
| Prompt injection in policy/ticket text | Data-only treatment plus server-side authorization | LLM may produce misleading prose; requires live eval/human judgment |
| AI closes ticket without approval | Proposal-only tool; distinct human review | Only one action policy implemented |
| JWT disclosure | HTTPS is expected outside localhost; token is short-lived | UI stores token in localStorage; no revocation/refresh flow |
| Credential brute force | BCrypt | Rate limiting and lockout not implemented |
| Secret committed accidentally | `.gitignore`, environment configuration | Manual secret scan still required before every commit |
| Database disclosure | No real PII; local Docker DB | No production encryption/backup/retention configuration |

## Known limitations

This PoC lacks OIDC, CSRF-bound cookie sessions, token revocation, rate limiting, formal penetration testing, deployment TLS/proxy policy, audit retention/immutability, key rotation, per-field access control, and real-provider privacy review. It must not be treated as production safe.
