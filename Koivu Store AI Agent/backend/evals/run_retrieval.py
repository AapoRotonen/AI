"""Compare retrieval methods on the local labelled query set.

Run from backend with: python evals/run_retrieval.py
Vector and hybrid modes call the configured embedding provider; unit tests do not.
"""

import json
from pathlib import Path

from core.retrieval import get_retriever
from core.retrieval_eval import evaluate_retrieval_dataset, load_cases


def main() -> None:
    cases = load_cases(Path("data/rag_eval.json"))
    report = evaluate_retrieval_dataset(get_retriever(), cases, k=4)
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
