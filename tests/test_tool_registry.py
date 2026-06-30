from pathlib import Path
from uuid import uuid4

from app.db.database import connect, init_db
from app.db.seed import seed_demo_data
from app.services.coupon_service import CouponService
from app.services.inventory_service import InventoryService
from app.services.order_service import OrderService
from app.services.product_service import ProductService
from app.tools.coupon_tools import register_coupon_tools
from app.tools.knowledge_tools import adapt_mcp_text_to_snippets
from app.tools.order_tools import register_order_tools
from app.tools.product_tools import register_product_tools
from app.tools.registry import ToolRegistry


def registry_with_services():
    path = Path("data/test_dbs") / f"test_{uuid4().hex}.db"
    conn = connect(path)
    init_db(conn, Path("app/db/schema.sql"))
    seed_demo_data(conn)
    registry = ToolRegistry()
    inventory = InventoryService(conn)
    register_product_tools(registry, ProductService(conn), inventory)
    register_coupon_tools(registry, CouponService(conn))
    register_order_tools(registry, OrderService(conn, inventory))
    return registry


def test_tool_registry_invokes_product_search():
    registry = registry_with_services()

    result = registry.call("product.search", {"category": "tablet", "max_price": 3000})

    assert result["products"][0]["id"] == "pad_mate_11"
    assert result["summary"].startswith("找到")


def test_tool_registry_invokes_coupon_calculation():
    registry = registry_with_services()

    result = registry.call(
        "coupon.calculate_best_plan",
        {
            "items": [{"product_id": "pad_mate_11", "category": "tablet", "price": 2699, "quantity": 1}],
            "is_student": True,
        },
    )

    assert result["best_plan"]["payable_amount"] < result["total_amount"]


def test_tool_registry_rejects_unknown_tool():
    registry = ToolRegistry()

    try:
        registry.call("missing.tool", {})
    except KeyError as exc:
        assert "missing.tool" in str(exc)
    else:
        raise AssertionError("unknown tool should raise KeyError")


def test_adapt_mcp_text_to_snippets():
    text = "七天无理由退货政策：平板激活后不支持七天无理由退货，质量问题除外。"

    result = adapt_mcp_text_to_snippets(text)

    assert result["snippets"] == [
        {
            "title": "RAG 检索结果",
            "policy_type": "unknown",
            "content": text,
            "source": "mcp:query_knowledge_hub",
            "score": None,
        }
    ]