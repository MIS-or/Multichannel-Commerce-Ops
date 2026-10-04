from __future__ import annotations

from typing import Any

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.integrations.contracts import RawOrderBatch
from app.modules.integrations.errors import ProviderConnectionError, ProviderRateLimitError
from app.modules.integrations.models import SyncStatus, SyncType
from app.modules.integrations.pipeline import NormalizationPipeline
from app.modules.integrations.providers.mock_shopee import MockShopeeConnector
from app.modules.integrations.registry import ConnectorRegistry
from app.modules.integrations.repository import SyncRunRepository
from app.modules.integrations.service import SyncManagerService


@pytest.fixture
def sync_repository(session: AsyncSession) -> SyncRunRepository:
    return SyncRunRepository(session)


@pytest.fixture
def mock_registry() -> ConnectorRegistry:
    registry = ConnectorRegistry()
    registry.register(MockShopeeConnector(channel_code="shopee"))
    return registry


@pytest.fixture
def sync_manager(
    session: AsyncSession,
    sync_repository: SyncRunRepository,
    mock_registry: ConnectorRegistry,
) -> SyncManagerService:
    pipeline = NormalizationPipeline()
    return SyncManagerService(
        session=session,
        repository=sync_repository,
        registry=mock_registry,
        pipeline=pipeline,
    )


@pytest.mark.asyncio
async def test_sync_orders_success(sync_manager: SyncManagerService) -> None:
    # Execute order sync for shopee
    run = await sync_manager.execute_sync(
        channel_code="shopee",
        sync_type=SyncType.ORDERS,
    )

    assert run.id is not None
    assert run.channel_code == "shopee"
    assert run.sync_type == SyncType.ORDERS
    assert run.status == SyncStatus.SUCCESS
    assert run.records_fetched > 0
    assert run.records_processed == run.records_fetched
    assert run.records_failed == 0
    assert run.duration_ms >= 0
    assert run.completed_at is not None

    # Check that the run was persisted to the database
    history = await sync_manager.list_sync_runs(channel_code="shopee")
    assert len(history) == 1
    assert history[0].id == run.id


@pytest.mark.asyncio
async def test_sync_inventory_success(sync_manager: SyncManagerService) -> None:
    run = await sync_manager.execute_sync(
        channel_code="shopee",
        sync_type=SyncType.INVENTORY,
    )

    assert run.status == SyncStatus.SUCCESS
    assert run.records_fetched > 0
    assert run.records_processed == run.records_fetched
    assert run.records_failed == 0


@pytest.mark.asyncio
async def test_sync_settlements_success(sync_manager: SyncManagerService) -> None:
    run = await sync_manager.execute_sync(
        channel_code="shopee",
        sync_type=SyncType.SETTLEMENT,
    )

    assert run.status == SyncStatus.SUCCESS
    assert run.records_fetched > 0
    assert run.records_processed == run.records_fetched


@pytest.mark.asyncio
async def test_sync_resiliency_retries_transient_failures(
    sync_manager: SyncManagerService, mock_registry: ConnectorRegistry
) -> None:
    # Configure fault injection on shopee connector: fail twice with rate limit, then succeed
    connector = mock_registry.get("shopee")
    assert isinstance(connector, MockShopeeConnector)
    
    attempts = 0
    original_fetch = connector.fetch_orders

    async def flaky_fetch(*args: Any, **kwargs: Any) -> RawOrderBatch:
        nonlocal attempts
        attempts += 1
        if attempts < 3:
            raise ProviderRateLimitError(
                "Shopee API rate limit reached (HTTP 429)",
                details={"retry_after": 0.01},
            )
        return await original_fetch(*args, **kwargs)

    connector.fetch_orders = flaky_fetch  # type: ignore[assignment]

    run = await sync_manager.execute_sync(
        channel_code="shopee",
        sync_type=SyncType.ORDERS,
        max_retries=3,
        backoff_base=0.01,
    )

    assert attempts == 3
    assert run.status == SyncStatus.SUCCESS
    assert run.records_processed > 0


@pytest.mark.asyncio
async def test_sync_permanent_failure_records_failed_status(
    sync_manager: SyncManagerService, mock_registry: ConnectorRegistry
) -> None:
    connector = mock_registry.get("shopee")
    assert isinstance(connector, MockShopeeConnector)

    async def broken_fetch(*args: Any, **kwargs: Any) -> RawOrderBatch:
        raise ProviderConnectionError("shopee", "TLS handshake timeout to Shopee gateway")

    connector.fetch_orders = broken_fetch  # type: ignore[assignment]

    run = await sync_manager.execute_sync(
        channel_code="shopee",
        sync_type=SyncType.ORDERS,
        max_retries=2,
        backoff_base=0.01,
    )

    assert run.status == SyncStatus.FAILED
    assert run.records_fetched == 0
    assert run.error_details is not None
    assert "TLS handshake timeout" in run.error_details.get("message", "")


@pytest.mark.asyncio
async def test_health_check_all_channels(sync_manager: SyncManagerService) -> None:
    health_reports = await sync_manager.check_all_health()
    assert len(health_reports) >= 1
    shopee_report = next(r for r in health_reports if r.channel_code == "shopee")
    assert shopee_report.is_healthy is True
    assert "Successfully connected" in shopee_report.message


@pytest.mark.asyncio
async def test_integrations_api_endpoints(session: AsyncSession) -> None:
    from httpx import ASGITransport, AsyncClient

    from app.database import get_session
    from app.main import app

    app.dependency_overrides[get_session] = lambda: session

    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # 1. Health check via GET /api/v1/integrations/health
            health_res = await client.get("/api/v1/integrations/health")
            assert health_res.status_code == 200
            data = health_res.json()
            assert data["total_count"] >= 1
            assert data["healthy_count"] >= 1

            # 2. Trigger manual sync via POST /api/v1/integrations/{channel_code}/sync
            sync_res = await client.post(
                "/api/v1/integrations/shopee/sync",
                json={"sync_type": "orders", "max_retries": 2},
            )
            assert sync_res.status_code == 200
            sync_data = sync_res.json()
            assert sync_data["sync_run"]["channel_code"] == "shopee"
            assert sync_data["sync_run"]["status"] == "success"

            # 3. List sync runs via GET /api/v1/integrations/sync-runs
            runs_res = await client.get("/api/v1/integrations/sync-runs?channel_code=shopee")
            assert runs_res.status_code == 200
            runs_list = runs_res.json()
            assert len(runs_list) >= 1
            assert runs_list[0]["channel_code"] == "shopee"
    finally:
        app.dependency_overrides.clear()
