from __future__ import annotations

from collections.abc import AsyncIterator
from pathlib import Path

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from newslens.config import Settings
from newslens.persistence.models import Base


@pytest.fixture
def settings() -> Settings:
    return Settings(
        database_url="sqlite+aiosqlite:///:memory:",
        interests_file=Path("config/interests.yaml"),
        feeds_file=Path("config/feeds.yaml"),
        primary_domains_file=Path("config/primary_domains.yaml"),
        embedding_dimensions=1536,
        openai_api_key=None,
        tavily_api_key=None,
    )


@pytest.fixture
async def sessions() -> AsyncIterator[async_sessionmaker[AsyncSession]]:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    yield async_sessionmaker(engine, expire_on_commit=False)
    await engine.dispose()
