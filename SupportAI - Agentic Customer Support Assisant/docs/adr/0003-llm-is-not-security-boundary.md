# ADR 0003: The LLM is not a security boundary

## Status

Accepted.

## Decision

Authentication, authorization, validation, business policy, and database access remain in Java services. AI tools are narrow and use the current Spring Security actor. Retrieved text and user input are treated as untrusted data.

## Consequences

Prompt wording improves task quality but never grants authority. A model that follows malicious text still cannot read unassigned tickets through the guarded service boundary or directly change state.
