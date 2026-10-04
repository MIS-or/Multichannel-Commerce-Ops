from datetime import UTC, date, datetime
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.channels.models import Channel
from app.modules.ledger.models import LedgerEntry, LedgerEntryType
from app.modules.orders.models import Order
from app.modules.reports.repository import ReportsRepository
from app.modules.reports.service import ReportsService


async def test_daily_report_aggregates_by_channel(session: AsyncSession) -> None:
    shopee = Channel(code="shopee", name="Shopee", platform_type="marketplace")
    website = Channel(code="website", name="Website", platform_type="direct")
    session.add_all([shopee, website])
    await session.flush()
    assert shopee.id is not None and website.id is not None

    orders = [
        Order(
            channel_id=shopee.id,
            external_order_id="SP-1",
            order_date=datetime(2026, 9, 1, 2, tzinfo=UTC),
            total_amount=Decimal("500.00"),
        ),
        Order(
            channel_id=website.id,
            external_order_id="WEB-1",
            order_date=datetime(2026, 9, 1, 3, tzinfo=UTC),
            total_amount=Decimal("300.00"),
        ),
    ]
    session.add_all(orders)
    await session.flush()
    for order, revenue, cogs in [
        (orders[0], Decimal("500.00"), Decimal("300.00")),
        (orders[1], Decimal("300.00"), Decimal("180.00")),
    ]:
        assert order.id is not None
        session.add_all(
            [
                LedgerEntry(order_id=order.id, entry_type=LedgerEntryType.REVENUE, amount=revenue),
                LedgerEntry(order_id=order.id, entry_type=LedgerEntryType.COGS, amount=cogs),
            ]
        )
    await session.commit()

    report = await ReportsService(ReportsRepository(session)).daily_report(date(2026, 9, 1))

    assert report.totals.orders == 2
    assert report.totals.revenue == Decimal("800.00")
    assert report.totals.cogs == Decimal("480.00")
    assert report.totals.gross_profit == Decimal("320.00")
    assert [channel.channel for channel in report.channels] == ["shopee", "website"]


async def test_operations_health_summary(session: AsyncSession) -> None:
    from app.modules.alerts.models import Alert, AlertSeverity, AlertType
    from app.modules.exceptions.models import (
        ExceptionDomain,
        ExceptionSeverity,
        ExceptionStatus,
        OperationalException,
    )
    from app.modules.integrations.models import SyncRun, SyncStatus, SyncType

    now = datetime.now(UTC)

    # 1. Add Sync runs (1 success, 1 failed)
    session.add_all(
        [
            SyncRun(
                channel_code="shopee",
                sync_type=SyncType.ORDERS,
                status=SyncStatus.SUCCESS,
                started_at=now,
                completed_at=now,
            ),
            SyncRun(
                channel_code="tiktok",
                sync_type=SyncType.ORDERS,
                status=SyncStatus.FAILED,
                started_at=now,
                completed_at=now,
            ),
        ]
    )

    # 2. Add Exceptions (1 critical open inventory, 1 resolved)
    session.add_all(
        [
            OperationalException(
                domain=ExceptionDomain.INVENTORY_VARIANCE,
                severity=ExceptionSeverity.CRITICAL,
                status=ExceptionStatus.OPEN,
                reference_id="SKU-100",
                title="Critical stock variance",
                description="Channel stock mismatch",
            ),
            OperationalException(
                domain=ExceptionDomain.SETTLEMENT_DISCREPANCY,
                severity=ExceptionSeverity.MEDIUM,
                status=ExceptionStatus.RESOLVED,
                reference_id="ORD-1",
                title="Settlement resolved",
                description="Notes",
            ),
        ]
    )

    # 3. Add Alert (1 critical active)
    session.add(
        Alert(
            type=AlertType.LOW_STOCK,
            severity=AlertSeverity.CRITICAL,
            dedup_key="crit_alert_1",
            message="Stock depleted",
            resolved=False,
        )
    )
    await session.commit()

    service = ReportsService(ReportsRepository(session))
    summary = await service.operations_health()

    assert summary.total_integrations >= 2
    assert summary.failed_syncs_24h >= 1
    assert summary.open_exceptions >= 1
    assert summary.critical_exceptions >= 1
    assert summary.inventory_mismatches >= 1
    assert summary.critical_alerts >= 1

