from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from app.modules.integrations import (
    CanonicalOrderStatus,
    RawInventoryBatch,
    RawOrderBatch,
    RawSettlementBatch,
    TikTokNormalizer,
)


def test_tiktok_normalizer_orders() -> None:
    normalizer = TikTokNormalizer()
    raw_batch = RawOrderBatch(
        channel_code="tiktok_shop_vn",
        raw_orders=[
            {
                "id": "576460752303423456",
                "status": "AWAITING_SHIPMENT",
                "create_time": 1774000000,
                "buyer_email": "buyer@example.com",
                "payment": {
                    "total_amount": "520000",
                    "currency": "VND",
                },
                "line_items": [
                    {
                        "seller_sku": "MCO-SKU-001",
                        "quantity": 2,
                        "sale_price": "260000",
                    }
                ],
            }
        ],
    )
    orders = normalizer.normalize_orders(raw_batch)
    assert len(orders) == 1
    ord1 = orders[0]
    assert ord1.channel_order_id == "576460752303423456"
    assert ord1.order_status == CanonicalOrderStatus.PROCESSING
    assert ord1.total_amount == Decimal("520000")
    assert ord1.customer_email == "buyer@example.com"
    assert len(ord1.items) == 1
    assert ord1.items[0].sku == "MCO-SKU-001"
    assert ord1.items[0].quantity == 2


def test_tiktok_normalizer_inventory() -> None:
    normalizer = TikTokNormalizer()
    raw_batch = RawInventoryBatch(
        source_system="tiktok_shop_vn",
        raw_items=[
            {
                "product_id": "123",
                "skus": [
                    {
                        "seller_sku": "MCO-SKU-001",
                        "inventory": [{"warehouse_id": "WH_01", "quantity": 88}],
                    }
                ],
            }
        ],
    )
    items = normalizer.normalize_inventory(raw_batch)
    assert len(items) == 1
    it = items[0]
    assert it.sku == "MCO-SKU-001"
    assert it.available_qty == Decimal("88")
    assert it.location_id == "WH_01"


def test_tiktok_normalizer_settlements() -> None:
    normalizer = TikTokNormalizer()
    now = datetime(2026, 3, 20, 12, 0, tzinfo=UTC)
    raw_batch = RawSettlementBatch(
        source_system="tiktok_shop_vn",
        period_start=now,
        period_end=now,
        raw_statements=[
            {
                "settlement_id": "SETTLE-TT-001",
                "settlement_time": 1774060000,
                "settlement_amount": "450000",
                "orders": [
                    {
                        "order_id": "576460752303423456",
                        "gross_sales": "500000",
                        "platform_commission": "30000",
                        "transaction_fee": "10000",
                        "shipping_fee_subsidy": "10000",
                        "refund_amount": "20000",
                        "net_settlement_amount": "450000",
                    }
                ],
            }
        ],
    )
    stmts = normalizer.normalize_settlements(raw_batch)
    assert len(stmts) == 1
    s = stmts[0]
    assert s.statement_id == "SETTLE-TT-001"
    assert s.total_gross_sales == Decimal("500000")
    assert s.total_net_payout == Decimal("450000")
    assert len(s.entries) == 1
    assert s.entries[0].net_payout == Decimal("450000")
