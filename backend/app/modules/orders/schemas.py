from datetime import datetime
from decimal import Decimal
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.modules.orders.models import OrderStatus


class OrderImportItem(BaseModel):
    sku: str = Field(min_length=1, max_length=64)
    quantity: int = Field(gt=0)
    unit_price: Decimal = Field(ge=Decimal("0"), max_digits=14, decimal_places=2)


class OrderImportRequest(BaseModel):
    channel: str = Field(min_length=1, max_length=32)
    external_order_id: str = Field(min_length=1, max_length=100)
    order_date: datetime
    status: OrderStatus = OrderStatus.PAID
    total_amount: Decimal = Field(ge=Decimal("0"), max_digits=14, decimal_places=2)
    source_updated_at: datetime | None = None
    items: list[OrderImportItem] = Field(min_length=1, max_length=100)

    @model_validator(mode="after")
    def validate_order_totals(self) -> "OrderImportRequest":
        skus = [item.sku for item in self.items]
        if len(skus) != len(set(skus)):
            raise ValueError("An order cannot contain duplicate SKU lines in V1")

        calculated_total = sum(
            (item.unit_price * item.quantity for item in self.items),
            start=Decimal("0.00"),
        )
        if calculated_total != self.total_amount:
            raise ValueError(f"total_amount must equal the sum of item lines ({calculated_total})")
        return self


class OrderImportStatus(StrEnum):
    IMPORTED = "imported"
    DUPLICATE = "duplicate"


class OrderImportResponse(BaseModel):
    status: OrderImportStatus
    order_id: int


class OrderItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    product_id: int
    quantity: int
    unit_price: Decimal
    unit_cost: Decimal
    sku: str | None = None
    product_name: str | None = None


class OrderRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    channel_id: int
    channel: str
    external_order_id: str
    order_date: datetime
    status: OrderStatus
    total_amount: Decimal
    source_updated_at: datetime | None
    created_at: datetime
    updated_at: datetime


class OrderDetail(OrderRead):
    items: list[OrderItemRead]
