from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

import pytest

from app.modules.integrations import (
    ConnectionStatus,
    MockErpConnector,
    MockShopeeConnector,
    MockTikTokConnector,
    ProviderAuthenticationError,
    ProviderConnectionError,
    ProviderPayloadError,
    ProviderRateLimitError,
)


@pytest.mark.asyncio
async def test_mock_erp_connector_success() -> None:
    erp = MockErpConnector(simulated_latency_ms=0.0)

    # 1. Health check
    health = await erp.test_connection()
    assert health.status == ConnectionStatus.HEALTHY
    assert "odoo_erp" in health.message

    # 2. Orders
    order_batch = await erp.fetch_orders(limit=10)
    assert order_batch.channel_code == "odoo_erp"
    assert len(order_batch.raw_orders) >= 2
    first_order = order_batch.raw_orders[0]
    assert first_order["name"] == "SO-2026-0001"
    assert "order_line" in first_order
    assert len(first_order["order_line"]) > 0

    # 3. Inventory
    inv_batch = await erp.fetch_inventory()
    assert inv_batch.source_system == "odoo_erp"
    assert len(inv_batch.raw_items) >= 3
    first_item = inv_batch.raw_items[0]
    assert first_item["default_code"] == "MCO-SKU-001"
    assert first_item["qty_available"] == 150.0

    # 4. Inventory with SKU filter
    filtered_batch = await erp.fetch_inventory(skus=["MCO-SKU-002"])
    assert len(filtered_batch.raw_items) == 1
    assert filtered_batch.raw_items[0]["default_code"] == "MCO-SKU-002"


@pytest.mark.asyncio
async def test_mock_erp_connector_fault_injection() -> None:
    # Timeout
    timeout_erp = MockErpConnector(
        simulated_latency_ms=0.0,
        simulated_failure="connection_timeout",
    )
    with pytest.raises(ProviderConnectionError):
        await timeout_erp.fetch_orders()
    health = await timeout_erp.test_connection()
    assert health.status == ConnectionStatus.UNHEALTHY

    # Auth
    auth_erp = MockErpConnector(
        simulated_latency_ms=0.0,
        simulated_failure="auth_failed",
    )
    with pytest.raises(ProviderAuthenticationError):
        await auth_erp.fetch_inventory()

    # Rate limit
    rate_erp = MockErpConnector(
        simulated_latency_ms=0.0,
        simulated_failure="rate_limit",
    )
    with pytest.raises(ProviderRateLimitError) as exc_info:
        await rate_erp.fetch_orders()
    assert exc_info.value.retry_after_seconds == 30

    # Payload corrupt
    corrupt_erp = MockErpConnector(
        simulated_latency_ms=0.0,
        simulated_failure="payload_corrupt",
    )
    with pytest.raises(ProviderPayloadError):
        await corrupt_erp.fetch_orders()


@pytest.mark.asyncio
async def test_mock_shopee_connector_success() -> None:
    shopee = MockShopeeConnector(simulated_latency_ms=0.0)

    # 1. Health check
    health = await shopee.test_connection()
    assert health.status == ConnectionStatus.HEALTHY
    assert "shopee_vn" in health.message

    # 2. Orders
    order_batch = await shopee.fetch_orders(limit=10)
    assert order_batch.channel_code == "shopee_vn"
    assert len(order_batch.raw_orders) >= 2
    first_order = order_batch.raw_orders[0]
    assert first_order["order_sn"] == "260320SHP0001"
    assert "item_list" in first_order
    assert first_order["item_list"][0]["item_sku"] == "MCO-SKU-001"

    # 3. Inventory
    inv_batch = await shopee.fetch_inventory()
    assert inv_batch.source_system == "shopee_vn"
    assert len(inv_batch.raw_items) >= 2
    first_inv = inv_batch.raw_items[0]
    assert first_inv["item_sku"] == "MCO-SKU-001"
    assert "stock_info_v2" in first_inv
    assert first_inv["stock_info_v2"]["summary_info"]["total_available_stock"] == 140

    # 4. Inventory SKU filter
    filtered_batch = await shopee.fetch_inventory(skus=["MCO-SKU-002"])
    assert len(filtered_batch.raw_items) == 1
    assert filtered_batch.raw_items[0]["item_sku"] == "MCO-SKU-002"

    # 5. Settlements
    start = datetime(2026, 3, 1, tzinfo=UTC)
    end = datetime(2026, 3, 31, tzinfo=UTC)
    settlement_batch = await shopee.fetch_settlements(start_date=start, end_date=end)
    assert settlement_batch.source_system == "shopee_vn"
    assert len(settlement_batch.raw_statements) >= 1
    stmt = settlement_batch.raw_statements[0]
    assert stmt["statement_id"] == "STMT-SHP-20260320-001"
    assert settlement_batch.total_payout_amount == Decimal("455000.0")


@pytest.mark.asyncio
async def test_mock_tiktok_connector_success() -> None:
    tiktok = MockTikTokConnector(simulated_latency_ms=0.0)

    # 1. Health check
    health = await tiktok.test_connection()
    assert health.status == ConnectionStatus.HEALTHY
    assert "tiktok_shop_vn" in health.message

    # 2. Orders
    order_batch = await tiktok.fetch_orders(limit=10)
    assert order_batch.channel_code == "tiktok_shop_vn"
    assert len(order_batch.raw_orders) >= 2
    first_order = order_batch.raw_orders[0]
    assert first_order["id"] == "576460752303423456"
    assert "line_items" in first_order
    assert first_order["line_items"][0]["seller_sku"] == "MCO-SKU-001"

    # 3. Inventory
    inv_batch = await tiktok.fetch_inventory()
    assert inv_batch.source_system == "tiktok_shop_vn"
    assert len(inv_batch.raw_items) >= 2
    first_item = inv_batch.raw_items[0]
    assert "skus" in first_item
    assert first_item["skus"][0]["seller_sku"] == "MCO-SKU-001"

    # 4. Inventory SKU filter
    filtered = await tiktok.fetch_inventory(skus=["MCO-SKU-002"])
    assert len(filtered.raw_items) == 1
    assert filtered.raw_items[0]["skus"][0]["seller_sku"] == "MCO-SKU-002"

    # 5. Settlements
    start = datetime(2026, 3, 1, tzinfo=UTC)
    end = datetime(2026, 3, 31, tzinfo=UTC)
    settlement_batch = await tiktok.fetch_settlements(start_date=start, end_date=end)
    assert settlement_batch.source_system == "tiktok_shop_vn"
    assert len(settlement_batch.raw_statements) >= 1
    assert settlement_batch.total_payout_amount == Decimal("450000")
