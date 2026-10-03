from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

from app.modules.reconciliation.models import ReconciliationStatus


class SourceOrderSnapshot(BaseModel):
    external_order_id: str = Field(min_length=1, max_length=100)
    total_amount: Decimal = Field(ge=Decimal("0"), max_digits=14, decimal_places=2)


class ReconciliationRequest(BaseModel):
    source_system: str = Field(min_length=1, max_length=64)
    orders: list[SourceOrderSnapshot] = Field(min_length=1, max_length=1000)


class ReconciliationMismatch(BaseModel):
    external_order_id: str
    code: str
    expected: str | None = None
    actual: str | None = None


class ReconciliationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    source_system: str
    status: ReconciliationStatus
    records_checked: int
    mismatches_found: int
    detail_json: dict[str, object]
    started_at: datetime
    completed_at: datetime


# --- Phase 4: Multi-Dimensional Settlement Reconciliation Schemas ---


class SettlementDiscrepancyType(StrEnum):
    CLEAN_MATCH = "clean_match"
    GHOST_ORDER = "ghost_order"
    UNSETTLED = "unsettled"
    FEE_OVERCHARGED = "fee_overcharged"
    PAYOUT_MISMATCH = "payout_mismatch"


class SettlementRateCard(BaseModel):
    """Channel agreed fee rate card for contractual audit."""

    channel_code: str
    commission_rate: Decimal = Field(
        default=Decimal("0.05"), ge=Decimal("0"), le=Decimal("1")
    )
    transaction_fee_rate: Decimal = Field(
        default=Decimal("0.02"), ge=Decimal("0"), le=Decimal("1")
    )
    service_fee_rate: Decimal = Field(
        default=Decimal("0.02"), ge=Decimal("0"), le=Decimal("1")
    )
    max_tolerance: Decimal = Field(default=Decimal("1000.00"), ge=Decimal("0"))


class SettlementReconciliationItem(BaseModel):
    """Reconciliation outcome for an individual order entry within a settlement payout batch."""

    channel_order_id: str
    discrepancy_type: SettlementDiscrepancyType
    internal_order_id: int | None = None
    reported_gross_sales: Decimal
    expected_gross_sales: Decimal | None = None
    reported_fees: Decimal
    expected_fees: Decimal | None = None
    reported_net_payout: Decimal
    expected_net_payout: Decimal | None = None
    variance: Decimal  # reported_net_payout - (expected_net_payout or reported_net_payout)
    message: str


class SettlementReconciliationSummary(BaseModel):
    """Aggregated financial reconciliation report for a channel payout statement."""

    statement_id: str
    channel_code: str
    total_orders_checked: int
    matched_count: int
    discrepancies_count: int
    total_reported_payout: Decimal
    total_expected_payout: Decimal
    total_payout_variance: Decimal
    items: list[SettlementReconciliationItem]
