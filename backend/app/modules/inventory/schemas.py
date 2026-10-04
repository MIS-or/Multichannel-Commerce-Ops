from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from enum import StrEnum

from pydantic import BaseModel, Field

from app.shared.time import utc_now


class InventoryItemRead(BaseModel):
    product_id: int
    sku: str
    name: str
    cost_price: Decimal
    current_stock: int
    reorder_threshold: int
    is_low_stock: bool


class DiscrepancyDirection(StrEnum):
    MATCHED = "MATCHED"
    OVER_ALLOCATED = "OVER_ALLOCATED"  # Channel > ERP (Oversell risk)
    UNDER_ALLOCATED = "UNDER_ALLOCATED"  # Channel < ERP


class InventoryVariance(BaseModel):
    """Calculated variance between physical ERP stock and channel-allocated stock."""

    sku: str
    channel_code: str
    erp_source: str = "odoo_erp"
    erp_available_qty: Decimal
    channel_available_qty: Decimal
    variance: Decimal  # channel_available_qty - erp_available_qty
    has_discrepancy: bool
    direction: DiscrepancyDirection
    calculated_at: datetime = Field(default_factory=utc_now)


class InventorySnapshotRead(BaseModel):
    """Read schema for stored inventory snapshot records."""

    id: int
    source_system: str
    sku: str
    location_id: str | None = None
    on_hand_qty: Decimal
    allocated_qty: Decimal
    available_qty: Decimal
    batch_id: str | None = None
    captured_at: datetime
