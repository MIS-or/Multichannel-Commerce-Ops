from __future__ import annotations

import re
from datetime import datetime
from decimal import Decimal

from app.modules.integrations.canonical.models import (
    CanonicalInventoryItem,
    CanonicalOrder,
    CanonicalOrderItem,
    CanonicalOrderStatus,
    CanonicalSettlementStatement,
)
from app.modules.integrations.contracts import (
    RawInventoryBatch,
    RawOrderBatch,
    RawSettlementBatch,
)
from app.modules.integrations.errors import ProviderPayloadError
from app.modules.integrations.normalizers.base import BaseNormalizer
from app.shared.time import utc_now

STATUS_MAP: dict[str, CanonicalOrderStatus] = {
    "draft": CanonicalOrderStatus.PENDING,
    "sent": CanonicalOrderStatus.PENDING,
    "sale": CanonicalOrderStatus.PROCESSING,
    "done": CanonicalOrderStatus.DELIVERED,
    "cancel": CanonicalOrderStatus.CANCELLED,
}

SKU_REGEX = re.compile(r"^\[(.*?)\]\s*(.*)$")


def parse_odoo_product_tuple(prod_data: list[object] | tuple[object, ...]) -> tuple[str, str]:
    """Parse Odoo product field.

    Example: [201, '[MCO-SKU-001] Coffee Beans'] -> ('MCO-SKU-001', 'Coffee Beans').
    """
    if len(prod_data) >= 2 and isinstance(prod_data[1], str):
        display_name = prod_data[1]
        match = SKU_REGEX.match(display_name)
        if match:
            return match.group(1), match.group(2)
        return display_name, display_name
    return "UNKNOWN_SKU", "Unknown Product"


class ErpNormalizer(BaseNormalizer):
    """Normalizer for ERP system (Odoo-style JSON-RPC / REST) payloads."""

    def normalize_orders(self, raw_batch: RawOrderBatch) -> list[CanonicalOrder]:
        orders: list[CanonicalOrder] = []
        for raw in raw_batch.raw_orders:
            order_name = raw.get("name") or str(raw.get("id"))
            if not order_name:
                raise ProviderPayloadError("odoo_erp", "Missing order name or id", raw_payload=raw)

            raw_state = str(raw.get("state", "")).lower()
            status = STATUS_MAP.get(raw_state, CanonicalOrderStatus.PROCESSING)

            raw_lines = raw.get("order_line", [])
            if not raw_lines:
                raise ProviderPayloadError(
                    "odoo_erp", f"Order {order_name} has no order_line", raw_payload=raw
                )

            items: list[CanonicalOrderItem] = []
            for line in raw_lines:
                prod = line.get("product_id")
                if not prod or not isinstance(prod, (list, tuple)):
                    raise ProviderPayloadError(
                        "odoo_erp",
                        f"Order {order_name} line missing product_id tuple",
                        raw_payload=line,
                    )
                sku, prod_name = parse_odoo_product_tuple(prod)
                qty = int(line.get("product_uom_qty", 1))
                price = Decimal(str(line.get("price_unit", 0)))
                subtotal = qty * price
                items.append(
                    CanonicalOrderItem(
                        sku=sku,
                        product_name=prod_name,
                        quantity=qty,
                        unit_price=price,
                        discount_amount=Decimal("0.00"),
                        subtotal=subtotal,
                    )
                )

            partner = raw.get("partner_id")
            customer_name = (
                partner[1] if isinstance(partner, (list, tuple)) and len(partner) > 1 else None
            )

            currency_id = raw.get("currency_id")
            currency = (
                str(currency_id[1])
                if isinstance(currency_id, (list, tuple)) and len(currency_id) > 1
                else "VND"
            )

            date_str = raw.get("date_order")
            placed_at = datetime.fromisoformat(date_str) if isinstance(date_str, str) else utc_now()

            orders.append(
                CanonicalOrder(
                    channel_code=raw_batch.channel_code,
                    channel_order_id=order_name,
                    order_status=status,
                    currency=currency,
                    total_amount=Decimal(str(raw.get("amount_total", 0))),
                    customer_name=customer_name,
                    placed_at=placed_at,
                    updated_at=utc_now(),
                    items=items,
                )
            )
        return orders

    def normalize_inventory(self, raw_batch: RawInventoryBatch) -> list[CanonicalInventoryItem]:
        items: list[CanonicalInventoryItem] = []
        for raw in raw_batch.raw_items:
            sku = raw.get("default_code")
            if not sku:
                raise ProviderPayloadError(
                    "odoo_erp",
                    "Inventory item missing default_code",
                    raw_payload=raw,
                )

            on_hand = Decimal(str(raw.get("qty_available", 0)))
            if on_hand < 0:
                raise ProviderPayloadError(
                    "odoo_erp",
                    (
                        f"SKU '{sku}' reports negative on_hand stock ({on_hand}), "
                        "must be greater than or equal to 0"
                    ),
                    raw_payload=raw,
                )
            allocated = Decimal(str(raw.get("outgoing_qty", 0)))
            available = Decimal(str(raw.get("virtual_available", on_hand - allocated)))

            loc = raw.get("location_id")
            location_id = loc[1] if isinstance(loc, (list, tuple)) and len(loc) > 1 else None

            items.append(
                CanonicalInventoryItem(
                    sku=sku,
                    source_system=raw_batch.source_system,
                    location_id=str(location_id) if location_id else None,
                    on_hand_qty=on_hand,
                    allocated_qty=allocated,
                    available_qty=available,
                    captured_at=raw_batch.captured_at,
                )
            )
        return items

    def normalize_settlements(
        self, raw_batch: RawSettlementBatch
    ) -> list[CanonicalSettlementStatement]:
        # ERP does not emit marketplace settlement statements
        return []
