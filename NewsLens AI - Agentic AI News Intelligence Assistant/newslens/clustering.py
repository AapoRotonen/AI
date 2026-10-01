from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from newslens.domain import ArticleCandidate, RelevanceAssessment

_TOKEN = re.compile(r"[a-z0-9+#]{3,}", re.IGNORECASE)
_STOP = {"the", "and", "for", "with", "from", "that", "this", "new", "how", "why", "its", "are"}


def title_tokens(text: str) -> set[str]:
    return {word.lower() for word in _TOKEN.findall(text) if word.lower() not in _STOP}


def title_similarity(left: str, right: str) -> float:
    a, b = title_tokens(left), title_tokens(right)
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def story_key(candidate: ArticleCandidate) -> str:
    tokens = sorted(title_tokens(candidate.title))
    return " ".join(tokens[:10]) or candidate.title.lower()[:100]


@dataclass(frozen=True)
class StoryCluster:
    key: str
    title: str
    summary: str
    last_seen_at: datetime
    article_count: int = 0


def find_matching_story(
    candidate: ArticleCandidate,
    stories: list[StoryCluster],
    assessment: RelevanceAssessment,
    threshold: float = 0.42,
    max_age: timedelta = timedelta(days=10),
) -> StoryCluster | None:
    """Match overlapping event headlines within a bounded time window."""
    published = candidate.published_at or candidate.discovered_at
    if published.tzinfo is None:
        published = published.replace(tzinfo=UTC)
    best: tuple[float, StoryCluster] | None = None
    candidate_topics = set(topic.lower() for topic in assessment.topics)
    for story in stories:
        story_date = story.last_seen_at
        if story_date.tzinfo is None:
            story_date = story_date.replace(tzinfo=UTC)
        if abs(published - story_date) > max_age:
            continue
        score = title_similarity(candidate.title, story.title)
        existing_topics = set(title_tokens(story.summary))
        if candidate_topics and candidate_topics & existing_topics:
            score += 0.05
        if score >= threshold and (best is None or score > best[0]):
            best = (score, story)
    return best[1] if best else None
