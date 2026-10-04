from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.channels.models import Channel
from app.modules.ledger.models import LedgerEntryType
from app.modules.ledger.repository import LedgerRepository
from app.modules.ledger.schemas import OrderSaleRecord, SaleItemRecord
from app.modules.ledger.service import LedgerService
from app.modules.orders.models import Order, OrderItem
from app.modules.products.models import Product


async def test_sale_ledger_calculates_revenue_and_cogs(session: AsyncSession) -> None:
    channel = Channel(code="website", name="Website", platform_type="direct")
    product = Product(
        sku="TEE-WHT-L",
        name="White Tee L",
        cost_price=Decimal("140000.00"),
        current_stock=10,
        reorder_threshold=2,
    )
    session.add_all([channel, product])
    await session.flush()
    assert channel.id is not None and product.id is not None

    order = Order(
        channel_id=channel.id,
        external_order_id="WEB-1",
        order_date=datetime.now(UTC),
        total_amount=Decimal("500000.00"),
    )
    session.add(order)
    await session.flush()
    assert order.id is not None

    items = [
        OrderItem(
            order_id=order.id,
            product_id=product.id,
            quantity=2,
            unit_price=Decimal("250000.00"),
            unit_cost=Decimal("140000.00"),
        )
    ]
    session.add_all(items)
    await session.flush()

    repository = LedgerRepository(session)
    await LedgerService(repository).record_sale(
        OrderSaleRecord(
            order_id=order.id,
            items=[
                SaleItemRecord(
                    unit_price=Decimal("250000.00"),
                    unit_cost=Decimal("140000.00"),
                    quantity=2,
                )
            ],
        )
    )
    entries = await repository.get_for_order(order.id)

    by_type = {entry.entry_type: entry.amount for entry in entries}
    assert by_type[LedgerEntryType.REVENUE] == Decimal("500000.00")
    assert by_type[LedgerEntryType.COGS] == Decimal("280000.00")


async def test_record_sale_accepts_pure_contract_without_orm_entities(
    session: AsyncSession,
) -> None:
    repository = LedgerRepository(session)
    service = LedgerService(repository)

    record = OrderSaleRecord(
        order_id=999,
        items=[
            SaleItemRecord(
                unit_price=Decimal("100.00"),
                unit_cost=Decimal("60.00"),
                quantity=3,
            ),
            SaleItemRecord(
                unit_price=Decimal("50.00"),
                unit_cost=Decimal("25.00"),
                quantity=2,
            ),
        ],
    )
    await service.record_sale(record)

    entries = await repository.get_for_order(999)
    assert len(entries) == 2
    by_type = {entry.entry_type: entry.amount for entry in entries}
    assert by_type[LedgerEntryType.REVENUE] == Decimal("400.00")
    assert by_type[LedgerEntryType.COGS] == Decimal("230.00")
