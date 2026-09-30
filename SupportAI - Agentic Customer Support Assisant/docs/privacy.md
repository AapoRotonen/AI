# Privacy notes

## Synthetic data

All seeded users, customers, addresses, tickets, and orders are fictional. Domains use `.demo` or `.invalid`. Do not replace these rows with production records in this PoC.

## Data minimization

An AI request contains the support employee's message plus only data a selected tool returns. The ticket service verifies the current principal before returning a ticket, history, customer summary, or ticket-linked orders. Customer summaries sent to the model contain only a synthetic customer ID and name. Knowledge lookup returns relevant internal policy chunks and source labels.

The LLM never receives password hashes, JWTs, database/model secrets, unrelated customer records, or arbitrary database access. Tool arguments and results are not printed by the application code.

## Optional external model boundary

When a real `OPENAI_API_KEY` is set, prompts and selected tool results are sent through Spring AI to the configured OpenAI model. Embedding indexing and semantic retrieval also use that provider. The `supportai-disabled` sentinel keeps chat offline and uses local keyword policy lookup. Before connecting real customer data, review the provider's current data handling, retention, region, contractual, and regulatory terms. This PoC does not decide those questions.

## Logging and audit

Request logs carry a correlation ID. Safe audit records capture actor, action/tool, resource type/ID, result, and timestamp. They do not store full prompts, ticket bodies, model outputs, hidden reasoning, credentials, or tokens. Avoid enabling verbose Spring AI logging in shared environments.

## Future production considerations

Use a data classification scheme, per-field minimization, a privacy-reviewed model contract, retention/deletion schedules, tenant isolation, encryption/key management, audited exports, prompt/log redaction, sensitive-data detection, and an incident process. Establish a lawful basis and notice before using actual customer data.
