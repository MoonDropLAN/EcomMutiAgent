from app.services.inventory_service import InventoryService
from app.services.product_service import ProductService
from app.tools.registry import ToolDefinition, ToolRegistry


def register_product_tools(registry: ToolRegistry, product_service: ProductService, inventory: InventoryService) -> None:
    def search(payload: dict) -> dict:
        products = product_service.search(
            category=payload.get("category"),
            max_price=payload.get("max_price"),
        )
        product_dicts = [product.model_dump(mode="json") for product in products]
        for product in product_dicts:
            product["stock"] = inventory.get_stock(product["id"])
        return {"products": product_dicts, "summary": f"找到 {len(product_dicts)} 个商品"}

    registry.register(
        ToolDefinition(
            name="product.search",
            description="Search products by category and budget",
            permission_level="read_only",
            handler=search,
        )
    )