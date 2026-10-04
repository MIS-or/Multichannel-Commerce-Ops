from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.alerts.repository import AlertRepository
from app.modules.alerts.service import AlertService
from app.modules.channels.models import Channel
from app.modules.channels.repository import ChannelRepository
from app.modules.channels.service import ChannelService
from app.modules.integrations import (
    CanonicalSettlementEntry,
    CanonicalSettlementStatement,
)
from app.modules.inventory.service import InventoryService
from app.modules.ledger.repository import LedgerRepository
from app.modules.ledger.service import LedgerService
from app.modules.orders.models import Order, OrderStatus
from app.modules.orders.repository import OrderRepository
from app.modules.orders.service import OrderService
from app.modules.products.repository import ProductRepository
from app.modules.products.service import ProductService
from app.modules.reconciliation import (
    ReconciliationService,
    SettlementDiscrepancyType,
    SettlementRateCard,
)
from app.modules.reconciliation.repository import ReconciliationRepository
from app.shared.time import utc_now


async def _make_recon_service(session: AsyncSession) -> ReconciliationService:
    channel_svc = ChannelService(ChannelRepository(session))
    prod_svc = ProductService(ProductRepository(session))
    alert_svc = AlertService(session, AlertRepository(session))
    inv_svc = InventoryService(session, prod_svc, alert_service=alert_svc)
    ledger_svc = LedgerService(LedgerRepository(session))
    order_svc = OrderService(
        session=session,
        repository=OrderRepository(session),
        channel_service=channel_svc,
        product_service=prod_svc,
        inventory_service=inv_svc,
        ledger_service=ledger_svc,
    )
    return ReconciliationService(
        session=session,
        repository=ReconciliationRepository(session),
        channel_service=channel_svc,
        order_service=order_svc,
        ledger_service=ledger_svc,
        alert_service=alert_svc,
    )


@pytest.mark.asyncio
async def test_settlement_reconciliation_clean_match(session: AsyncSession) -> None:
    svc = await _make_recon_service(session)
    channel = Channel(code="shopee_vn", name="Shopee VN", platform_type="marketplace")
    session.add(channel)
    await session.flush()

    # Create internal matching order
    order = Order(
        channel_id=channel.id,
        external_order_id="260320SHP0001",
        status=OrderStatus.PAID,
        total_amount=Decimal("500000.00"),
        order_date=utc_now(),
    )
    session.add(order)
    await session.commit()

    # Canonical settlement statement
    now = datetime(2026, 3, 20, 12, 0, tzinfo=UTC)
    statement = CanonicalSettlementStatement(
        channel_code="shopee_vn",
        statement_id="STMT-SHP-001",
        period_start=now,
        period_end=now,
        payout_at=now,
        total_gross_sales=Decimal("500000.00"),
        total_platform_fees=Decimal("45000.00"),
        total_net_payout=Decimal("455000.00"),
        entries=[
            CanonicalSettlementEntry(
                channel_order_id="260320SHP0001",
                gross_sales=Decimal("500000.00"),
                commission_fee=Decimal("25000.00"),  # 5%
                service_fee=Decimal("10000.00"),  # 2%
                transaction_fee=Decimal("10000.00"),  # 2%
                net_payout=Decimal("455000.00"),
            )
        ],
    )

    rate_card = SettlementRateCard(
        channel_code="shopee_vn",
        commission_rate=Decimal("0.05"),
        service_fee_rate=Decimal("0.02"),
        transaction_fee_rate=Decimal("0.02"),
    )

    summary = await svc.reconcile_settlement_statement(statement, rate_card)

    assert summary.total_orders_checked == 1
    assert summary.matched_count == 1
    assert summary.discrepancies_count == 0
    assert summary.total_payout_variance == Decimal("0.00")
    assert summary.items[0].discrepancy_type == SettlementDiscrepancyType.CLEAN_MATCH


