from __future__ import annotations

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import col

from app.modules.inventory.models import InventorySnapshot
from app.modules.products.models import Product
from app.shared.time import utc_now


class InventoryRepository:
    """Encapsulates inventory storage operations and multi-source snapshots.

    ERP is the source of truth for physical stock.
    Snapshots track periodic stock balances reported by external channels and ERP.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def consume_stock(self, product_id: int, quantity: int) -> Product | None:
        """Atomically decrement stock if and only if sufficient stock exists."""
        statement = (
            update(Product)
            .where(col(Product.id) == product_id, col(Product.current_stock) >= quantity)
            .values(
                current_stock=Product.current_stock - quantity,
                updated_at=utc_now(),
            )
            .returning(Product)
        )
        result = await self._session.execute(statement)
        return result.scalar_one_or_none()

    async def save_snapshots(self, snapshots: list[InventorySnapshot]) -> list[InventorySnapshot]:
        """Persist a batch of inventory snapshot records."""
        for snap in snapshots:
            self._session.add(snap)
        await self._session.flush()
        return snapshots

    async def get_latest_snapshots(
        self, source_system: str, skus: list[str] | None = None
    ) -> dict[str, InventorySnapshot]:
        """Fetch the latest snapshot for each SKU from the specified source system."""
        statement = (
            select(InventorySnapshot)
            .where(col(InventorySnapshot.source_system) == source_system)
            .order_by(col(InventorySnapshot.captured_at).desc(), col(InventorySnapshot.id).desc())
        )
        if skus is not None:
            statement = statement.where(col(InventorySnapshot.sku).in_(skus))

        result = await self._session.execute(statement)
        snapshots = result.scalars().all()

        latest_by_sku: dict[str, InventorySnapshot] = {}
        for snap in snapshots:
            if snap.sku not in latest_by_sku:
                latest_by_sku[snap.sku] = snap
        return latest_by_sku
