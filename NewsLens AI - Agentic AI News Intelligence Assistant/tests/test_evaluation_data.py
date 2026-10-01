import json
from pathlib import Path

import pytest

from newslens.config import load_interests
from newslens.domain import ArticleCandidate
from newslens.relevance import RuleBasedRelevanceClassifier


@pytest.mark.asyncio
async def test_relevance_evaluation_cases_match_reviewed_labels() -> None:
    profile = load_interests(Path("config/interests.yaml"))
    classifier = RuleBasedRelevanceClassifier(profile)
    cases = [
        json.loads(line)
        for line in Path("evals/relevance_cases.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert cases
    for case in cases:
        candidate = ArticleCandidate(
            title=case["title"],
            url=f"https://eval.example/{case['id']}",
            source_name="Evaluation fixture",
            snippet=case["snippet"],
        )
        result = await classifier.classify(candidate)
        assert result.relevant is case["expected_relevant"], case["id"]
        if case["expected_topic"]:
            assert case["expected_topic"] in result.topics, case["id"]


def test_evidence_scenarios_have_expectations_for_each_evidence_shape() -> None:
    scenarios = json.loads(Path("evals/evidence_scenarios.json").read_text(encoding="utf-8"))
    assert {scenario["id"] for scenario in scenarios} == {
        "primary-and-independent",
        "primary-only",
        "conflicting-reporting",
        "historical-vs-current",
        "insufficient-evidence",
    }
    assert all(scenario["expected_behavior"] for scenario in scenarios)
