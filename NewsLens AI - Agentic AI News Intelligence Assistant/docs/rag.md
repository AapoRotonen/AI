# Historical retrieval (RAG)

Each stored article receives an embedding for title, short snippet, and classified topics. The embedding mode/model is stored with each article so retrieval does not compare vectors produced by different providers. With `OPENAI_API_KEY`, the configured embedding model is called using the initial schema's 1536 dimensions. Otherwise `HashEmbedding` generates a deterministic signed token-hash vector. The fallback is useful for offline matching but is not semantic understanding.

PostgreSQL uses pgvector cosine distance and an HNSW cosine index. SQLite tests load candidate rows and compute cosine scores in Python. Results include article title, publisher, source relationship, publication timestamp, short snippet, and canonical URL. Full article bodies are not retained.

Changing vector dimensions requires a new migration and coordinated model/configuration change; the current setting is constrained to 1536.
