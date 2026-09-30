# Implementation summary

## Previous architecture

The original application already had a FastAPI backend, a LangGraph workflow, an intent classifier before RAG, Chroma vector retrieval, BM25, RRF, optional Tavily search, a browser storefront, and six mocked route tests. The classifier parsed free-form label text. Order requests went to a generic escalation response, and the follow-up “Maija” path used another LLM persona. There were no user accounts, authorization checks, order service, persisted support cases, labelled retrieval metrics, or request-level observability.

## Limitations identified

- Model outputs were parsed from strings and classifier exceptions could fail a chat request.
- Chat routes were anonymous and could initiate paid provider calls.
- No database represented users, sessions, orders, or human-support cases.
- The simulated human path did not create work a human could review.
- RAG used hybrid ranking but had no benchmark or source-ID validation in the answer path.
- The project had no agent evaluation dataset, API security suite, CI workflow, or technical architecture documentation.

## Implemented and verified

### Agent and routing

- Added typed Pydantic intent, evidence, and answer schemas.
- Kept graph routing in an explicit Python allowlist; malformed/unknown intent output and classifier exceptions fall back to clarification.
- Added a login-required route for private order requests, a structured evidence decision, bounded untrusted-context prompts, and answer source-ID validation.
- Added deterministic safe fallbacks for unsupported evidence, invalid citations, model failures, Tavily failures, and order-tool failures.

### Authentication, authorization, and orders

- Added SQLite tables and repository methods for accounts, hashed sessions, demo orders, and support cases.
- Added salted PBKDF2 password hashes and opaque HttpOnly/SameSite sessions; only SHA-256 token digests are stored.
- Added account registration/login/logout/current-user endpoints and frontend account UI.
- Added local demo-order creation and owner-scoped listing.
- Added a validated, read-only order-status tool with the authenticated user ID bound by the backend. The SQL lookup filters by both order and owner; foreign and missing orders have the same response.

### Human review

- Replaced the Maija persona with persisted support cases. The signed-in customer can see case status and the human response.
- Added support-operator list/reply/close routes protected by a server-side shared key and a local protected operator console. The demo chat reply is fixed and labelled; there is no live staff notification channel.
- Redact common email, phone, long numeric, and token-like strings in stored case text.

### RAG, tests, evaluation, and observability

- Preserved Chroma + BM25 + RRF; added product-code metadata to new product chunks and retrieval modes for vector-only, BM25-only, and hybrid comparison.
- Added a labelled Finnish product-query set and Recall@K, Precision@K, and MRR functions. Added an opt-in runner for provider-backed vector/hybrid evaluation.
- Added route, API/auth, order-ownership, prompt-injection, safe-failure, RRF, and metric tests. The suite uses standard-library unittest and mocks external model/web calls.
- Added request IDs, no-store headers for account/order/support/chat responses, and structured logs for route, duration, tool/fallback outcome, and provider token usage without prompt/answer content.
- Added GitHub Actions checks for Python compile, deterministic unit tests, and frontend JavaScript syntax.

### Privacy and AI-native development

- Added technical data-flow and security documents, architecture diagrams, evaluation instructions, a repository coding-agent guide, and a user-facing demo privacy page.
- Updated README and root security/privacy summaries. Added SQLite files to .gitignore and test-only HTTPX to backend/requirements-dev.txt.

## Files/components added or changed

### Added

- Backend: core/database.py, core/security.py, core/orders.py, core/observability.py, core/retrieval_eval.py, agent/schemas.py, evals/run_retrieval.py, evals/__init__.py.
- Data: data/agent_eval.json and data/rag_eval.json.
- Tests: test_api_security.py, test_agent_evals.py, test_agent_safety.py, and test_retrieval_evaluation.py; test_agent_routing.py was expanded.
- Project: backend/requirements-dev.txt, .github/workflows/ci.yml, and docs/architecture.md, docs/architecture-design.md, docs/security.md, docs/privacy.md, docs/rag-evaluation.md, docs/agent-evaluation.md.

### Modified

- Backend API, graph, node, state, configuration, and retrieval files; backend/.env.example and the root .gitignore.
- Frontend index, store JavaScript/CSS, and privacy page.
- README.md, SECURITY.md, PRIVACY.md, and AGENTS.md.

## Security improvements

Authentication, session storage, order ownership, customer case ownership, staff API-key checks, catalog-setup key checks, bounded inputs, untrusted-context prompts, and source-ID validation are enforced or checked in backend code. This is a demo foundation, not a production security certification.

## Privacy improvements

Passwords and session tokens are not stored in plaintext. Application event logs omit message and answer text. Order records are not sent to the answer-generation model. Support cases receive pattern-based redaction before persistence. The remaining provider data flow and retention limitations are documented in docs/privacy.md.

## RAG and agent improvements

The system preserves hybrid retrieval, exposes three retrieval methods to the evaluation runner, adds stable product identifiers for new ingestion, requires typed evidence assessment, and validates generated citations against the retrieved set. The classifier still uses a hosted LLM and semantic source entailment is not mechanically proven.

## Testing and verification status

### Verified locally on 2026-09-30

- The complete deterministic unittest suite passed: 41 tests. Model and web calls are mocked; API tests use temporary SQLite databases.
- Python compileall passed for the backend, tests, and evaluation runner.
- Node syntax checks passed for frontend/store.js and frontend/support-console.js.
- git diff --check passed.
- No live OpenAI or Tavily calls, provider-backed retrieval evaluation, production deployment, or GitHub Actions run was performed.

## Remaining limitations

- No rate limit, login lockout, email verification, password reset, MFA, CSRF token workflow, account deletion, retention job, encrypted database, managed backup, or multiserver session store.
- The support operator key is shared and actions are not attributable to individual staff users. Cases are polled through an API; there is no notification or SLA.
- The order database contains only synthetic fixture orders, not commerce or payment data.
- Pattern-based case sanitization is incomplete. Chat messages/history may contain personal information and are sent to OpenAI; Tavily receives the question on the external route.
- Source-ID validation checks that references were supplied, not that every generated claim is semantically entailed.
- The existing Chroma collection is preserved. Existing stored metadata is not migrated; product-code fallback is derived from retrieved text.

## Planned / future work

- Connect a real order-service adapter only after defining its authentication, authorization, and data-minimization contract.
- Add per-operator staff identities, audit attribution, case notifications, retention/deletion controls, rate limits, and production secrets management.
- Expand and manually review retrieval/groundedness cases, record live provider scores in an explicitly opted-in evaluation, and add deployment integration tests.
- Consider a reranker or specialized agents only after comparative evaluation demonstrates a concrete benefit.
