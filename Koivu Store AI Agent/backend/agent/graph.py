"""Allowlisted LangGraph routing with separate style, order, RAG, and web paths."""

from langgraph.graph import END, StateGraph

from agent.nodes import (
    auth_required_node,
    clarify_intent_node,
    classify_intent_node,
    escalation_node,
    evaluate_rag_node,
    generate_answer_node,
    greeting_node,
    order_status_node,
    offer_human_node,
    rag_node,
    support_request_node,
    style_advice_node,
    web_search_node,
)
from agent.schemas import Intent
from agent.state import AgentState
from core.config import get_settings

settings = get_settings()


def route_after_intent(state: AgentState) -> str:
    """Map a known intent to a fixed capability; never accept an LLM node name."""
    intent = state.get("intent")
    if intent == Intent.GREETING.value:
        return "greeting"
    if intent in (Intent.PRODUCT.value, Intent.STYLE_ADVICE.value):
        return "rag"
    if intent == Intent.ORDER_SUPPORT.value:
        if not state.get("user_id"):
            return "auth_required"
        if state.get("human_requested"):
            return "support_request"
        if state.get("human_recommended"):
            return "offer_human"
        return "order_status"
    if intent == Intent.EXTERNAL.value:
        return "web" if settings.tavily_api_key else "escalate"
    return "clarify"


def route_after_rag(state: AgentState) -> str:
    # Style advice can combine retrieved product facts with general fashion knowledge.
    # The catalogue is not expected to contain every compatible accessory.
    if state.get("intent") == Intent.STYLE_ADVICE.value:
        if state.get("web_search_needed") and settings.tavily_api_key:
            return "web"
        return "style_advice"
    if state.get("rag_was_sufficient"):
        return "generate"
    if state.get("evaluation_failed") or state.get("iteration_count", 0) >= settings.max_iterations:
        return "escalate"
    return "web" if settings.tavily_api_key else "escalate"


def route_after_web(state: AgentState) -> str:
    if state.get("intent") == Intent.STYLE_ADVICE.value:
        return "style_advice"
    if state.get("should_escalate") or not state.get("web_results"):
        return "escalate"
    return "generate"


def create_agent():
    workflow = StateGraph(AgentState)
    workflow.add_node("classify_intent", classify_intent_node)
    workflow.add_node("greeting", greeting_node)
    workflow.add_node("clarify", clarify_intent_node)
    workflow.add_node("auth_required", auth_required_node)
    workflow.add_node("support_request", support_request_node)
    workflow.add_node("offer_human", offer_human_node)
    workflow.add_node("order_status", order_status_node)
    workflow.add_node("rag", rag_node)
    workflow.add_node("evaluate", evaluate_rag_node)
    workflow.add_node("style_advice", style_advice_node)
    workflow.add_node("web", web_search_node)
    workflow.add_node("escalate", escalation_node)
    workflow.add_node("generate", generate_answer_node)

    workflow.set_entry_point("classify_intent")
    workflow.add_conditional_edges(
        "classify_intent",
        route_after_intent,
        {
            "greeting": "greeting",
            "rag": "rag",
            "order_status": "order_status",
            "auth_required": "auth_required",
            "support_request": "support_request",
            "offer_human": "offer_human",
            "web": "web",
            "escalate": "escalate",
            "clarify": "clarify",
        },
    )
    workflow.add_edge("greeting", END)
    workflow.add_edge("clarify", END)
    workflow.add_edge("auth_required", END)
    workflow.add_edge("support_request", END)
    workflow.add_edge("offer_human", END)
    workflow.add_edge("order_status", END)
    workflow.add_edge("rag", "evaluate")
    workflow.add_conditional_edges(
        "evaluate",
        route_after_rag,
        {"generate": "generate", "style_advice": "style_advice", "web": "web", "escalate": "escalate"},
    )
    workflow.add_edge("style_advice", END)
    workflow.add_conditional_edges(
        "web",
        route_after_web,
        {"generate": "generate", "style_advice": "style_advice", "escalate": "escalate"},
    )
    workflow.add_edge("escalate", "generate")
    workflow.add_edge("generate", END)
    return workflow.compile()


_agent = None


def get_agent():
    global _agent
    if _agent is None:
        _agent = create_agent()
    return _agent
