from __future__ import annotations

import math
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.orm import selectinload

from newslens.clustering import StoryCluster, find_matching_story
from newslens.domain import ArticleCandidate, RelevanceAssessment
from newslens.persistence.models import ArticleRecord, StoryRecord
from newslens.security.urls import canonicalize_url


def _as_utc(value: datetime) -> datetime:
    return value.replace(tzinfo=value.tzinfo or UTC).astimezone(UTC)


class NewsRepository:
    def __init__(self, sessions: async_sessionmaker[AsyncSession]) -> None:
        self.sessions = sessions

    async def save_article(
        self,
        candidate: ArticleCandidate,
        assessment: RelevanceAssessment,
        embedding: list[float],
        embedding_mode: str,
    ) -> bool:
        canonical_url = canonicalize_url(str(candidate.url))
        async with self.sessions() as session:
            exists = await session.scalar(
                select(ArticleRecord.id).where(ArticleRecord.canonical_url == canonical_url)
            )
            if exists:
                return False

            cutoff = _as_utc(candidate.published_at or candidate.discovered_at) - timedelta(days=10)
            records = (
                await session.scalars(select(StoryRecord).where(StoryRecord.last_seen_at >= cutoff))
            ).all()
            clusters = [
                StoryCluster(
                    key=record.id,
                    title=record.title,
                    summary=record.summary,
                    last_seen_at=_as_utc(record.last_seen_at),
                    article_count=0,
                )
                for record in records
            ]
            match = find_matching_story(candidate, clusters, assessment)
            now = _as_utc(candidate.published_at or candidate.discovered_at)
            if match:
                story = await session.get(StoryRecord, match.key)
                assert story is not None
                story.last_seen_at = max(_as_utc(story.last_seen_at), now)
                story.topics = list(dict.fromkeys([*(story.topics or []), *assessment.topics]))[:12]
                if not story.summary and candidate.snippet:
                    story.summary = candidate.snippet[:1500]
            else:
                story = StoryRecord(
                    title=candidate.title,
                    summary=candidate.snippet[:1500],
                    topics=assessment.topics,
                    geography=assessment.geography,
                    first_seen_at=now,
                    last_seen_at=now,
                )
                session.add(story)
                await session.flush()
            session.add(
                ArticleRecord(
                    canonical_url=canonical_url,
                    title=candidate.title,
                    source_name=candidate.source_name,
                    source_type=candidate.source_type.value,
                    published_at=_as_utc(candidate.published_at)
                    if candidate.published_at
                    else None,
                    discovered_at=_as_utc(candidate.discovered_at),
                    snippet=candidate.snippet[:2000],
                    content_hash=_content_hash(canonical_url, candidate.title, candidate.snippet),
                    relevance_score=assessment.score,
                    topics=assessment.topics,
                    geography=assessment.geography,
                    embedding=embedding,
                    embedding_mode=embedding_mode[:128],
                    story_id=story.id,
                )
            )
            await session.commit()
        return True

    async def list_recent_stories(self, since: datetime, limit: int = 20) -> list[StoryRecord]:
        async with self.sessions() as session:
            result = await session.scalars(
                select(StoryRecord)
                .options(selectinload(StoryRecord.articles))
                .where(StoryRecord.last_seen_at >= _as_utc(since))
                .order_by(StoryRecord.last_seen_at.desc())
                .limit(limit)
            )
            return list(result.unique().all())

    async def search_history(
        self,
        query_vector: list[float],
        limit: int = 8,
        embedding_mode: str | None = None,
    ) -> list[ArticleRecord]:
        async with self.sessions() as session:
            filters = [ArticleRecord.embedding.is_not(None)]
            if embedding_mode:
                filters.append(ArticleRecord.embedding_mode == embedding_mode)
            if session.bind and session.bind.dialect.name == "postgresql":
                result = await session.scalars(
                    select(ArticleRecord)
                    .where(*filters)
                    .order_by(ArticleRecord.embedding.cosine_distance(query_vector))
                    .limit(limit)
                )
                return list(result.all())
            records = list((await session.scalars(select(ArticleRecord).where(*filters))).all())
            records.sort(key=lambda item: _cosine_distance(item.embedding or [], query_vector))
            return records[:limit]


def _content_hash(url: str, title: str, snippet: str) -> str:
    import hashlib

    return hashlib.sha256(f"{url}\n{title}\n{snippet[:400]}".encode()).hexdigest()


def _cosine_distance(left: list[float], right: list[float]) -> float:
    if len(left) != len(right) or not left:
        return 1.0
    dot = sum(a * b for a, b in zip(left, right, strict=True))
    norm_left = math.sqrt(sum(a * a for a in left))
    norm_right = math.sqrt(sum(b * b for b in right))
    if not norm_left or not norm_right:
        return 1.0
    return 1.0 - dot / (norm_left * norm_right)
