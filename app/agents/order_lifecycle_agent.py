from app.services.order_service import OrderService
from app.services.session_service import SessionService


def prepare_create_order_node(state: dict, session_service: SessionService) -> dict:
    context = session_service.get_context(state["session_id"])
    items = state.get("selected_items") or context.get("selected_items")
    coupon_plan = state.get("coupon_plan", {}).get("best_plan") or context.get("coupon_plan", {}).get("best_plan")
    if not items or not coupon_plan:
        state["need_clarification"] = True
        state["need_user_confirmation"] = False
        state["pending_action"] = None
        state["final_answer"] = "我还没有可下单的已选商品和优惠方案。请先选择一个推荐方案，或告诉我要购买哪一款商品。"
        state.setdefault("trace_steps", []).append({
            "agent_name": "OrderLifecycleAgent",
            "intent": state.get("intent"),
            "tool_name": None,
            "tool_output_summary": "缺少 selected_items 或 coupon_plan，未创建 pending_action",
            "decision_reason": "创建订单必须基于用户已选方案，不能默认购买商品",
        })
        return state
    pending_action = {
        "action_type": "create_order",
        "payload": {"items": items, "coupon_plan": coupon_plan},
        "summary": f"创建订单，预计支付 {coupon_plan['payable_amount']} 元",
    }
    session_service.save_context(state["session_id"], {"pending_action": pending_action})
    state["need_user_confirmation"] = True
    state["pending_action"] = pending_action
    state["final_answer"] = pending_action["summary"] + "。请确认是否继续。"
    state.setdefault("trace_steps", []).append({
        "agent_name": "OrderLifecycleAgent",
        "intent": state.get("intent"),
        "tool_name": "order.create",
        "tool_output_summary": "高风险动作已暂停，等待用户确认",
        "decision_reason": "创建订单会锁库存和优惠券，必须先确认",
    })
    return state


def confirm_pending_action_node(state: dict, session_service: SessionService, order_service: OrderService) -> dict:
    context = session_service.get_context(state["session_id"])
    pending_action = context.get("pending_action")
    if not pending_action:
        state["pending_action"] = None
        state["final_answer"] = "当前没有需要确认的操作。"
        return state
    if pending_action["action_type"] != "create_order":
        state["pending_action"] = pending_action
        state["final_answer"] = "当前确认动作暂不支持自动执行，请转人工处理。"
        return state
    payload = pending_action["payload"]
    order = order_service.create_order(
        session_id=state["session_id"],
        items=payload["items"],
        coupon_plan=payload["coupon_plan"],
    )
    session_service.save_context(state["session_id"], {"pending_action": None, "last_order_id": order["id"]})
    state["need_user_confirmation"] = False
    state["pending_action"] = None
    state["order"] = order
    state["final_answer"] = f"已创建订单 {order['id']}，状态 {order['status']}，请在支付倒计时内完成支付。"
    state.setdefault("trace_steps", []).append({
        "agent_name": "OrderLifecycleAgent",
        "intent": state.get("intent"),
        "tool_name": "order.create",
        "tool_output_summary": f"创建订单 {order['id']}",
        "decision_reason": "用户已确认高风险动作",
    })
    return state


def payment_timeout_node(state: dict, session_service: SessionService, order_service: OrderService) -> dict:
    context = session_service.get_context(state["session_id"])
    order_id = context.get("last_order_id")
    if not order_id:
        state["need_clarification"] = True
        state["final_answer"] = "当前会话没有可模拟支付超时的订单。"
        return state
    order = order_service.handle_timeout(order_id)
    state["order"] = order
    state["final_answer"] = f"已模拟支付超时，订单 {order['id']} 状态变为 {order['status']}，库存和优惠券已释放。"
    state.setdefault("trace_steps", []).append({
        "agent_name": "OrderLifecycleAgent",
        "intent": state.get("intent"),
        "tool_name": "order.handle_timeout",
        "tool_output_summary": f"订单状态 {order['status']}",
        "decision_reason": "用户请求模拟支付超时",
    })
    return state


def after_sales_node(state: dict, session_service: SessionService, order_service: OrderService) -> dict:
    context = session_service.get_context(state["session_id"])
    order_id = context.get("last_order_id")
    if not order_id:
        state["need_clarification"] = True
        state["final_answer"] = "我需要订单 ID 才能判断这个订单是否可以退款。"
        return state
    order = order_service.get_order(order_id)
    state["order"] = order
    if order["status"] == "Paid":
        state["final_answer"] = f"订单 {order_id} 已支付，可以根据售后政策申请退款。"
    elif order["status"] == "TimeoutCanceled":
        state["final_answer"] = f"订单 {order_id} 未支付成功，已超时取消，不需要走退款；库存和优惠券已释放。"
    else:
        state["final_answer"] = f"订单 {order_id} 当前状态为 {order['status']}，需要结合售后政策进一步判断。"
    state.setdefault("trace_steps", []).append({
        "agent_name": "OrderLifecycleAgent",
        "intent": state.get("intent"),
        "tool_name": "order.get_status",
        "tool_output_summary": f"订单状态 {order['status']}",
        "decision_reason": "具体订单售后问题必须先查询订单状态",
    })
    return state