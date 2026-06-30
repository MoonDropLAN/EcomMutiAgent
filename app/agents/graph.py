import re
import sqlite3

from langgraph.graph import END, StateGraph

from app.agents.coupon_agent import coupon_node
from app.agents.knowledge_qa_agent import knowledge_qa_node
from app.agents.order_lifecycle_agent import (
    after_sales_node,
    confirm_pending_action_node,
    payment_timeout_node,
    prepare_create_order_node,
)
from app.agents.product_guide_agent import product_guide_node
from app.agents.response_composer import compose_response
from app.agents.router_agent import route_intent
from app.agents.state import AgentState
from app.config import get_settings
from app.services.coupon_service import CouponService
from app.services.inventory_service import InventoryService
from app.services.order_service import OrderService
from app.services.product_service import ProductService
from app.services.session_service import SessionService
from app.tools.knowledge_tools import KnowledgeTools


def _extract_budget(message: str) -> int | None:
    match = re.search(r"(\d{3,5})", message)
    return int(match.group(1)) if match else None


def router_node(state: AgentState) -> AgentState:
    routing = route_intent(state["user_message"])
    state["intent"] = routing["intent"]
    state["missing_slots"] = routing["missing_slots"]
    state["session_context"] = {"budget": _extract_budget(state["user_message"]) or 4000}
    state["trace_steps"] = [
        {
            "agent_name": "TaskRouterAgent",
            "intent": routing["intent"],
            "tool_name": None,
            "tool_output_summary": None,
            "decision_reason": "基于关键词和必要槽位进行 V1 路由",
        }
    ]
    if routing["missing_slots"]:
        state["need_clarification"] = True
    return state


def route_after_router(state: AgentState) -> str:
    if state.get("need_clarification"):
        return "compose"
    intent = state["intent"]
    if intent in {"product_guide", "product_guide_with_coupon"}:
        return "product_guide"
    if intent == "coupon_query":
        return "coupon"
    if intent == "knowledge_qa":
        return "knowledge_qa"
    if intent == "create_order":
        return "prepare_create_order"
    if intent == "confirm_pending_action":
        return "confirm_pending_action"
    if intent == "simulate_payment_timeout":
        return "payment_timeout"
    if intent == "after_sales_query":
        return "after_sales"
    return "compose"


def route_after_product(state: AgentState) -> str:
    if state["intent"] == "product_guide_with_coupon":
        return "coupon"
    return "compose"


def build_graph(conn: sqlite3.Connection):
    product_service = ProductService(conn)
    coupon_service = CouponService(conn)
    inventory_service = InventoryService(conn)
    order_service = OrderService(conn, inventory_service)
    session_service = SessionService(conn)
    knowledge_tools = KnowledgeTools(get_settings())

    graph = StateGraph(AgentState)
    graph.add_node("router", router_node)
    graph.add_node("product_guide", lambda state: product_guide_node(state, product_service, session_service))
    graph.add_node("coupon", lambda state: coupon_node(state, coupon_service, session_service))
    graph.add_node("knowledge_qa", lambda state: knowledge_qa_node(state, knowledge_tools))
    graph.add_node("prepare_create_order", lambda state: prepare_create_order_node(state, session_service))
    graph.add_node("confirm_pending_action", lambda state: confirm_pending_action_node(state, session_service, order_service))
    graph.add_node("payment_timeout", lambda state: payment_timeout_node(state, session_service, order_service))
    graph.add_node("after_sales", lambda state: after_sales_node(state, session_service, order_service))
    graph.add_node("compose", compose_response)

    graph.set_entry_point("router")
    graph.add_conditional_edges(
        "router",
        route_after_router,
        {
            "product_guide": "product_guide",
            "coupon": "coupon",
            "knowledge_qa": "knowledge_qa",
            "prepare_create_order": "prepare_create_order",
            "confirm_pending_action": "confirm_pending_action",
            "payment_timeout": "payment_timeout",
            "after_sales": "after_sales",
            "compose": "compose",
        },
    )
    graph.add_conditional_edges("product_guide", route_after_product, {"coupon": "coupon", "compose": "compose"})
    graph.add_edge("coupon", "compose")
    graph.add_edge("knowledge_qa", "compose")
    graph.add_edge("prepare_create_order", END)
    graph.add_edge("confirm_pending_action", END)
    graph.add_edge("payment_timeout", END)
    graph.add_edge("after_sales", END)
    graph.add_edge("compose", END)
    return graph.compile()


def run_agent_flow(conn: sqlite3.Connection, session_id: str, message: str) -> dict:
    app = build_graph(conn)
    return app.invoke({"session_id": session_id, "user_message": message})