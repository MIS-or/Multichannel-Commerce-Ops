from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.modules.integrations import (
    CanonicalInventoryItem,
    CanonicalOrder,
    CanonicalOrderItem,
    CanonicalOrderStatus,
    CanonicalSettlementEntry,
)


def test_canonical_order_item_creation_and_validation() -> None:
    item = CanonicalOrderItem(
        sku="SKU-001",
        product_name="Test Product",
        quantity=2,
        unit_price=Decimal("150000.00"),
        subtotal=Decimal("300000.00"),
    )
    assert item.sku == "SKU-001"
    assert item.quantity == 2
    assert item.unit_price == Decimal("150000.00")
    assert item.subtotal == Decimal("300000.00")

    # Quantity cannot be zero or negative
    with pytest.raises(ValidationError):
        CanonicalOrderItem(
            sku="SKU-001",
            quantity=0,
            unit_price=Decimal("100"),
            subtotal=Decimal("0"),
        )


def test_canonical_order_creation() -> None:
    now = datetime(2026, 3, 20, 10, 0, 0, tzinfo=UTC)
    order = CanonicalOrder(
        channel_code="shopee",
        channel_order_id="ORD-001",
        order_status=CanonicalOrderStatus.PROCESSING,
        total_amount=Decimal("300000.00"),
        placed_at=now,
        items=[
            CanonicalOrderItem(
                sku="SKU-001",
                quantity=2,
                unit_price=Decimal("150000.00"),
                subtotal=Decimal("300000.00"),
            )
        ],
    )
    assert order.channel_code == "shopee"
    assert order.channel_order_id == "ORD-001"
    assert order.order_status == CanonicalOrderStatus.PROCESSING
    assert len(order.items) == 1

    # Items cannot be empty
    with pytest.raises(ValidationError):
        CanonicalOrder(
            channel_code="shopee",
            channel_order_id="ORD-002",
            order_status=CanonicalOrderStatus.PROCESSING,
            total_amount=Decimal("100"),
            placed_at=now,
            items=[],
        )


def test_canonical_inventory_item() -> None:
    inv = CanonicalInventoryItem(
        sku="SKU-001",
        source_system="odoo_erp",
        location_id="WH/Stock",
        on_hand_qty=Decimal("100"),
        allocated_qty=Decimal("20"),
        available_qty=Decimal("80"),
    )
    assert inv.sku == "SKU-001"
    assert inv.available_qty == Decimal("80")

    # Negative on_hand is rejected
    with pytest.raises(ValidationError):
        CanonicalInventoryItem(
            sku="SKU-001",
            source_system="odoo_erp",
            on_hand_qty=Decimal("-5"),
            available_qty=Decimal("0"),
        )


def test_canonical_settlement_entry_formula_validation() -> None:
    # gross: 500,000; fees: 25,000 + 10,000 + 10,000 = 45,000; net: 455,000 -> Valid
    entry = CanonicalSettlementEntry(
        channel_order_id="ORD-001",
        gross_sales=Decimal("500000.00"),
        commission_fee=Decimal("25000.00"),
        service_fee=Decimal("10000.00"),
        transaction_fee=Decimal("10000.00"),
        net_payout=Decimal("455000.00"),
    )
    assert entry.net_payout == Decimal("455000.00")

    # Mismatched net payout raises validation error
    with pytest.raises(ValidationError) as exc_info:
        CanonicalSettlementEntry(
            channel_order_id="ORD-001",
            gross_sales=Decimal("500000.00"),
            commission_fee=Decimal("25000.00"),
            service_fee=Decimal("10000.00"),
            transaction_fee=Decimal("10000.00"),
            net_payout=Decimal("480000.00"),  # Incorrect net payout!
        )
    assert "Net payout" in str(exc_info.value)
