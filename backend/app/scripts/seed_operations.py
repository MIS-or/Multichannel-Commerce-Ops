import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any, cast

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.database import SessionFactory, engine
from app.modules.alerts.models import Alert, AlertSeverity, AlertType
from app.modules.audit.models import AuditAction, AuditLog
from app.modules.channels.models import Channel
from app.modules.exceptions.models import (
    ExceptionDomain,
    ExceptionSeverity,
    ExceptionStatus,
    OperationalException,
    RootCauseCategory,
)
from app.modules.integrations.models import SyncRun, SyncStatus, SyncType
from app.modules.inventory.models import InventorySnapshot
from app.modules.jobs.models import JobRun, JobStatus, JobType
from app.modules.ledger.models import LedgerEntry, LedgerEntryType
from app.modules.orders.models import Order, OrderItem, OrderStatus
from app.modules.products.models import Product
from app.modules.reconciliation.models import ReconciliationLog, ReconciliationStatus
from app.modules.rules.models import (
    ActionType,
    Rule,
    RuleExecutionLog,
    RuleExecutionStatus,
    TriggerEvent,
)

CHANNELS = [
    Channel(code="shopee", name="Shopee", platform_type="marketplace"),
    Channel(code="tiktok", name="TikTok Shop", platform_type="marketplace"),
    Channel(code="website", name="Website", platform_type="direct"),
]

PRODUCTS = [
    Product(
        sku="BAG-CNV",
        name="Canvas Tote Bag - Cream",
        cost_price=Decimal("120000.00"),
        current_stock=0,
        reorder_threshold=10,
    ),
    Product(
        sku="TEE-BLK-M",
        name="Classic Tee - Black / M",
        cost_price=Decimal("150000.00"),
        current_stock=40,
        reorder_threshold=8,
    ),
    Product(
        sku="CAP-BLK",
        name="Logo Cap - Black",
        cost_price=Decimal("180000.00"),
        current_stock=5,
        reorder_threshold=10,
    ),
    Product(
        sku="HOODIE-GRY-M",
        name="Oversized Hoodie - Gray / M",
        cost_price=Decimal("320000.00"),
        current_stock=3,
        reorder_threshold=15,
    ),
    Product(
        sku="HOODIE-BLK-M",
        name="Oversized Hoodie - Black / M",
        cost_price=Decimal("320000.00"),
        current_stock=22,
        reorder_threshold=10,
    ),
    Product(
        sku="TEE-WHT-L",
        name="Classic Tee - White / L",
        cost_price=Decimal("140000.00"),
        current_stock=35,
        reorder_threshold=8,
    ),
    Product(
        sku="CAP-WHT",
        name="Logo Cap - White",
        cost_price=Decimal("180000.00"),
        current_stock=18,
        reorder_threshold=5,
    ),
    Product(
        sku="TEE-WHT-M",
        name="Classic Tee - White / M",
        cost_price=Decimal("140000.00"),
        current_stock=50,
        reorder_threshold=8,
    ),
]


@asynccontextmanager
async def _get_session_scope(db_session: AsyncSession | None = None) -> AsyncIterator[AsyncSession]:
    if db_session is not None:
        yield db_session
    else:
        async with SessionFactory() as session, session.begin():
            yield session


