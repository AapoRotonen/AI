from __future__ import annotations

import logging
from email.utils import parsedate_to_datetime
from typing import Protocol
from urllib.parse import urlsplit

import httpx

from newslens.config import Settings
from newslens.domain import EvidenceItem, SourceType
from newslens.security.urls import validate_public_url

logger = logging.getLogger(__name__)


class SearchProvider(Protocol):
    async def search(self, query: str, limit: int) -> list[EvidenceItem]: ...


class TavilySearchProvider:
    """Optional, capped Tavily news/web search adapter."""

    def __init__(
        self, settings: Settings, primary_domains: set[str], independent_domains: set[str]
    ) -> None:
        self.api_key = settings.tavily_api_key
        self.limit = settings.max_search_results
        self.primary_domains = primary_domains
        self.independent_domains = independent_domains

    async def search(self, query: str, limit: int) -> list[EvidenceItem]:
        if not self.api_key:
            return []
        query = " ".join(query.split())[:300]
        async with httpx.AsyncClient(timeout=25) as client:
            response = await client.post(
                "https://api.tavily.com/search",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={
                    "query": query,
                    "search_depth": "basic",
                    "max_results": min(max(1, limit), self.limit, 10),
                    "topic": "news",
                    "include_published_date": True,
                    "include_answer": False,
                    "include_raw_content": False,
                },
            )
            response.raise_for_status()
        items: list[EvidenceItem] = []
        for index, result in enumerate(response.json().get("results", [])):
            url = result.get("url")
            if not isinstance(url, str):
                continue
            try:
                safe_url = await validate_public_url(url)
            except ValueError:
                logger.info("Ignored a search result outside the public URL boundary")
                continue
            host = (urlsplit(safe_url).hostname or "").lower()
            if any(
                host == domain or host.endswith("." + domain) for domain in self.primary_domains
            ):
                source_type = SourceType.PRIMARY
            elif any(
                host == domain or host.endswith("." + domain) for domain in self.independent_domains
            ):
                source_type = SourceType.INDEPENDENT_REPORTING
            else:
                source_type = SourceType.UNKNOWN
            published_at = None
            published = result.get("published_date")
            if isinstance(published, str):
                try:
                    published_at = parsedate_to_datetime(published)
                except (TypeError, ValueError, OverflowError):
                    published_at = None
            items.append(
                EvidenceItem(
                    evidence_id=f"search-{index + 1}",
                    title=str(result.get("title", "Untitled"))[:500],
                    url=safe_url,
                    publisher=host,
                    source_type=source_type,
                    excerpt=str(result.get("content", ""))[:900],
                    published_at=published_at,
                )
            )
        return items
