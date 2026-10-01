from __future__ import annotations

from urllib.parse import urlsplit

import httpx
from bs4 import BeautifulSoup

from newslens.config import Settings
from newslens.domain import EvidenceItem, SourceType
from newslens.security.urls import validate_public_url


async def investigate_url(
    url: str, settings: Settings, source_type: SourceType = SourceType.UNKNOWN
) -> EvidenceItem:
    """Read one public HTML/text URL without following redirects or retaining full article text."""
    safe_url = await validate_public_url(url)
    excerpt_parts: list[bytes] = []
    size = 0
    async with httpx.AsyncClient(timeout=20, follow_redirects=False) as client:
        async with client.stream(
            "GET", safe_url, headers={"User-Agent": "NewsLensAI/0.1 (research)"}
        ) as response:
            response.raise_for_status()
            content_type = response.headers.get("content-type", "").lower()
            if not any(
                kind in content_type for kind in ("text/html", "text/plain", "application/xhtml")
            ):
                raise ValueError("Only public HTML or plain-text article pages are supported")
            async for chunk in response.aiter_bytes():
                remaining = settings.max_article_bytes - size
                if remaining <= 0:
                    break
                bounded = chunk[:remaining]
                excerpt_parts.append(bounded)
                size += len(bounded)
                if len(chunk) > remaining:
                    break
    payload = b"".join(excerpt_parts).decode("utf-8", errors="replace")
    soup = BeautifulSoup(payload, "html.parser")
    for node in soup(["script", "style", "noscript", "svg", "nav", "footer"]):
        node.decompose()
    title = soup.title.get_text(" ", strip=True) if soup.title else safe_url
    excerpt = " ".join(soup.get_text(" ", strip=True).split())[:900]
    host = urlsplit(safe_url).hostname or "unknown"
    return EvidenceItem(
        evidence_id="article-1",
        title=title[:500],
        url=safe_url,
        publisher=host,
        source_type=source_type,
        excerpt=excerpt,
    )
