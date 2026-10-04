from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from sqlalchemy import JSON, Column, Index, String
from sqlalchemy import Enum as SAEnum
from sqlmodel import Field, SQLModel

from app.shared.time import Timestamptz, utc_now


class SyncType(StrEnum):
    ORDERS = "orders"
    INVENTORY = "inventory"
    SETTLEMENT = "settlement"


class SyncStatus(StrEnum):
    SUCCESS = "success"
    PARTIAL = "partial"
    FAILED = "failed"


class SyncRun(SQLModel, table=True):
    """Execution telemetry and tracking for connector sync runs."""

    __tablename__ = "sync_runs"
    __table_args__ = (
        Index("ix_sync_runs_channel_type", "channel_code", "sync_type"),
        Index("ix_sync_runs_started_at", "started_at"),
    )

    id: int | None = Field(default=None, primary_key=True)
    channel_code: str = Field(
        sa_column=Column(String(64), nullable=False, index=True)
    )
    sync_type: SyncType = Field(
        sa_column=Column(
            SAEnum(SyncType, native_enum=False, length=32),
            nullable=False,
            index=True,
        )
    )
    status: SyncStatus = Field(
        sa_column=Column(
            SAEnum(SyncStatus, native_enum=False, length=20),
            nullable=False,
            index=True,
        )
    )
    records_fetched: int = Field(default=0, nullable=False)
    records_processed: int = Field(default=0, nullable=False)
    records_failed: int = Field(default=0, nullable=False)
    cursor_value: str | None = Field(
        default=None,
        sa_column=Column(String(100), nullable=True),
    )
    error_details: dict[str, Any] | None = Field(
        default=None,
        sa_column=Column(JSON, nullable=True),
    )
    duration_ms: int = Field(default=0, nullable=False)
    started_at: datetime = Field(
        default_factory=utc_now,
        sa_column=Column(Timestamptz, nullable=False),
    )
    completed_at: datetime | None = Field(
        default=None,
        sa_column=Column(Timestamptz, nullable=True),
    )
