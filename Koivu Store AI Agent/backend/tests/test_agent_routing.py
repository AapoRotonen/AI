"""Deterministic intent-routing tests. All model and capability calls are mocked."""

import unittest
from contextlib import ExitStack
from unittest.mock import patch

from langchain_core.messages import AIMessage

from agent.graph import create_agent, route_after_intent
from agent.nodes import classify_intent_node
from agent.schemas import Intent, IntentClassification


def initial_state(message, *, user_id=None):
    return {
        "question": message,
        "intent": "",
        "rag_results": [],
        "web_results": [],
        "answer": "",
        "path_taken": "",
        "should_escalate": False,
        "needs_human": False,
        "iteration_count": 0,
        "rag_was_sufficient": False,
        "history": [],
        "user_id": user_id,
        "order_tool": object() if user_id else None,
        "request_id": "test-request",
        "llm_calls": 0,
        "input_tokens": 0,
        "output_tokens": 0,
    }


class IntentRoutingTests(unittest.TestCase):
    def run_graph(self, message, intent, tavily_key="test-key", *, human_requested=False, authenticated=None):
        calls = []
        intent_values = {
            "product": Intent.PRODUCT,
            "style_advice": Intent.STYLE_ADVICE,
            "personal_support": Intent.ORDER_SUPPORT,
            "external_info": Intent.EXTERNAL,
            "ambiguous": Intent.AMBIGUOUS,
        }

        def node(name, **updates):
            def run(state):
                calls.append(name)
                return {**state, **updates}
            return run

        with ExitStack() as stack:
            stack.enter_context(patch("agent.graph.settings.tavily_api_key", tavily_key))
            model = stack.enter_context(patch("agent.nodes.ChatOpenAI"))
            model.return_value.with_structured_output.return_value.invoke.return_value = {
                "parsed": IntentClassification(
                    intent=intent_values[intent],
                    standalone_question="resolved test question",
                    human_requested=human_requested,
                ),
                "raw": AIMessage(content="{}"),
            }
            classifier_spy = stack.enter_context(
                patch("agent.graph.classify_intent_node", wraps=classify_intent_node)
            )
            stack.enter_context(patch("agent.graph.rag_node", side_effect=node("rag", rag_results=[{"source_id": "doc-1"}])))
            stack.enter_context(patch("agent.graph.evaluate_rag_node", side_effect=node("evaluate", rag_was_sufficient=True, source_ids=["doc-1"])))
            stack.enter_context(patch("agent.graph.web_search_node", side_effect=node("web", web_results=[{"source_id": "web-1"}])))
            stack.enter_context(patch("agent.graph.order_status_node", side_effect=node("order_status", answer="mock order result")))
            stack.enter_context(patch("agent.graph.support_request_node", side_effect=node("support_request", create_support_case=True)))
            stack.enter_context(patch("agent.graph.style_advice_node", side_effect=node("style_advice", answer="mock shoe advice")))
            stack.enter_context(patch("agent.graph.auth_required_node", side_effect=node("auth_required", answer="login required", auth_required=True)))
            stack.enter_context(patch("agent.graph.escalation_node", side_effect=node("escalate", should_escalate=True)))
            stack.enter_context(patch("agent.graph.generate_answer_node", side_effect=node("generate", answer="mock generated answer")))
            stack.enter_context(patch("agent.graph.clarify_intent_node", side_effect=node("clarify", answer="mock clarification")))
            stack.enter_context(patch("agent.graph.greeting_node", side_effect=node("greeting", answer="mock greeting")))
            signed_in = intent == "personal_support" if authenticated is None else authenticated
            user_id = "customer-1" if signed_in else None
            result = create_agent().invoke(initial_state(message, user_id=user_id))
            if classifier_spy.call_count:
                calls.insert(0, "classify")
        return result, calls

    def test_product_question_routes_to_rag(self):
        result, calls = self.run_graph("Do you have black shirts?", "product")
        self.assertEqual(calls, ["classify", "rag", "evaluate", "generate"])
        self.assertEqual(result["intent"], "product")

    def test_style_question_routes_through_rag_to_general_style_advice(self):
        result, calls = self.run_graph("What shoes match that sweater?", "style_advice")
        self.assertEqual(calls, ["classify", "rag", "evaluate", "web", "style_advice"])
        self.assertEqual(result["answer"], "mock shoe advice")
        self.assertFalse(result.get("create_support_case", False))

    def test_explicit_human_request_opens_support_route_only_when_signed_in(self):
        result, calls = self.run_graph("Can you bring a person into chat?", "personal_support", human_requested=True)
        self.assertEqual(calls, ["classify", "support_request"])
        self.assertTrue(result["create_support_case"])

    def test_explicit_human_request_overrides_style_context_and_requires_authentication(self):
        result, calls = self.run_graph(
            "Saisinko ihmisen chattiin?", "style_advice", authenticated=True,
        )
        self.assertEqual(calls, ["classify", "support_request"])
        self.assertTrue(result["human_requested"])
        self.assertTrue(result["create_support_case"])

        anonymous, anonymous_calls = self.run_graph(
            "Saisinko ihmisen chattiin?", "style_advice", authenticated=False,
        )
        self.assertEqual(anonymous_calls, ["classify", "auth_required"])
        self.assertTrue(anonymous["auth_required"])
        self.assertFalse(anonymous.get("create_support_case", False))

    def test_personal_order_question_without_login_routes_to_auth_message(self):
        result, calls = self.run_graph("Mikähän on tilaukseni tilanne?", "style_advice", authenticated=False)
        self.assertEqual(calls, ["classify", "auth_required"])
        self.assertTrue(result["auth_required"])
        self.assertEqual(result["intent"], "personal_support")

    def test_greeting_gets_a_greeting_instead_of_clarification(self):
        result, calls = self.run_graph("terve", "ambiguous")
        self.assertEqual(calls, ["classify", "greeting"])
        self.assertEqual(result["answer"], "mock greeting")
        self.assertEqual(result["intent"], "greeting")

    def test_shoe_styling_falls_back_to_rag_and_stylist_when_web_is_unavailable(self):
        result, calls = self.run_graph("What shoes match that sweater?", "style_advice", tavily_key="")
        self.assertEqual(calls, ["classify", "rag", "evaluate", "style_advice"])
        self.assertFalse(result.get("create_support_case", False))

    def test_authenticated_order_question_routes_to_scoped_order_tool_node(self):
        result, calls = self.run_graph("Where is order ORD-1234ABCD?", "personal_support")
        self.assertEqual(calls, ["classify", "order_status"])
        self.assertEqual(result["intent"], "personal_support")

    def test_current_trends_route_to_web_without_rag(self):
        result, calls = self.run_graph("What are the latest fashion trends?", "external_info")
        self.assertEqual(calls, ["classify", "web", "generate"])
        self.assertEqual(result["web_results"], [{"source_id": "web-1"}])
        self.assertNotIn("rag", calls)

    def test_ambiguous_question_asks_for_clarification_without_capability_calls(self):
        result, calls = self.run_graph("Can you help me?", "ambiguous")
        self.assertEqual(calls, ["classify", "clarify"])
        self.assertEqual(result["answer"], "mock clarification")
        self.assertNotIn("rag", calls)
        self.assertNotIn("web", calls)

    def test_external_request_without_tavily_key_escalates(self):
        result, calls = self.run_graph("What are the latest fashion trends?", "external_info", tavily_key="")
        self.assertEqual(calls, ["classify", "escalate", "generate"])
        self.assertTrue(result["should_escalate"])

    def test_unknown_classifier_value_cannot_select_a_graph_node(self):
        self.assertEqual(route_after_intent({"intent": "admin_sql", "user_id": "customer-1"}), "clarify")

    def test_malformed_structured_output_fails_to_ambiguity(self):
        state = initial_state("Can you help me?")
        with patch("agent.nodes.ChatOpenAI") as model:
            model.return_value.with_structured_output.return_value.invoke.return_value = {
                "parsed": None,
                "raw": AIMessage(content="not structured"),
                "parsing_error": ValueError("invalid schema"),
            }
            result = classify_intent_node(state)
        self.assertEqual(result["intent"], "ambiguous")
        self.assertTrue(result["classification_failed"])

    def test_classifier_exception_fails_to_ambiguity(self):
        state = initial_state("Can you help me?")
        with patch("agent.nodes.ChatOpenAI") as model:
            model.return_value.with_structured_output.return_value.invoke.side_effect = RuntimeError("provider down")
            result = classify_intent_node(state)
        self.assertEqual(result["intent"], "ambiguous")
        self.assertTrue(result["classification_failed"])

    def test_invalid_enum_value_fails_to_ambiguity(self):
        state = initial_state("Do something")
        with patch("agent.nodes.ChatOpenAI") as model:
            model.return_value.with_structured_output.return_value.invoke.return_value = {
                "parsed": {"intent": "arbitrary_node_name", "confidence": 1.0},
                "raw": AIMessage(content="{}"),
            }
            result = classify_intent_node(state)
        self.assertEqual(result["intent"], "ambiguous")
        self.assertTrue(result["classification_failed"])


if __name__ == "__main__":
    unittest.main()
