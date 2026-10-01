# Development

## Local environment

```powershell
Copy-Item .env.example .env
uv sync --extra dev
docker compose up -d db
uv run newslens init-db
```

## Checks

```powershell
uv run ruff check .
uv run ruff format --check .
uv run pytest
uv build
```

## Run

```powershell
uv run newslens ingest
uv run newslens brief
uv run newslens ask "What happened with coding agents this week?"
uv run newslens bot
```

The app uses an async SQLAlchemy URL (`postgresql+asyncpg://...`). Tests use SQLite and fake network providers. Docker Compose exposes PostgreSQL on localhost port 5432 and stores data in a named volume.

## Configuration

Edit `config/interests.yaml`, `config/feeds.yaml`, and `config/primary_domains.yaml`. Credentials are loaded from `.env`/environment. A model provider is optional; Tavily is optional; Discord requires a token only when starting the bot.
