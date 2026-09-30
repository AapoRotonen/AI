"""Run the lightweight routing evaluation cases using deterministic policy only."""

import json
import unittest
from pathlib import Path
from unittest.mock import patch

from agent.graph import route_after_intent, route_after_web


class AgentEvaluationTests(unittest.TestCase):
    def test_routing_cases_match_the_reviewed_expected_routes(self):
        cases = json.loads((Path(__file__).parents[1] / "data" / "agent_eval.json").read_text(encoding="utf-8"))
        with patch("agent.graph.settings.tavily_api_key", "test-key"):
            for case in cases:
                with self.subTest(case=case["id"]):
                    state = {
                        "question": case["message"],
                        "intent": case["intent"],
                        "user_id": "fixture-user" if case["authenticated"] else None,
                        "human_requested": case.get("human_requested", False),
                    }
                    self.assertEqual(route_after_intent(state), case["expected_route"])
                    if "expected_failure_route" in case:
                        self.assertEqual(
                            route_after_web({"web_results": [], "should_escalate": True}),
                            case["expected_failure_route"],
                        )

    def test_without_tavily_external_requests_do_not_invoke_web(self):
        with patch("agent.graph.settings.tavily_api_key", ""):
            self.assertEqual(
                route_after_intent({"intent": "external_info", "user_id": None}),
                "escalate",
            )


if __name__ == "__main__":
    unittest.main()
