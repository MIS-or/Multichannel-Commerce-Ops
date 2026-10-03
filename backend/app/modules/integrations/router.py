from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.modules.audit import AuditAction, AuditService
from app.modules.auth import Permission, UserContext, require_permission
from app.modules.integrations.models import SyncType
from app.modules.integrations.repository import SyncRunRepository
from app.modules.integrations.schemas import (
    IntegrationHealthResponse,
    SyncRunRead,
    SyncTriggerRequest,
    SyncTriggerResponse,
)
from app.modules.integrations.service import SyncManagerService

router = APIRouter(prefix="/integrations", tags=["integrations"])


async def get_sync_service(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> SyncManagerService:
    repo = SyncRunRepository(session)
    return SyncManagerService(session=session, repository=repo)


@router.post(
    "/{channel_code}/sync",
    response_model=SyncTriggerResponse,
    status_code=status.HTTP_200_OK,
)
async def trigger_sync(
    channel_code: str,
    payload: SyncTriggerRequest,
    service: Annotated[SyncManagerService, Depends(get_sync_service)],
    user: Annotated[UserContext, Depends(require_permission(Permission.INTEGRATIONS_WRITE))],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> SyncTriggerResponse:
    run = await service.execute_sync(
        channel_code=channel_code,
        sync_type=payload.sync_type,
        cursor=payload.cursor,
        max_retries=payload.max_retries,
    )
    audit_service = AuditService(session)
    await audit_service.record_event(
        actor_id=user.user_id,
        actor_role=user.role.value,
        action=AuditAction.SYNC_TRIGGERED,
        entity_type="sync_run",
        entity_id=str(run.id),
        after_state={
            "channel_code": channel_code,
            "sync_type": payload.sync_type.value,
            "status": run.status.value,
            "records_processed": run.records_processed,
            "records_failed": run.records_failed,
        },
        reason=f"Manual sync triggered for {channel_code}",
    )
    return SyncTriggerResponse(
        sync_run=run,
        message=f"Sync {payload.sync_type} completed for {channel_code} with status {run.status}",
    )



@router.get("/sync-runs", response_model=list[SyncRunRead])
async def list_sync_runs(
    service: Annotated[SyncManagerService, Depends(get_sync_service)],
    _user: Annotated[UserContext, Depends(require_permission(Permission.INTEGRATIONS_READ))],
    channel_code: str | None = Query(default=None),
    sync_type: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=500),
) -> list[SyncRunRead]:
    resolved_sync_type: SyncType | None = None
    if sync_type:
        st_clean = sync_type.lower().strip()
        if st_clean in ("settlement", "settlements"):
            resolved_sync_type = SyncType.SETTLEMENT
        elif st_clean == "orders":
            resolved_sync_type = SyncType.ORDERS
        elif st_clean == "inventory":
            resolved_sync_type = SyncType.INVENTORY

    return await service.list_sync_runs(
        channel_code=channel_code,
        sync_type=resolved_sync_type,
        limit=limit,
    )


@router.get("/health", response_model=IntegrationHealthResponse)
async def get_integrations_health(
    service: Annotated[SyncManagerService, Depends(get_sync_service)],
    _user: Annotated[UserContext, Depends(require_permission(Permission.INTEGRATIONS_READ))],
) -> IntegrationHealthResponse:
    health_list = await service.check_all_health()
    healthy_count = sum(1 for h in health_list if h.is_healthy)
    return IntegrationHealthResponse(
        connectors=health_list,
        healthy_count=healthy_count,
        total_count=len(health_list),
    )
