from collections.abc import Sequence

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.modules.products.models import Product
from app.modules.products.repository import ProductRepository
from app.shared.errors import NotFoundError


class ProductService:
    def __init__(self, repository: ProductRepository) -> None:
        self._repository = repository

    async def get_by_sku(self, sku: str) -> Product:
        product = await self._repository.get_by_sku(sku)
        if product is None:
            raise NotFoundError(
                "PRODUCT_NOT_FOUND",
                f"Product SKU '{sku}' does not exist",
                details={"sku": sku},
            )
        return product

    async def get_by_id(self, product_id: int) -> Product | None:
        return await self._repository.get_by_id(product_id)

    async def get_by_ids(self, product_ids: Sequence[int]) -> list[Product]:
        return await self._repository.get_by_ids(product_ids)

    async def list_all(self) -> list[Product]:
        return await self._repository.list_all()


def get_product_service(session: AsyncSession = Depends(get_session)) -> ProductService:
    return ProductService(ProductRepository(session))
