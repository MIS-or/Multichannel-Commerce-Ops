from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from sqlalchemy import JSON, CheckConstraint, Column, Index, Integer, String
from sqlmodel import Field, SQLModel

from app.shared.time import Timestamptz, utc_now


class JobStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class JobType(StrEnum):
    CHANNEL_SYNC = "channel_sync"
    SETTLEMENT_RECONCILIATION = "settlement_reconciliation"
    INVENTORY_VARIANCE_CHECK = "inventory_variance_check"
    RULE_EVALUATION = "rule_evaluation"


class JobRun(SQLModel, table=True):
    """Database-backed asynchronous operational job execution record."""

    __tablename__ = "job_runs"
    __table_args__ = (
        Index("ix_job_runs_status", "status"),
        Index("ix_job_runs_job_type", "job_type"),
        Index("ix_job_runs_created_at", "created_at"),
        CheckConstraint("retry_count >= 0", name="ck_job_runs_retry_nonnegative"),
        CheckConstraint("max_retries >= 0", name="ck_job_runs_max_retries_nonnegative"),
    )

    id: int | None = Field(default=None, primary_key=True)
    job_type: str = Field(sa_column=Column(String(64), nullable=False))
    status: str = Field(default=JobStatus.PENDING, sa_column=Column(String(32), nullable=False))
    payload: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON, nullable=False))
    result: dict[str, Any] | None = Field(default=None, sa_column=Column(JSON, nullable=True))
    error_message: str | None = Field(default=None, sa_column=Column(String(1000), nullable=True))
    retry_count: int = Field(default=0, sa_column=Column(Integer, nullable=False))
    max_retries: int = Field(default=3, sa_column=Column(Integer, nullable=False))
    enqueued_by: str = Field(default="system", sa_column=Column(String(100), nullable=False))
    started_at: datetime | None = Field(default=None, sa_type=Timestamptz)
    completed_at: datetime | None = Field(default=None, sa_type=Timestamptz)
    created_at: datetime = Field(default_factory=utc_now, sa_type=Timestamptz)
    updated_at: datetime = Field(default_factory=utc_now, sa_type=Timestamptz)
