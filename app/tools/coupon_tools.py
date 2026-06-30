from app.services.coupon_service import CouponService
from app.tools.registry import ToolDefinition, ToolRegistry


def register_coupon_tools(registry: ToolRegistry, coupon_service: CouponService) -> None:
    def calculate(payload: dict) -> dict:
        return coupon_service.calculate_best_plan(
            items=payload.get("items", []),
            is_student=bool(payload.get("is_student", True)),
        )

    registry.register(
        ToolDefinition(
            name="coupon.calculate_best_plan",
            description="Calculate best coupon plan for selected items",
            permission_level="business_calculation",
            handler=calculate,
        )
    )