# Implementation summary

## Implemented and runtime-verified

- Docker Compose stack built and started; PostgreSQL became healthy and the application health endpoint returned `UP`.
- The configured OpenAI key was present in the application container, and a minimal model-backed chat smoke test returned successfully.
- Maven `verify` completed: eight tests reported, five passed, zero failed, and three Testcontainers integration tests were skipped because the Maven verification container had no Docker socket.

## Implemented; broader runtime verification remains

- Spring Boot REST application, static support UI, PostgreSQL/Flyway schema, and demo seed runner.
- BCrypt login, signed JWT bearer authentication, role mapping, and service-level assigned-ticket checks.
- Ticket/customer-by-ticket/orders-by-ticket/history/service-status domain flows.
- Spring AI ChatClient with typed tool methods, service boundaries, eight-call tool budget, and an explicit offline sentinel that prevents any model or embedding calls without a real key.
- Markdown knowledge corpus chunking, source metadata, optional OpenAI/pgvector indexing/search, and lexical fallback.
- Pending review for ticket close; distinct senior/admin approval or rejection; deterministic close/history/audit service path.
- Request IDs, safe audit records, Actuator configuration, UI, docs, CI, unit and Testcontainers integration tests, and evaluation fixtures.

## Planned / not implemented

- Full Docker-backed integration-test execution, live RAG evaluation, and quality measurements.
- Production-grade token revocation/refresh, rate limiting, external identity, multiple writable actions, policy management UI, deployment, retention controls, advanced tracing exporter, and real customer data handling.

## Architecture and domain

Feature-oriented packages separate API, security, domain entities/repositories, authorization-aware services, AI tools, and RAG. PostgreSQL tables are created by Flyway; synthetic users/customers/tickets/orders/status/history are seeded idempotently on application startup. Hibernate validates rather than mutates the schema.

## Authentication and authorization

Passwords use BCrypt. A successful login gets an eight-hour HMAC JWT. Support agents list/read assigned tickets. Senior support and admins can read broader ticket data. Ticket-bound tools call service methods that re-check the principal. Unauthorized ticket reads return generic 404. Review endpoints are role-gated and proposal ownership is checked by the service.

## Agent and tools

The authenticated assistant uses Spring AI `ChatClient` and tools for ticket detail/history, minimal ticket customer, ticket-linked orders, known service status, policy search, and close proposals. A request budget stops Java tool execution after eight calls. A minimal live provider smoke test passed; the complete tool workflow has not been evaluated end to end.

## RAG

Nine checked-in support-policy Markdown files are chunked and given source/title/category metadata. With OpenAI configured, Spring AI embeddings and pgvector provide semantic retrieval. Without it, a keyword search operates over the same corpus. Full retrieval quality and database integration coverage remain unverified.

## Human-in-the-Loop

Only `CLOSE_TICKET` can be proposed. Proposal creation produces `PENDING`; Java policy blocks unsupported actions. The author cannot decide their own review. A different senior/admin approves or rejects, and approval triggers a deterministic ticket close plus history and audit events.

## Security, privacy, and observability

The model is not an authorization boundary. No repository/SQL/shell/filesystem/arbitrary URL tool exists. Logs/audit exclude prompt bodies, credentials, and reasoning. Request IDs are propagated to logs/responses; Actuator and Micrometer metrics are configured. The PoC uses localStorage for the browser bearer token and requires additional production hardening.

## Tests and verification performed

`mvn verify` completed successfully with eight tests reported: five passed, zero failed, and three PostgreSQL Testcontainers tests were skipped because the Maven verification container had no Docker socket. Docker Compose started the app and database; the database became healthy and the app health endpoint returned `UP`. A minimal live model smoke test also passed. The complete Docker-backed integration suite and broader AI/RAG evaluations remain outstanding.

## Git and repository practices

No commit was created. `.gitignore` excludes environment secrets, generated output, and local data. Before committing, run the full suite in a Java 21/Docker environment, inspect `git diff` and `git status`, and scan for secrets. Keep this project in an isolated repository so unrelated files from a parent workspace cannot be included.

## Known limitations and next improvements

The code compiles and the local smoke checks passed, but skipped integration tests and unmeasured agent/RAG behavior leave gaps. Run CI with Docker access, add measured agent/RAG evaluations and authorization tests for every tool, and implement external identity, token revocation, and rate limiting before any production-like use.
