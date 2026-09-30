# Retrieval evaluation

The labelled dataset is `backend/data/rag_eval.json`. Each case includes a Finnish product question, expected product code(s), and facts a reviewer should verify. Product codes are carried as retrieval metadata, including on all chunks split from a product section.

## Metrics

For cutoff `K`, the runner reports:

- **Recall@K:** relevant expected product codes found in the top K divided by all expected codes.
- **Precision@K:** relevant distinct product codes among the first K distinct products divided by K; repeated chunks of one product count once.
- **MRR:** reciprocal rank of the first relevant result, or zero if none is found.

`backend/core/retrieval.py` exposes `vector`, `bm25`, and `hybrid` retrieval modes. Hybrid retrieval combines the vector and BM25 rankings using deterministic reciprocal-rank fusion (RRF, `k=60`). There is no reranker; adding one requires measured improvement on this dataset and a maintainable implementation.

## Run

From `backend/`:

```powershell
.\.venv\Scripts\python.exe -m evals.run_retrieval
```

The command prints a JSON report by method and query. BM25 uses the local corpus. Vector and hybrid methods call the configured embedding provider and may incur API cost; they are not part of the regular unit-test or CI run. The evaluation runner was added, but live retrieval scores have not been recorded as part of this implementation.

Unit tests cover the metric calculations, RRF ordering, and product-code metadata without OpenAI calls. The small dataset is a starting point, not a statistically representative benchmark. Add reviewed queries for policies, paraphrases, stock and size edge cases, multilingual input, and unsupported questions before using the scores to compare model or corpus changes.
