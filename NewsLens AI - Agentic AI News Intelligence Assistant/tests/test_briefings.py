from datetime import UTC, datetime

import pytest

from newslens.briefings import BriefingService
from newslens.domain import ArticleCandidate, RelevanceAssessment
from newslens.persistence.repository import NewsRepository
from newslens.rag.embeddings import HashEmbedding


@pytest.mark.asyncio
async def test_fallback_brief_keeps_source_links(settings, sessions) -> None:
    repository = NewsRepository(sessions)
    candidate = ArticleCandidate(
        title="Anthropic introduces a coding agent",
        url="https://example.com/news/agent",
        source_name="Example News",
        published_at=datetime.now(UTC),
        snippet="The report describes a new AI coding agent.",
    )
    assessment = RelevanceAssessment(relevant=True, score=0.8, topics=["coding agents"])
    vector = await HashEmbedding(1536).embed(candidate.title)
    await repository.save_article(candidate, assessment, vector, "lexical-fallback")

    briefing = await BriefingService(settings, repository).generate()
    messages = briefing.to_discord_messages()
    assert len(briefing.items) == 1
    assert briefing.items[0].source_urls == ["https://example.com/news/agent"]
    assert "https://example.com/news/agent" in messages[0]
    assert len(messages[0]) < 2000


def test_brief_discord_output_escapes_untrusted_markdown() -> None:
    from newslens.briefings import BriefItem, DailyBriefing

    briefing = DailyBriefing(
        items=[
            BriefItem(
                story_id="story-1",
                title="[click](https://evil.example)",
                what_happened="@everyone\n> fake source",
                why_it_matters="**trusted?**",
                source_urls=["javascript:alert(1)", "https://example.com/path)"],
            )
        ]
    )

    message = briefing.to_discord_messages()[0]
    assert "\\[click\\]" in message
    assert "@everyone" not in message
    assert "\\> fake source" in message
    assert "javascript:" not in message
    assert "path%29" in message
