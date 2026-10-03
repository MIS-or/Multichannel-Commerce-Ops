from datetime import UTC, datetime
from decimal import Decimal

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.channels.models import Channel
from app.modules.channels.repository import ChannelRepository
from app.modules.channels.service import ChannelService
from app.modules.inventory.service import InventoryService
from app.modules.ledger.repository import LedgerRepository
from app.modules.ledger.service import LedgerService
from app.modules.orders.models import Order
from app.modules.orders.repository import OrderRepository
from app.modules.orders.service import OrderService
from app.modules.products.models import Product
from app.modules.products.repository import ProductRepository
from app.modules.products.service import ProductService
from app.shared.errors import NotFoundError


def build_service(session: AsyncSession) -> OrderService:
    product_service = ProductService(ProductRepository(session))
    return OrderService(
        session=session,
        repository=OrderRepository(session),
        channel_service=ChannelService(ChannelRepository(session)),
        product_service=product_service,
        inventory_service=InventoryService(session, product_service),
        ledger_service=LedgerService(LedgerRepository(session)),
    )


async def test_order_query_returns_newest_first(session: AsyncSession) -> None:
    channel = Channel(code="website", name="Website", platform_type="direct")
    product = Product(
        sku="TEE-WHT-L",
        name="White Tee",
        cost_price=Decimal("140000.00"),
        current_stock=10,
        reorder_threshold=2,
    )
    session.add_all([channel, product])
    await session.flush()
    assert channel.id is not None
    session.add_all(
        [
            Order(
                channel_id=channel.id,
                external_order_id="WEB-OLD",
                order_date=datetime(2026, 9, 1, tzinfo=UTC),
                total_amount=Decimal("250000.00"),
            ),
            Order(
                channel_id=channel.id,
                external_order_id="WEB-NEW",
                order_date=datetime(2026, 9, 2, tzinfo=UTC),
                total_amount=Decimal("250000.00"),
            ),
        ]
    )
    await session.commit()

    orders = await build_service(session).list_orders(limit=10, offset=0)

    assert [order.external_order_id for order in orders] == ["WEB-NEW", "WEB-OLD"]
    assert {order.channel for order in orders} == {"website"}


async def test_order_detail_rejects_unknown_id(session: AsyncSession) -> None:
    with pytest.raises(NotFoundError) as error:
        await build_service(session).get_order(999)

    assert error.value.code == "ORDER_NOT_FOUND"


async def test_order_query_filters_by_channel_and_search(session: AsyncSession) -> None:
    ch_shopee = Channel(code="shopee", name="Shopee", platform_type="marketplace")
    ch_tiktok = Channel(code="tiktok", name="TikTok Shop", platform_type="marketplace")
    session.add_all([ch_shopee, ch_tiktok])
    await session.flush()
    assert ch_shopee.id is not None
    assert ch_tiktok.id is not None

    session.add_all(
        [
            Order(
                channel_id=ch_shopee.id,
                external_order_id="SHP-101",
                order_date=datetime(2026, 9, 3, tzinfo=UTC),
                total_amount=Decimal("150000.00"),
            ),
            Order(
                channel_id=ch_tiktok.id,
                external_order_id="TT-202",
                order_date=datetime(2026, 9, 3, tzinfo=UTC),
                total_amount=Decimal("200000.00"),
            ),
        ]
    )
    await session.commit()

    service = build_service(session)
    # Filter by channel
    shopee_orders = await service.list_orders(limit=10, offset=0, channel="shopee")
    assert len(shopee_orders) == 1
    assert shopee_orders[0].external_order_id == "SHP-101"

    # Filter by search
    searched = await service.list_orders(limit=10, offset=0, search="202")
    assert len(searched) == 1
    assert searched[0].external_order_id == "TT-202"
