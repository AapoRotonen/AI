"""Offline metrics and a small runner for comparing retrieval rankings."""

from __future__ import annotations

import json
from pathlib import Path
from statistics import mean
from typing import Iterable


def retrieval_metrics(retrieved_ids: Iterable[str], relevant_ids: Iterable[str], k: int) -> dict[str, float]:
    if k <= 0:
        raise ValueError("k must be greater than zero")
    ranked = []
    seen = set()
    for identifier in retrieved_ids:
        if identifier not in seen:
            ranked.append(identifier)
            seen.add(identifier)
        if len(ranked) == k:
            break
    relevant = set(relevant_ids)
    if not relevant:
        raise ValueError("relevant_ids must not be empty")
    hits = [index for index, identifier in enumerate(ranked, start=1) if identifier in relevant]
    return {
        f"recall@{k}": len(hits) / len(relevant),
        f"precision@{k}": len(hits) / k,
        "mrr": 1 / hits[0] if hits else 0.0,
    }


def evaluate_retrieval_dataset(
    retriever,
    cases: list[dict],
    *,
    methods: tuple[str, ...] = ("vector", "bm25", "hybrid"),
    k: int = 4,
) -> dict:
    report = {method: {"cases": [], "mean": {}} for method in methods}
    for case in cases:
        for method in methods:
            results = retriever.retrieve_for_evaluation(case["question"], top_k=k, method=method)
            identifiers = [
                metadata.get("product_code") or metadata.get("document_id", "")
                for _, metadata, _ in results
            ]
            metrics = retrieval_metrics(identifiers, case["expected_product_codes"], k)
            report[method]["cases"].append({"id": case["id"], **metrics})
    for method in methods:
        rows = report[method]["cases"]
        metric_names = rows[0].keys() - {"id"} if rows else set()
        report[method]["mean"] = {
            name: mean(row[name] for row in rows) for name in metric_names
        }
    return report


def load_cases(path: str | Path) -> list[dict]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError("retrieval evaluation data must be a JSON array")
    for case in data:
        if not case.get("question") or not case.get("expected_product_codes"):
            raise ValueError("each case requires question and expected_product_codes")
    return data
