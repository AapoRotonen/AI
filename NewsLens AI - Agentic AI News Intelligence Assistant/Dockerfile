FROM ghcr.io/astral-sh/uv:0.12.19 AS uv-bin
FROM python:3.12-slim

COPY --from=uv-bin /uv /uvx /bin/

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PATH="/app/.venv/bin:$PATH"
WORKDIR /app

COPY pyproject.toml uv.lock README.md ./
RUN uv sync --frozen --no-dev --no-install-project

COPY newslens ./newslens
COPY migrations ./migrations
COPY alembic.ini ./
COPY config ./config
RUN uv sync --frozen --no-dev

RUN useradd --create-home --uid 10001 newslens
USER newslens
CMD ["newslens", "bot"]
