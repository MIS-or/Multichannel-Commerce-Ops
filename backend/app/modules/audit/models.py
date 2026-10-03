from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from sqlalchemy import JSON, Column, Index, String
from sqlmodel import Field, SQLModel

from app.shared.time import Timestamptz, utc_now


class AuditAction(StrEnum):
    EXCEPTION_CREATED = "exception.created"
    EXCEPTION_STATUS_CHANGED = "exception.status_changed"
    EXCEPTION_ASSIGNED = "exception.assigned"
    EXCEPTION_RESOLVED = "exception.resolved"
    RECONCILIATION_RUN = "reconciliation.run"
    SYNC_TRIGGERED = "sync.triggered"
    RULE_CREATED = "rule.created"
    RULE_TOGGLED = "rule.toggled"
    MANUAL_OVERRIDE = "manual.override"
    JOB_SUBMITTED = "job.submitted"
    JOB_STARTED = "job.started"
    JOB_COMPLETED = "job.completed"
    JOB_FAILED = "job.failed"
    JOB_CANCELLED = "job.cancelled"


class AuditLog(SQLModel, table=True):
    """Immutable operational audit log record."""

    __tablename__ = "audit_logs"
    __table_args__ = (
        Index("ix_audit_logs_entity", "entity_type", "entity_id"),
        Index("ix_audit_logs_action", "action"),
        Index("ix_audit_logs_actor", "actor_id"),
        Index("ix_audit_logs_created_at", "created_at"),
    )

    id: int | None = Field(default=None, primary_key=True)
    actor_id: str = Field(sa_column=Column(String(100), nullable=False))
    actor_role: str = Field(sa_column=Column(String(50), nullable=False))
    action: str = Field(sa_column=Column(String(64), nullable=False))
    entity_type: str = Field(sa_column=Column(String(64), nullable=False))
    entity_id: str = Field(sa_column=Column(String(100), nullable=False))
    before_state: dict[str, Any] | None = Field(default=None, sa_column=Column(JSON, nullable=True))
    after_state: dict[str, Any] | None = Field(default=None, sa_column=Column(JSON, nullable=True))
    reason: str | None = Field(default=None, sa_column=Column(String(500), nullable=True))
    ip_address: str | None = Field(default=None, sa_column=Column(String(64), nullable=True))
    created_at: datetime = Field(
        default_factory=utc_now,
        sa_column=Column(Timestamptz(), nullable=False, default=utc_now),
    )
