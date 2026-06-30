import json
import sqlite3


PRODUCTS = [
    ("pad_mate_11", "MatePad 11 学习版", "tablet", "Huawei", 2699, ["note", "student"], {"screen": "11 inch", "stylus": True, "battery": "8300mAh"}, 95),
    ("pad_xiaomi_6", "Xiaomi Pad 6", "tablet", "Xiaomi", 2299, ["note", "budget"], {"screen": "11 inch", "stylus": True, "battery": "8840mAh"}, 90),
    ("pad_lenovo_xiaoxin", "Lenovo Xiaoxin Pad Pro", "tablet", "Lenovo", 1999, ["budget", "video"], {"screen": "12.7 inch", "stylus": True, "battery": "10200mAh"}, 82),
    ("pad_apple_air", "iPad Air 学习版", "tablet", "Apple", 4399, ["note", "premium"], {"screen": "10.9 inch", "stylus": True, "battery": "all-day"}, 88),
    ("phone_redmi_k", "Redmi K 学生性能版", "phone", "Xiaomi", 2499, ["gaming", "student"], {"refresh_rate": "120Hz", "battery": "5000mAh", "charging": "67W"}, 86),
    ("phone_honor_x", "Honor X 长续航版", "phone", "Honor", 1899, ["battery", "daily"], {"battery": "5800mAh", "camera": "108MP"}, 80),
    ("phone_iqoo_z", "iQOO Z 游戏版", "phone", "iQOO", 2999, ["gaming", "performance"], {"refresh_rate": "144Hz", "cooling": True}, 84),
    ("earbuds_sony_nc", "Sony 入门降噪耳机", "earphone", "Sony", 899, ["noise_cancel", "commute"], {"anc": True, "battery": "30h"}, 83),
    ("earbuds_huawei_freebuds", "FreeBuds 学生降噪版", "earphone", "Huawei", 699, ["noise_cancel", "budget"], {"anc": True, "battery": "28h"}, 81),
    ("earbuds_xiaomi_nc", "Xiaomi Buds 通勤版", "earphone", "Xiaomi", 399, ["commute", "budget"], {"anc": True, "battery": "36h"}, 78),
    ("stylus_huawei", "Huawei M-Pencil", "accessory", "Huawei", 599, ["stylus"], {"compatible": "pad_mate_11"}, 80),
    ("keyboard_huawei", "Huawei Smart Keyboard", "accessory", "Huawei", 499, ["keyboard"], {"compatible": "pad_mate_11"}, 75),
    ("case_tablet_student", "学生平板保护壳", "accessory", "Generic", 129, ["case"], {"compatible": "tablet"}, 65),
]

COUPONS = [
    ("coupon_tablet_200", "平板品类券满 2000 减 200", "category", "tablet", None, 2000, 200, "category", 0, 1),
    ("coupon_phone_150", "手机品类券满 2000 减 150", "category", "phone", None, 2000, 150, "category", 0, 1),
    ("coupon_earphone_80", "耳机品类券满 500 减 80", "category", "earphone", None, 500, 80, "category", 0, 1),
    ("coupon_bundle_300", "学习套装券减 300", "bundle", None, None, 3000, 300, "bundle", 0, 1),
    ("coupon_student_100", "学生优惠减 100", "student", None, None, 1000, 100, "student", 1, 1),
    ("coupon_full_250", "全场满 3500 减 250", "threshold", None, None, 3500, 250, "threshold", 0, 1),
]


def seed_demo_data(conn: sqlite3.Connection) -> None:
    for product in PRODUCTS:
        conn.execute(
            """
            INSERT INTO products
            (id, name, category, brand, base_price, tags_json, specs_json, student_scenario_score)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
              name = excluded.name,
              category = excluded.category,
              brand = excluded.brand,
              base_price = excluded.base_price,
              tags_json = excluded.tags_json,
              specs_json = excluded.specs_json,
              student_scenario_score = excluded.student_scenario_score
            """,
            (
                product[0],
                product[1],
                product[2],
                product[3],
                product[4],
                json.dumps(product[5], ensure_ascii=False),
                json.dumps(product[6], ensure_ascii=False),
                product[7],
            ),
        )
        conn.execute(
            "INSERT OR IGNORE INTO inventory (product_id, available_stock, locked_stock) VALUES (?, ?, ?)",
            (product[0], 10, 0),
        )
    for coupon in COUPONS:
        conn.execute(
            """
            INSERT INTO coupons
            (id, name, coupon_type, target_category, target_product_id, threshold_amount,
             discount_amount, stack_group, is_student_only, is_active)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
              name = excluded.name,
              coupon_type = excluded.coupon_type,
              target_category = excluded.target_category,
              target_product_id = excluded.target_product_id,
              threshold_amount = excluded.threshold_amount,
              discount_amount = excluded.discount_amount,
              stack_group = excluded.stack_group,
              is_student_only = excluded.is_student_only,
              is_active = excluded.is_active
            """,
            coupon,
        )
    conn.commit()