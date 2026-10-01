from datetime import UTC, datetime

import pytest

from newslens.clustering import StoryCluster, find_matching_story, title_similarity
from newslens.config import InterestProfile
from newslens.domain import ArticleCandidate
from newslens.relevance import RuleBasedRelevanceClassifier


@pytest.mark.asyncio
async def test_rule_classifier_accepts_coding_agent_story() -> None:
    profile = InterestProfile(
        interests=["coding agents", "OpenAI"],
        high_priority=["coding agents"],
        geographies=["GLOBAL"],
    )
    candidate = ArticleCandidate(
        title="New coding agent for software development",
        url="https://example.com/story",
        source_name="Example",
    )
    result = await RuleBasedRelevanceClassifier(profile).classify(candidate)
    assert result.relevant is True
    assert result.priority == "HIGH"


def test_title_similarity_separates_same_story_from_unrelated() -> None:
    assert (
        title_similarity("OpenAI announces a coding agent", "OpenAI launches coding agent") >= 0.42
    )
    assert (
        title_similarity("OpenAI announces a coding agent", "Finland announces a wind farm") < 0.42
    )


def test_cluster_respects_recency_window() -> None:
    now = datetime.now(UTC)
    candidate = ArticleCandidate(
        title="OpenAI announces new coding agent",
        url="https://example.com/story",
        source_name="Example",
        published_at=now,
    )
    story = StoryCluster("s1", "OpenAI launches new coding agent", "coding agent", now, 1)
    from newslens.domain import RelevanceAssessment

    assert (
        find_matching_story(candidate, [story], RelevanceAssessment(relevant=True, score=0.8))
        is story
    )
