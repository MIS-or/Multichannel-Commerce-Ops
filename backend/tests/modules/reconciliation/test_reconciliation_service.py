from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.alerts.repository import AlertRepository
from app.modules.alerts.service import AlertService
from app.modules.channels.models import Channel
from app.modules.channels.repository import ChannelRepository
from app.modules.channels.service import ChannelService
from app.modules.inventory.service import InventoryService
from app.modules.ledger.models import LedgerEntry, LedgerEntryType
from app.modules.ledger.repository import LedgerRepository
from app.modules.ledger.service import LedgerService
from app.modules.orders.models import Order, OrderItem
from app.modules.orders.repository import OrderRepository
from app.modules.orders.service import OrderService
from app.modules.products.models import Product
from app.modules.products.repository import ProductRepository
from app.modules.products.service import ProductService
from app.modules.reconciliation.models import ReconciliationStatus
from app.modules.reconciliation.repository import ReconciliationRepository
from app.modules.reconciliation.schemas import (
    ReconciliationRequest,
    SourceOrderSnapshot,
)
from app.modules.reconciliation.service import ReconciliationService


async def _service(session: AsyncSession) -> ReconciliationService:
    channel_service = ChannelService(ChannelRepository(session))
    product_service = ProductService(ProductRepository(session))
    alert_service = AlertService(session, AlertRepository(session))
    inventory_service = InventoryService(session, product_service, alert_service=alert_service)
    ledger_service = LedgerService(LedgerRepository(session))
    order_service = OrderService(
        session=session,
        repository=OrderRepository(session),
        channel_service=channel_service,
        product_service=product_service,
        inventory_service=inventory_service,
        ledger_service=ledger_service,
    )
    return ReconciliationService(
        session=session,
        repository=ReconciliationRepository(session),
        channel_service=channel_service,
        order_service=order_service,
        ledger_service=ledger_service,
        alert_service=alert_service,
    )


async def test_reconciliation_detects_wrong_revenue(session: AsyncSession) -> None:
    channel = Channel(code="shopee", name="Shopee", platform_type="marketplace")
    product = Product(
        sku="TEE-BLK-M",
        name="Black Tee",
        cost_price=Decimal("150.00"),
        current_stock=10,
        reorder_threshold=2,
    )
    session.add_all([channel, product])
    await session.flush()
    assert channel.id is not None and product.id is not None

    order = Order(
        channel_id=channel.id,
        external_order_id="SP-1",
        order_date=datetime(2026, 9, 1, tzinfo=UTC),
        total_amount=Decimal("500.00"),
    )
    session.add(order)
    await session.flush()
    assert order.id is not None
    session.add(
        OrderItem(
            order_id=order.id,
            product_id=product.id,
            quantity=2,
            unit_price=Decimal("250.00"),
            unit_cost=Decimal("150.00"),
        )
    )
    session.add_all(
        [
            LedgerEntry(
                order_id=order.id,
                entry_type=LedgerEntryType.REVENUE,
                amount=Decimal("450.00"),
            ),
            LedgerEntry(
                order_id=order.id,
                entry_type=LedgerEntryType.COGS,
                amount=Decimal("300.00"),
            ),
        ]
    )
    await session.commit()

    result = await (await _service(session)).reconcile(
        ReconciliationRequest(
            source_system="shopee",
            orders=[SourceOrderSnapshot(external_order_id="SP-1", total_amount=Decimal("500.00"))],
        )
    )

    assert result.status is ReconciliationStatus.MISMATCH
    assert result.mismatches_found == 1
    mismatches = result.detail_json.get("mismatches", [])
    assert isinstance(mismatches, list)
    codes = [item["code"] for item in mismatches if isinstance(item, dict)]
    assert codes == ["REVENUE_MISMATCH"]
    active_alerts = await AlertRepository(session).list_all(resolved=False)
    assert len(active_alerts) == 1


