from __future__ import annotations

import asyncio
from typing import Any

from app.modules.integrations.contracts import (
    BaseConnector,
    ConnectionHealth,
    ConnectionStatus,
)
from app.modules.integrations.errors import (
    ProviderAuthenticationError,
    ProviderConnectionError,
    ProviderPayloadError,
    ProviderRateLimitError,
)
from app.shared.time import utc_now


class BaseMockConnector(BaseConnector):
    """Base class for test and development mock connectors with fault-injection support."""

    def __init__(
        self,
        *,
        channel_code: str,
        platform_type: str,
        simulated_latency_ms: float = 5.0,
        simulated_failure: str | None = None,
        config: dict[str, Any] | None = None,
    ) -> None:
        self._channel_code = channel_code
        self._platform_type = platform_type
        self.simulated_latency_ms = simulated_latency_ms
        self.simulated_failure = simulated_failure
        self.config = config or {}

    @property
    def channel_code(self) -> str:
        return self._channel_code

    @property
    def platform_type(self) -> str:
        return self._platform_type

    async def _simulate_network_overhead(self) -> None:
        """Simulate real network latency and evaluate fault injection."""
        if self.simulated_latency_ms > 0:
            await asyncio.sleep(self.simulated_latency_ms / 1000.0)

        if self.simulated_failure == "connection_timeout":
            raise ProviderConnectionError(
                self.channel_code,
                "Simulated socket read timeout after 10000ms",
            )
        if self.simulated_failure == "auth_failed":
            raise ProviderAuthenticationError(
                self.channel_code,
                "Simulated API key rejected by platform",
            )
        if self.simulated_failure == "rate_limit":
            raise ProviderRateLimitError(
                self.channel_code,
                retry_after_seconds=30,
            )
        if self.simulated_failure == "payload_corrupt":
            raise ProviderPayloadError(
                self.channel_code,
                "Malformed JSON response body: unexpected EOF",
                raw_payload="<html 502 Bad Gateway>",
            )

    async def test_connection(self) -> ConnectionHealth:
        start_time = utc_now()
        try:
            await self._simulate_network_overhead()
            latency = (utc_now() - start_time).total_seconds() * 1000.0
            return ConnectionHealth(
                status=ConnectionStatus.HEALTHY,
                latency_ms=round(latency, 2),
                message=f"Successfully connected to {self.channel_code} ({self.platform_type})",
            )
        except Exception as e:
            latency = (utc_now() - start_time).total_seconds() * 1000.0
            return ConnectionHealth(
                status=ConnectionStatus.UNHEALTHY,
                latency_ms=round(latency, 2),
                message=str(e),
            )
