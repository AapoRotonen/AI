from __future__ import annotations

import asyncio
import calendar
import logging
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from time import struct_time

import feedparser
import httpx

from newslens.config import FeedConfig
from newslens.domain import ArticleCandidate, SourceType
from newslens.security.urls import canonicalize_url, validate_public_url

logger = logging.getLogger(__name__)


def _entry_date(entry: object) -> datetime | None:
    value = getattr(entry, "published", None) or getattr(entry, "updated", None)
    if isinstance(value, str):
        try:
            parsed = parsedate_to_datetime(value)
            return parsed.replace(tzinfo=parsed.tzinfo or UTC).astimezone(UTC)
        except (TypeError, ValueError, OverflowError):
            pass
    parsed_tuple: struct_time | None = getattr(entry, "published_parsed", None) or getattr(
        entry, "updated_parsed", None
    )
    if parsed_tuple:
        return datetime.fromtimestamp(calendar.timegm(parsed_tuple), tz=UTC)
    return None


class RSSDiscoveryProvider:
    """Fetch a configured set of RSS/Atom feeds with bounded size and redirects disabled."""

    def __init__(self, feeds: list[FeedConfig], max_feed_bytes: int = 2_000_000) -> None:
        self.feeds = feeds
        self.max_feed_bytes = max_feed_bytes
        self._lock = asyncio.Semaphore(2)

    async def _fetch(self, feed: FeedConfig) -> bytes:
        safe_url = await validate_public_url(feed.url)
        chunks: list[bytes] = []
        size = 0
        async with self._lock, httpx.AsyncClient(timeout=20, follow_redirects=False) as client:
            async with client.stream(
                "GET", safe_url, headers={"User-Agent": "NewsLensAI/0.1 (+RSS reader)"}
            ) as response:
                response.raise_for_status()
                async for chunk in response.aiter_bytes():
                    size += len(chunk)
                    if size > self.max_feed_bytes:
                        raise ValueError(f"Feed exceeded the {self.max_feed_bytes}-byte limit")
                    chunks.append(chunk)
        return b"".join(chunks)

    async def discover(self, since: datetime, limit: int = 100) -> list[ArticleCandidate]:
        since = since.replace(tzinfo=since.tzinfo or UTC).astimezone(UTC)
        candidates: list[ArticleCandidate] = []
        for feed in self.feeds:
            if len(candidates) >= limit:
                break
            try:
                payload = await self._fetch(feed)
                parsed = feedparser.parse(payload)
                for entry in parsed.entries:
                    link = getattr(entry, "link", "")
                    title = " ".join(str(getattr(entry, "title", "")).split())
                    if not title or not link:
                        continue
                    try:
                        url = canonicalize_url(link)
                    except ValueError:
                        continue
                    published_at = _entry_date(entry)
                    if published_at and published_at < since:
                        continue
                    summary = (
                        getattr(entry, "summary", "") or getattr(entry, "description", "") or ""
                    )
                    summary = " ".join(str(summary).split())[:2000]
                    try:
                        source_type = SourceType(feed.source_type.upper())
                    except ValueError:
                        source_type = SourceType.UNKNOWN
                    candidates.append(
                        ArticleCandidate(
                            title=title[:500],
                            url=url,
                            source_name=feed.name,
                            source_type=source_type,
                            published_at=published_at,
                            snippet=summary,
                            author=getattr(entry, "author", None),
                            geography=feed.geography.upper(),
                        )
                    )
                    if len(candidates) >= limit:
                        break
            except (httpx.HTTPError, ValueError, OSError) as exc:
                logger.warning(
                    "Could not read configured feed %s (%s)", feed.name, type(exc).__name__
                )
        return candidates