async def test_reconciliation_reports_clean_match(session: AsyncSession) -> None:
    channel = Channel(code="website", name="Website", platform_type="direct")
    product = Product(
        sku="CAP-WHT",
        name="White Cap",
        cost_price=Decimal("180.00"),
        current_stock=10,
        reorder_threshold=2,
    )
    session.add_all([channel, product])
    await session.flush()
    assert channel.id is not None and product.id is not None
    order = Order(
        channel_id=channel.id,
        external_order_id="WEB-1",
        order_date=datetime(2026, 9, 1, tzinfo=UTC),
        total_amount=Decimal("320.00"),
    )
    session.add(order)
    await session.flush()
    assert order.id is not None
    session.add(
        OrderItem(
            order_id=order.id,
            product_id=product.id,
            quantity=1,
            unit_price=Decimal("320.00"),
            unit_cost=Decimal("180.00"),
        )
    )
    session.add_all(
        [
            LedgerEntry(
                order_id=order.id,
                entry_type=LedgerEntryType.REVENUE,
                amount=Decimal("320.00"),
            ),
            LedgerEntry(
                order_id=order.id,
                entry_type=LedgerEntryType.COGS,
                amount=Decimal("180.00"),
            ),
        ]
    )
    await session.commit()

    result = await (await _service(session)).reconcile(
        ReconciliationRequest(
            source_system="website",
            orders=[SourceOrderSnapshot(external_order_id="WEB-1", total_amount=Decimal("320.00"))],
        )
    )

    assert result.status is ReconciliationStatus.SUCCESS
    assert result.mismatches_found == 0


async def test_reconciliation_detects_order_missing(session: AsyncSession) -> None:
    channel = Channel(code="tiktok", name="TikTok Shop", platform_type="marketplace")
    session.add(channel)
    await session.commit()

    result = await (await _service(session)).reconcile(
        ReconciliationRequest(
            source_system="tiktok",
            orders=[
                SourceOrderSnapshot(
                    external_order_id="TK-MISSING",
                    total_amount=Decimal("100.00"),
                )
            ],
        )
    )

    assert result.status is ReconciliationStatus.MISMATCH
    assert result.mismatches_found == 1
    mismatches = result.detail_json.get("mismatches", [])
    assert isinstance(mismatches, list)
    codes = [item["code"] for item in mismatches if isinstance(item, dict)]
    assert codes == ["MISSING_ORDER"]


async def test_reconciliation_detects_total_and_cogs_mismatches(session: AsyncSession) -> None:
    channel = Channel(code="shopee", name="Shopee", platform_type="marketplace")
    product = Product(
        sku="TEE-RED-L",
        name="Red Tee",
        cost_price=Decimal("100.00"),
        current_stock=10,
        reorder_threshold=2,
    )
    session.add_all([channel, product])
    await session.flush()
    assert channel.id is not None and product.id is not None

    order = Order(
        channel_id=channel.id,
        external_order_id="SP-2",
        order_date=datetime(2026, 9, 1, tzinfo=UTC),
        total_amount=Decimal("200.00"),
    )
    session.add(order)
    await session.flush()
    assert order.id is not None

    session.add(
        OrderItem(
            order_id=order.id,
            product_id=product.id,
            quantity=1,
            unit_price=Decimal("200.00"),
            unit_cost=Decimal("100.00"),
        )
    )
    session.add_all(
        [
            LedgerEntry(
                order_id=order.id,
                entry_type=LedgerEntryType.REVENUE,
                amount=Decimal("200.00"),
            ),
            # Corrupted COGS in ledger (50.00 instead of expected 100.00)
            LedgerEntry(
                order_id=order.id,
                entry_type=LedgerEntryType.COGS,
                amount=Decimal("50.00"),
            ),
        ]
    )
    await session.commit()

    # Pass external order with total_amount 250.00
    # (triggers TOTAL_MISMATCH & REVENUE_MISMATCH against local 200.00)
    result = await (await _service(session)).reconcile(
        ReconciliationRequest(
            source_system="shopee",
            orders=[SourceOrderSnapshot(external_order_id="SP-2", total_amount=Decimal("250.00"))],
        )
    )

    assert result.status is ReconciliationStatus.MISMATCH
    assert result.mismatches_found == 3
    mismatches = result.detail_json.get("mismatches", [])
    assert isinstance(mismatches, list)
    codes = {item["code"] for item in mismatches if isinstance(item, dict)}
    assert codes == {"TOTAL_MISMATCH", "REVENUE_MISMATCH", "COGS_MISMATCH"}
