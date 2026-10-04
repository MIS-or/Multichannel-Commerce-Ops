from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from typing import Any

from sqlalchemy import JSON, Column, Index, Numeric, String
from sqlalchemy import Enum as SAEnum
from sqlmodel import Field, SQLModel

from app.shared.time import Timestamptz, utc_now


class ExceptionDomain(StrEnum):
    INVENTORY_VARIANCE = "inventory_variance"
    SETTLEMENT_DISCREPANCY = "settlement_discrepancy"
    ORDER_SYNC_FAILED = "order_sync_failed"
    DATA_NORMALIZATION = "data_normalization"


class ExceptionSeverity(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ExceptionStatus(StrEnum):
    OPEN = "open"
    INVESTIGATING = "investigating"
    RESOLVED = "resolved"
    IGNORED = "ignored"


class RootCauseCategory(StrEnum):
    PLATFORM_FEE_OVERCHARGE = "platform_fee_overcharge"
    PHYSICAL_INVENTORY_SHRINKAGE = "physical_inventory_shrinkage"
    CHANNEL_SYNC_DELAY = "channel_sync_delay"
    MALFORMED_EXTERNAL_PAYLOAD = "malformed_external_payload"
    OPERATOR_DATA_ENTRY_ERROR = "operator_data_entry_error"
    OTHER = "other"


class OperationalException(SQLModel, table=True):
    """Managed operational discrepancy with full resolution lifecycle."""

    __tablename__ = "operational_exceptions"
    __table_args__ = (
        Index("ix_exceptions_status_domain", "status", "domain"),
        Index("ix_exceptions_reference_id", "reference_id"),
        Index("ix_exceptions_created_at", "created_at"),
    )

    id: int | None = Field(default=None, primary_key=True)
    domain: ExceptionDomain = Field(
        sa_column=Column(
            SAEnum(ExceptionDomain, native_enum=False, length=40),
            nullable=False,
            index=True,
        )
    )
    severity: ExceptionSeverity = Field(
        sa_column=Column(
            SAEnum(ExceptionSeverity, native_enum=False, length=16),
            nullable=False,
        )
    )
    status: ExceptionStatus = Field(
        default=ExceptionStatus.OPEN,
        sa_column=Column(
            SAEnum(ExceptionStatus, native_enum=False, length=20),
            nullable=False,
            index=True,
        ),
    )
    reference_id: str = Field(
        sa_column=Column(String(100), nullable=False, index=True)
    )
    channel_code: str | None = Field(
        default=None,
        sa_column=Column(String(64), nullable=True, index=True),
    )
    title: str = Field(sa_column=Column(String(200), nullable=False))
    description: str = Field(sa_column=Column(String(1000), nullable=False))
    variance_amount: Decimal | None = Field(
        default=None,
        sa_column=Column(Numeric(14, 2), nullable=True),
    )
    payload_snapshot: dict[str, Any] = Field(
        default_factory=dict,
        sa_column=Column(JSON, nullable=False),
    )
    assigned_to: str | None = Field(
        default=None,
        sa_column=Column(String(100), nullable=True),
    )
    root_cause: RootCauseCategory | None = Field(
        default=None,
        sa_column=Column(
            SAEnum(RootCauseCategory, native_enum=False, length=40),
            nullable=True,
        ),
    )
    resolution_notes: str | None = Field(
        default=None,
        sa_column=Column(String(1000), nullable=True),
    )
    created_at: datetime = Field(
        default_factory=utc_now,
        sa_column=Column(Timestamptz, nullable=False),
    )
    updated_at: datetime = Field(
        default_factory=utc_now,
        sa_column=Column(Timestamptz, nullable=False),
    )
    resolved_at: datetime | None = Field(
        default=None,
        sa_column=Column(Timestamptz, nullable=True),
    )
