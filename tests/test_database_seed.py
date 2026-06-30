from pathlib import Path
from uuid import uuid4

from app.db.database import connect, init_db
from app.db.seed import seed_demo_data


def new_db_path() -> Path:
    path = Path("data/test_dbs") / f"test_{uuid4().hex}.db"
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def test_seed_demo_data_creates_multicategory_products_and_coupons():
    conn = connect(new_db_path())
    init_db(conn, Path("app/db/schema.sql"))

    seed_demo_data(conn)

    product_count = conn.execute("SELECT COUNT(*) FROM products").fetchone()[0]
    coupon_count = conn.execute("SELECT COUNT(*) FROM coupons").fetchone()[0]
    categories = {
        row[0]
        for row in conn.execute("SELECT DISTINCT category FROM products").fetchall()
    }

    assert product_count >= 12
    assert coupon_count >= 6
    assert {"tablet", "phone", "earphone", "accessory"}.issubset(categories)


def test_seed_demo_data_does_not_reset_runtime_inventory_state():
    conn = connect(new_db_path())
    init_db(conn, Path("app/db/schema.sql"))
    seed_demo_data(conn)
    conn.execute(
        "UPDATE inventory SET available_stock = 3, locked_stock = 2 WHERE product_id = ?",
        ("pad_mate_11",),
    )
    conn.commit()

    seed_demo_data(conn)

    stock = conn.execute(
        "SELECT available_stock, locked_stock FROM inventory WHERE product_id = ?",
        ("pad_mate_11",),
    ).fetchone()
    assert dict(stock) == {"available_stock": 3, "locked_stock": 2}