# News pipeline

1. `RSSDiscoveryProvider` reads `config/feeds.yaml` sequentially, checks public HTTP(S) destinations, disables redirects, and caps each response at 2 MB.
2. `feedparser` handles RSS/Atom. Items are normalized to `ArticleCandidate` with title, canonical URL, publisher label, source type, timestamp, snippet, and geography.
3. `ModelBackedRelevanceClassifier` uses structured output when configured. The deterministic fallback scores configured interest text/tokens and marks Finland when common geography markers appear.
4. The repository skips duplicate canonical URLs. New candidates are attached to the most similar recent story (token overlap threshold 0.42, up to ten days) or create a new story.
5. Story, article, source relationship, timestamp, short excerpt, relevance score, and embedding are persisted.
6. `/brief` can run ingestion on demand. APScheduler repeats ingestion and publishes to a configured text channel at the configured interval.

The clustering and fallback relevance rules are intentionally transparent PoC heuristics. They should be evaluated against a reviewed dataset before they drive important editorial decisions.
