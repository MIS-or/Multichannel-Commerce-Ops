from __future__ import annotations

from datetime import datetime
from decimal import Decimal

import pytest

from app.modules.integrations import (
    BaseConnector,
    ConnectionHealth,
    ConnectionStatus,
    IntegrationError,
    InventoryProvider,
    OrderProvider,
    ProviderAuthenticationError,
    ProviderConnectionError,
    ProviderPayloadError,
    ProviderRateLimitError,
    RawInventoryBatch,
    RawOrderBatch,
    RawSettlementBatch,
    SettlementProvider,
)
from app.shared.time import utc_now


def test_connection_health_model() -> None:
    health = ConnectionHealth(
        status=ConnectionStatus.HEALTHY,
        latency_ms=12.5,
        message="Connected OK",
    )
    assert health.status == ConnectionStatus.HEALTHY
    assert health.latency_ms == 12.5
    assert health.message == "Connected OK"
    assert isinstance(health.checked_at, datetime)


def test_raw_order_batch_model() -> None:
    batch = RawOrderBatch(
        channel_code="shopee",
        raw_orders=[{"order_sn": "123", "amount": 100}],
        total_count=1,
    )
    assert batch.channel_code == "shopee"
    assert len(batch.raw_orders) == 1
    assert batch.total_count == 1
    assert isinstance(batch.fetched_at, datetime)


def test_raw_inventory_batch_model() -> None:
    batch = RawInventoryBatch(
        source_system="odoo_erp",
        raw_items=[{"default_code": "SKU-1", "qty": 50}],
    )
    assert batch.source_system == "odoo_erp"
    assert len(batch.raw_items) == 1
    assert isinstance(batch.captured_at, datetime)


def test_raw_settlement_batch_model() -> None:
    now = utc_now()
    batch = RawSettlementBatch(
        source_system="shopee",
        raw_statements=[{"stmt_id": "STMT-1"}],
        period_start=now,
        period_end=now,
        total_payout_amount=Decimal("450000.00"),
    )
    assert batch.source_system == "shopee"
    assert batch.total_payout_amount == Decimal("450000.00")
    assert len(batch.raw_statements) == 1


def test_cannot_instantiate_abstract_interfaces() -> None:
    with pytest.raises(TypeError):
        BaseConnector()  # type: ignore[abstract]

    with pytest.raises(TypeError):
        OrderProvider()  # type: ignore[abstract]

    with pytest.raises(TypeError):
        InventoryProvider()  # type: ignore[abstract]

    with pytest.raises(TypeError):
        SettlementProvider()  # type: ignore[abstract]


def test_integration_errors_hierarchy() -> None:
    err = ProviderConnectionError("shopee", "Timeout connecting")
    assert isinstance(err, IntegrationError)
    assert err.code == "PROVIDER_CONNECTION_ERROR"
    assert err.status_code == 504
    assert err.details["provider"] == "shopee"

    auth_err = ProviderAuthenticationError("odoo", "Invalid API token")
    assert isinstance(auth_err, IntegrationError)
    assert auth_err.code == "PROVIDER_AUTH_ERROR"
    assert auth_err.status_code == 502

    rate_err = ProviderRateLimitError("tiktok", retry_after_seconds=45)
    assert isinstance(rate_err, IntegrationError)
    assert rate_err.code == "PROVIDER_RATE_LIMIT"
    assert rate_err.status_code == 429
    assert rate_err.retry_after_seconds == 45

    payload_err = ProviderPayloadError("shopee", "Corrupted JSON", raw_payload="<not json>")
    assert isinstance(payload_err, IntegrationError)
    assert payload_err.code == "PROVIDER_PAYLOAD_ERROR"
    assert payload_err.details["raw_payload"] == "<not json>"
