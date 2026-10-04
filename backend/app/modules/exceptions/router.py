from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.modules.auth import Permission, UserContext, require_permission
from app.modules.exceptions.models import (
    ExceptionDomain,
    ExceptionSeverity,
    ExceptionStatus,
)
from app.modules.exceptions.schemas import (
    ExceptionAssign,
    ExceptionCreate,
    ExceptionIgnore,
    ExceptionRead,
    ExceptionResolve,
)
from app.modules.exceptions.service import ExceptionService

router = APIRouter(prefix="/exceptions", tags=["exceptions"])


async def get_exception_service(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> ExceptionService:
    return ExceptionService(session)


@router.post("", response_model=ExceptionRead, status_code=status.HTTP_201_CREATED)
async def create_exception(
    payload: ExceptionCreate,
    service: Annotated[ExceptionService, Depends(get_exception_service)],
    _user: Annotated[UserContext, Depends(require_permission(Permission.EXCEPTIONS_WRITE))],
) -> ExceptionRead:
    exception = await service.create_exception(payload)
    return ExceptionRead.model_validate(exception)


@router.get("", response_model=list[ExceptionRead])
async def list_exceptions(
    service: Annotated[ExceptionService, Depends(get_exception_service)],
    _user: Annotated[UserContext, Depends(require_permission(Permission.EXCEPTIONS_READ))],
    status: ExceptionStatus | None = Query(default=None),
    domain: ExceptionDomain | None = Query(default=None),
    severity: ExceptionSeverity | None = Query(default=None),
    channel_code: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
) -> list[ExceptionRead]:
    exceptions = await service.list_exceptions(
        status=status,
        domain=domain,
        severity=severity,
        channel_code=channel_code,
        limit=limit,
    )
    return [ExceptionRead.model_validate(e) for e in exceptions]


@router.get("/{exception_id}", response_model=ExceptionRead)
async def get_exception(
    exception_id: int,
    service: Annotated[ExceptionService, Depends(get_exception_service)],
    _user: Annotated[UserContext, Depends(require_permission(Permission.EXCEPTIONS_READ))],
) -> ExceptionRead:
    exception = await service.get(exception_id)
    return ExceptionRead.model_validate(exception)


@router.post("/{exception_id}/assign", response_model=ExceptionRead)
async def assign_exception(
    exception_id: int,
    payload: ExceptionAssign,
    service: Annotated[ExceptionService, Depends(get_exception_service)],
    user: Annotated[UserContext, Depends(require_permission(Permission.EXCEPTIONS_WRITE))],
) -> ExceptionRead:
    exception = await service.assign(
        exception_id,
        payload.assigned_to,
        actor_id=user.user_id,
        actor_role=user.role.value,
    )
    return ExceptionRead.model_validate(exception)


@router.post("/{exception_id}/resolve", response_model=ExceptionRead)
async def resolve_exception(
    exception_id: int,
    payload: ExceptionResolve,
    service: Annotated[ExceptionService, Depends(get_exception_service)],
    user: Annotated[UserContext, Depends(require_permission(Permission.EXCEPTIONS_WRITE))],
) -> ExceptionRead:
    exception = await service.resolve(
        exception_id,
        root_cause=payload.root_cause,
        resolution_notes=payload.resolution_notes,
        actor_id=user.user_id,
        actor_role=user.role.value,
    )
    return ExceptionRead.model_validate(exception)


@router.post("/{exception_id}/ignore", response_model=ExceptionRead)
async def ignore_exception(
    exception_id: int,
    payload: ExceptionIgnore,
    service: Annotated[ExceptionService, Depends(get_exception_service)],
    user: Annotated[UserContext, Depends(require_permission(Permission.EXCEPTIONS_WRITE))],
) -> ExceptionRead:
    exception = await service.ignore(
        exception_id,
        payload.reason,
        actor_id=user.user_id,
        actor_role=user.role.value,
    )
    return ExceptionRead.model_validate(exception)

