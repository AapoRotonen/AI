# ADR 0005: PostgreSQL and optional pgvector retrieval

## Status

Accepted.

## Context

The PoC needs relational support data and source-linked internal knowledge retrieval without operating another database.

## Decision

Use PostgreSQL for application data and Spring AI's pgvector store for embeddings when an OpenAI key is configured. Keep a local keyword search fallback over the same policy files.

## Consequences

Local API/UI development does not need paid embeddings. Semantic retrieval requires pgvector and provider configuration. pgvector indexing is optional and does not establish the factual correctness of generated answers.
