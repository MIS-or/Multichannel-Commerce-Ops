from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from app.modules.integrations.canonical.models import (
    CanonicalInventoryItem,
    CanonicalOrder,
    CanonicalOrderItem,
    CanonicalOrderStatus,
    CanonicalSettlementEntry,
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
    "UNPAID": CanonicalOrderStatus.PENDING,
    "AWAITING_SHIPMENT": CanonicalOrderStatus.PROCESSING,
    "AWAITING_COLLECTION": CanonicalOrderStatus.PROCESSING,
    "IN_TRANSIT": CanonicalOrderStatus.SHIPPED,
    "DELIVERED": CanonicalOrderStatus.DELIVERED,
    "COMPLETED": CanonicalOrderStatus.DELIVERED,
    "CANCELLED": CanonicalOrderStatus.CANCELLED,
}


class TikTokNormalizer(BaseNormalizer):
    """Normalizer for TikTok Shop Partner API payloads."""

    def normalize_orders(self, raw_batch: RawOrderBatch) -> list[CanonicalOrder]:
        orders: list[CanonicalOrder] = []
        for raw in raw_batch.raw_orders:
            order_id = raw.get("id")
            if not order_id:
                raise ProviderPayloadError("tiktok", "Missing id in raw order", raw_payload=raw)

            raw_status = str(raw.get("status", "")).upper()
            status = STATUS_MAP.get(raw_status, CanonicalOrderStatus.PROCESSING)

            raw_items = raw.get("line_items", [])
            if not raw_items:
                raise ProviderPayloadError(
                    "tiktok", f"Order {order_id} has no line_items", raw_payload=raw
                )

            items: list[CanonicalOrderItem] = []
            for item in raw_items:
                sku = item.get("seller_sku")
                if not sku:
                    raise ProviderPayloadError(
                        "tiktok",
                        f"Order {order_id} line item missing seller_sku",
                        raw_payload=item,
                    )
                qty = int(item.get("quantity", 1))
                price = Decimal(str(item.get("sale_price", 0)))
                subtotal = qty * price
                items.append(
                    CanonicalOrderItem(
                        sku=sku,
                        product_name=item.get("product_name"),
                        quantity=qty,
                        unit_price=price,
                        discount_amount=Decimal("0.00"),
                        subtotal=subtotal,
                    )
                )

            payment = raw.get("payment", {})
            total_amt = Decimal(str(payment.get("total_amount", 0)))
            create_time = raw.get("create_time")
            placed_at = datetime.fromtimestamp(create_time, tz=UTC) if create_time else utc_now()

            orders.append(
                CanonicalOrder(
                    channel_code=raw_batch.channel_code,
                    channel_order_id=str(order_id),
                    order_status=status,
                    currency=payment.get("currency", "VND"),
                    total_amount=total_amt,
                    customer_email=raw.get("buyer_email"),
                    placed_at=placed_at,
                    updated_at=utc_now(),
                    items=items,
                )
            )
        return orders

    def normalize_inventory(self, raw_batch: RawInventoryBatch) -> list[CanonicalInventoryItem]:
        items: list[CanonicalInventoryItem] = []
        for raw in raw_batch.raw_items:
            skus_list = raw.get("skus", [])
            for sku_data in skus_list:
                sku = sku_data.get("seller_sku")
                if not sku:
                    continue

                inventory_records = sku_data.get("inventory", [])
                total_qty = Decimal("0")
                wh_id: str | None = None
                for inv in inventory_records:
                    total_qty += Decimal(str(inv.get("quantity", 0)))
                    if wh_id is None:
                        wh_id = inv.get("warehouse_id")

                items.append(
                    CanonicalInventoryItem(
                        sku=sku,
                        source_system=raw_batch.source_system,
                        location_id=wh_id,
                        on_hand_qty=total_qty,
                        allocated_qty=Decimal("0"),
                        available_qty=total_qty,
                        captured_at=raw_batch.captured_at,
                    )
                )
        return items

    def normalize_settlements(
        self, raw_batch: RawSettlementBatch
    ) -> list[CanonicalSettlementStatement]:
        statements: list[CanonicalSettlementStatement] = []
        for raw in raw_batch.raw_statements:
            stmt_id = raw.get("settlement_id")
            if not stmt_id:
                raise ProviderPayloadError(
                    "tiktok", "Missing settlement_id in raw settlement", raw_payload=raw
                )

            settle_time = raw.get("settlement_time")
            payout_at = datetime.fromtimestamp(settle_time, tz=UTC) if settle_time else utc_now()

            raw_orders = raw.get("orders", [])
            entries: list[CanonicalSettlementEntry] = []
            total_gross = Decimal("0.00")
            total_fees = Decimal("0.00")
            total_net = Decimal("0.00")

            for ord_data in raw_orders:
                order_id = ord_data.get("order_id")
                if not order_id:
                    continue
                gross = Decimal(str(ord_data.get("gross_sales", 0)))
                comm = Decimal(str(ord_data.get("platform_commission", 0)))
                tx = Decimal(str(ord_data.get("transaction_fee", 0)))
                subsidy = Decimal(str(ord_data.get("shipping_fee_subsidy", 0)))
                refund = Decimal(str(ord_data.get("refund_amount", 0)))
                net = Decimal(str(ord_data.get("net_settlement_amount", 0)))

                entry = CanonicalSettlementEntry(
                    channel_order_id=order_id,
                    gross_sales=gross,
                    commission_fee=comm,
                    service_fee=Decimal("0.00"),
                    transaction_fee=tx,
                    seller_shipping_discount=Decimal("0.00"),
                    shipping_fee_subsidy=subsidy,
                    refund_amount=refund,
                    net_payout=net,
                )
                entries.append(entry)
                total_gross += gross
                total_fees += comm + tx
                total_net += net

            statements.append(
                CanonicalSettlementStatement(
                    channel_code=raw_batch.source_system,
                    statement_id=stmt_id,
                    period_start=raw_batch.period_start,
                    period_end=raw_batch.period_end,
                    payout_at=payout_at,
                    currency=raw.get("currency", "VND"),
                    total_gross_sales=total_gross,
                    total_platform_fees=total_fees,
                    total_net_payout=total_net,
                    entries=entries,
                )
            )
        return statements
