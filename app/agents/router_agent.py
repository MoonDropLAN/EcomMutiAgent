import re


def route_intent(message: str) -> dict:
    normalized = message.strip()
    missing_slots: list[str] = []
    has_budget = bool(re.search(r"\d{3,5}", message))

    if normalized in {"确认", "继续", "是", "确定"}:
        return {"intent": "confirm_pending_action", "missing_slots": []}

    if any(word in message for word in ["支付超时", "超时", "模拟支付"]):
        return {"intent": "simulate_payment_timeout", "missing_slots": []}

    if any(word in message for word in ["下单", "购买", "帮我买"]):
        return {"intent": "create_order", "missing_slots": []}

    if "订单" in message and any(word in message for word in ["退款", "退货", "售后", "状态"]):
        return {"intent": "after_sales_query", "missing_slots": []}

    if any(word in message for word in ["政策", "规则", "保修", "七天无理由", "退货", "退款", "价保"]):
        return {"intent": "knowledge_qa", "missing_slots": []}

    if any(word in message for word in ["优惠", "券", "最便宜", "划算"]):
        if any(word in message for word in ["平板", "手机", "耳机", "记笔记"]):
            if not has_budget:
                missing_slots.append("budget")
            return {"intent": "product_guide_with_coupon", "missing_slots": missing_slots}
        return {"intent": "coupon_query", "missing_slots": []}

    if any(word in message for word in ["平板", "手机", "耳机", "记笔记", "推荐", "对比"]):
        if not has_budget:
            missing_slots.append("budget")
        return {"intent": "product_guide", "missing_slots": missing_slots}

    return {"intent": "general", "missing_slots": []}