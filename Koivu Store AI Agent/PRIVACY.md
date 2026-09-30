# Privacy

This repository's privacy description documents the demo's technical data flows; it is not a legal privacy notice. Do not use real customer information until the controller, purpose, legal basis, recipients, retention, provider terms, and user rights have been reviewed.

The current application stores account email and password hashes, hashed session-token identifiers, demo orders, and sanitized support cases in local SQLite. Chat messages/history can be sent to OpenAI; a Tavily query is made only on the external-information route. The app's event logs omit message and answer content. The provider's retention and processing location depend on the configured account and are not established by this repository.

See [docs/privacy.md](docs/privacy.md) for the data inventory, access model, retention behavior, and limitations. The user-facing disclosure is in frontend/privacy.html.
