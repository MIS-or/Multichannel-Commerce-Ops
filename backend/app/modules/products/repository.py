from collections.abc import Sequence

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import col, select

from app.modules.products.models import Product


class ProductRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_sku(self, sku: str) -> Product | None:
        result = await self._session.execute(select(Product).where(Product.sku == sku))
        return result.scalar_one_or_none()

    async def get_by_id(self, product_id: int) -> Product | None:
        return await self._session.get(Product, product_id)

    async def get_by_ids(self, product_ids: Sequence[int]) -> list[Product]:
        if not product_ids:
            return []
        result = await self._session.execute(
            select(Product).where(col(Product.id).in_(product_ids))
        )
        return list(result.scalars().all())

    async def list_all(self) -> list[Product]:
        result = await self._session.execute(select(Product).order_by(Product.sku))
        return list(result.scalars().all())
