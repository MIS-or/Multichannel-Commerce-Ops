from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from enum import StrEnum

from pydantic import BaseModel, Field, model_validator


def _utc_now() -> datetime:
    return datetime.now(UTC)


class CanonicalOrderStatus(StrEnum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    SHIPPED = "SHIPPED"
    DELIVERED = "DELIVERED"
    CANCELLED = "CANCELLED"
    RETURNED = "RETURNED"




class CanonicalOrderItem(BaseModel):
    """Normalized line item belonging to a canonical order."""

    sku: str = Field(min_length=1)
    product_name: str | None = None
    quantity: int = Field(gt=0)
    unit_price: Decimal = Field(ge=Decimal("0"))
    discount_amount: Decimal = Field(default=Decimal("0.00"), ge=Decimal("0"))
    subtotal: Decimal = Field(ge=Decimal("0"))

    @model_validator(mode="after")
    def validate_subtotal(self) -> CanonicalOrderItem:
        if self.subtotal < 0:
            raise ValueError("Subtotal cannot be negative")
        return self


class CanonicalOrder(BaseModel):
    """Neutral, standardized order payload normalized across all sales channels."""

    channel_code: str = Field(min_length=1)
    channel_order_id: str = Field(min_length=1)
    order_status: CanonicalOrderStatus
    currency: str = Field(default="VND", min_length=3, max_length=3)
    total_amount: Decimal = Field(ge=Decimal("0"))
    customer_name: str | None = None
    customer_email: str | None = None
    placed_at: datetime
    updated_at: datetime = Field(default_factory=_utc_now)
    items: list[CanonicalOrderItem] = Field(min_length=1)
    raw_payload_checksum: str | None = None


class CanonicalInventoryItem(BaseModel):
    """Normalized stock snapshot for a specific SKU from an external source system."""

    sku: str = Field(min_length=1)
    source_system: str = Field(min_length=1)
    location_id: str | None = None
    on_hand_qty: Decimal = Field(ge=Decimal("0"))
    allocated_qty: Decimal = Field(default=Decimal("0"), ge=Decimal("0"))
    available_qty: Decimal = Field(ge=Decimal("0"))
    captured_at: datetime = Field(default_factory=_utc_now)


class CanonicalSettlementEntry(BaseModel):
    """Normalized single-order financial settlement line item."""

    channel_order_id: str = Field(min_length=1)
    gross_sales: Decimal = Field(ge=Decimal("0"))
    commission_fee: Decimal = Field(default=Decimal("0.00"), ge=Decimal("0"))
    service_fee: Decimal = Field(default=Decimal("0.00"), ge=Decimal("0"))
    transaction_fee: Decimal = Field(default=Decimal("0.00"), ge=Decimal("0"))
    seller_shipping_discount: Decimal = Field(default=Decimal("0.00"), ge=Decimal("0"))
    shipping_fee_subsidy: Decimal = Field(default=Decimal("0.00"), ge=Decimal("0"))
    refund_amount: Decimal = Field(default=Decimal("0.00"), ge=Decimal("0"))
    net_payout: Decimal

    @model_validator(mode="after")
    def validate_net_payout(self) -> CanonicalSettlementEntry:
        # Payout formula: gross_sales - all fees - refund + subsidies
        total_deductions = (
            self.commission_fee
            + self.service_fee
            + self.transaction_fee
            + self.seller_shipping_discount
            + self.refund_amount
        )
        calculated_net = self.gross_sales - total_deductions + self.shipping_fee_subsidy
        if abs(self.net_payout - calculated_net) > Decimal("1.0"):  # 1 unit tolerance
            raise ValueError(
                f"Net payout ({self.net_payout}) mismatch with calculated net ({calculated_net})"
            )
        return self


class CanonicalSettlementStatement(BaseModel):
    """Normalized financial statement representing an aggregated payout batch."""

    channel_code: str = Field(min_length=1)
    statement_id: str = Field(min_length=1)
    period_start: datetime
    period_end: datetime
    payout_at: datetime
    currency: str = Field(default="VND", min_length=3, max_length=3)
    total_gross_sales: Decimal = Field(ge=Decimal("0"))
    total_platform_fees: Decimal = Field(ge=Decimal("0"))
    total_net_payout: Decimal = Field(ge=Decimal("0"))
    entries: list[CanonicalSettlementEntry] = Field(default_factory=list)
