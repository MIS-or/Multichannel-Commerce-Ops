from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.modules.exceptions.models import (
    ExceptionDomain,
    ExceptionSeverity,
    ExceptionStatus,
    RootCauseCategory,
)


class ExceptionCreate(BaseModel):
    """Payload to record an operational discrepancy for lifecycle management."""

    domain: ExceptionDomain
    severity: ExceptionSeverity
    reference_id: str = Field(min_length=1, max_length=100)
    channel_code: str | None = Field(default=None, max_length=64)
    title: str = Field(min_length=1, max_length=200)
    description: str = Field(min_length=1, max_length=1000)
    variance_amount: Decimal | None = None
    payload_snapshot: dict[str, Any] = Field(default_factory=dict)


class ExceptionAssign(BaseModel):
    """Payload to assign an exception to an operations or accounting member."""

    assigned_to: str = Field(min_length=1, max_length=100)


class ExceptionResolve(BaseModel):
    """Payload to mark an operational exception as resolved with audited root cause."""

    root_cause: RootCauseCategory
    resolution_notes: str = Field(min_length=5, max_length=1000)


class ExceptionIgnore(BaseModel):
    """Payload to ignore a known false-positive or expected discrepancy."""

    reason: str = Field(min_length=5, max_length=1000)


class ExceptionRead(BaseModel):
    """DTO for viewing an operational exception and its resolution status."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    domain: ExceptionDomain
    severity: ExceptionSeverity
    status: ExceptionStatus
    reference_id: str
    channel_code: str | None = None
    title: str
    description: str
    variance_amount: Decimal | None = None
    payload_snapshot: dict[str, Any]
    assigned_to: str | None = None
    root_cause: RootCauseCategory | None = None
    resolution_notes: str | None = None
    created_at: datetime
    updated_at: datetime
    resolved_at: datetime | None = None
