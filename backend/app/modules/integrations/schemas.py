from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.modules.integrations.models import SyncStatus, SyncType


class SyncRunRead(BaseModel):
    id: int
    channel_code: str
    sync_type: SyncType
    status: SyncStatus
    records_fetched: int
    records_processed: int
    records_failed: int
    cursor_value: str | None = None
    error_details: dict[str, Any] | None = None
    duration_ms: int
    started_at: datetime
    completed_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class SyncTriggerRequest(BaseModel):
    sync_type: SyncType = Field(default=SyncType.ORDERS)
    cursor: str | None = None
    max_retries: int = Field(default=3, ge=1, le=10)

    @field_validator("sync_type", mode="before")
    @classmethod
    def normalize_sync_type(cls, v: Any) -> Any:
        if isinstance(v, str) and v.lower().strip() in ("settlement", "settlements"):
            return SyncType.SETTLEMENT
        return v


class SyncTriggerResponse(BaseModel):
    sync_run: SyncRunRead
    message: str


class ConnectorHealthStatus(BaseModel):
    channel_code: str
    is_healthy: bool
    latency_ms: int | None = None
    message: str
    details: dict[str, Any] = Field(default_factory=dict)


class IntegrationHealthResponse(BaseModel):
    connectors: list[ConnectorHealthStatus]
    healthy_count: int
    total_count: int
