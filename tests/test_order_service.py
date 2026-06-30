from pathlib import Path
from uuid import uuid4

import pytest

from app.db.database import connect, init_db
from app.db.seed import seed_demo_data
from app.services.inventory_service import InventoryService
from app.services.order_service import OrderService


def services():
    path = Path("data/test_dbs") / f"test_{uuid4().hex}.db"
    conn = connect(path)
    init_db(conn, Path("app/db/schema.sql"))
    seed_demo_data(conn)
    inventory = InventoryService(conn)
    orders = OrderService(conn, inventory)
    return conn, inventory, orders


def test_create_order_locks_inventory_and_timeout_releases_it():
    _conn, inventory, orders = services()
    order = orders.create_order(
        session_id="demo",
        items=[{"product_id": "pad_mate_11", "price": 2699, "quantity": 1}],
        coupon_plan={"coupon_ids": ["coupon_student_100"], "discount_amount": 100, "payable_amount": 2599},
    )

    assert order["status"] == "PendingPayment"
    assert inventory.get_stock("pad_mate_11") == {"available_stock": 9, "locked_stock": 1}
    assert orders.get_coupon_lock_statuses(order["id"]) == {"coupon_student_100": "LOCKED"}

    canceled = orders.handle_timeout(order["id"])

    assert canceled["status"] == "TimeoutCanceled"
    assert inventory.get_stock("pad_mate_11") == {"available_stock": 10, "locked_stock": 0}
    assert orders.get_coupon_lock_statuses(order["id"]) == {"coupon_student_100": "RELEASED"}
    assert [event["status"] for event in orders.get_order_events(order["id"])] == ["PendingPayment", "TimeoutCanceled"]


def test_paid_order_consumes_inventory_and_can_request_refund():
    _conn, inventory, orders = services()
    order = orders.create_order(
        session_id="demo",
        items=[{"product_id": "pad_mate_11", "price": 2699, "quantity": 1}],
        coupon_plan={"coupon_ids": ["coupon_student_100"], "discount_amount": 100, "payable_amount": 2599},
    )

    paid = orders.simulate_payment(order["id"])
    assert paid["status"] == "Paid"
    assert inventory.get_stock("pad_mate_11") == {"available_stock": 9, "locked_stock": 0}
    assert orders.get_coupon_lock_statuses(order["id"]) == {"coupon_student_100": "USED"}

    refund = orders.request_refund(order["id"], eligible=True)
    assert refund["status"] == "RefundProcessing"


def test_cancel_pending_order_releases_inventory_and_coupon():
    _conn, inventory, orders = services()
    order = orders.create_order(
        session_id="demo",
        items=[{"product_id": "pad_mate_11", "price": 2699, "quantity": 1}],
        coupon_plan={"coupon_ids": ["coupon_student_100"], "discount_amount": 100, "payable_amount": 2599},
    )

    canceled = orders.cancel_pending_order(order["id"])

    assert canceled["status"] == "UserCanceled"
    assert inventory.get_stock("pad_mate_11") == {"available_stock": 10, "locked_stock": 0}
    assert orders.get_coupon_lock_statuses(order["id"]) == {"coupon_student_100": "RELEASED"}


def test_create_order_rolls_back_inventory_when_any_item_lock_fails():
    conn, inventory, orders = services()

    with pytest.raises(ValueError, match="库存不足"):
        orders.create_order(
            session_id="demo",
            items=[
                {"product_id": "pad_mate_11", "price": 2699, "quantity": 1},
                {"product_id": "pad_xiaomi_6", "price": 2299, "quantity": 99},
            ],
            coupon_plan={"coupon_ids": ["coupon_student_100"], "discount_amount": 100, "payable_amount": 4898},
        )

    assert inventory.get_stock("pad_mate_11") == {"available_stock": 10, "locked_stock": 0}
    assert conn.execute("SELECT COUNT(*) FROM orders").fetchone()[0] == 0