from pathlib import Path
from uuid import uuid4

from app.db.database import connect, init_db
from app.db.seed import seed_demo_data
from app.services.coupon_service import CouponService


def seeded_conn():
    path = Path("data/test_dbs") / f"test_{uuid4().hex}.db"
    conn = connect(path)
    init_db(conn, Path("app/db/schema.sql"))
    seed_demo_data(conn)
    return conn


def test_calculate_best_plan_for_student_tablet_bundle():
    service = CouponService(seeded_conn())
    items = [
        {"product_id": "pad_mate_11", "category": "tablet", "price": 2699, "quantity": 1},
        {"product_id": "stylus_huawei", "category": "accessory", "price": 599, "quantity": 1},
        {"product_id": "keyboard_huawei", "category": "accessory", "price": 499, "quantity": 1},
    ]

    result = service.calculate_best_plan(items=items, is_student=True)

    assert result["total_amount"] == 3797
    assert result["best_plan"]["discount_amount"] == 850
    assert result["best_plan"]["payable_amount"] == 2947
    assert set(result["best_plan"]["coupon_ids"]) == {
        "coupon_tablet_200",
        "coupon_bundle_300",
        "coupon_student_100",
        "coupon_full_250",
    }


def test_student_coupon_is_ineligible_for_non_student():
    service = CouponService(seeded_conn())
    items = [{"product_id": "pad_mate_11", "category": "tablet", "price": 2699, "quantity": 1}]

    result = service.calculate_best_plan(items=items, is_student=False)

    assert "coupon_student_100" not in result["best_plan"]["coupon_ids"]
    assert {item["coupon_id"]: item["reason"] for item in result["ineligible_coupons"]}["coupon_student_100"] == "仅学生用户可用"


def test_same_stack_group_uses_largest_discount_only():
    conn = seeded_conn()
    conn.execute(
        """
        INSERT INTO coupons
        (id, name, coupon_type, target_category, target_product_id, threshold_amount,
         discount_amount, stack_group, is_student_only, is_active)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        ("coupon_tablet_300", "平板品类券满 2000 减 300", "category", "tablet", None, 2000, 300, "category", 0, 1),
    )
    conn.commit()
    service = CouponService(conn)
    items = [{"product_id": "pad_mate_11", "category": "tablet", "price": 2699, "quantity": 1}]

    result = service.calculate_best_plan(items=items, is_student=True)

    assert "coupon_tablet_300" in result["best_plan"]["coupon_ids"]
    assert "coupon_tablet_200" not in result["best_plan"]["coupon_ids"]