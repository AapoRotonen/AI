# ADR 0002: Spring AI ChatClient and bounded application tools

## Status

Accepted.

## Context

The product needs dynamic selection among a small allowlist of ticket, history, customer, order, status, knowledge, and proposal operations.

## Decision

Use Spring AI `ChatClient` and `@Tool` methods. Tool methods call domain services, validate arguments, audit safe metadata, and share a per-request eight-call budget.

## Consequences

Spring handles model/tool round trips. The LLM never receives repositories or generic infrastructure access. Live model quality, provider failure behavior, and the end-to-end tool budget must be verified with the configured model before relying on them.
