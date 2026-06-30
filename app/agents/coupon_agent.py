from app.services.coupon_service import CouponService
from app.services.session_service import SessionService


def coupon_node(state: dict, coupon_service: CouponService, session_service: SessionService) -> dict:
    items = state.get("selected_items") or session_service.get_context(state["session_id"]).get("selected_items", [])
    state["selected_items"] = items
    state["coupon_plan"] = coupon_service.calculate_best_plan(items=items, is_student=True)
    session_service.save_context(
        state["session_id"],
        {"selected_items": items, "coupon_plan": state["coupon_plan"]},
    )
    state.setdefault("trace_steps", []).append({
        "agent_name": "CouponAgent",
        "intent": state.get("intent"),
        "tool_name": "coupon.calculate_best_plan",
        "tool_output_summary": "完成最优优惠计算",
        "decision_reason": "用户询问优惠或最划算方案",
    })
    return state