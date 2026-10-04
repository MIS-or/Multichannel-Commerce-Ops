from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.modules.rules.models import (
    ActionType,
    RuleCondition,
    RuleExecutionStatus,
    TriggerEvent,
)


class RuleActionSchema(BaseModel):
    action_type: ActionType
    parameters: dict[str, Any] = Field(default_factory=dict)


class RuleCreate(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    description: str | None = Field(default=None, max_length=500)
    trigger_event: TriggerEvent
    conditions: list[RuleCondition] = Field(default_factory=list)
    actions: list[dict[str, Any]] = Field(default_factory=list)
    is_active: bool = True
    priority: int = Field(default=10, ge=1, le=1000)


class RuleUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=150)
    description: str | None = Field(default=None, max_length=500)
    conditions: list[RuleCondition] | None = None
    actions: list[dict[str, Any]] | None = None
    is_active: bool | None = None
    priority: int | None = Field(default=None, ge=1, le=1000)


class RuleRead(BaseModel):
    id: int
    name: str
    description: str | None = None
    trigger_event: TriggerEvent
    conditions: list[dict[str, Any]]
    actions: list[dict[str, Any]]
    is_active: bool
    priority: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RuleExecutionLogRead(BaseModel):
    id: int
    rule_id: int
    trigger_event: TriggerEvent
    matched: bool
    status: RuleExecutionStatus
    payload_snapshot: dict[str, Any]
    actions_taken: list[dict[str, Any]]
    error_message: str | None = None
    executed_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RuleEvaluateRequest(BaseModel):
    trigger_event: TriggerEvent
    context: dict[str, Any]


class RuleEvaluateResponse(BaseModel):
    evaluated_count: int
    matched_count: int
    logs: list[RuleExecutionLogRead]
