from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

import pytest

from app.modules.integrations import (
    IntegrationError,
    MockErpConnector,
    MockShopeeConnector,
    MockTikTokConnector,
    NormalizationPipeline,
    ProviderPayloadError,
    RawInventoryBatch,
    RawOrderBatch,
)


@pytest.mark.asyncio
async def test_pipeline_normalizes_mock_orders_across_all_platforms() -> None:
    erp = MockErpConnector(simulated_latency_ms=0.0)
    shopee = MockShopeeConnector(simulated_latency_ms=0.0)
    tiktok = MockTikTokConnector(simulated_latency_ms=0.0)

    # 1. ERP Orders
    erp_batch = await erp.fetch_orders()
    canonical_erp_orders = NormalizationPipeline.process_orders(erp_batch)
    assert len(canonical_erp_orders) >= 2
    assert canonical_erp_orders[0].channel_order_id == "SO-2026-0001"
    assert canonical_erp_orders[0].items[0].sku == "MCO-SKU-001"

    # 2. Shopee Orders
    shopee_batch = await shopee.fetch_orders()
    canonical_shopee_orders = NormalizationPipeline.process_orders(shopee_batch)
    assert len(canonical_shopee_orders) >= 2
    assert canonical_shopee_orders[0].channel_order_id == "260320SHP0001"
    assert canonical_shopee_orders[0].items[0].sku == "MCO-SKU-001"

    # 3. TikTok Orders
    tiktok_batch = await tiktok.fetch_orders()
    canonical_tiktok_orders = NormalizationPipeline.process_orders(tiktok_batch)
    assert len(canonical_tiktok_orders) >= 2
    assert canonical_tiktok_orders[0].channel_order_id == "576460752303423456"
    assert canonical_tiktok_orders[0].items[0].sku == "MCO-SKU-001"


@pytest.mark.asyncio
async def test_pipeline_normalizes_mock_inventory_across_all_platforms() -> None:
    erp = MockErpConnector(simulated_latency_ms=0.0)
    shopee = MockShopeeConnector(simulated_latency_ms=0.0)
    tiktok = MockTikTokConnector(simulated_latency_ms=0.0)

    # ERP
    erp_batch = await erp.fetch_inventory()
    erp_items = NormalizationPipeline.process_inventory(erp_batch)
    assert len(erp_items) >= 3
    assert erp_items[0].sku == "MCO-SKU-001"
    assert erp_items[0].available_qty == Decimal("120.0")

    # Shopee
    shopee_batch = await shopee.fetch_inventory()
    shopee_items = NormalizationPipeline.process_inventory(shopee_batch)
    assert len(shopee_items) >= 2
    assert shopee_items[0].sku == "MCO-SKU-001"
    assert shopee_items[0].available_qty == Decimal("140")

    # TikTok
    tiktok_batch = await tiktok.fetch_inventory()
    tiktok_items = NormalizationPipeline.process_inventory(tiktok_batch)
    assert len(tiktok_items) >= 2
    assert tiktok_items[0].sku == "MCO-SKU-001"
    assert tiktok_items[0].available_qty == Decimal("135")


@pytest.mark.asyncio
async def test_pipeline_normalizes_mock_settlements() -> None:
    shopee = MockShopeeConnector(simulated_latency_ms=0.0)
    tiktok = MockTikTokConnector(simulated_latency_ms=0.0)
    start = datetime(2026, 3, 1, tzinfo=UTC)
    end = datetime(2026, 3, 31, tzinfo=UTC)

    # Shopee
    shopee_batch = await shopee.fetch_settlements(start_date=start, end_date=end)
    shopee_stmts = NormalizationPipeline.process_settlements(shopee_batch)
    assert len(shopee_stmts) == 1
    assert shopee_stmts[0].total_net_payout == Decimal("455000.0")

    # TikTok
    tiktok_batch = await tiktok.fetch_settlements(start_date=start, end_date=end)
    tiktok_stmts = NormalizationPipeline.process_settlements(tiktok_batch)
    assert len(tiktok_stmts) == 1
    assert tiktok_stmts[0].total_net_payout == Decimal("450000")


def test_pipeline_unknown_channel_raises() -> None:
    raw_batch = RawOrderBatch(channel_code="unknown_channel_xyz", raw_orders=[])
    with pytest.raises(IntegrationError) as exc_info:
        NormalizationPipeline.process_orders(raw_batch)
    assert exc_info.value.code == "NORMALIZER_NOT_FOUND"


def test_pipeline_rejects_negative_stock() -> None:
    raw_batch = RawInventoryBatch(
        source_system="odoo_erp",
        raw_items=[
            {
                "default_code": "MCO-SKU-001",
                "qty_available": -10.0,
            }
        ],
    )
    with pytest.raises(ProviderPayloadError) as exc_info:
        NormalizationPipeline.process_inventory(raw_batch)
    assert "greater than or equal to 0" in str(exc_info.value)
