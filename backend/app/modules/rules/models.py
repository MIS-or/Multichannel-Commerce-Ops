from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel
from sqlalchemy import JSON, Column, Index, String, Text
from sqlalchemy import Enum as SAEnum
from sqlmodel import Field, SQLModel

from app.shared.time import Timestamptz, utc_now


class TriggerEvent(StrEnum):
    INVENTORY_VARIANCE_DETECTED = "inventory_variance_detected"
    SETTLEMENT_DISCREPANCY_DETECTED = "settlement_discrepancy_detected"
    EXCEPTION_CREATED = "exception_created"
    ORDER_INGESTED = "order_ingested"


class ActionType(StrEnum):
    CREATE_EXCEPTION = "create_exception"
    CREATE_ALERT = "create_alert"
    TRIGGER_WEBHOOK = "trigger_webhook"
    AUTO_ASSIGN_EXCEPTION = "auto_assign_exception"


class ConditionOperator(StrEnum):
    EQUALS = "equals"
    NOT_EQUALS = "not_equals"
    GREATER_THAN = "greater_than"
    GREATER_THAN_OR_EQUAL = "greater_than_or_equal"
    LESS_THAN = "less_than"
    LESS_THAN_OR_EQUAL = "less_than_or_equal"
    CONTAINS = "contains"
    IN = "in"


class RuleExecutionStatus(StrEnum):
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"


class RuleCondition(BaseModel):
    field: str
    operator: ConditionOperator
    value: Any


class Rule(SQLModel, table=True):
    """Declarative automation rule defining triggers, conditions, and actions."""

    __tablename__ = "automation_rules"
    __table_args__ = (
        Index("ix_rules_trigger_active_priority", "trigger_event", "is_active", "priority"),
        Index("ix_rules_created_at", "created_at"),
    )

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(sa_column=Column(String(150), nullable=False))
    description: str | None = Field(default=None, sa_column=Column(String(500), nullable=True))
    trigger_event: TriggerEvent = Field(
        sa_column=Column(
            SAEnum(TriggerEvent, native_enum=False, length=50),
            nullable=False,
            index=True,
        )
    )
    conditions: list[dict[str, Any]] = Field(
        default_factory=list,
        sa_column=Column(JSON, nullable=False),
    )
    actions: list[dict[str, Any]] = Field(
        default_factory=list,
        sa_column=Column(JSON, nullable=False),
    )
    is_active: bool = Field(default=True, nullable=False, index=True)
    priority: int = Field(default=10, nullable=False, index=True)
    created_at: datetime = Field(
        default_factory=utc_now,
        sa_column=Column(Timestamptz, nullable=False),
    )
    updated_at: datetime = Field(
        default_factory=utc_now,
        sa_column=Column(Timestamptz, nullable=False),
    )


class RuleExecutionLog(SQLModel, table=True):
    """Audit log tracking rule trigger evaluation and action dispatch outcomes."""

    __tablename__ = "automation_rule_executions"
    __table_args__ = (
        Index("ix_rule_executions_rule_status", "rule_id", "status"),
        Index("ix_rule_executions_executed_at", "executed_at"),
    )

    id: int | None = Field(default=None, primary_key=True)
    rule_id: int = Field(foreign_key="automation_rules.id", nullable=False, index=True)
    trigger_event: TriggerEvent = Field(
        sa_column=Column(
            SAEnum(TriggerEvent, native_enum=False, length=50),
            nullable=False,
        )
    )
    matched: bool = Field(nullable=False)
    status: RuleExecutionStatus = Field(
        sa_column=Column(
            SAEnum(RuleExecutionStatus, native_enum=False, length=20),
            nullable=False,
        )
    )
    payload_snapshot: dict[str, Any] = Field(
        default_factory=dict,
        sa_column=Column(JSON, nullable=False),
    )
    actions_taken: list[dict[str, Any]] = Field(
        default_factory=list,
        sa_column=Column(JSON, nullable=False),
    )
    error_message: str | None = Field(
        default=None,
        sa_column=Column(Text, nullable=True),
    )
    executed_at: datetime = Field(
        default_factory=utc_now,
        sa_column=Column(Timestamptz, nullable=False, index=True),
    )
