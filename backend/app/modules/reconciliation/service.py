from collections import defaultdict
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.alerts.models import AlertSeverity, AlertType
from app.modules.alerts.service import AlertService
from app.modules.channels.service import ChannelService
from app.modules.integrations import CanonicalSettlementStatement
from app.modules.ledger.models import LedgerEntryType
from app.modules.ledger.service import LedgerService
from app.modules.orders.service import OrderService
from app.modules.reconciliation.models import ReconciliationLog, ReconciliationStatus
from app.modules.reconciliation.repository import ReconciliationRepository
from app.modules.reconciliation.schemas import (
    ReconciliationMismatch,
    ReconciliationRead,
    ReconciliationRequest,
    SettlementDiscrepancyType,
    SettlementRateCard,
    SettlementReconciliationItem,
    SettlementReconciliationSummary,
)
from app.shared.errors import NotFoundError
from app.shared.time import utc_now


class ReconciliationService:
    def __init__(
        self,
        session: AsyncSession,
        repository: ReconciliationRepository,
        channel_service: ChannelService,
        order_service: OrderService,
        ledger_service: LedgerService,
        alert_service: AlertService,
    ) -> None:
        self._session = session
        self._repository = repository
        self._channels = channel_service
        self._orders = order_service
        self._ledger = ledger_service
        self._alerts = alert_service

    async def reconcile(self, payload: ReconciliationRequest) -> ReconciliationRead:
        started_at = utc_now()
        tx = (
            self._session.begin_nested()
            if self._session.in_transaction()
            else self._session.begin()
        )
        async with tx:
            channel = await self._channels.get_by_code(payload.source_system)
            assert channel.id is not None

            source_ids = [order.external_order_id for order in payload.orders]
            local_orders = await self._orders.get_orders_for_reconciliation(channel.id, source_ids)
            local_by_external = {order.external_order_id: order for order in local_orders}
            order_ids = [order.id for order in local_orders if order.id is not None]

            ledger_entries = await self._ledger.get_entries_for_orders(order_ids)
            ledger_by_order: dict[int, dict[LedgerEntryType, Decimal]] = defaultdict(dict)
            for entry in ledger_entries:
                ledger_by_order[entry.order_id][entry.entry_type] = entry.amount

            expected_cogs = await self._orders.get_order_items_cogs(order_ids)

            mismatches: list[ReconciliationMismatch] = []
            for source_order in payload.orders:
                local = local_by_external.get(source_order.external_order_id)
                if local is None or local.id is None:
                    mismatches.append(
                        ReconciliationMismatch(
                            external_order_id=source_order.external_order_id,
                            code="MISSING_ORDER",
                            expected=str(source_order.total_amount),
                            actual=None,
                        )
                    )
                    continue

                if local.total_amount != source_order.total_amount:
                    mismatches.append(
                        ReconciliationMismatch(
                            external_order_id=source_order.external_order_id,
                            code="TOTAL_MISMATCH",
                            expected=str(source_order.total_amount),
                            actual=str(local.total_amount),
                        )
                    )

                entries = ledger_by_order.get(local.id, {})
                revenue = entries.get(LedgerEntryType.REVENUE)
                if revenue != source_order.total_amount:
                    mismatches.append(
                        ReconciliationMismatch(
                            external_order_id=source_order.external_order_id,
                            code="REVENUE_MISMATCH",
                            expected=str(source_order.total_amount),
                            actual=None if revenue is None else str(revenue),
                        )
                    )

                cogs = entries.get(LedgerEntryType.COGS)
                expected = expected_cogs[local.id]
                if cogs != expected:
                    mismatches.append(
                        ReconciliationMismatch(
                            external_order_id=source_order.external_order_id,
                            code="COGS_MISMATCH",
                            expected=str(expected),
                            actual=None if cogs is None else str(cogs),
                        )
                    )

            status = ReconciliationStatus.MISMATCH if mismatches else ReconciliationStatus.SUCCESS
            log = await self._repository.create(
                ReconciliationLog(
                    source_system=payload.source_system,
                    status=status,
                    records_checked=len(payload.orders),
                    mismatches_found=len(mismatches),
                    detail_json={"mismatches": [mismatch.model_dump() for mismatch in mismatches]},
                    started_at=started_at,
                    completed_at=utc_now(),
                )
            )

            if mismatches:
                await self._alerts.create_once(
                    alert_type=AlertType.RECONCILIATION_MISMATCH,
                    severity=AlertSeverity.CRITICAL,
                    dedup_key=f"reconciliation_mismatch:{payload.source_system}",
                    message=(
                        f"{payload.source_system} reconciliation found "
                        f"{len(mismatches)} mismatch(es)"
                    ),
                )

        return ReconciliationRead.model_validate(log)

    async def list_history(self) -> list[ReconciliationRead]:
        return [ReconciliationRead.model_validate(log) for log in await self._repository.list()]

    async def get(self, reconciliation_id: int) -> ReconciliationRead:
        log = await self._repository.get_by_id(reconciliation_id)
        if log is None:
            raise NotFoundError(
                "RECONCILIATION_NOT_FOUND",
                f"Reconciliation id '{reconciliation_id}' does not exist",
                details={"reconciliation_id": reconciliation_id},
            )
        return ReconciliationRead.model_validate(log)

    async def reconcile_settlement_statement(
        self,
        statement: CanonicalSettlementStatement,
        rate_card: SettlementRateCard | None = None,
    ) -> SettlementReconciliationSummary:
        """Reconcile a channel payout statement against internal orders and rate card."""
        started_at = utc_now()
        channel_id: int | None = None
        try:
            channel = await self._channels.get_by_code(statement.channel_code)
            channel_id = channel.id
        except NotFoundError:
            pass

        # Fetch matching local orders
        external_ids = [entry.channel_order_id for entry in statement.entries]
        local_orders = (
            await self._orders.get_orders_for_reconciliation(channel_id, external_ids)
            if channel_id is not None
            else []
        )
        orders_by_ext = {o.external_order_id: o for o in local_orders}

        items: list[SettlementReconciliationItem] = []
        tolerance = rate_card.max_tolerance if rate_card else Decimal("1.00")

        for entry in statement.entries:
            local = orders_by_ext.get(entry.channel_order_id)
            actual_fees = (
                entry.commission_fee
                + entry.service_fee
                + entry.transaction_fee
                + entry.seller_shipping_discount
            )

            if local is None:
                # Ghost order: Payout reported by channel for an unknown internal order
                items.append(
                    SettlementReconciliationItem(
                        channel_order_id=entry.channel_order_id,
                        discrepancy_type=SettlementDiscrepancyType.GHOST_ORDER,
                        internal_order_id=None,
                        reported_gross_sales=entry.gross_sales,
                        expected_gross_sales=None,
                        reported_fees=actual_fees,
                        expected_fees=None,
                        reported_net_payout=entry.net_payout,
                        expected_net_payout=None,
                        variance=entry.net_payout,
                        message=(
                            f"Order '{entry.channel_order_id}' was paid by "
                            f"{statement.channel_code} but does not exist in MCO orders"
                        ),
                    )
                )
                continue

            order_gross = Decimal(str(local.total_amount))
            expected_fees: Decimal | None = None

            if rate_card is not None:
                expected_commission = order_gross * rate_card.commission_rate
                expected_tx = order_gross * rate_card.transaction_fee_rate
                expected_svc = order_gross * rate_card.service_fee_rate
                expected_fees = expected_commission + expected_tx + expected_svc

            expected_payout = (
                order_gross
                - (expected_fees if expected_fees is not None else actual_fees)
                + entry.shipping_fee_subsidy
                - entry.refund_amount
            )

            payout_variance = entry.net_payout - expected_payout

            # Check for fee overcharge
            if expected_fees is not None and (actual_fees - expected_fees) > tolerance:
                items.append(
                    SettlementReconciliationItem(
                        channel_order_id=entry.channel_order_id,
                        discrepancy_type=SettlementDiscrepancyType.FEE_OVERCHARGED,
                        internal_order_id=local.id,
                        reported_gross_sales=entry.gross_sales,
                        expected_gross_sales=order_gross,
                        reported_fees=actual_fees,
                        expected_fees=expected_fees,
                        reported_net_payout=entry.net_payout,
                        expected_net_payout=expected_payout,
                        variance=payout_variance,
                        message=(
                            f"Channel deducted {actual_fees} in fees, exceeding rate card "
                            f"expectation of {expected_fees} by +{actual_fees - expected_fees}"
                        ),
                    )
                )
            # Check for payout math mismatch
            elif abs(payout_variance) > tolerance:
                items.append(
                    SettlementReconciliationItem(
                        channel_order_id=entry.channel_order_id,
                        discrepancy_type=SettlementDiscrepancyType.PAYOUT_MISMATCH,
                        internal_order_id=local.id,
                        reported_gross_sales=entry.gross_sales,
                        expected_gross_sales=order_gross,
                        reported_fees=actual_fees,
                        expected_fees=expected_fees,
                        reported_net_payout=entry.net_payout,
                        expected_net_payout=expected_payout,
                        variance=payout_variance,
                        message=(
                            f"Reported payout ({entry.net_payout}) differs from "
                            f"expected calculation ({expected_payout}) by {payout_variance}"
                        ),
                    )
                )
            else:
                items.append(
                    SettlementReconciliationItem(
                        channel_order_id=entry.channel_order_id,
                        discrepancy_type=SettlementDiscrepancyType.CLEAN_MATCH,
                        internal_order_id=local.id,
                        reported_gross_sales=entry.gross_sales,
                        expected_gross_sales=order_gross,
                        reported_fees=actual_fees,
                        expected_fees=expected_fees,
                        reported_net_payout=entry.net_payout,
                        expected_net_payout=expected_payout,
                        variance=Decimal("0.00"),
                        message="Settlement matches order total and fee card perfectly",
                    )
                )

        total_orders = len(items)
        matched = len(
            [it for it in items if it.discrepancy_type == SettlementDiscrepancyType.CLEAN_MATCH]
        )
        discrepancies = total_orders - matched

        total_reported = sum((it.reported_net_payout for it in items), start=Decimal("0.00"))
        total_expected = sum(
            (it.expected_net_payout or it.reported_net_payout for it in items),
            start=Decimal("0.00"),
        )
        total_var = total_reported - total_expected

        summary = SettlementReconciliationSummary(
            statement_id=statement.statement_id,
            channel_code=statement.channel_code,
            total_orders_checked=total_orders,
            matched_count=matched,
            discrepancies_count=discrepancies,
            total_reported_payout=total_reported,
            total_expected_payout=total_expected,
            total_payout_variance=total_var,
            items=items,
        )

        # Trigger alert if discrepancies detected
        if discrepancies > 0 and self._alerts is not None:
            has_ghost = any(
                it.discrepancy_type == SettlementDiscrepancyType.GHOST_ORDER for it in items
            )
            severity = AlertSeverity.CRITICAL if has_ghost else AlertSeverity.WARNING
            await self._alerts.create_once(
                alert_type=AlertType.RECONCILIATION_MISMATCH,
                severity=severity,
                dedup_key=(
                    f"settlement_discrepancy:{statement.channel_code}:{statement.statement_id}"
                ),
                message=(
                    f"Settlement statement '{statement.statement_id}' on {statement.channel_code} "
                    f"has {discrepancies} discrepancy(s). Reported: {total_reported}, "
                    f"Expected: {total_expected}, Variance: {total_var}"
                ),
            )

        # Audit log persistence
        status = (
            ReconciliationStatus.MISMATCH if discrepancies > 0 else ReconciliationStatus.SUCCESS
        )
        log = ReconciliationLog(
            source_system=statement.channel_code,
            status=status,
            records_checked=total_orders,
            mismatches_found=discrepancies,
            detail_json={
                "statement_id": statement.statement_id,
                "total_reported": str(total_reported),
                "total_expected": str(total_expected),
                "variance": str(total_var),
                "discrepancies": [
                    {
                        "channel_order_id": it.channel_order_id,
                        "type": it.discrepancy_type.value,
                        "variance": str(it.variance),
                        "message": it.message,
                    }
                    for it in items
                    if it.discrepancy_type != SettlementDiscrepancyType.CLEAN_MATCH
                ],
            },
            started_at=started_at,
            completed_at=utc_now(),
        )
        await self._repository.create(log)

        return summary
