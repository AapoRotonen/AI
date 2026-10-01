from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from newslens.config import Settings, load_feeds, load_interests
from newslens.discovery.base import NewsDiscoveryProvider
from newslens.discovery.rss import RSSDiscoveryProvider
from newslens.llm import OpenAICompatibleClient
from newslens.persistence.repository import NewsRepository
from newslens.rag.embeddings import EmbeddingService
from newslens.relevance import ModelBackedRelevanceClassifier

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class PipelineStats:
    discovered: int
    relevant: int
    stored: int
    duplicates: int


class NewsPipeline:
    def __init__(
        self,
        settings: Settings,
        repository: NewsRepository,
        discovery: NewsDiscoveryProvider | None = None,
    ) -> None:
        self.settings = settings
        self.repository = repository
        self.discovery = discovery or RSSDiscoveryProvider(load_feeds(settings.feeds_file))
        profile = load_interests(settings.interests_file)
        self.classifier = ModelBackedRelevanceClassifier(profile, OpenAICompatibleClient(settings))
        self.embeddings = EmbeddingService(settings, OpenAICompatibleClient(settings))

    async def run_once(self, limit: int = 100) -> PipelineStats:
        since = datetime.now(UTC) - timedelta(hours=self.settings.news_lookback_hours)
        candidates = await self.discovery.discover(since=since, limit=limit)
        relevant = stored = duplicates = 0
        for candidate in candidates:
            assessment = await self.classifier.classify(candidate)
            if not assessment.relevant:
                continue
            relevant += 1
            vector, embedding_mode = await self.embeddings.embed(
                f"{candidate.title}\n{candidate.snippet}\n{' '.join(assessment.topics)}"
            )
            if await self.repository.save_article(candidate, assessment, vector, embedding_mode):
                stored += 1
            else:
                duplicates += 1
        logger.info(
            "news_pipeline_complete",
            extra={
                "discovered": len(candidates),
                "relevant": relevant,
                "stored": stored,
                "duplicates": duplicates,
            },
        )
        return PipelineStats(
            discovered=len(candidates), relevant=relevant, stored=stored, duplicates=duplicates
        )
