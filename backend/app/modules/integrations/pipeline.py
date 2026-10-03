from __future__ import annotations

import logging

from app.modules.integrations.canonical.models import (
    CanonicalInventoryItem,
    CanonicalOrder,
    CanonicalSettlementStatement,
)
from app.modules.integrations.contracts import (
    RawInventoryBatch,
    RawOrderBatch,
    RawSettlementBatch,
)
from app.modules.integrations.errors import ProviderPayloadError
from app.modules.integrations.normalizers import get_normalizer_for_channel

logger = logging.getLogger("mco.integrations.pipeline")


class NormalizationPipeline:
    """Orchestrates ingesting raw heterogeneous batches, normalizing them to Canonical DTOs,

    and enforcing data quality and business sanity checks.
    """

    @classmethod
    def process_orders(cls, raw_batch: RawOrderBatch) -> list[CanonicalOrder]:
        """Normalize raw orders into CanonicalOrder DTOs and validate constraints."""
        normalizer = get_normalizer_for_channel(raw_batch.channel_code)
        try:
            canonical_orders = normalizer.normalize_orders(raw_batch)
        except Exception as e:
            if isinstance(e, ProviderPayloadError):
                raise
            raise ProviderPayloadError(
                raw_batch.channel_code,
                f"Failed to normalize orders: {e}",
            ) from e

        # Business sanity checks
        for order in canonical_orders:
            if not order.items:
                raise ProviderPayloadError(
                    raw_batch.channel_code,
                    f"Order '{order.channel_order_id}' contains zero line items",
                )
            if order.total_amount < 0:
                raise ProviderPayloadError(
                    raw_batch.channel_code,
                    f"Order '{order.channel_order_id}' has negative total amount",
                )

        logger.info(
            "Normalized %d orders from channel '%s'",
            len(canonical_orders),
            raw_batch.channel_code,
        )
        return canonical_orders

    @classmethod
    def process_inventory(cls, raw_batch: RawInventoryBatch) -> list[CanonicalInventoryItem]:
        """Normalize raw inventory snapshots into CanonicalInventoryItem DTOs."""
        normalizer = get_normalizer_for_channel(raw_batch.source_system)
        try:
            canonical_items = normalizer.normalize_inventory(raw_batch)
        except Exception as e:
            if isinstance(e, ProviderPayloadError):
                raise
            raise ProviderPayloadError(
                raw_batch.source_system,
                f"Failed to normalize inventory: {e}",
            ) from e

        # Business sanity checks
        for item in canonical_items:
            if item.on_hand_qty < 0:
                raise ProviderPayloadError(
                    raw_batch.source_system,
                    f"SKU '{item.sku}' reports negative on_hand stock ({item.on_hand_qty})",
                )

        logger.info(
            "Normalized %d inventory records from '%s'",
            len(canonical_items),
            raw_batch.source_system,
        )
        return canonical_items

    @classmethod
    def process_settlements(
        cls, raw_batch: RawSettlementBatch
    ) -> list[CanonicalSettlementStatement]:
        """Normalize raw settlement statements into CanonicalSettlementStatement DTOs."""
        normalizer = get_normalizer_for_channel(raw_batch.source_system)
        try:
            statements = normalizer.normalize_settlements(raw_batch)
        except Exception as e:
            if isinstance(e, ProviderPayloadError):
                raise
            raise ProviderPayloadError(
                raw_batch.source_system,
                f"Failed to normalize settlements: {e}",
            ) from e

        logger.info(
            "Normalized %d settlement statements from '%s'",
            len(statements),
            raw_batch.source_system,
        )
        return statements
