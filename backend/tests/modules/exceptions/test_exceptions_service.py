from __future__ import annotations

from decimal import Decimal

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.exceptions import (
    ExceptionCreate,
    ExceptionDomain,
    ExceptionService,
    ExceptionSeverity,
    ExceptionStatus,
    RootCauseCategory,
)
from app.modules.inventory import DiscrepancyDirection, InventoryVariance
from app.modules.reconciliation import (
    SettlementDiscrepancyType,
    SettlementReconciliationItem,
)
from app.shared.errors import BusinessRuleError, NotFoundError
from app.shared.time import utc_now


@pytest.fixture
def exception_service(session: AsyncSession) -> ExceptionService:
    return ExceptionService(session)


@pytest.mark.asyncio
async def test_create_and_deduplicate_exception(
    exception_service: ExceptionService,
) -> None:
    payload = ExceptionCreate(
        domain=ExceptionDomain.INVENTORY_VARIANCE,
        severity=ExceptionSeverity.HIGH,
        reference_id="SKU-DEDUP-01",
        channel_code="shopee_vn",
        title="Stock discrepancy on Shopee",
        description="Available stock mismatch: 140 vs 120",
        variance_amount=Decimal("20.00"),
    )

    created1 = await exception_service.create_exception(payload)
    assert created1.id is not None
    assert created1.status == ExceptionStatus.OPEN
    assert created1.reference_id == "SKU-DEDUP-01"

    # Second creation with same domain and reference returns existing
    created2 = await exception_service.create_exception(payload)
    assert created2.id == created1.id


@pytest.mark.asyncio
async def test_lifecycle_open_to_investigating_to_resolved(
    exception_service: ExceptionService,
) -> None:
    payload = ExceptionCreate(
        domain=ExceptionDomain.SETTLEMENT_DISCREPANCY,
        severity=ExceptionSeverity.HIGH,
        reference_id="ORD-LIFECYCLE-01",
        channel_code="tiktok_shop_vn",
        title="Platform fee overcharged",
        description="Channel deducted 15,000 VND extra",
        variance_amount=Decimal("-15000.00"),
    )
    exc = await exception_service.create_exception(payload)
    assert exc.status == ExceptionStatus.OPEN
    assert exc.assigned_to is None

    # 1. Assign -> moves to INVESTIGATING
    assigned = await exception_service.assign(exc.id, assigned_to="accountant_jane")
    assert assigned.status == ExceptionStatus.INVESTIGATING
    assert assigned.assigned_to == "accountant_jane"

    # 2. Resolve -> moves to RESOLVED
    resolved = await exception_service.resolve(
        exc.id,
        root_cause=RootCauseCategory.PLATFORM_FEE_OVERCHARGE,
        resolution_notes="Filed dispute ticket #9824 with TikTok Shop. Refund received.",
    )
    assert resolved.status == ExceptionStatus.RESOLVED
    assert resolved.root_cause == RootCauseCategory.PLATFORM_FEE_OVERCHARGE
    assert resolved.resolved_at is not None

    # 3. Cannot re-assign resolved exception
    with pytest.raises(BusinessRuleError):
        await exception_service.assign(exc.id, assigned_to="ops_lead")


@pytest.mark.asyncio
async def test_lifecycle_ignore(exception_service: ExceptionService) -> None:
    payload = ExceptionCreate(
        domain=ExceptionDomain.DATA_NORMALIZATION,
        severity=ExceptionSeverity.LOW,
        reference_id="REF-IGNORE-01",
        title="Minor timestamp jitter",
        description="Difference under 2 seconds",
    )
    exc = await exception_service.create_exception(payload)
    assert exc.status == ExceptionStatus.OPEN

    ignored = await exception_service.ignore(exc.id, reason="Expected clock drift")
    assert ignored.status == ExceptionStatus.IGNORED
    assert "IGNORED: Expected clock drift" in (ignored.resolution_notes or "")


@pytest.mark.asyncio
async def test_create_from_inventory_variance(
    exception_service: ExceptionService,
) -> None:
    variance = InventoryVariance(
        sku="SKU-OVERSELL-99",
        channel_code="shopee_vn",
        erp_available_qty=Decimal("50"),
        channel_available_qty=Decimal("80"),
        variance=Decimal("30"),
        has_discrepancy=True,
        direction=DiscrepancyDirection.OVER_ALLOCATED,
        calculated_at=utc_now(),
    )

    exc = await exception_service.create_from_inventory_variance(variance)
    assert exc.domain == ExceptionDomain.INVENTORY_VARIANCE
    assert exc.severity == ExceptionSeverity.CRITICAL
    assert exc.reference_id == "SKU-OVERSELL-99"
    assert exc.variance_amount == Decimal("30")


@pytest.mark.asyncio
async def test_create_from_settlement_discrepancy(
    exception_service: ExceptionService,
) -> None:
    item = SettlementReconciliationItem(
        channel_order_id="GHOST-999",
        discrepancy_type=SettlementDiscrepancyType.GHOST_ORDER,
        reported_gross_sales=Decimal("300000.00"),
        reported_fees=Decimal("25000.00"),
        reported_net_payout=Decimal("275000.00"),
        variance=Decimal("275000.00"),
        message="Unknown order in statement",
    )

    exc = await exception_service.create_from_settlement_discrepancy(
        item, channel_code="shopee_vn", statement_id="STMT-2026-001"
    )
    assert exc.domain == ExceptionDomain.SETTLEMENT_DISCREPANCY
    assert exc.severity == ExceptionSeverity.CRITICAL
    assert exc.reference_id == "GHOST-999"


@pytest.mark.asyncio
async def test_get_unknown_exception_raises(
    exception_service: ExceptionService,
) -> None:
    with pytest.raises(NotFoundError):
        await exception_service.get(999999)
