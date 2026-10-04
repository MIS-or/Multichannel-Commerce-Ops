from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.modules.audit.models import AuditAction


class AuditLogRead(BaseModel):
    id: int
    actor_id: str
    actor_role: str
    action: str
    entity_type: str
    entity_id: str
    before_state: dict[str, Any] | None = None
    after_state: dict[str, Any] | None = None
    reason: str | None = None
    ip_address: str | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AuditLogFilter(BaseModel):
    actor_id: str | None = None
    action: str | None = None
    entity_type: str | None = None
    entity_id: str | None = None
    limit: int = Field(default=50, ge=1, le=200)
    offset: int = Field(default=0, ge=0)


class AuditLogCreate(BaseModel):
    actor_id: str
    actor_role: str
    action: AuditAction | str
    entity_type: str
    entity_id: str
    before_state: dict[str, Any] | None = None
    after_state: dict[str, Any] | None = None
    reason: str | None = None
    ip_address: str | None = None
