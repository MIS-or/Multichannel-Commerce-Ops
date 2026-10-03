from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.modules.audit.schemas import AuditLogRead
from app.modules.audit.service import AuditService
from app.modules.auth import Permission, UserContext, require_permission

router = APIRouter(prefix="/audit-logs", tags=["audit"])


async def get_audit_service(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> AuditService:
    return AuditService(session)


@router.get("", response_model=list[AuditLogRead])
async def list_audit_logs(
    service: Annotated[AuditService, Depends(get_audit_service)],
    _user: Annotated[UserContext, Depends(require_permission(Permission.AUDIT_READ))],
    actor_id: str | None = Query(default=None),
    action: str | None = Query(default=None),
    entity_type: str | None = Query(default=None),
    entity_id: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> list[AuditLogRead]:
    logs = await service.list_logs(
        actor_id=actor_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        limit=limit,
        offset=offset,
    )
    return [AuditLogRead.model_validate(log) for log in logs]


@router.get("/count", response_model=dict[str, int])
async def count_audit_logs(
    service: Annotated[AuditService, Depends(get_audit_service)],
    _user: Annotated[UserContext, Depends(require_permission(Permission.AUDIT_READ))],
    actor_id: str | None = Query(default=None),
    action: str | None = Query(default=None),
    entity_type: str | None = Query(default=None),
    entity_id: str | None = Query(default=None),
) -> dict[str, int]:
    count = await service.count_logs(
        actor_id=actor_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
    )
    return {"count": count}
