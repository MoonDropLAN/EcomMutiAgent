import sqlite3
from collections import defaultdict


class CouponService:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def calculate_best_plan(self, items: list[dict], is_student: bool) -> dict:
        total_amount = sum(item["price"] * item["quantity"] for item in items)
        categories = {item["category"] for item in items}
        product_ids = {item["product_id"] for item in items}
        coupons = self.conn.execute("SELECT * FROM coupons WHERE is_active = 1").fetchall()

        eligible_by_group: dict[str, list[dict]] = defaultdict(list)
        ineligible = []
        for coupon in coupons:
            reason = self._ineligible_reason(coupon, total_amount, categories, product_ids, is_student)
            if reason:
                ineligible.append({"coupon_id": coupon["id"], "reason": reason})
                continue
            eligible_by_group[coupon["stack_group"]].append(
                {
                    "coupon_id": coupon["id"],
                    "name": coupon["name"],
                    "discount_amount": coupon["discount_amount"],
                    "stack_group": coupon["stack_group"],
                }
            )

        eligible = []
        for group_coupons in eligible_by_group.values():
            eligible.append(max(group_coupons, key=lambda item: item["discount_amount"]))

        eligible.sort(key=lambda item: item["coupon_id"])
        discount_amount = sum(item["discount_amount"] for item in eligible)
        coupon_ids = [item["coupon_id"] for item in eligible]
        return {
            "total_amount": total_amount,
            "eligible_coupons": eligible,
            "ineligible_coupons": ineligible,
            "best_plan": {
                "coupon_ids": coupon_ids,
                "discount_amount": discount_amount,
                "payable_amount": total_amount - discount_amount,
                "explanation": "按 V1 规则选择每个可叠加组中优惠金额最高的组合",
            },
        }

    def _ineligible_reason(
        self,
        coupon,
        total_amount: int,
        categories: set[str],
        product_ids: set[str],
        is_student: bool,
    ) -> str | None:
        if coupon["threshold_amount"] is not None and total_amount < coupon["threshold_amount"]:
            return "未达到满减门槛"
        if coupon["is_student_only"] and not is_student:
            return "仅学生用户可用"
        if coupon["target_category"] and coupon["target_category"] not in categories:
            return "不适用于当前品类"
        if coupon["target_product_id"] and coupon["target_product_id"] not in product_ids:
            return "不适用于当前商品"
        return None