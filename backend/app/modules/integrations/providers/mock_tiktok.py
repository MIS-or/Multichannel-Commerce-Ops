from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any

from app.modules.integrations.contracts import (
    InventoryProvider,
    OrderProvider,
    RawInventoryBatch,
    RawOrderBatch,
    RawSettlementBatch,
    SettlementProvider,
)
from app.modules.integrations.providers.base import BaseMockConnector
from app.shared.time import utc_now


class MockTikTokConnector(BaseMockConnector, OrderProvider, InventoryProvider, SettlementProvider):
    """Mock connector simulating TikTok Shop Partner API.

    Emits raw TikTok Shop payloads using platform naming conventions:
    - Orders: `id`, `line_items` with `seller_sku`, string amounts in `payment`
    - Inventory: nested under `skus` list with `warehouse_id` & `quantity`
    - Settlements: `settlement_id`, `settlement_amount`, `orders` list with fees breakdown
    """

    def __init__(
        self,
        *,
        channel_code: str = "tiktok_shop_vn",
        platform_type: str = "marketplace",
        simulated_latency_ms: float = 5.0,
        simulated_failure: str | None = None,
        config: dict[str, Any] | None = None,
        custom_orders: list[dict[str, Any]] | None = None,
        custom_inventory: list[dict[str, Any]] | None = None,
        custom_settlements: list[dict[str, Any]] | None = None,
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
        self._custom_settlements = custom_settlements

    def _default_raw_orders(self) -> list[dict[str, Any]]:
        return [
            {
                "id": "576460752303423456",
                "status": "AWAITING_SHIPMENT",
                "create_time": 1774000000,
                "update_time": 1774002000,
                "buyer_email": "buyer_tiktok_01@example.com",
                "payment": {
                    "total_amount": "520000",
                    "currency": "VND",
                    "sub_total": "500000",
                    "shipping_fee": "20000",
                },
                "line_items": [
                    {
                        "id": "item_1001",
                        "product_id": "17293849182",
                        "sku_id": "28374619",
                        "seller_sku": "MCO-SKU-001",
                        "quantity": 2,
                        "sale_price": "250000",
                    }
                ],
            },
            {
                "id": "576460752303423457",
                "status": "COMPLETED",
                "create_time": 1774001000,
                "update_time": 1774045000,
                "buyer_email": "buyer_tiktok_02@example.com",
                "payment": {
                    "total_amount": "370000",
                    "currency": "VND",
                    "sub_total": "350000",
                    "shipping_fee": "20000",
                },
                "line_items": [
                    {
                        "id": "item_1002",
                        "product_id": "17293849183",
                        "sku_id": "28374620",
                        "seller_sku": "MCO-SKU-002",
                        "quantity": 1,
                        "sale_price": "350000",
                    }
                ],
            },
        ]

    def _default_raw_inventory(self) -> list[dict[str, Any]]:
        return [
            {
                "product_id": "17293849182",
                "skus": [
                    {
                        "id": "28374619",
                        "seller_sku": "MCO-SKU-001",
                        "inventory": [
                            {
                                "warehouse_id": "WH_TTS_01",
                                "quantity": 135,
                            }
                        ],
                    }
                ],
            },
            {
                "product_id": "17293849183",
                "skus": [
                    {
                        "id": "28374620",
                        "seller_sku": "MCO-SKU-002",
                        "inventory": [
                            {
                                "warehouse_id": "WH_TTS_01",
                                "quantity": 80,
                            }
                        ],
                    }
                ],
            },
        ]

    def _default_raw_settlements(self) -> list[dict[str, Any]]:
        return [
            {
                "settlement_id": "SETTLE-TT-20260320-001",
                "settlement_time": 1774060000,
                "settlement_amount": "450000",
                "currency": "VND",
                "orders": [
                    {
                        "order_id": "576460752303423456",
                        "gross_sales": "500000",
                        "platform_commission": "30000",
                        "transaction_fee": "10000",
                        "shipping_fee_subsidy": "0",
                        "refund_amount": "10000",
                        "net_settlement_amount": "450000",
                    }
                ],
            }
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
            filtered_items: list[dict[str, Any]] = []
            for item in raw_items:
                matched_skus = [s for s in item.get("skus", []) if s.get("seller_sku") in sku_set]
                if matched_skus:
                    filtered_items.append({**item, "skus": matched_skus})
            raw_items = filtered_items

        return RawInventoryBatch(
            source_system=self.channel_code,
            raw_items=raw_items[:limit],
            captured_at=utc_now(),
        )

    async def fetch_settlements(
        self,
        *,
        start_date: datetime,
        end_date: datetime,
    ) -> RawSettlementBatch:
        await self._simulate_network_overhead()
        raw_statements = (
            self._custom_settlements
            if self._custom_settlements is not None
            else self._default_raw_settlements()
        )
        total_payout = sum(
            (Decimal(str(s.get("settlement_amount", "0"))) for s in raw_statements),
            Decimal("0"),
        )
        return RawSettlementBatch(
            source_system=self.channel_code,
            raw_statements=raw_statements,
            period_start=start_date,
            period_end=end_date,
            total_payout_amount=total_payout,
            fetched_at=utc_now(),
        )
