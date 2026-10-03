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


class MockShopeeConnector(BaseMockConnector, OrderProvider, InventoryProvider, SettlementProvider):
    """Mock connector simulating Shopee Open API v2.

    Emits raw Shopee payloads using platform naming conventions:
    - Orders: `order_sn`, `item_list` with `item_sku`, `model_quantity_purchased`
    - Inventory: `item_sku`, `stock_info_v2` with `total_available_stock` & `total_reserved_stock`
    - Settlements: `statement_id`, `order_income_list` with fees breakdown & `escrow_amount`
    """

    def __init__(
        self,
        *,
        channel_code: str = "shopee_vn",
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
                "order_sn": "260320SHP0001",
                "order_status": "READY_TO_SHIP",
                "create_time": 1774000000,
                "update_time": 1774001200,
                "buyer_username": "shopee_user_alpha",
                "total_amount": 500000.0,
                "currency": "VND",
                "item_list": [
                    {
                        "item_id": 9901,
                        "model_id": 8801,
                        "item_sku": "MCO-SKU-001",
                        "model_quantity_purchased": 2,
                        "model_discounted_price": 250000.0,
                    }
                ],
            },
            {
                "order_sn": "260320SHP0002",
                "order_status": "COMPLETED",
                "create_time": 1774003600,
                "update_time": 1774040000,
                "buyer_username": "shopee_user_beta",
                "total_amount": 380000.0,
                "currency": "VND",
                "item_list": [
                    {
                        "item_id": 9902,
                        "model_id": 8802,
                        "item_sku": "MCO-SKU-002",
                        "model_quantity_purchased": 1,
                        "model_discounted_price": 380000.0,
                    }
                ],
            },
        ]

    def _default_raw_inventory(self) -> list[dict[str, Any]]:
        return [
            {
                "item_id": 9901,
                "model_id": 8801,
                "item_sku": "MCO-SKU-001",
                "stock_info_v2": {
                    "summary_info": {
                        "total_reserved_stock": 10,
                        "total_available_stock": 140,
                    },
                    "seller_stock": [
                        {
                            "location_id": "VN_WH_NORTH",
                            "stock": 140,
                        }
                    ],
                },
            },
            {
                "item_id": 9902,
                "model_id": 8802,
                "item_sku": "MCO-SKU-002",
                "stock_info_v2": {
                    "summary_info": {
                        "total_reserved_stock": 2,
                        "total_available_stock": 83,
                    },
                    "seller_stock": [
                        {
                            "location_id": "VN_WH_NORTH",
                            "stock": 83,
                        }
                    ],
                },
            },
        ]

    def _default_raw_settlements(self) -> list[dict[str, Any]]:
        return [
            {
                "statement_id": "STMT-SHP-20260320-001",
                "payout_time": 1774050000,
                "escrow_amount": 455000.0,
                "currency": "VND",
                "order_income_list": [
                    {
                        "order_sn": "260320SHP0001",
                        "buyer_total_amount": 500000.0,
                        "commission_fee": 25000.0,
                        "service_fee": 10000.0,
                        "transaction_fee": 10000.0,
                        "seller_voucher_rebate": 0.0,
                        "seller_shipping_discount": 0.0,
                        "escrow_amount": 455000.0,
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
            raw_items = [item for item in raw_items if item.get("item_sku") in sku_set]

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
            (Decimal(str(s.get("escrow_amount", 0))) for s in raw_statements),
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
