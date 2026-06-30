from app.agents.router_agent import route_intent


def test_route_product_guide_with_coupon():
    result = route_intent("我预算 3000，想买适合上课记笔记的平板，有没有优惠")

    assert result["intent"] == "product_guide_with_coupon"
    assert result["missing_slots"] == []


def test_route_product_guide_missing_budget():
    result = route_intent("想买适合上课记笔记的平板")

    assert result["intent"] == "product_guide"
    assert "budget" in result["missing_slots"]


def test_route_pure_policy_question():
    result = route_intent("平板激活后还能七天无理由退货吗")

    assert result["intent"] == "knowledge_qa"
    assert result["missing_slots"] == []


def test_route_order_refund_uses_after_sales_intent_without_order_id():
    result = route_intent("这个订单能退款吗")

    assert result["intent"] == "after_sales_query"
    assert result["missing_slots"] == []


def test_route_payment_timeout_simulation():
    result = route_intent("模拟支付超时")

    assert result["intent"] == "simulate_payment_timeout"
    assert result["missing_slots"] == []


def test_route_confirmation():
    result = route_intent("确认")

    assert result["intent"] == "confirm_pending_action"
    assert result["missing_slots"] == []