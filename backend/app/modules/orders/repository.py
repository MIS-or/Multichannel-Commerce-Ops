from collections.abc import Sequence

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import col, select

from app.modules.channels.models import Channel
from app.modules.orders.models import Order, OrderItem, OrderStatus


class OrderRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_identity(self, channel_id: int, external_order_id: str) -> Order | None:
        result = await self._session.execute(
            select(Order).where(
                col(Order.channel_id) == channel_id,
                col(Order.external_order_id) == external_order_id,
            )
        )
        return result.scalar_one_or_none()

    async def get_by_id(self, order_id: int) -> Order | None:
        return await self._session.get(Order, order_id)

    async def create(self, order: Order) -> Order:
        self._session.add(order)
        await self._session.flush()
        return order

    async def add_items(self, items: Sequence[OrderItem]) -> None:
        self._session.add_all(list(items))
        await self._session.flush()

    async def list_with_channel(
        self,
        *,
        limit: int,
        offset: int,
        channel: str | None = None,
        status: OrderStatus | None = None,
        search: str | None = None,
    ) -> list[tuple[Order, str]]:
        stmt = select(Order, Channel.code).join(Channel, col(Channel.id) == col(Order.channel_id))
        if channel is not None:
            stmt = stmt.where(col(Channel.code) == channel)
        if status is not None:
            stmt = stmt.where(col(Order.status) == status)
        if search is not None and search.strip():
            stmt = stmt.where(col(Order.external_order_id).ilike(f"%{search.strip()}%"))

        stmt = (
            stmt.order_by(col(Order.order_date).desc(), col(Order.id).desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self._session.execute(stmt)

        return [(order, str(channel_code)) for order, channel_code in result.all()]

    async def get_with_channel(self, order_id: int) -> tuple[Order, str] | None:
        result = await self._session.execute(
            select(Order, Channel.code)
            .join(Channel, col(Channel.id) == col(Order.channel_id))
            .where(col(Order.id) == order_id)
        )
        row = result.one_or_none()
        if row is None:
            return None
        return row[0], str(row[1])

    async def get_items(self, order_id: int) -> list[OrderItem]:
        result = await self._session.execute(
            select(OrderItem).where(col(OrderItem.order_id) == order_id).order_by(col(OrderItem.id))
        )
        return list(result.scalars().all())

    async def get_by_external_ids(
        self,
        channel_id: int,
        external_order_ids: Sequence[str],
    ) -> list[Order]:
        if not external_order_ids:
            return []
        result = await self._session.execute(
            select(Order).where(
                col(Order.channel_id) == channel_id,
                col(Order.external_order_id).in_(external_order_ids),
            )
        )
        return list(result.scalars().all())

    async def get_items_for_orders(self, order_ids: Sequence[int]) -> list[OrderItem]:
        if not order_ids:
            return []
        result = await self._session.execute(
            select(OrderItem).where(col(OrderItem.order_id).in_(order_ids))
        )
        return list(result.scalars().all())
