from __future__ import annotations

from abc import ABC, abstractmethod

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


class BaseNormalizer(ABC):
    """Abstract normalizer converting platform-specific payloads into Canonical DTOs."""

    @abstractmethod
    def normalize_orders(self, raw_batch: RawOrderBatch) -> list[CanonicalOrder]:
        """Convert a batch of platform-specific orders into canonical orders."""
        ...

    @abstractmethod
    def normalize_inventory(self, raw_batch: RawInventoryBatch) -> list[CanonicalInventoryItem]:
        """Convert platform-specific inventory balances into canonical inventory items."""
        ...

    @abstractmethod
    def normalize_settlements(
        self, raw_batch: RawSettlementBatch
    ) -> list[CanonicalSettlementStatement]:
        """Convert platform payout batches into canonical settlement statements."""
        ...
