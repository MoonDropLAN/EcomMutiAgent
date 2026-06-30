from app.services.order_service import OrderService
from app.tools.registry import ToolDefinition, ToolRegistry


def register_order_tools(registry: ToolRegistry, order_service: OrderService) -> None:
    registry.register(
        ToolDefinition(
            name="order.create",
            description="Create order after user confirmation",
            permission_level="high_risk",
            handler=lambda payload: order_service.create_order(
                session_id=payload["session_id"],
                items=payload["items"],
                coupon_plan=payload["coupon_plan"],
            ),
        )
    )
    registry.register(
        ToolDefinition(
            name="order.get_status",
            description="Get order status",
            permission_level="read_only",
            handler=lambda payload: order_service.get_order(payload["order_id"]),
        )
    )
    registry.register(
        ToolDefinition(
            name="order.handle_timeout",
            description="Simulate payment timeout and rollback locks",
            permission_level="state_mutation",
            handler=lambda payload: order_service.handle_timeout(payload["order_id"]),
        )
    )