@pytest.mark.asyncio
async def test_settlement_reconciliation_ghost_order_triggers_alert(
    session: AsyncSession,
) -> None:
    svc = await _make_recon_service(session)
    channel = Channel(code="shopee_vn", name="Shopee VN", platform_type="marketplace")
    session.add(channel)
    await session.commit()

    now = datetime(2026, 3, 20, 12, 0, tzinfo=UTC)
    statement = CanonicalSettlementStatement(
        channel_code="shopee_vn",
        statement_id="STMT-SHP-GHOST",
        period_start=now,
        period_end=now,
        payout_at=now,
        total_gross_sales=Decimal("200000.00"),
        total_platform_fees=Decimal("18000.00"),
        total_net_payout=Decimal("182000.00"),
        entries=[
            CanonicalSettlementEntry(
                channel_order_id="GHOST-ORDER-9999",
                gross_sales=Decimal("200000.00"),
                commission_fee=Decimal("10000.00"),
                service_fee=Decimal("4000.00"),
                transaction_fee=Decimal("4000.00"),
                net_payout=Decimal("182000.00"),
            )
        ],
    )

    summary = await svc.reconcile_settlement_statement(statement)

    assert summary.total_orders_checked == 1
    assert summary.discrepancies_count == 1
    ghost_item = summary.items[0]
    assert ghost_item.discrepancy_type == SettlementDiscrepancyType.GHOST_ORDER
    assert "does not exist in MCO orders" in ghost_item.message

    # Verify critical alert was created
    alert_repo = AlertRepository(session)
    alerts = await alert_repo.list_all(resolved=False)
    recon_alerts = [a for a in alerts if "STMT-SHP-GHOST" in a.message]
    assert len(recon_alerts) == 1
    assert recon_alerts[0].severity == "critical"


@pytest.mark.asyncio
async def test_settlement_reconciliation_fee_overcharged(session: AsyncSession) -> None:
    svc = await _make_recon_service(session)
    channel = Channel(code="shopee_vn", name="Shopee VN", platform_type="marketplace")
    session.add(channel)
    await session.flush()

    order = Order(
        channel_id=channel.id,
        external_order_id="260320SHP0002",
        status=OrderStatus.PAID,
        total_amount=Decimal("500000.00"),
        order_date=utc_now(),
    )
    session.add(order)
    await session.commit()

    now = datetime(2026, 3, 20, 12, 0, tzinfo=UTC)
    # Channel deducted 65,000 in fees instead of 45,000 (9%) -> +20,000 overcharge!
    statement = CanonicalSettlementStatement(
        channel_code="shopee_vn",
        statement_id="STMT-SHP-OVERCHARGE",
        period_start=now,
        period_end=now,
        payout_at=now,
        total_gross_sales=Decimal("500000.00"),
        total_platform_fees=Decimal("65000.00"),
        total_net_payout=Decimal("435000.00"),
        entries=[
            CanonicalSettlementEntry(
                channel_order_id="260320SHP0002",
                gross_sales=Decimal("500000.00"),
                commission_fee=Decimal("40000.00"),  # 8% instead of 5%!
                service_fee=Decimal("15000.00"),  # 3% instead of 2%!
                transaction_fee=Decimal("10000.00"),  # 2%
                net_payout=Decimal("435000.00"),
            )
        ],
    )

    rate_card = SettlementRateCard(
        channel_code="shopee_vn",
        commission_rate=Decimal("0.05"),
        service_fee_rate=Decimal("0.02"),
        transaction_fee_rate=Decimal("0.02"),
        max_tolerance=Decimal("100.00"),
    )

    summary = await svc.reconcile_settlement_statement(statement, rate_card)

    assert summary.discrepancies_count == 1
    overcharged = summary.items[0]
    assert overcharged.discrepancy_type == SettlementDiscrepancyType.FEE_OVERCHARGED
    assert "exceeding rate card expectation" in overcharged.message
    assert overcharged.variance == Decimal("-20000.00")
