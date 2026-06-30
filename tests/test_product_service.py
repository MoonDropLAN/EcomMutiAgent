from pathlib import Path
from uuid import uuid4

from app.db.database import connect, init_db
from app.db.seed import seed_demo_data
from app.services.inventory_service import InventoryService
from app.services.product_service import ProductService


def seeded_conn():
    path = Path("data/test_dbs") / f"test_{uuid4().hex}.db"
    conn = connect(path)
    init_db(conn, Path("app/db/schema.sql"))
    seed_demo_data(conn)
    return conn


def test_search_tablets_under_budget_orders_by_student_fit():
    service = ProductService(seeded_conn())

    products = service.search(category="tablet", max_price=3000)

    assert [p.id for p in products[:2]] == ["pad_mate_11", "pad_xiaomi_6"]
    assert all(p.base_price <= 3000 for p in products)


def test_lock_and_release_inventory():
    service = InventoryService(seeded_conn())

    assert service.lock("pad_mate_11", quantity=2) is True
    assert service.get_stock("pad_mate_11") == {"available_stock": 8, "locked_stock": 2}

    service.release("pad_mate_11", quantity=2)

    assert service.get_stock("pad_mate_11") == {"available_stock": 10, "locked_stock": 0}


def test_consume_locked_inventory_after_payment():
    service = InventoryService(seeded_conn())

    assert service.lock("pad_mate_11", quantity=1) is True
    service.consume_locked("pad_mate_11", quantity=1)

    assert service.get_stock("pad_mate_11") == {"available_stock": 9, "locked_stock": 0}


def test_lock_returns_false_when_stock_is_insufficient():
    service = InventoryService(seeded_conn())

    assert service.lock("pad_mate_11", quantity=99) is False
    assert service.get_stock("pad_mate_11") == {"available_stock": 10, "locked_stock": 0}