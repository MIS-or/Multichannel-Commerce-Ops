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
    "READY_TO_SHIP": CanonicalOrderStatus.PROCESSING,
    "PROCESSED": CanonicalOrderStatus.PROCESSING,
    "SHIPPED": CanonicalOrderStatus.SHIPPED,
    "COMPLETED": CanonicalOrderStatus.DELIVERED,
    "CANCELLED": CanonicalOrderStatus.CANCELLED,
    "IN_CANCEL": CanonicalOrderStatus.CANCELLED,
    "TO_RETURN": CanonicalOrderStatus.RETURNED,
}


class ShopeeNormalizer(BaseNormalizer):
    """Normalizer for Shopee Open API v2 payloads."""

    def normalize_orders(self, raw_batch: RawOrderBatch) -> list[CanonicalOrder]:
        orders: list[CanonicalOrder] = []
        for raw in raw_batch.raw_orders:
            order_sn = raw.get("order_sn")
            if not order_sn:
                raise ProviderPayloadError(
                    "shopee",
                    "Missing order_sn in raw order",
                    raw_payload=raw,
                )

            raw_status = str(raw.get("order_status", "")).upper()
            status = STATUS_MAP.get(raw_status, CanonicalOrderStatus.PROCESSING)

            raw_items = raw.get("item_list", [])
            if not raw_items:
                raise ProviderPayloadError(
                    "shopee", f"Order {order_sn} has no item_list", raw_payload=raw
                )

            items: list[CanonicalOrderItem] = []
            for item in raw_items:
                sku = item.get("item_sku") or item.get("model_sku")
                if not sku:
                    raise ProviderPayloadError(
                        "shopee",
                        f"Order {order_sn} item missing item_sku",
                        raw_payload=item,
                    )
                qty = int(item.get("model_quantity_purchased", 1))
                price = Decimal(str(item.get("model_discounted_price", 0)))
                subtotal = qty * price
                items.append(
                    CanonicalOrderItem(
                        sku=sku,
                        product_name=item.get("item_name"),
                        quantity=qty,
                        unit_price=price,
                        discount_amount=Decimal("0.00"),
                        subtotal=subtotal,
                    )
                )

            create_time = raw.get("create_time")
            placed_at = datetime.fromtimestamp(create_time, tz=UTC) if create_time else utc_now()

            orders.append(
                CanonicalOrder(
                    channel_code=raw_batch.channel_code,
                    channel_order_id=str(order_sn),
                    order_status=status,
                    currency=raw.get("currency", "VND"),
                    total_amount=Decimal(str(raw.get("total_amount", 0))),
                    customer_name=raw.get("buyer_username"),
                    placed_at=placed_at,
                    updated_at=utc_now(),
                    items=items,
                )
            )
        return orders

    def normalize_inventory(self, raw_batch: RawInventoryBatch) -> list[CanonicalInventoryItem]:
        items: list[CanonicalInventoryItem] = []
        for raw in raw_batch.raw_items:
            sku = raw.get("item_sku") or raw.get("model_sku")
            if not sku:
                raise ProviderPayloadError(
                    "shopee",
                    "Inventory item missing item_sku",
                    raw_payload=raw,
                )

            stock_info = raw.get("stock_info_v2", {})
            summary = stock_info.get("summary_info", {})
            avail = Decimal(str(summary.get("total_available_stock", 0)))
            reserved = Decimal(str(summary.get("total_reserved_stock", 0)))
            on_hand = avail + reserved

            # Extract location if available
            seller_stock = stock_info.get("seller_stock", [])
            location_id = seller_stock[0].get("location_id") if seller_stock else None

            items.append(
                CanonicalInventoryItem(
                    sku=sku,
                    source_system=raw_batch.source_system,
                    location_id=location_id,
                    on_hand_qty=on_hand,
                    allocated_qty=reserved,
                    available_qty=avail,
                    captured_at=raw_batch.captured_at,
                )
            )
        return items

    def normalize_settlements(
        self, raw_batch: RawSettlementBatch
    ) -> list[CanonicalSettlementStatement]:
        statements: list[CanonicalSettlementStatement] = []
        for raw in raw_batch.raw_statements:
            stmt_id = raw.get("statement_id")
            if not stmt_id:
                raise ProviderPayloadError(
                    "shopee", "Missing statement_id in raw settlement", raw_payload=raw
                )

            payout_time = raw.get("payout_time")
            payout_at = datetime.fromtimestamp(payout_time, tz=UTC) if payout_time else utc_now()

            raw_incomes = raw.get("order_income_list", [])
            entries: list[CanonicalSettlementEntry] = []
            total_gross = Decimal("0.00")
            total_fees = Decimal("0.00")
            total_net = Decimal("0.00")

            for inc in raw_incomes:
                order_sn = inc.get("order_sn")
                if not order_sn:
                    continue
                gross = Decimal(str(inc.get("buyer_total_amount", 0)))
                comm = Decimal(str(inc.get("commission_fee", 0)))
                svc = Decimal(str(inc.get("service_fee", 0)))
                tx = Decimal(str(inc.get("transaction_fee", 0)))
                rebate = Decimal(str(inc.get("seller_voucher_rebate", 0)))
                ship_disc = Decimal(str(inc.get("seller_shipping_discount", 0)))
                escrow = Decimal(str(inc.get("escrow_amount", 0)))

                entry = CanonicalSettlementEntry(
                    channel_order_id=order_sn,
                    gross_sales=gross,
                    commission_fee=comm,
                    service_fee=svc,
                    transaction_fee=tx,
                    seller_shipping_discount=ship_disc,
                    shipping_fee_subsidy=rebate,
                    refund_amount=Decimal("0.00"),
                    net_payout=escrow,
                )
                entries.append(entry)
                total_gross += gross
                total_fees += comm + svc + tx + ship_disc
                total_net += escrow

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
