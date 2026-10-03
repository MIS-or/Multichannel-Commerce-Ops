from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.modules.alerts import AlertService, get_alert_service
from app.modules.audit import AuditAction, AuditService
from app.modules.auth import Permission, UserContext, require_permission
from app.modules.exceptions import ExceptionService, get_exception_service
from app.modules.rules.repository import RuleRepository
from app.modules.rules.schemas import (
    RuleCreate,
    RuleEvaluateRequest,
    RuleEvaluateResponse,
    RuleExecutionLogRead,
    RuleRead,
    RuleUpdate,
)
from app.modules.rules.service import RuleEngineService

router = APIRouter(prefix="/rules", tags=["rules"])


async def get_rule_service(
    session: Annotated[AsyncSession, Depends(get_session)],
    alert_service: Annotated[AlertService, Depends(get_alert_service)],
    exception_service: Annotated[ExceptionService, Depends(get_exception_service)],
) -> RuleEngineService:
    repo = RuleRepository(session)
    return RuleEngineService(
        session=session,
        repository=repo,
        alert_service=alert_service,
        exception_service=exception_service,
    )


@router.post("", response_model=RuleRead, status_code=status.HTTP_201_CREATED)
async def create_rule(
    payload: RuleCreate,
    service: Annotated[RuleEngineService, Depends(get_rule_service)],
    user: Annotated[UserContext, Depends(require_permission(Permission.RULES_WRITE))],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> RuleRead:
    rule = await service.create_rule(payload)
    audit = AuditService(session)
    await audit.record_event(
        actor_id=user.user_id,
        actor_role=user.role.value,
        action=AuditAction.RULE_CREATED,
        entity_type="automation_rule",
        entity_id=str(rule.id),
        after_state=rule.model_dump(mode="json"),
        reason=f"Created automation rule: {rule.name}",
    )
    return rule


@router.get("", response_model=list[RuleRead])
async def list_rules(
    service: Annotated[RuleEngineService, Depends(get_rule_service)],
    _user: Annotated[UserContext, Depends(require_permission(Permission.RULES_READ))],
    active_only: bool = Query(default=False),
) -> list[RuleRead]:
    return await service.list_rules(active_only=active_only)


@router.get("/logs", response_model=list[RuleExecutionLogRead])
async def list_all_rule_logs(
    service: Annotated[RuleEngineService, Depends(get_rule_service)],
    _user: Annotated[UserContext, Depends(require_permission(Permission.RULES_READ))],
    rule_id: int | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=500),
) -> list[RuleExecutionLogRead]:
    return await service.list_logs(rule_id=rule_id, limit=limit)


@router.get("/{rule_id}", response_model=RuleRead)
async def get_rule(
    rule_id: int,
    service: Annotated[RuleEngineService, Depends(get_rule_service)],
    _user: Annotated[UserContext, Depends(require_permission(Permission.RULES_READ))],
) -> RuleRead:
    return await service.get_rule(rule_id)


@router.patch("/{rule_id}", response_model=RuleRead)
async def update_rule(
    rule_id: int,
    payload: RuleUpdate,
    service: Annotated[RuleEngineService, Depends(get_rule_service)],
    user: Annotated[UserContext, Depends(require_permission(Permission.RULES_WRITE))],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> RuleRead:
    existing = await service.get_rule(rule_id)
    before_state = existing.model_dump(mode="json")
    updated = await service.update_rule(rule_id, payload)
    audit = AuditService(session)
    await audit.record_event(
        actor_id=user.user_id,
        actor_role=user.role.value,
        action=AuditAction.RULE_TOGGLED if payload.is_active is not None else "rule.updated",
        entity_type="automation_rule",
        entity_id=str(updated.id),
        before_state=before_state,
        after_state=updated.model_dump(mode="json"),
        reason=f"Updated rule {updated.name}",
    )
    return updated



@router.delete("/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_rule(
    rule_id: int,
    service: Annotated[RuleEngineService, Depends(get_rule_service)],
    _user: Annotated[UserContext, Depends(require_permission(Permission.RULES_WRITE))],
) -> None:
    await service.delete_rule(rule_id)


@router.get("/{rule_id}/logs", response_model=list[RuleExecutionLogRead])
async def list_rule_logs(
    rule_id: int,
    service: Annotated[RuleEngineService, Depends(get_rule_service)],
    _user: Annotated[UserContext, Depends(require_permission(Permission.RULES_READ))],
    limit: int = Query(default=50, ge=1, le=500),
) -> list[RuleExecutionLogRead]:
    return await service.list_logs(rule_id=rule_id, limit=limit)


@router.post("/evaluate", response_model=RuleEvaluateResponse)
async def evaluate_rules(
    payload: RuleEvaluateRequest,
    service: Annotated[RuleEngineService, Depends(get_rule_service)],
    _user: Annotated[UserContext, Depends(require_permission(Permission.RULES_WRITE))],
) -> RuleEvaluateResponse:
    logs = await service.evaluate_trigger(payload.trigger_event, payload.context)
    matched_count = sum(1 for log in logs if log.matched)
    return RuleEvaluateResponse(
        evaluated_count=len(logs),
        matched_count=matched_count,
        logs=logs,
    )
