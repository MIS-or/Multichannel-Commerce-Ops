from datetime import UTC, date, datetime, time, timedelta
from decimal import Decimal

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import col

from app.modules.alerts.models import Alert, AlertSeverity
from app.modules.channels.models import Channel
from app.modules.exceptions.models import (
    ExceptionDomain,
    ExceptionSeverity,
    ExceptionStatus,
    OperationalException,
)
from app.modules.integrations.models import SyncRun, SyncStatus
from app.modules.ledger.models import LedgerEntry, LedgerEntryType
from app.modules.orders.models import Order
from app.modules.reconciliation.models import ReconciliationLog, ReconciliationStatus
from app.modules.reports.schemas import OperationsHealthSummary


class ReportsRepository:
    """Read-only cross-domain aggregation repository."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    @staticmethod
    def _range(report_date: date) -> tuple[datetime, datetime]:
        start = datetime.combine(report_date, time.min, tzinfo=UTC)
        return start, start + timedelta(days=1)

    async def daily_channels(
        self,
        report_date: date,
    ) -> list[tuple[str, str, int, Decimal, Decimal]]:
        start, end = self._range(report_date)
        revenue = func.coalesce(
            func.sum(
                case(
                    (col(LedgerEntry.entry_type) == LedgerEntryType.REVENUE, LedgerEntry.amount),
                    else_=0,
                )
            ),
            0,
        )
        cogs = func.coalesce(
            func.sum(
                case(
                    (col(LedgerEntry.entry_type) == LedgerEntryType.COGS, LedgerEntry.amount),
                    else_=0,
                )
            ),
            0,
        )
        statement = (
            select(
                col(Channel.code),
                col(Channel.name),
                func.count(func.distinct(col(Order.id))),
                revenue,
                cogs,
            )
            .join(Order, col(Order.channel_id) == col(Channel.id))
            .join(LedgerEntry, col(LedgerEntry.order_id) == col(Order.id))
            .where(col(Order.order_date) >= start, col(Order.order_date) < end)
            .group_by(col(Channel.id), col(Channel.code), col(Channel.name))
            .order_by(col(Channel.code))
        )
        result = await self._session.execute(statement)
        return [
            (str(code), str(name), int(order_count), Decimal(revenue_total), Decimal(cogs_total))
            for code, name, order_count, revenue_total, cogs_total in result.all()
        ]

    async def get_latest_date(self) -> date | None:
        result = await self._session.execute(select(func.max(Order.order_date)))
        latest = result.scalar_one_or_none()
        if latest is None:
            return None
        return latest.date()

    async def operations_health(self) -> OperationsHealthSummary:
        now = datetime.now(UTC)
        since_24h = now - timedelta(hours=24)

        # 1. Integrations & Syncs
        total_integrations = (
            await self._session.scalar(select(func.count(func.distinct(col(SyncRun.channel_code)))))
        ) or 0
        failed_syncs = (
            await self._session.scalar(
                select(func.count()).select_from(SyncRun).where(
                    col(SyncRun.status) == SyncStatus.FAILED,
                    col(SyncRun.started_at) >= since_24h,
                )
            )
        ) or 0
        healthy_integrations = max(0, total_integrations - (1 if failed_syncs > 0 else 0))

        # 2. Exceptions
        open_statuses = [ExceptionStatus.OPEN, ExceptionStatus.INVESTIGATING]
        open_exc = (
            await self._session.scalar(
                select(func.count()).select_from(OperationalException).where(
                    col(OperationalException.status).in_(open_statuses)
                )
            )
        ) or 0
        crit_exc = (
            await self._session.scalar(
                select(func.count()).select_from(OperationalException).where(
                    col(OperationalException.status).in_(open_statuses),
                    col(OperationalException.severity) == ExceptionSeverity.CRITICAL,
                )
            )
        ) or 0
        inv_mismatch = (
            await self._session.scalar(
                select(func.count()).select_from(OperationalException).where(
                    col(OperationalException.status).in_(open_statuses),
                    col(OperationalException.domain) == ExceptionDomain.INVENTORY_VARIANCE,
                )
            )
        ) or 0
        set_mismatch = (
            await self._session.scalar(
                select(func.count()).select_from(OperationalException).where(
                    col(OperationalException.status).in_(open_statuses),
                    col(OperationalException.domain) == ExceptionDomain.SETTLEMENT_DISCREPANCY,
                )
            )
        ) or 0

        # 3. Reconciliation & Alerts
        recon_mismatches = (
            await self._session.scalar(
                select(func.count()).select_from(ReconciliationLog).where(
                    col(ReconciliationLog.status) == ReconciliationStatus.MISMATCH,
                    col(ReconciliationLog.started_at) >= since_24h,
                )
            )
        ) or 0
        crit_alerts = (
            await self._session.scalar(
                select(func.count()).select_from(Alert).where(
                    ~col(Alert.resolved),
                    col(Alert.severity) == AlertSeverity.CRITICAL,
                )
            )
        ) or 0

        return OperationsHealthSummary(
            healthy_integrations=healthy_integrations,
            total_integrations=total_integrations,
            failed_syncs_24h=failed_syncs,
            open_exceptions=open_exc,
            critical_exceptions=crit_exc,
            inventory_mismatches=inv_mismatch,
            settlement_mismatches=set_mismatch,
            pending_reconciliations=recon_mismatches,
            critical_alerts=crit_alerts,
        )

