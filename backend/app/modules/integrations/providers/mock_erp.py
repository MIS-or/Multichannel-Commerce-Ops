from __future__ import annotations

from datetime import datetime
from typing import Any

from app.modules.integrations.contracts import (
    InventoryProvider,
    OrderProvider,
    RawInventoryBatch,
    RawOrderBatch,
)
from app.modules.integrations.providers.base import BaseMockConnector
from app.shared.time import utc_now


class MockErpConnector(BaseMockConnector, InventoryProvider, OrderProvider):
    """Mock connector simulating an ERP system (Odoo-style JSON-RPC / REST interface).

    Emits raw Odoo payloads using internal naming conventions:
    - Products: `default_code`, `qty_available`, `virtual_available`, `incoming_qty`, `outgoing_qty`
    - Orders: `name` (SO number), `partner_id` [id, name], `order_line` with product tuple
    """

    def __init__(
        self,
        *,
        channel_code: str = "odoo_erp",
        platform_type: str = "erp",
        simulated_latency_ms: float = 5.0,
        simulated_failure: str | None = None,
        config: dict[str, Any] | None = None,
        custom_orders: list[dict[str, Any]] | None = None,
        custom_inventory: list[dict[str, Any]] | None = None,
    ) -> None:
        super().__init__(
            channel_code=channel_code,
            platform_type=platform_type,
            simulated_latency_ms=simulated_latency_ms,
            simulated_failure=simulated_failure,
            config=config,
        )
        self._custom_orders = custom_orders
        self._custom_inventory = custom_inventory

    def _default_raw_orders(self) -> list[dict[str, Any]]:
        return [
            {
                "id": 1001,
                "name": "SO-2026-0001",
                "state": "sale",
                "date_order": "2026-03-20T09:15:00Z",
                "partner_id": [101, "Nguyen Van A"],
                "amount_total": 450000.0,
                "currency_id": [1, "VND"],
                "order_line": [
                    {
                        "id": 5001,
                        "product_id": [201, "[MCO-SKU-001] Premium Coffee Beans 500g"],
                        "product_uom_qty": 2.0,
                        "price_unit": 225000.0,
                        "price_subtotal": 450000.0,
                    }
                ],
            },
            {
                "id": 1002,
                "name": "SO-2026-0002",
                "state": "done",
                "date_order": "2026-03-20T10:30:00Z",
                "partner_id": [102, "Tran Thi B"],
                "amount_total": 350000.0,
                "currency_id": [1, "VND"],
                "order_line": [
                    {
                        "id": 5002,
                        "product_id": [202, "[MCO-SKU-002] Stainless Steel Drip Filter"],
                        "product_uom_qty": 1.0,
                        "price_unit": 350000.0,
                        "price_subtotal": 350000.0,
                    }
                ],
            },
        ]

    def _default_raw_inventory(self) -> list[dict[str, Any]]:
        return [
            {
                "id": 201,
                "default_code": "MCO-SKU-001",
                "name": "Premium Coffee Beans 500g",
                "qty_available": 150.0,
                "virtual_available": 120.0,
                "incoming_qty": 20.0,
                "outgoing_qty": 30.0,
                "location_id": [5, "WH/Stock"],
                "write_date": "2026-03-20T08:00:00Z",
            },
            {
                "id": 202,
                "default_code": "MCO-SKU-002",
                "name": "Stainless Steel Drip Filter",
                "qty_available": 85.0,
                "virtual_available": 80.0,
                "incoming_qty": 0.0,
                "outgoing_qty": 5.0,
                "location_id": [5, "WH/Stock"],
                "write_date": "2026-03-20T08:00:00Z",
            },
            {
                "id": 203,
                "default_code": "MCO-SKU-003",
                "name": "Ceramic Mug Set",
                "qty_available": 40.0,
                "virtual_available": 40.0,
                "incoming_qty": 10.0,
                "outgoing_qty": 0.0,
                "location_id": [5, "WH/Stock"],
                "write_date": "2026-03-20T08:00:00Z",
            },
        ]

    async def fetch_orders(
        self,
        *,
        cursor: str | None = None,
        updated_since: datetime | None = None,
        limit: int = 50,
    ) -> RawOrderBatch:
        await self._simulate_network_overhead()
        raw_list = (
            self._custom_orders if self._custom_orders is not None else self._default_raw_orders()
        )
        return RawOrderBatch(
            channel_code=self.channel_code,
            raw_orders=raw_list[:limit],
            total_count=len(raw_list),
            fetched_at=utc_now(),
        )

    async def fetch_inventory(
        self,
        *,
        skus: list[str] | None = None,
        cursor: str | None = None,
        limit: int = 100,
    ) -> RawInventoryBatch:
        await self._simulate_network_overhead()
        raw_items = (
            self._custom_inventory
            if self._custom_inventory is not None
            else self._default_raw_inventory()
        )
        if skus is not None:
            sku_set = set(skus)
            raw_items = [item for item in raw_items if item.get("default_code") in sku_set]

        return RawInventoryBatch(
            source_system=self.channel_code,
            raw_items=raw_items[:limit],
            captured_at=utc_now(),
        )
