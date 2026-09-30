# Development

## Prerequisites

- Java 21
- Maven Wrapper (downloads Maven 3.9.11 on first use)
- Docker with Compose for PostgreSQL and Testcontainers

## Local setup

1. Copy `.env.example` to `.env`; set a unique 32+ byte `JWT_SECRET`.
2. Run `docker compose up -d db` to start PostgreSQL with pgvector.
3. Run `./mvnw.cmd spring-boot:run` / `./mvnw.cmd test` on Windows, or `bash ./mvnw spring-boot:run` / `bash ./mvnw test` on Unix.
4. To run the complete container application, use `docker compose up --build`.

The app migrates the schema on startup and adds fictional sample rows idempotently. Spring Boot imports `.env` locally as optional properties. Keep `OPENAI_API_KEY=supportai-disabled` for offline mode. No real OpenAI key is needed for REST, the UI, deterministic tests, or lexical knowledge search. Live model and semantic vector calls need a real key.

## Useful commands

```text
bash ./mvnw test
bash ./mvnw verify
bash ./mvnw spring-boot:run
docker compose up -d db
docker compose up --build
docker compose down
```

## Adding schema changes

Add a new ordered SQL migration in `src/main/resources/db/migration/`; do not rely on Hibernate update mode. Keep JPA mappings aligned and add or update a database-backed test.

## Security-sensitive changes

Add tests at the service boundary, including a negative authorization case. If a tool reads a customer/order, derive it through an already-authorized ticket. If a tool writes state, add a Java policy and human-review rule; do not give the model a direct write path.

## Repository hygiene

Before a commit, inspect `git status --short`, `git diff --check`, and `git diff`. Search for real credentials, tokens, `.env`, generated `target/`, and unneeded IDE files. Commit only when the user requests it.
