from app.services.product_service import ProductService
from app.services.session_service import SessionService


def product_guide_node(state: dict, product_service: ProductService, session_service: SessionService) -> dict:
    budget = state.get("session_context", {}).get("budget", 4000)
    products = product_service.search(category="tablet", max_price=budget)
    recommended = [product.model_dump(mode="json") for product in products[:2]]
    selected_items = []
    if recommended:
        selected_items = [
            {
                "product_id": recommended[0]["id"],
                "category": recommended[0]["category"],
                "price": recommended[0]["base_price"],
                "quantity": 1,
            }
        ]
    state["recommended_products"] = recommended
    state["selected_items"] = selected_items
    session_service.save_context(
        state["session_id"],
        {"recommended_products": recommended, "selected_items": selected_items},
    )
    state.setdefault("trace_steps", []).append({
        "agent_name": "ProductGuideAgent",
        "intent": state.get("intent"),
        "tool_name": "product.search",
        "tool_output_summary": f"推荐 {len(recommended)} 个商品",
        "decision_reason": "用户需要学生记笔记平板推荐",
    })
    return state