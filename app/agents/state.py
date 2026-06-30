from typing import Any, TypedDict


class AgentState(TypedDict, total=False):
    session_id: str
    user_message: str
    intent: str
    missing_slots: list[str]
    session_context: dict[str, Any]
    recommended_products: list[dict]
    selected_items: list[dict]
    coupon_plan: dict
    cart: dict
    order: dict
    knowledge_snippets: list[dict]
    need_clarification: bool
    need_user_confirmation: bool
    pending_action: dict | None
    final_answer: str
    trace_steps: list[dict]