from __future__ import annotations

from decimal import Decimal

import pytest

from app.modules.integrations import (
    CanonicalOrderStatus,
    ErpNormalizer,
    ProviderPayloadError,
    RawInventoryBatch,
    RawOrderBatch,
)


def test_erp_normalizer_orders() -> None:
    normalizer = ErpNormalizer()
    raw_batch = RawOrderBatch(
        channel_code="odoo_erp",
        raw_orders=[
            {
                "id": 1001,
                "name": "SO-2026-0001",
                "state": "sale",
                "date_order": "2026-03-20T09:15:00+00:00",
                "partner_id": [101, "Nguyen Van A"],
                "amount_total": 450000.0,
                "currency_id": [1, "VND"],
                "order_line": [
                    {
                        "product_id": [201, "[MCO-SKU-001] Premium Coffee Beans 500g"],
                        "product_uom_qty": 2.0,
                        "price_unit": 225000.0,
                    }
                ],
            }
        ],
    )
    orders = normalizer.normalize_orders(raw_batch)
    assert len(orders) == 1
    ord1 = orders[0]
    assert ord1.channel_order_id == "SO-2026-0001"
    assert ord1.order_status == CanonicalOrderStatus.PROCESSING
    assert ord1.customer_name == "Nguyen Van A"
    assert ord1.total_amount == Decimal("450000.0")
    assert len(ord1.items) == 1
    assert ord1.items[0].sku == "MCO-SKU-001"
    assert ord1.items[0].product_name == "Premium Coffee Beans 500g"
    assert ord1.items[0].quantity == 2


def test_erp_normalizer_inventory() -> None:
    normalizer = ErpNormalizer()
    raw_batch = RawInventoryBatch(
        source_system="odoo_erp",
        raw_items=[
            {
                "default_code": "MCO-SKU-001",
                "name": "Premium Coffee",
                "qty_available": 150.0,
                "outgoing_qty": 30.0,
                "virtual_available": 120.0,
                "location_id": [5, "WH/Stock"],
            }
        ],
    )
    items = normalizer.normalize_inventory(raw_batch)
    assert len(items) == 1
    it = items[0]
    assert it.sku == "MCO-SKU-001"
    assert it.on_hand_qty == Decimal("150.0")
    assert it.allocated_qty == Decimal("30.0")
    assert it.available_qty == Decimal("120.0")
    assert it.location_id == "WH/Stock"


def test_erp_normalizer_missing_default_code_raises() -> None:
    normalizer = ErpNormalizer()
    raw_batch = RawInventoryBatch(
        source_system="odoo_erp",
        raw_items=[{"qty_available": 50}],
    )
    with pytest.raises(ProviderPayloadError) as exc_info:
        normalizer.normalize_inventory(raw_batch)
    assert "missing default_code" in str(exc_info.value)
