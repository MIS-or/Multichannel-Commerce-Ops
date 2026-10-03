from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class MockOrderItem(BaseModel):
    sku: str
    quantity: int = Field(gt=0)
    unit_price: Decimal = Field(ge=Decimal("0"))


class MockOrder(BaseModel):
    external_order_id: str
    order_date: datetime
    status: str = "paid"
    total_amount: Decimal = Field(ge=Decimal("0"))
    items: list[MockOrderItem] = Field(min_length=1)


class MockOrderFeed(BaseModel):
    channel: str
    orders: list[MockOrder]
