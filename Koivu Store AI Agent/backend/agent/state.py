"""Typed LangGraph workflow state. User identity is injected by FastAPI, not the LLM."""

from typing import Any, NotRequired, TypedDict


class AgentState(TypedDict):
    question: str
    standalone_question: NotRequired[str]
    intent: NotRequired[str]
    human_requested: NotRequired[bool]
    human_recommended: NotRequired[bool]
    web_search_needed: NotRequired[bool]
    human_offer_pending: NotRequired[bool]
    create_support_case: NotRequired[bool]
    rag_results: NotRequired[list[dict[str, Any]]]
    web_results: NotRequired[list[dict[str, Any]]]
    answer: NotRequired[str]
    path_taken: NotRequired[str]
    should_escalate: NotRequired[bool]
    escalation_reason: NotRequired[str]
    needs_human: NotRequired[bool]
    iteration_count: NotRequired[int]
    rag_was_sufficient: NotRequired[bool]
    history: NotRequired[list[dict[str, str]]]
    user_id: NotRequired[str | None]
    order_tool: NotRequired[Any]
    support_case_id: NotRequired[str | None]
    auth_required: NotRequired[bool]
    source_ids: NotRequired[list[str]]
    request_id: NotRequired[str]
    llm_calls: NotRequired[int]
    input_tokens: NotRequired[int]
    output_tokens: NotRequired[int]
    classification_failed: NotRequired[bool]
    rag_failed: NotRequired[bool]
    evaluation_failed: NotRequired[bool]
    order_status_checked: NotRequired[bool]
