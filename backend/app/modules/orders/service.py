from collections import defaultdict
from collections.abc import Sequence
from decimal import Decimal

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.channels.service import ChannelService
from app.modules.inventory.service import InventoryService
from app.modules.ledger.schemas import OrderSaleRecord, SaleItemRecord
from app.modules.ledger.service import LedgerService
from app.modules.orders.models import Order, OrderItem, OrderStatus
from app.modules.orders.repository import OrderRepository
from app.modules.orders.schemas import (
    OrderDetail,
    OrderImportRequest,
    OrderImportResponse,
    OrderImportStatus,
    OrderItemRead,
    OrderRead,
)
from app.modules.products.service import ProductService
from app.shared.errors import NotFoundError


class OrderService:
    """Application service owning the order-import transaction boundary."""

    def __init__(
        self,
        session: AsyncSession,
        repository: OrderRepository,
        channel_service: ChannelService,
        product_service: ProductService,
        inventory_service: InventoryService,
        ledger_service: LedgerService,
    ) -> None:
        self._session = session
        self._repository = repository
        self._channel_service = channel_service
        self._product_service = product_service
        self._inventory_service = inventory_service
        self._ledger_service = ledger_service

    async def list_orders(
        self,
        *,
        limit: int,
        offset: int,
        channel: str | None = None,
        status: OrderStatus | None = None,
        search: str | None = None,
    ) -> list[OrderRead]:
        rows = await self._repository.list_with_channel(
            limit=limit,
            offset=offset,
            channel=channel,
            status=status,
            search=search,
        )
        return [self._to_read(order, channel) for order, channel in rows]

    async def get_order(self, order_id: int) -> OrderDetail:
        row = await self._repository.get_with_channel(order_id)
        if row is None:
            raise NotFoundError(
                "ORDER_NOT_FOUND",
                f"Order id '{order_id}' does not exist",
                details={"order_id": order_id},
            )
        order, channel = row
        items = await self._repository.get_items(order_id)
        product_ids = [item.product_id for item in items]
        products = await self._product_service.get_by_ids(product_ids)
        product_by_id = {p.id: p for p in products if p.id is not None}

        item_reads: list[OrderItemRead] = []
        for item in items:
            if item.id is None:
                continue
            product = product_by_id.get(item.product_id)
            item_reads.append(
                OrderItemRead(
                    id=item.id,
                    product_id=item.product_id,
                    quantity=item.quantity,
                    unit_price=item.unit_price,
                    unit_cost=item.unit_cost,
                    sku=product.sku if product is not None else None,
                    product_name=product.name if product is not None else None,
                )
            )

        return OrderDetail(
            **self._to_read(order, channel).model_dump(),
            items=item_reads,
        )

    async def get_orders_for_reconciliation(
        self,
        channel_id: int,
        external_order_ids: Sequence[str],
    ) -> list[Order]:
        return await self._repository.get_by_external_ids(channel_id, external_order_ids)

    async def get_order_items_cogs(
        self,
        order_ids: Sequence[int],
    ) -> dict[int, Decimal]:
        items = await self._repository.get_items_for_orders(order_ids)
        expected_cogs: dict[int, Decimal] = defaultdict(lambda: Decimal("0.00"))
        for item in items:
            expected_cogs[item.order_id] += item.unit_cost * item.quantity
        return dict(expected_cogs)

    @staticmethod
    def _to_read(order: Order, channel: str) -> OrderRead:
        assert order.id is not None
        return OrderRead(
            id=order.id,
            channel_id=order.channel_id,
            channel=channel,
            external_order_id=order.external_order_id,
            order_date=order.order_date,
            status=order.status,
            total_amount=order.total_amount,
            source_updated_at=order.source_updated_at,
            created_at=order.created_at,
            updated_at=order.updated_at,
        )

    async def import_order(self, payload: OrderImportRequest) -> OrderImportResponse:
        tx = (
            self._session.begin_nested()
            if self._session.in_transaction()
            else self._session.begin()
        )
        try:
            async with tx:
                channel = await self._channel_service.get_by_code(payload.channel)
                assert channel.id is not None

                existing = await self._repository.get_by_identity(
                    channel.id,
                    payload.external_order_id,
                )
                if existing is not None:
                    assert existing.id is not None
                    return OrderImportResponse(
                        status=OrderImportStatus.DUPLICATE,
                        order_id=existing.id,
                    )

                product_by_sku = {
                    item.sku: await self._product_service.get_by_sku(item.sku)
                    for item in payload.items
                }

                order = await self._repository.create(
                    Order(
                        channel_id=channel.id,
                        external_order_id=payload.external_order_id,
                        order_date=payload.order_date,
                        status=payload.status,
                        total_amount=payload.total_amount,
                        source_updated_at=payload.source_updated_at,
                    )
                )
                assert order.id is not None

                order_items: list[OrderItem] = []
                for item in payload.items:
                    product = product_by_sku[item.sku]
                    assert product.id is not None
                    order_items.append(
                        OrderItem(
                            order_id=order.id,
                            product_id=product.id,
                            quantity=item.quantity,
                            unit_price=item.unit_price,
                            unit_cost=product.cost_price,
                        )
                    )
                await self._repository.add_items(order_items)

                for order_item in order_items:
                    await self._inventory_service.consume(
                        order_item.product_id,
                        order_item.quantity,
                    )

                assert order.id is not None
                await self._ledger_service.record_sale(
                    OrderSaleRecord(
                        order_id=order.id,
                        items=[
                            SaleItemRecord(
                                unit_price=order_item.unit_price,
                                unit_cost=order_item.unit_cost,
                                quantity=order_item.quantity,
                            )
                            for order_item in order_items
                        ],
                    )
                )

            return OrderImportResponse(
                status=OrderImportStatus.IMPORTED,
                order_id=order.id,
            )
        except IntegrityError:
            # A concurrent retry can race the pre-insert lookup. The database unique
            # constraint is the final authority; the losing request becomes a no-op.
            channel = await self._channel_service.get_by_code(payload.channel)
            assert channel.id is not None
            existing = await self._repository.get_by_identity(
                channel.id,
                payload.external_order_id,
            )
            if existing is None:
                raise
            assert existing.id is not None
            return OrderImportResponse(
                status=OrderImportStatus.DUPLICATE,
                order_id=existing.id,
            )
