# ADR 0003: PostgreSQL and pgvector memory

Status: accepted for the PoC.

PostgreSQL stores stories and article provenance, and pgvector stores embeddings in the same schema. This minimizes operational components and supports nearest-neighbor retrieval. SQLite is only a test adapter, not the target runtime.
