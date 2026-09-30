# Evaluation strategy

## Deterministic tests vs probabilistic evaluation

JUnit tests verify deterministic Java behavior: authentication, authorization, role rules, action policy, DTO validation, status transitions, and review ownership. These tests do not require paid model calls.

Agent and RAG quality is probabilistic. `evals/tickets.jsonl` is a hand-authored expectation dataset, not an executable harness and not a measured result. No accuracy or refusal percentage is claimed.

## Current test assets

- Unit tests: action whitelist, eight-call tool budget, and service-level ticket ownership/masking.
- Integration test: PostgreSQL/pgvector Testcontainer, Flyway startup, login, ticket access, and proposal → attempted self-approval → separate senior approval → close.
- Security regression examples: ticket enumeration, cross-agent access, role escalation, database/secret exfiltration, direct state changes, and indirect injection.
- RAG corpus: nine synthetic policy documents with source names/categories and bounded chunking.

## Suggested live agent evaluation

When a provider key and a reviewed model are available, run each fixture with fixed demo data and capture only answer, tool names, source references, latency, token usage when available, and pass/fail assertions. Check tool selection, facts grounded in records, source citation, safe uncertainty, and correct review behavior. Never store hidden chain-of-thought.

## Suggested RAG evaluation

Create queries with expected document IDs, measure recall@k and citation correctness, test paraphrases, and include no-answer/ambiguous queries. Add a malicious document fixture and assert that the Java authorization boundary still blocks unauthorized ticket access even if the model follows the malicious text.

## Suggested security evaluation

Keep tests independent of the model for access-control invariants. Test direct prompt attacks and indirect retrieved-text attacks against domain services and tool invocation with authenticated principals. Model refusal quality is useful but is not the security boundary.

## Optional live evaluation

Not implemented. Normal CI must remain offline from model providers and must not require `OPENAI_API_KEY`. Live evaluations should be explicitly selected, rate-limited, use only synthetic data, and record the provider/model/version/configuration without credentials or reasoning traces.
