# Security and data handling

- URL parsing accepts absolute HTTP(S) only; userinfo is rejected, hosts are IDNA-normalized, and tracking parameters/fragments are removed. DNS resolution rejects non-global IPv4/IPv6 addresses; redirects are disabled and response bodies are capped.
- Model provider URLs require HTTPS. Cleartext HTTP is allowed only for localhost development endpoints.
- The research graph exposes capped search, one URL fetch, and read-only historical retrieval. Model outputs are validated and source references must match retrieved evidence IDs.
- RSS entries, article pages, search results, and model text are untrusted. Discord output escapes Markdown, disables mentions, and only embeds canonical HTTP(S) source links.
- Discord commands are denied by default. Set `DISCORD_ALLOWED_USER_IDS` to authorize specific users; `DISCORD_ALLOW_PUBLIC_COMMANDS=true` explicitly makes commands public.
- Full article bodies and Discord user IDs are not intentionally persisted. PostgreSQL stores story/article titles, canonical URLs, publisher/source metadata, short snippets, derived summaries, and embeddings. No automatic expiry or deletion job is implemented; the operator owns retention, backups, and deletion.
- Research questions and selected evidence can be sent to the configured model provider. Search terms can be sent to Tavily. Discord processes interactions and any published briefings. Do not submit personal or confidential information.
- `.env`, `.env.*` (except `.env.example`), local secret directories, and common private-key/certificate files are ignored by Git and excluded from Docker build context. CI has read-only repository permissions, does not persist checkout credentials, and pins third-party actions to commit SHAs.
- Compose binds PostgreSQL to `127.0.0.1`; the Docker image installs dependencies from the checked-in `uv.lock`.

The DNS preflight and later HTTP connection resolve hostnames separately. A rebinding-resistant pinned transport remains future work. This PoC also does not eliminate malicious provider responses, model hallucination, source misclassification, or copyright risk. Review provider terms and feed rights before broader use.

See [the privacy and security audit](tietosuoja-ja-tietoturvatarkastus.md) for the 2026-10-01 repository review, including dependency and Git-history checks.
