from __future__ import annotations

from datetime import datetime
from typing import Protocol

from newslens.domain import ArticleCandidate


class NewsDiscoveryProvider(Protocol):
    async def discover(self, since: datetime, limit: int = 100) -> list[ArticleCandidate]: ...
