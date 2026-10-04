from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field

from app.shared.time import utc_now


class ConnectionStatus(StrEnum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


class ConnectionHealth(BaseModel):
    """Health check outcome for an external integration endpoint."""

    status: ConnectionStatus
    latency_ms: float = Field(ge=0)
    message: str
    checked_at: datetime = Field(default_factory=utc_now)


class RawOrderBatch(BaseModel):
    """Envelope holding raw, platform-specific order payloads from an external channel."""

    channel_code: str
    raw_orders: list[dict[str, Any]]
    next_cursor: str | None = None
    total_count: int | None = None
    fetched_at: datetime = Field(default_factory=utc_now)


class RawInventoryBatch(BaseModel):
    """Envelope holding raw, platform-specific inventory stock snapshots."""

    source_system: str
    raw_items: list[dict[str, Any]]
    next_cursor: str | None = None
    captured_at: datetime = Field(default_factory=utc_now)


class RawSettlementBatch(BaseModel):
    """Envelope holding raw, platform-specific financial settlement/escrow statements."""

    source_system: str
    raw_statements: list[dict[str, Any]]
    period_start: datetime
    period_end: datetime
    total_payout_amount: Decimal | None = None
    fetched_at: datetime = Field(default_factory=utc_now)


class BaseConnector(ABC):
    """Base abstraction for all external systems (ERP, Marketplaces, WMS, Payment Gateways)."""

    @property
    @abstractmethod
    def channel_code(self) -> str:
        """Unique identifier matching the channel registry code (e.g. 'shopee', 'odoo')."""
        ...

    @property
    @abstractmethod
    def platform_type(self) -> str:
        """Category of platform (e.g. 'marketplace', 'erp', 'ecommerce_store')."""
        ...

    @abstractmethod
    async def test_connection(self) -> ConnectionHealth:
        """Perform a lightweight ping/handshake to verify credentials and connectivity."""
        ...


class OrderProvider(BaseConnector):
    """Interface for systems that emit sales orders (Marketplaces, Brand Webstore)."""

    @abstractmethod
    async def fetch_orders(
        self,
        *,
        cursor: str | None = None,
        updated_since: datetime | None = None,
        limit: int = 50,
    ) -> RawOrderBatch:
        """Fetch a page of orders modified since updated_since or from cursor."""
        ...


class InventoryProvider(BaseConnector):
    """Interface for systems maintaining inventory balances (ERP, WMS, Marketplace channels)."""

    @abstractmethod
    async def fetch_inventory(
        self,
        *,
        skus: list[str] | None = None,
        cursor: str | None = None,
        limit: int = 100,
    ) -> RawInventoryBatch:
        """Fetch stock balances for specified SKUs or full inventory snapshot."""
        ...


class SettlementProvider(BaseConnector):
    """Interface for systems reporting settlement statements, payout batches, and fee deductions."""

    @abstractmethod
    async def fetch_settlements(
        self,
        *,
        start_date: datetime,
        end_date: datetime,
    ) -> RawSettlementBatch:
        """Fetch financial payout statements and platform fee breakdowns within a date range."""
        ...
