from pathlib import Path
from uuid import uuid4

from app.agents.graph import run_agent_flow
from app.db.database import connect, init_db
from app.db.seed import seed_demo_data
from app.services.inventory_service import InventoryService


def seeded_conn():
    path = Path("data/test_dbs") / f"test_{uuid4().hex}.db"
    conn = connect(path)
    init_db(conn, Path("app/db/schema.sql"))
    seed_demo_data(conn)
    return conn


def test_product_guide_with_coupon_flow_persists_selected_plan():
    conn = seeded_conn()

    result = run_agent_flow(
        conn=conn,
        session_id="demo",
        message="我预算 4000，想买适合上课记笔记的平板，有没有优惠",
    )

    assert result["intent"] == "product_guide_with_coupon"
    assert result["recommended_products"]
    assert result["selected_items"]
    assert result["coupon_plan"]["best_plan"]["payable_amount"] < result["coupon_plan"]["total_amount"]
    assert result["trace_steps"]


def test_create_order_without_selected_plan_asks_clarification():
    result = run_agent_flow(seeded_conn(), "demo", "帮我下单")

    assert result["need_clarification"] is True
    assert result.get("need_user_confirmation") is not True
    assert result.get("pending_action") is None
    assert "已选商品" in result["final_answer"]


def test_recommend_then_confirm_order_then_timeout_rolls_back_inventory():
    conn = seeded_conn()
    run_agent_flow(conn, "demo", "我预算 4000，想买适合上课记笔记的平板，有没有优惠")

    pending = run_agent_flow(conn, "demo", "帮我下单")
    assert pending["need_user_confirmation"] is True
    assert pending["pending_action"]["action_type"] == "create_order"

    confirmed = run_agent_flow(conn, "demo", "确认")
    order_id = confirmed["order"]["id"]
    assert confirmed["order"]["status"] == "PendingPayment"
    assert InventoryService(conn).get_stock("pad_mate_11") == {"available_stock": 9, "locked_stock": 1}

    timed_out = run_agent_flow(conn, "demo", "模拟支付超时")

    assert timed_out["order"]["id"] == order_id
    assert timed_out["order"]["status"] == "TimeoutCanceled"
    assert InventoryService(conn).get_stock("pad_mate_11") == {"available_stock": 10, "locked_stock": 0}


def test_after_sales_query_uses_latest_order_status():
    conn = seeded_conn()
    run_agent_flow(conn, "demo", "我预算 4000，想买适合上课记笔记的平板，有没有优惠")
    run_agent_flow(conn, "demo", "帮我下单")
    run_agent_flow(conn, "demo", "确认")
    run_agent_flow(conn, "demo", "模拟支付超时")

    result = run_agent_flow(conn, "demo", "这个订单能退款吗")

    assert result["intent"] == "after_sales_query"
    assert result["order"]["status"] == "TimeoutCanceled"
    assert "未支付成功" in result["final_answer"]