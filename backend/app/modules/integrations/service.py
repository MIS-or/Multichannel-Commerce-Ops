from __future__ import annotations

import asyncio
import logging
import time
from datetime import timedelta
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.integrations.contracts import (
    ConnectionStatus,
    InventoryProvider,
    OrderProvider,
    SettlementProvider,
)
from app.modules.integrations.errors import (
    IntegrationError,
    ProviderConnectionError,
    ProviderRateLimitError,
)
from app.modules.integrations.models import SyncRun, SyncStatus, SyncType
from app.modules.integrations.pipeline import NormalizationPipeline
from app.modules.integrations.registry import ConnectorRegistry, get_connector_registry
from app.modules.integrations.repository import SyncRunRepository
from app.modules.integrations.schemas import ConnectorHealthStatus, SyncRunRead
from app.shared.errors import NotFoundError
from app.shared.time import utc_now

logger = logging.getLogger(__name__)


class SyncManagerService:
    """Orchestrates channel synchronization, cursor state tracking, resiliency,

    and health checks.
    """

    def __init__(
        self,
        session: AsyncSession,
        repository: SyncRunRepository | None = None,
        registry: ConnectorRegistry | None = None,
        pipeline: NormalizationPipeline | None = None,
    ) -> None:
        self._session = session
        self._repository = repository or SyncRunRepository(session)
        self._registry = registry or get_connector_registry()
        self._pipeline = pipeline or NormalizationPipeline()

    async def execute_sync(
        self,
        *,
        channel_code: str,
        sync_type: SyncType,
        cursor: str | None = None,
        max_retries: int = 3,
        backoff_base: float = 0.5,
    ) -> SyncRunRead:
        connector = self._registry.get(channel_code)
        if connector is None:
            raise NotFoundError(
                "CONNECTOR_NOT_FOUND",
                f"No connector registered for channel '{channel_code}'",
                details={"channel_code": channel_code},
            )

        active_cursor = cursor
        if active_cursor is None:
            active_cursor = await self._repository.get_last_successful_cursor(
                channel_code, sync_type
            )

        start_time = time.monotonic()
        started_at = utc_now()
        records_fetched = 0
        records_processed = 0
        records_failed = 0
        next_cursor: str | None = None
        error_details: dict[str, Any] | None = None
        final_status = SyncStatus.SUCCESS

        for attempt in range(max_retries):
            try:
                if sync_type == SyncType.ORDERS:
                    if not isinstance(connector, OrderProvider):
                        raise IntegrationError(
                            code="PROVIDER_CAPABILITY_ERROR",
                            message=f"Connector '{channel_code}' does not implement OrderProvider",
                        )
                    raw_orders = await connector.fetch_orders(cursor=active_cursor)
                    records_fetched = len(raw_orders.raw_orders)
                    canonical_orders = self._pipeline.process_orders(raw_orders)
                    records_processed = len(canonical_orders)
                    next_cursor = raw_orders.next_cursor

                elif sync_type == SyncType.INVENTORY:
                    if not isinstance(connector, InventoryProvider):
                        raise IntegrationError(
                            code="PROVIDER_CAPABILITY_ERROR",
                            message=(
                                f"Connector '{channel_code}' does not implement InventoryProvider"
                            ),
                        )
                    raw_inventory = await connector.fetch_inventory()
                    records_fetched = len(raw_inventory.raw_items)
                    canonical_inventory = self._pipeline.process_inventory(raw_inventory)
                    records_processed = len(canonical_inventory)

                elif sync_type == SyncType.SETTLEMENT:
                    if not isinstance(connector, SettlementProvider):
                        raise IntegrationError(
                            code="PROVIDER_CAPABILITY_ERROR",
                            message=(
                                f"Connector '{channel_code}' does not implement SettlementProvider"
                            ),
                        )
                    now_dt = utc_now()
                    raw_settlements = await connector.fetch_settlements(
                        start_date=now_dt - timedelta(days=30),
                        end_date=now_dt,
                    )
                    records_fetched = len(raw_settlements.raw_statements)
                    canonical_statements = self._pipeline.process_settlements(raw_settlements)
                    records_processed = len(canonical_statements)
                    next_cursor = getattr(raw_settlements, "next_cursor", None)

                # Successful execution break out of retry loop
                break

            except (ProviderRateLimitError, ProviderConnectionError) as transient_exc:
                logger.warning(
                    "Transient error during sync attempt %d/%d for '%s': %s",
                    attempt + 1,
                    max_retries,
                    channel_code,
                    transient_exc,
                )
                if attempt == max_retries - 1:
                    final_status = SyncStatus.FAILED
                    error_details = {
                        "error_type": transient_exc.__class__.__name__,
                        "message": str(transient_exc),
                        "details": transient_exc.details,
                    }
                    records_failed = records_fetched
                    records_processed = 0
                else:
                    await asyncio.sleep(backoff_base * (2**attempt))

            except Exception as exc:
                logger.exception("Non-retriable error during sync for '%s': %s", channel_code, exc)
                final_status = SyncStatus.FAILED
                error_details = {
                    "error_type": exc.__class__.__name__,
                    "message": str(exc),
                }
                records_failed = records_fetched
                records_processed = 0
                break

        completed_at = utc_now()
        duration_ms = int((time.monotonic() - start_time) * 1000)

        sync_run = SyncRun(
            channel_code=channel_code,
            sync_type=sync_type,
            status=final_status,
            records_fetched=records_fetched,
            records_processed=records_processed,
            records_failed=records_failed,
            cursor_value=next_cursor or active_cursor,
            error_details=error_details,
            duration_ms=duration_ms,
            started_at=started_at,
            completed_at=completed_at,
        )
        saved = await self._repository.create(sync_run)
        return SyncRunRead.model_validate(saved)

    async def list_sync_runs(
        self,
        *,
        channel_code: str | None = None,
        sync_type: SyncType | None = None,
        limit: int = 50,
    ) -> list[SyncRunRead]:
        runs = await self._repository.list_runs(
            channel_code=channel_code,
            sync_type=sync_type,
            limit=limit,
        )
        return [SyncRunRead.model_validate(r) for r in runs]

    async def check_all_health(self) -> list[ConnectorHealthStatus]:
        results: list[ConnectorHealthStatus] = []
        for channel_code in self._registry.list_channel_codes():
            connector = self._registry.get(channel_code)
            if connector is None:
                continue

            health = await connector.test_connection()
            results.append(
                ConnectorHealthStatus(
                    channel_code=channel_code,
                    is_healthy=health.status == ConnectionStatus.HEALTHY,
                    latency_ms=int(health.latency_ms),
                    message=health.message,
                    details={
                        "status": health.status,
                        "checked_at": health.checked_at.isoformat(),
                    },
                )
            )
        return results