async def seed_operations(db_session: AsyncSession | None = None) -> None:
    async with _get_session_scope(db_session) as session:
        now = datetime.now(UTC)

        # 1. Channels
        channel_map: dict[str, Channel] = {}
        for ch in CHANNELS:
            existing = await session.scalar(select(Channel).where(Channel.code == ch.code))
            if existing is None:
                session.add(ch)
                await session.flush()
                channel_map[ch.code] = ch
            else:
                channel_map[ch.code] = existing

        # 2. Products
        product_map: dict[str, Product] = {}
        for prod in PRODUCTS:
            existing = await session.scalar(select(Product).where(Product.sku == prod.sku))
            if existing is None:
                session.add(prod)
                await session.flush()
                product_map[prod.sku] = prod
            else:
                existing.name = prod.name
                existing.cost_price = prod.cost_price
                existing.current_stock = prod.current_stock
                existing.reorder_threshold = prod.reorder_threshold
                session.add(existing)
                await session.flush()
                product_map[prod.sku] = existing

        # 3. Multi-channel Orders & Ledger
        order_templates = [
            # Today's orders
            (
                "shopee",
                "ORD-SHP-8801",
                now - timedelta(minutes=15),
                [
                    ("TEE-BLK-M", 2, Decimal("250000.00")),
                ],
            ),
            (
                "tiktok",
                "ORD-TT-9840",
                now - timedelta(minutes=45),
                [
                    ("HOODIE-BLK-M", 1, Decimal("490000.00")),
                ],
            ),
            (
                "website",
                "ORD-WEB-3011",
                now - timedelta(hours=1, minutes=10),
                [
                    ("TEE-WHT-L", 1, Decimal("220000.00")),
                    ("CAP-WHT", 1, Decimal("280000.00")),
                ],
            ),
            (
                "shopee",
                "ORD-SHP-8802",
                now - timedelta(hours=2),
                [
                    ("TEE-BLK-M", 1, Decimal("250000.00")),
                    ("TEE-WHT-M", 1, Decimal("220000.00")),
                ],
            ),
            (
                "tiktok",
                "ORD-TT-9841",
                now - timedelta(hours=3, minutes=20),
                [
                    ("CAP-BLK", 2, Decimal("280000.00")),
                ],
            ),
            (
                "website",
                "ORD-WEB-3012",
                now - timedelta(hours=4),
                [
                    ("HOODIE-GRY-M", 1, Decimal("490000.00")),
                ],
            ),
            (
                "shopee",
                "ORD-SHP-8803",
                now - timedelta(hours=5),
                [
                    ("HOODIE-BLK-M", 2, Decimal("480000.00")),
                ],
            ),
            (
                "tiktok",
                "ORD-TT-9842",
                now - timedelta(hours=6, minutes=15),
                [
                    ("TEE-WHT-L", 1, Decimal("220000.00")),
                    ("CAP-BLK", 1, Decimal("200000.00")),
                ],
            ),
            (
                "website",
                "ORD-WEB-3013",
                now - timedelta(hours=7),
                [
                    ("TEE-BLK-M", 3, Decimal("240000.00")),
                ],
            ),
            (
                "shopee",
                "ORD-SHP-8804",
                now - timedelta(hours=8, minutes=30),
                [
                    ("CAP-WHT", 1, Decimal("280000.00")),
                ],
            ),
            # Yesterday's orders
            (
                "shopee",
                "ORD-SHP-8790",
                now - timedelta(days=1, hours=2),
                [
                    ("TEE-WHT-M", 2, Decimal("220000.00")),
                ],
            ),
            (
                "tiktok",
                "ORD-TT-9830",
                now - timedelta(days=1, hours=4),
                [
                    ("HOODIE-BLK-M", 1, Decimal("490000.00")),
                ],
            ),
            (
                "website",
                "ORD-WEB-3005",
                now - timedelta(days=1, hours=6),
                [
                    ("TEE-BLK-M", 2, Decimal("250000.00")),
                ],
            ),
            (
                "shopee",
                "ORD-SHP-8791",
                now - timedelta(days=1, hours=8),
                [
                    ("CAP-BLK", 1, Decimal("280000.00")),
                ],
            ),
            (
                "tiktok",
                "ORD-TT-9831",
                now - timedelta(days=1, hours=10),
                [
                    ("TEE-WHT-L", 2, Decimal("220000.00")),
                    ("CAP-WHT", 1, Decimal("280000.00")),
                ],
            ),
            (
                "website",
                "ORD-WEB-3006",
                now - timedelta(days=1, hours=12),
                [
                    ("HOODIE-GRY-M", 2, Decimal("490000.00")),
                ],
            ),
        ]

        for ch_code, ext_id, order_time, items in order_templates:
            channel = channel_map[ch_code]
            assert channel.id is not None
            existing_order = await session.scalar(
                select(Order).where(
                    Order.channel_id == channel.id,
                    Order.external_order_id == ext_id,
                )
            )

            if existing_order is not None:
                continue

            total_amount = sum((qty * price for _, qty, price in items), start=Decimal("0.00"))
            order = Order(
                channel_id=channel.id,
                external_order_id=ext_id,
                order_date=order_time,
                status=OrderStatus.PAID,
                total_amount=total_amount,
                source_updated_at=order_time,
            )
            session.add(order)
            await session.flush()
            assert order.id is not None

            total_cogs = Decimal("0.00")
            for sku, qty, price in items:
                prod = product_map[sku]
                assert prod.id is not None
                order_item = OrderItem(
                    order_id=order.id,
                    product_id=prod.id,
                    quantity=qty,
                    unit_price=price,
                    unit_cost=prod.cost_price,
                )
                session.add(order_item)
                total_cogs += prod.cost_price * qty

            session.add(
                LedgerEntry(
                    order_id=order.id,
                    entry_type=LedgerEntryType.REVENUE,
                    amount=total_amount,
                    created_at=order_time,
                )
            )
            session.add(
                LedgerEntry(
                    order_id=order.id,
                    entry_type=LedgerEntryType.COGS,
                    amount=total_cogs,
                    created_at=order_time,
                )
            )

        # 4. Alerts
        alerts_data = [
            (
                AlertType.LOW_STOCK,
                AlertSeverity.CRITICAL,
                "low_stock:BAG-CNV",
                "Stock level for 'BAG-CNV' (Canvas Tote Bag - Cream) is at 0 units, "
                "below reorder threshold of 10.",
                False,
                None,
            ),
            (
                AlertType.LOW_STOCK,
                AlertSeverity.WARNING,
                "low_stock:HOODIE-GRY-M",
                "Stock level for 'HOODIE-GRY-M' (Oversized Hoodie - Gray / M) is at 3 units, "
                "below reorder threshold of 15.",
                False,
                None,
            ),
            (
                AlertType.RECONCILIATION_MISMATCH,
                AlertSeverity.WARNING,
                "recon_mismatch:tiktok:ORD-TT-9842",
                "Reconciliation mismatch on TikTok Shop: ORD-TT-9842 amount mismatch "
                "(expected 450,000 VND, actual 420,000 VND).",
                False,
                None,
            ),
            (
                AlertType.LOW_STOCK,
                AlertSeverity.INFO,
                "low_stock:CAP-BLK",
                "Stock level for 'CAP-BLK' was low (5 units) and "
                "supplier reorder PO-401 has been triggered.",
                True,
                now - timedelta(hours=3),
            ),
        ]

        for a_type, a_sev, dedup, msg, is_resolved, resolved_time in alerts_data:
            existing_alert = await session.scalar(select(Alert).where(Alert.dedup_key == dedup))
            if existing_alert is None:
                session.add(
                    Alert(
                        type=a_type,
                        severity=a_sev,
                        dedup_key=dedup,
                        message=msg,
                        resolved=is_resolved,
                        resolved_at=resolved_time,
                        created_at=now - timedelta(hours=4),
                    )
                )

        # 5. Reconciliation runs
        existing_recons = await session.scalars(select(ReconciliationLog))
        if len(list(existing_recons.all())) == 0:
            session.add(
                ReconciliationLog(
                    source_system="shopee",
                    status=ReconciliationStatus.SUCCESS,
                    records_checked=50,
                    mismatches_found=0,
                    detail_json={"mismatches": []},
                    started_at=now - timedelta(hours=2),
                    completed_at=now - timedelta(hours=2) + timedelta(seconds=3),
                )
            )
            session.add(
                ReconciliationLog(
                    source_system="tiktok",
                    status=ReconciliationStatus.MISMATCH,
                    records_checked=45,
                    mismatches_found=2,
                    detail_json={
                        "mismatches": [
                            {
                                "external_order_id": "ORD-TT-9842",
                                "code": "TOTAL_MISMATCH",
                                "expected": "450000.00",
                                "actual": "420000.00",
                            },
                            {
                                "external_order_id": "ORD-TT-9845",
                                "code": "MISSING_ORDER",
                                "expected": "280000.00",
                                "actual": None,
                            },
                        ]
                    },
                    started_at=now - timedelta(hours=1),
                    completed_at=now - timedelta(hours=1) + timedelta(seconds=4),
                )
            )
            session.add(
                ReconciliationLog(
                    source_system="website",
                    status=ReconciliationStatus.SUCCESS,
                    records_checked=32,
                    mismatches_found=0,
                    detail_json={"mismatches": []},
                    started_at=now - timedelta(minutes=30),
                    completed_at=now - timedelta(minutes=30) + timedelta(seconds=2),
                )
            )

        # 6. Multi-Source Inventory Snapshots
        snapshots_data = [
            # ERP (Physical SoT)
            ("erp", "TEE-BLK-M", Decimal("40.00"), Decimal("5.00"), Decimal("35.00")),
            ("erp", "TEE-WHT-L", Decimal("35.00"), Decimal("2.00"), Decimal("33.00")),
            ("erp", "CAP-BLK", Decimal("5.00"), Decimal("0.00"), Decimal("5.00")),
            ("erp", "HOODIE-GRY-M", Decimal("3.00"), Decimal("1.00"), Decimal("2.00")),
            ("erp", "BAG-CNV", Decimal("0.00"), Decimal("0.00"), Decimal("0.00")),
            # Shopee VN Channel Snapshot
            ("shopee_vn", "TEE-BLK-M", Decimal("40.00"), Decimal("6.00"), Decimal("34.00")),
            ("shopee_vn", "TEE-WHT-L", Decimal("35.00"), Decimal("2.00"), Decimal("33.00")),
            ("shopee_vn", "CAP-BLK", Decimal("5.00"), Decimal("0.00"), Decimal("5.00")),
            ("shopee_vn", "HOODIE-GRY-M", Decimal("3.00"), Decimal("5.00"), Decimal("-2.00")),
            # TikTok Shop VN Channel Snapshot
            ("tiktok_shop_vn", "TEE-BLK-M", Decimal("40.00"), Decimal("2.00"), Decimal("38.00")),
            ("tiktok_shop_vn", "TEE-WHT-L", Decimal("35.00"), Decimal("1.00"), Decimal("34.00")),
            ("tiktok_shop_vn", "BAG-CNV", Decimal("0.00"), Decimal("2.00"), Decimal("-2.00")),
        ]

        for src, sku, on_hand, allocated, available in snapshots_data:
            existing_snap = await session.scalar(
                select(InventorySnapshot).where(
                    InventorySnapshot.source_system == src,
                    InventorySnapshot.sku == sku,
                )
            )
            if existing_snap is None:
                session.add(
                    InventorySnapshot(
                        source_system=src,
                        sku=sku,
                        on_hand_qty=on_hand,
                        allocated_qty=allocated,
                        available_qty=available,
                        captured_at=now - timedelta(hours=1),
                    )
                )

        # 7. Operational Exceptions
        exceptions_data = [
            (
                ExceptionDomain.INVENTORY_VARIANCE,
                ExceptionSeverity.CRITICAL,
                ExceptionStatus.OPEN,
                "HOODIE-GRY-M",
                "shopee_vn",
                "Over-allocation discrepancy on Shopee VN",
                "Shopee allocated 5 units while ERP available quantity is only 2 units. "
                "Risk of overselling and fulfillment cancellation penalty.",
                Decimal("3.00"),
                {"erp_available": 2, "channel_allocated": 5},
                None,
                None,
                None,
                None,
            ),
            (
                ExceptionDomain.SETTLEMENT_DISCREPANCY,
                ExceptionSeverity.HIGH,
                ExceptionStatus.INVESTIGATING,
                "ORD-TT-9842",
                "tiktok_shop_vn",
                "Platform fee overcharge detected on TikTok Settlement",
                "Calculated net payout was 420,000 VND, expected 450,000 VND. "
                "Service fee deducted exceeded rate card agreed limit by 30,000 VND.",
                Decimal("30000.00"),
                {"expected_payout": 450000, "actual_payout": 420000, "difference": 30000},
                "sarah.accounting@mco.internal",
                None,
                None,
                None,
            ),
            (
                ExceptionDomain.ORDER_SYNC_FAILED,
                ExceptionSeverity.MEDIUM,
                ExceptionStatus.RESOLVED,
                "ORD-SHP-8802",
                "shopee_vn",
                "Malformed customer address payload during webhook ingest",
                "Customer delivery postal code was null; normalized using district fallback.",
                Decimal("0.00"),
                {"raw_code": "ADDR_PARSE_WARN"},
                "dev.integration@mco.internal",
                RootCauseCategory.MALFORMED_EXTERNAL_PAYLOAD,
                "Applied schema transformer fallback in normalization pipeline and "
                "re-ingested successfully.",
                now - timedelta(hours=1),
            ),
        ]

        for (
            domain,
            sev,
            stat,
            ref,
            ch_code,
            title,
            desc,
            var_amt,
            snap,
            assignee,
            cause,
            notes,
            res_time,
        ) in exceptions_data:
            existing_exc = await session.scalar(
                select(OperationalException).where(
                    OperationalException.reference_id == ref,
                    OperationalException.domain == domain,
                )
            )
            if existing_exc is None:
                session.add(
                    OperationalException(
                        domain=domain,
                        severity=sev,
                        status=stat,
                        reference_id=ref,
                        channel_code=ch_code,
                        title=title,
                        description=desc,
                        variance_amount=var_amt,
                        payload_snapshot=cast(dict[str, Any], snap),
                        assigned_to=assignee,
                        root_cause=cause,
                        resolution_notes=notes,
                        resolved_at=res_time,
                        created_at=now - timedelta(hours=3),
                        updated_at=now - timedelta(hours=1),
                    )
                )

        # 8. Automation Rules
        rules_data = [
            (
                "Auto-Triage Critical Inventory Discrepancy",
                "Create an operational exception when inventory variance severity is CRITICAL.",
                TriggerEvent.INVENTORY_VARIANCE_DETECTED,
                [{"field": "severity", "operator": "equals", "value": "critical"}],
                [
                    {
                        "action_type": ActionType.CREATE_EXCEPTION,
                        "parameters": {
                            "domain": "inventory_variance",
                            "severity": "critical",
                            "title": "Auto-triaged Critical Inventory Discrepancy",
                            "description": (
                                "Triggered by automation rule for critical inventory variance."
                            ),
                        },
                    }
                ],
            ),
            (
                "Alert Finance on Settlement Discrepancy",
                "Dispatch alert to internal channel when settlement payout difference "
                "exceeds 20,000 VND.",
                TriggerEvent.SETTLEMENT_DISCREPANCY_DETECTED,
                [{"field": "variance_amount", "operator": "greater_than_or_equal", "value": 20000}],
                [
                    {
                        "action_type": ActionType.CREATE_ALERT,
                        "parameters": {
                            "severity": "warning",
                            "channel": "finance",
                            "message": "Settlement variance exceeds 20,000 VND threshold.",
                        },
                    }
                ],
            ),
            (
                "Notify n8n Workflow on High-Value Order",
                (
                    "Trigger n8n webhook workflow whenever an ingested "
                    "order total exceeds 1,000,000 VND."
                ),
                TriggerEvent.ORDER_INGESTED,
                [
                    {
                        "field": "total_amount",
                        "operator": "greater_than_or_equal",
                        "value": 1000000,
                    }
                ],
                [
                    {
                        "action_type": ActionType.TRIGGER_WEBHOOK,
                        "parameters": {
                            "webhook_url": "http://n8n:5678/webhook/high-value-order",
                            "method": "POST",
                        },
                    }
                ],
            ),
        ]

        for r_name, r_desc, r_trig, r_conds, r_actions in rules_data:
            existing_rule = await session.scalar(select(Rule).where(Rule.name == r_name))
            if existing_rule is None:
                session.add(
                    Rule(
                        name=r_name,
                        description=r_desc,
                        trigger_event=r_trig,
                        is_active=True,
                        conditions=cast(list[dict[str, Any]], r_conds),
                        actions=cast(list[dict[str, Any]], r_actions),
                        created_at=now - timedelta(days=2),
                        updated_at=now - timedelta(days=2),
                    )
                )

        await session.flush()

        # Seed Rule Execution Logs
        rule_1 = await session.scalar(
            select(Rule).where(Rule.name == "Auto-Triage Critical Inventory Discrepancy")
        )
        rule_2 = await session.scalar(
            select(Rule).where(Rule.name == "Alert Finance on Settlement Discrepancy")
        )
        rule_3 = await session.scalar(
            select(Rule).where(Rule.name == "Notify n8n Workflow on High-Value Order")
        )

        if rule_1 and rule_1.id:
            existing_log = await session.scalar(
                select(RuleExecutionLog).where(RuleExecutionLog.rule_id == rule_1.id)
            )
            if existing_log is None:
                session.add(
                    RuleExecutionLog(
                        rule_id=rule_1.id,
                        trigger_event=TriggerEvent.INVENTORY_VARIANCE_DETECTED,
                        matched=True,
                        status=RuleExecutionStatus.SUCCESS,
                        payload_snapshot={
                            "sku": "BAG-CNV",
                            "channel_code": "shopee_vn",
                            "variance_amount": 12,
                            "severity": "critical",
                        },
                        actions_taken=[
                            {
                                "action_type": "create_exception",
                                "status": "executed",
                                "exception_id": 1,
                            }
                        ],
                        error_message=None,
                        executed_at=now - timedelta(hours=2),
                    )
                )
        if rule_2 and rule_2.id:
            existing_log = await session.scalar(
                select(RuleExecutionLog).where(RuleExecutionLog.rule_id == rule_2.id)
            )
            if existing_log is None:
                session.add(
                    RuleExecutionLog(
                        rule_id=rule_2.id,
                        trigger_event=TriggerEvent.SETTLEMENT_DISCREPANCY_DETECTED,
                        matched=True,
                        status=RuleExecutionStatus.SUCCESS,
                        payload_snapshot={
                            "channel_code": "tiktok_shop_vn",
                            "variance_amount": 30000,
                            "expected_payout": 450000,
                            "actual_payout": 420000,
                        },
                        actions_taken=[
                            {
                                "action_type": "create_alert",
                                "status": "executed",
                                "channel": "finance",
                            }
                        ],
                        error_message=None,
                        executed_at=now - timedelta(hours=1, minutes=30),
                    )
                )
        if rule_3 and rule_3.id:
            existing_log = await session.scalar(
                select(RuleExecutionLog).where(RuleExecutionLog.rule_id == rule_3.id)
            )
            if existing_log is None:
                session.add(
                    RuleExecutionLog(
                        rule_id=rule_3.id,
                        trigger_event=TriggerEvent.ORDER_INGESTED,
                        matched=True,
                        status=RuleExecutionStatus.SUCCESS,
                        payload_snapshot={
                            "order_id": "ORD-2026-0904-001",
                            "channel_code": "shopee",
                            "total_amount": 1250000,
                        },
                        actions_taken=[
                            {
                                "action_type": "trigger_webhook",
                                "status": "dispatched",
                                "url": "http://n8n:5678/webhook/high-value-order",
                            }
                        ],
                        error_message=None,
                        executed_at=now - timedelta(minutes=45),
                    )
                )

        # 9. Sync Runs Telemetry
        sync_runs_data = [
            (
                "shopee_vn",
                SyncType.ORDERS,
                SyncStatus.SUCCESS,
                25,
                25,
                0,
                "2026-10-03T10:00:00Z",
                185,
                now - timedelta(hours=2),
            ),
            (
                "tiktok_shop_vn",
                SyncType.ORDERS,
                SyncStatus.SUCCESS,
                18,
                18,
                0,
                "2026-10-03T10:00:00Z",
                142,
                now - timedelta(hours=1, minutes=45),
            ),
            (
                "odoo_erp",
                SyncType.INVENTORY,
                SyncStatus.SUCCESS,
                8,
                8,
                0,
                None,
                64,
                now - timedelta(hours=1),
            ),
            (
                "shopee_vn",
                SyncType.INVENTORY,
                SyncStatus.SUCCESS,
                8,
                8,
                0,
                None,
                92,
                now - timedelta(minutes=45),
            ),
            (
                "shopee_vn",
                SyncType.SETTLEMENT,
                SyncStatus.SUCCESS,
                15,
                15,
                0,
                "2026-10-03T00:00:00Z",
                210,
                now - timedelta(minutes=30),
            ),
        ]

        for (
            c_code,
            stype,
            status,
            fetched,
            processed,
            failed,
            cursor,
            duration,
            start_time,
        ) in sync_runs_data:
            existing_run = await session.scalar(
                select(SyncRun).where(
                    SyncRun.channel_code == c_code,
                    SyncRun.sync_type == stype,
                    SyncRun.started_at == start_time,
                )
            )
            if existing_run is None:
                session.add(
                    SyncRun(
                        channel_code=c_code,
                        sync_type=stype,
                        status=status,
                        records_fetched=fetched,
                        records_processed=processed,
                        records_failed=failed,
                        cursor_value=cursor,
                        duration_ms=duration,
                        started_at=start_time,
                        completed_at=start_time + timedelta(milliseconds=duration),
                    )
                )

        # ---------------------------------------------------------------------
        # 10. Operational Audit Logs
        # ---------------------------------------------------------------------
        audit_logs_data = [
            (
                "usr_ops_01",
                "operations",
                AuditAction.EXCEPTION_ASSIGNED.value,
                "operational_exception",
                "1",
                {"assigned_to": None, "status": "open"},
                {"assigned_to": "warehouse_lead", "status": "investigating"},
                "Assigned stock variance to warehouse lead",
                now - timedelta(hours=3),
            ),
            (
                "usr_finance_01",
                "finance",
                AuditAction.EXCEPTION_RESOLVED.value,
                "operational_exception",
                "2",
                {"status": "investigating"},
                {
                    "status": "resolved",
                    "root_cause": "platform_fee_overcharge",
                    "resolution_notes": "Claim submitted to platform partner",
                },
                "Dispute accepted by platform partner",
                now - timedelta(hours=1),
            ),
            (
                "usr_admin_01",
                "admin",
                AuditAction.RULE_TOGGLED.value,
                "automation_rule",
                "1",
                {"is_active": False},
                {"is_active": True},
                "Activated critical stock alert routing rule",
                now - timedelta(hours=5),
            ),
            (
                "usr_ops_01",
                "operations",
                AuditAction.SYNC_TRIGGERED.value,
                "sync_run",
                "1",
                None,
                {"channel": "shopee", "sync_type": "orders", "status": "success"},
                "Manual synchronization verified during shift handoff",
                now - timedelta(minutes=45),
            ),
        ]

        for (
            actor_id,
            actor_role,
            action,
            entity_type,
            entity_id,
            before_state,
            after_state,
            reason,
            created_at_time,
        ) in audit_logs_data:
            existing_audit = await session.scalar(
                select(AuditLog).where(
                    AuditLog.actor_id == actor_id,
                    AuditLog.action == action,
                    AuditLog.entity_id == entity_id,
                )
            )
            if existing_audit is None:
                session.add(
                    AuditLog(
                        actor_id=actor_id,
                        actor_role=actor_role,
                        action=action,
                        entity_type=entity_type,
                        entity_id=entity_id,
                        before_state=cast(dict[str, Any] | None, before_state),
                        after_state=cast(dict[str, Any] | None, after_state),
                        reason=reason,
                        created_at=created_at_time,
                    )
                )

        # 11. Background Operational Jobs (JobRun)
        jobs_data = [
            (
                JobType.CHANNEL_SYNC.value,
                JobStatus.COMPLETED.value,
                {"channel_code": "shopee", "sync_type": "orders"},
                {"status": "success", "records_processed": 142},
                None,
                0,
                3,
                "system",
                now - timedelta(minutes=30),
                now - timedelta(minutes=29),
                now - timedelta(minutes=31),
            ),
            (
                JobType.SETTLEMENT_RECONCILIATION.value,
                JobStatus.COMPLETED.value,
                {"channel_code": "tiktok", "sample_size": 28},
                {"status": "completed", "entries_reconciled": 28},
                None,
                0,
                3,
                "usr_finance_01",
                now - timedelta(hours=2),
                now - timedelta(hours=2) + timedelta(seconds=45),
                now - timedelta(hours=2, minutes=1),
            ),
            (
                JobType.INVENTORY_VARIANCE_CHECK.value,
                JobStatus.PENDING.value,
                {"channel_code": "shopee", "erp_source": "odoo_erp"},
                None,
                None,
                0,
                3,
                "usr_ops_01",
                None,
                None,
                now - timedelta(minutes=5),
            ),
            (
                JobType.RULE_EVALUATION.value,
                JobStatus.FAILED.value,
                {"rule_ids": [1, 2]},
                None,
                "Rate limit exceeded on upstream webhook notification",
                3,
                3,
                "system",
                now - timedelta(hours=1),
                now - timedelta(minutes=58),
                now - timedelta(hours=1, minutes=2),
            ),
        ]

        for (
            job_type,
            job_status,
            payload,
            result,
            error_message,
            retry_count,
            max_retries,
            enqueued_by,
            started_at,
            completed_at,
            created_at_time,
        ) in jobs_data:
            existing_job = await session.scalar(
                select(JobRun).where(
                    JobRun.job_type == job_type,
                    JobRun.enqueued_by == enqueued_by,
                    JobRun.status == job_status,
                )
            )
            if existing_job is None:
                session.add(
                    JobRun(
                        job_type=job_type,
                        status=job_status,
                        payload=cast(dict[str, Any], payload),
                        result=cast(dict[str, Any] | None, result),
                        error_message=error_message,
                        retry_count=retry_count,
                        max_retries=max_retries,
                        enqueued_by=enqueued_by,
                        started_at=started_at,
                        completed_at=completed_at,
                        created_at=created_at_time,
                    )
                )


async def main() -> None:
    try:
        await seed_operations()
        print("Operational data successfully seeded!")
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
