# Evaluation

`evals/relevance_cases.jsonl` contains relevance examples. `evals/evidence_scenarios.json` records expected evidence behaviors: primary plus independent reporting, only primary evidence, conflicting sources, old/current context, and insufficient evidence.

These are evaluation inputs and expectations, not generated result scores. Automated tests cover deterministic fallback classification, URL boundaries, clustering, SQLite persistence/retrieval, and a fake-provider research workflow. Normal CI does not require OpenAI, Tavily, Discord, or PostgreSQL credentials.

Live model evaluations are not implemented. Before changing prompts/models for a release, add reviewed examples with expected structured output, run them against the configured model, and report failures and uncertainty rather than inventing aggregate results.
