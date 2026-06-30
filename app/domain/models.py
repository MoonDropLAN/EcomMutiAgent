from enum import StrEnum
from pydantic import BaseModel, Field


class ProductCategory(StrEnum):
    TABLET = "tablet"
    PHONE = "phone"
    EARPHONE = "earphone"
    ACCESSORY = "accessory"


class OrderStatus(StrEnum):
    PENDING_PAYMENT = "PendingPayment"
    PAID = "Paid"
    TIMEOUT_CANCELED = "TimeoutCanceled"
    USER_CANCELED = "UserCanceled"
    REFUND_REQUESTED = "RefundRequested"
    REFUND_PROCESSING = "RefundProcessing"
    REFUNDED = "Refunded"
    REFUND_REJECTED = "RefundRejected"


class Product(BaseModel):
    id: str
    name: str
    category: ProductCategory
    brand: str
    base_price: int
    tags: list[str] = Field(default_factory=list)
    specs: dict[str, str | int | float | bool] = Field(default_factory=dict)
    student_scenario_score: int = 0