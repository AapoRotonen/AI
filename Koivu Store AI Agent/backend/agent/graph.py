"""
agent/graph.py - LangGraph-agentin rakenne
"""
from langgraph.graph import StateGraph, END
from agent.state import AgentState
from agent.nodes import rag_node, evaluate_rag_node, web_search_node, escalation_node, generate_answer_node
from core.config import get_settings

settings = get_settings()


def route_after_rag(state: AgentState) -> str:
    """Reitti RAG- ja asiakaspalveluluokituksen jälkeen."""
    if state.get("needs_human") and not state.get("human_mode"):
        return "escalate"
    if state.get("rag_was_sufficient"):
        return "generate"
    if state.get("iteration_count", 0) >= settings.max_iterations:
        return "escalate"
    if not settings.tavily_api_key:
        return "escalate"
    return "web"


def route_after_web(state: AgentState) -> str:
    """Reitti web-haun jälkeen."""
    if state.get("should_escalate") or not state.get("web_results"):
        return "escalate"
    return "generate"


def create_agent():
    """Rakentaa ja palauttaa LangGraph-agentin."""
    wf = StateGraph(AgentState)

    wf.add_node("rag", rag_node)
    wf.add_node("evaluate", evaluate_rag_node)
    wf.add_node("web", web_search_node)
    wf.add_node("escalate", escalation_node)
    wf.add_node("generate", generate_answer_node)

    wf.set_entry_point("rag")
    wf.add_edge("rag", "evaluate")
    wf.add_conditional_edges("evaluate", route_after_rag, {
        "generate": "generate",
        "web": "web",
        "escalate": "escalate"
    })
    wf.add_conditional_edges("web", route_after_web, {
        "generate": "generate",
        "escalate": "escalate"
    })
    wf.add_edge("escalate", "generate")
    wf.add_edge("generate", END)

    return wf.compile()


_agent = None


def get_agent():
    global _agent
    if _agent is None:
        _agent = create_agent()
    return _agent
