import json
import sqlite3
from datetime import datetime, timezone
from uuid import uuid4

from app.services.inventory_service import InventoryService


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class OrderService:
    def __init__(self, conn: sqlite3.Connection, inventory: InventoryService):
        self.conn = conn
        self.inventory = inventory

    def create_order(self, session_id: str, items: list[dict], coupon_plan: dict) -> dict:
        locked_items: list[dict] = []
        for item in items:
            if not self.inventory.lock(item["product_id"], item["quantity"]):
                for locked in locked_items:
                    self.inventory.release(locked["product_id"], locked["quantity"])
                raise ValueError(f"库存不足: {item['product_id']}")
            locked_items.append(item)

        total_amount = sum(item["price"] * item["quantity"] for item in items)
        discount_amount = int(coupon_plan.get("discount_amount", 0))
        payable_amount = int(coupon_plan.get("payable_amount", total_amount - discount_amount))
        order_id = f"order_{uuid4().hex[:8]}"
        now = utc_now()
        self.conn.execute(
            """
            INSERT INTO orders
            (id, session_id, status, items_json, coupon_plan_json, total_amount,
             discount_amount, payable_amount, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                order_id,
                session_id,
                "PendingPayment",
                json.dumps(items, ensure_ascii=False),
                json.dumps(coupon_plan, ensure_ascii=False),
                total_amount,
                discount_amount,
                payable_amount,
                now,
                now,
            ),
        )
        self._lock_coupons(order_id, coupon_plan.get("coupon_ids", []))
        self._add_event(order_id, "PendingPayment", "订单已创建，库存和优惠券已锁定")
        self.conn.commit()
        return self.get_order(order_id)

    def get_order(self, order_id: str) -> dict:
        row = self.conn.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()
        if row is None:
            raise ValueError(f"订单不存在: {order_id}")
        order = dict(row)
        order["items"] = json.loads(order["items_json"])
        order["coupon_plan"] = json.loads(order["coupon_plan_json"])
        return order

    def get_latest_order_for_session(self, session_id: str) -> dict | None:
        row = self.conn.execute(
            "SELECT id FROM orders WHERE session_id = ? ORDER BY created_at DESC LIMIT 1",
            (session_id,),
        ).fetchone()
        return self.get_order(row["id"]) if row else None

    def handle_timeout(self, order_id: str) -> dict:
        order = self.get_order(order_id)
        if order["status"] != "PendingPayment":
            return order
        for item in order["items"]:
            self.inventory.release(item["product_id"], item["quantity"])
        self._mark_coupon_locks(order_id, "RELEASED")
        self._update_status(order_id, "TimeoutCanceled", "支付超时，库存和优惠券已释放")
        return self.get_order(order_id)

    def simulate_payment(self, order_id: str) -> dict:
        order = self.get_order(order_id)
        if order["status"] != "PendingPayment":
            return order
        for item in order["items"]:
            self.inventory.consume_locked(item["product_id"], item["quantity"])
        self._mark_coupon_locks(order_id, "USED")
        self._update_status(order_id, "Paid", "支付成功，库存已扣减，优惠券已使用")
        return self.get_order(order_id)

    def cancel_pending_order(self, order_id: str) -> dict:
        order = self.get_order(order_id)
        if order["status"] != "PendingPayment":
            return order
        for item in order["items"]:
            self.inventory.release(item["product_id"], item["quantity"])
        self._mark_coupon_locks(order_id, "RELEASED")
        self._update_status(order_id, "UserCanceled", "用户取消待支付订单，库存和优惠券已释放")
        return self.get_order(order_id)

    def request_refund(self, order_id: str, eligible: bool) -> dict:
        order = self.get_order(order_id)
        if order["status"] != "Paid":
            raise ValueError("只有已支付订单才能申请退款")
        self._update_status(order_id, "RefundRequested", "用户已申请退款")
        final_status = "RefundProcessing" if eligible else "RefundRejected"
        message = "退款申请符合规则，进入处理" if eligible else "退款申请不符合规则，已拒绝"
        self._update_status(order_id, final_status, message)
        return self.get_order(order_id)

    def get_coupon_lock_statuses(self, order_id: str) -> dict[str, str]:
        rows = self.conn.execute(
            "SELECT coupon_id, status FROM coupon_locks WHERE order_id = ? ORDER BY coupon_id",
            (order_id,),
        ).fetchall()
        return {row["coupon_id"]: row["status"] for row in rows}

    def get_order_events(self, order_id: str) -> list[dict]:
        rows = self.conn.execute(
            "SELECT status, message, created_at FROM order_events WHERE order_id = ? ORDER BY id",
            (order_id,),
        ).fetchall()
        return [dict(row) for row in rows]

    def _lock_coupons(self, order_id: str, coupon_ids: list[str]) -> None:
        for coupon_id in coupon_ids:
            self.conn.execute(
                "INSERT INTO coupon_locks (order_id, coupon_id, status) VALUES (?, ?, ?)",
                (order_id, coupon_id, "LOCKED"),
            )

    def _mark_coupon_locks(self, order_id: str, status: str) -> None:
        self.conn.execute("UPDATE coupon_locks SET status = ? WHERE order_id = ?", (status, order_id))

    def _update_status(self, order_id: str, status: str, message: str) -> None:
        self.conn.execute(
            "UPDATE orders SET status = ?, updated_at = ? WHERE id = ?",
            (status, utc_now(), order_id),
        )
        self._add_event(order_id, status, message)
        self.conn.commit()

    def _add_event(self, order_id: str, status: str, message: str) -> None:
        self.conn.execute(
            "INSERT INTO order_events (order_id, status, message, created_at) VALUES (?, ?, ?, ?)",
            (order_id, status, message, utc_now()),
        )