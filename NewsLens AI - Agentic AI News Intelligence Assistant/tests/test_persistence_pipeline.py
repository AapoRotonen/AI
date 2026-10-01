from datetime import UTC, datetime

import pytest

from newslens.domain import ArticleCandidate, RelevanceAssessment
from newslens.persistence.repository import NewsRepository
from newslens.rag.embeddings import HashEmbedding


@pytest.mark.asyncio
async def test_repository_stores_and_deduplicates_article(sessions) -> None:
    repository = NewsRepository(sessions)
    candidate = ArticleCandidate(
        title="OpenAI releases a coding agent",
        url="https://example.com/story?utm_source=rss",
        source_name="Example News",
        published_at=datetime.now(UTC),
        snippet="A bounded summary of the announcement.",
    )
    assessment = RelevanceAssessment(relevant=True, score=0.8, topics=["coding agents"])
    vector = await HashEmbedding(1536).embed(candidate.title)
    assert await repository.save_article(candidate, assessment, vector, "lexical-fallback") is True
    assert await repository.save_article(candidate, assessment, vector, "lexical-fallback") is False
    matches = await repository.search_history(vector, limit=5, embedding_mode="lexical-fallback")
    assert len(matches) == 1
    assert matches[0].source_name == "Example News"


class _FakeDiscovery:
    def __init__(self, candidate: ArticleCandidate) -> None:
        self.candidate = candidate

    async def discover(self, since, limit=100):
        return [self.candidate]


@pytest.mark.asyncio
async def test_pipeline_ingests_a_normalized_candidate(settings, sessions) -> None:
    from newslens.persistence.repository import NewsRepository
    from newslens.pipeline import NewsPipeline

    candidate = ArticleCandidate(
        title="Anthropic introduces an AI coding agent",
        url="https://example.com/anthropic-agent",
        source_name="Example News",
        published_at=datetime.now(UTC),
        snippet="The company announced a coding agent for developers.",
    )
    pipeline = NewsPipeline(settings, NewsRepository(sessions), discovery=_FakeDiscovery(candidate))
    stats = await pipeline.run_once()
    assert stats.discovered == 1
    assert stats.relevant == 1
    assert stats.stored == 1
