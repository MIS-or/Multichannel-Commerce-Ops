from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

import pytest

from app.modules.integrations import (
    CanonicalOrderStatus,
    ProviderPayloadError,
    RawInventoryBatch,
    RawOrderBatch,
    RawSettlementBatch,
    ShopeeNormalizer,
)


def test_shopee_normalizer_orders() -> None:
    normalizer = ShopeeNormalizer()
    raw_batch = RawOrderBatch(
        channel_code="shopee_vn",
        raw_orders=[
            {
                "order_sn": "260320SHP0001",
                "order_status": "READY_TO_SHIP",
                "create_time": 1774000000,
                "buyer_username": "buyer_01",
                "total_amount": 500000.0,
                "currency": "VND",
                "item_list": [
                    {
                        "item_sku": "MCO-SKU-001",
                        "item_name": "Premium Coffee",
                        "model_quantity_purchased": 2,
                        "model_discounted_price": 250000.0,
                    }
                ],
            }
        ],
    )
    orders = normalizer.normalize_orders(raw_batch)
    assert len(orders) == 1
    ord1 = orders[0]
    assert ord1.channel_order_id == "260320SHP0001"
    assert ord1.order_status == CanonicalOrderStatus.PROCESSING
    assert ord1.total_amount == Decimal("500000.0")
    assert ord1.customer_name == "buyer_01"
    assert len(ord1.items) == 1
    assert ord1.items[0].sku == "MCO-SKU-001"
    assert ord1.items[0].quantity == 2


def test_shopee_normalizer_orders_missing_sku_raises() -> None:
    normalizer = ShopeeNormalizer()
    raw_batch = RawOrderBatch(
        channel_code="shopee_vn",
        raw_orders=[
            {
                "order_sn": "260320SHP0001",
                "order_status": "READY_TO_SHIP",
                "item_list": [{"model_quantity_purchased": 1}],
            }
        ],
    )
    with pytest.raises(ProviderPayloadError) as exc_info:
        normalizer.normalize_orders(raw_batch)
    assert "missing item_sku" in str(exc_info.value)


def test_shopee_normalizer_inventory() -> None:
    normalizer = ShopeeNormalizer()
    raw_batch = RawInventoryBatch(
        source_system="shopee_vn",
        raw_items=[
            {
                "item_sku": "MCO-SKU-001",
                "stock_info_v2": {
                    "summary_info": {
                        "total_reserved_stock": 10,
                        "total_available_stock": 140,
                    },
                    "seller_stock": [{"location_id": "VN_WH_1", "stock": 140}],
                },
            }
        ],
    )
    items = normalizer.normalize_inventory(raw_batch)
    assert len(items) == 1
    it = items[0]
    assert it.sku == "MCO-SKU-001"
    assert it.on_hand_qty == Decimal("150")
    assert it.allocated_qty == Decimal("10")
    assert it.available_qty == Decimal("140")
    assert it.location_id == "VN_WH_1"


def test_shopee_normalizer_settlements() -> None:
    normalizer = ShopeeNormalizer()
    now = datetime(2026, 3, 20, 12, 0, tzinfo=UTC)
    raw_batch = RawSettlementBatch(
        source_system="shopee_vn",
        period_start=now,
        period_end=now,
        raw_statements=[
            {
                "statement_id": "STMT-001",
                "payout_time": 1774050000,
                "escrow_amount": 455000.0,
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
        ],
    )
    stmts = normalizer.normalize_settlements(raw_batch)
    assert len(stmts) == 1
    s = stmts[0]
    assert s.statement_id == "STMT-001"
    assert s.total_gross_sales == Decimal("500000.0")
    assert s.total_net_payout == Decimal("455000.0")
    assert len(s.entries) == 1
    assert s.entries[0].channel_order_id == "260320SHP0001"
