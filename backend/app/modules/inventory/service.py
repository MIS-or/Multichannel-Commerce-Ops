from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.alerts.models import AlertSeverity, AlertType
from app.modules.alerts.schemas import LowStockAlertRequest
from app.modules.alerts.service import AlertService
from app.modules.inventory.models import InventorySnapshot
from app.modules.inventory.repository import InventoryRepository
from app.modules.inventory.schemas import (
    DiscrepancyDirection,
    InventoryItemRead,
    InventoryVariance,
)
from app.modules.products.models import Product
from app.modules.products.service import ProductService
from app.shared.errors import BusinessRuleError, NotFoundError
from app.shared.time import utc_now

if TYPE_CHECKING:
    from app.modules.integrations import CanonicalInventoryItem


class InventoryService:
    def __init__(
        self,
        session: AsyncSession,
        product_service: ProductService,
        inventory_repository: InventoryRepository | None = None,
        alert_service: AlertService | None = None,
    ) -> None:
        self._session = session
        self._products = product_service
        self._inventory = inventory_repository or InventoryRepository(session)
        self._alerts = alert_service

    async def consume(self, product_id: int, quantity: int) -> Product:
        if quantity <= 0:
            raise ValueError("quantity must be positive")

        product = await self._inventory.consume_stock(product_id, quantity)
        if product is not None:
            if self._alerts is not None:
                await self._alerts.create_low_stock(
                    LowStockAlertRequest(
                        product_id=product.id,
                        sku=product.sku,
                        name=product.name,
                        current_stock=product.current_stock,
                        reorder_threshold=product.reorder_threshold,
                    )
                )
            return product

        existing = await self._products.get_by_id(product_id)
        if existing is None:
            raise NotFoundError(
                "PRODUCT_NOT_FOUND",
                f"Product id '{product_id}' does not exist",
                details={"product_id": product_id},
            )
        raise BusinessRuleError(
            "INSUFFICIENT_STOCK",
            f"Insufficient stock for SKU '{existing.sku}'",
            details={
                "sku": existing.sku,
                "requested": quantity,
                "available": existing.current_stock,
            },
        )

    async def list_inventory(self) -> list[InventoryItemRead]:
        products = await self._products.list_all()
        return [
            InventoryItemRead(
                product_id=p.id or 0,
                sku=p.sku,
                name=p.name,
                cost_price=p.cost_price,
                current_stock=p.current_stock,
                reorder_threshold=p.reorder_threshold,
                is_low_stock=p.current_stock <= p.reorder_threshold,
            )
            for p in products
        ]

    # --- Phase 3: Multi-Source Inventory Snapshot & Variance Engine ---

    async def record_canonical_snapshots(
        self,
        canonical_items: list[CanonicalInventoryItem],
        batch_id: str | None = None,
    ) -> list[InventorySnapshot]:
        """Ingest normalized inventory items and persist them as snapshots."""
        now = utc_now()
        snapshots = [
            InventorySnapshot(
                source_system=item.source_system,
                sku=item.sku,
                location_id=item.location_id,
                on_hand_qty=item.on_hand_qty,
                allocated_qty=item.allocated_qty,
                available_qty=item.available_qty,
                batch_id=batch_id,
                captured_at=item.captured_at or now,
                created_at=now,
            )
            for item in canonical_items
        ]
        return await self._inventory.save_snapshots(snapshots)

    async def calculate_variances(
        self,
        channel_code: str,
        *,
        erp_source: str = "odoo_erp",
        tolerance: Decimal = Decimal("0"),
    ) -> list[InventoryVariance]:
        """Compare channel reported stock with ERP physical source of truth."""
        erp_snaps = await self._inventory.get_latest_snapshots(erp_source)
        chan_snaps = await self._inventory.get_latest_snapshots(channel_code)

        all_skus = sorted(set(erp_snaps.keys()) | set(chan_snaps.keys()))
        variances: list[InventoryVariance] = []

        now = utc_now()
        for sku in all_skus:
            erp_item = erp_snaps.get(sku)
            chan_item = chan_snaps.get(sku)

            erp_avail = erp_item.available_qty if erp_item else Decimal("0.00")
            chan_avail = chan_item.available_qty if chan_item else Decimal("0.00")
            var = chan_avail - erp_avail

            has_discrepancy = abs(var) > tolerance
            if var > tolerance:
                direction = DiscrepancyDirection.OVER_ALLOCATED
            elif var < -tolerance:
                direction = DiscrepancyDirection.UNDER_ALLOCATED
            else:
                direction = DiscrepancyDirection.MATCHED

            variances.append(
                InventoryVariance(
                    sku=sku,
                    channel_code=channel_code,
                    erp_source=erp_source,
                    erp_available_qty=erp_avail,
                    channel_available_qty=chan_avail,
                    variance=var,
                    has_discrepancy=has_discrepancy,
                    direction=direction,
                    calculated_at=now,
                )
            )

        return variances

    async def detect_discrepancies(
        self,
        channel_code: str,
        *,
        erp_source: str = "odoo_erp",
        tolerance: Decimal = Decimal("0"),
        trigger_alerts: bool = True,
    ) -> list[InventoryVariance]:
        """Detect and return only SKUs exhibiting stock variance beyond tolerance.

        Optionally dispatches alerts for over-allocated SKUs (oversell danger).
        """
        all_vars = await self.calculate_variances(
            channel_code, erp_source=erp_source, tolerance=tolerance
        )
        discrepancies = [v for v in all_vars if v.has_discrepancy]

        if trigger_alerts and self._alerts is not None:
            for disc in discrepancies:
                if disc.direction == DiscrepancyDirection.OVER_ALLOCATED:
                    msg = (
                        f"OVERSELL RISK on {channel_code} for SKU '{disc.sku}': "
                        f"Channel stock ({disc.channel_available_qty}) exceeds ERP physical stock "
                        f"({disc.erp_available_qty}) by +{disc.variance}"
                    )
                    await self._alerts.create_once(
                        alert_type=AlertType.RECONCILIATION_MISMATCH,
                        severity=AlertSeverity.CRITICAL,
                        dedup_key=f"inv_oversell_{channel_code}_{disc.sku}",
                        message=msg,
                    )

        return discrepancies
