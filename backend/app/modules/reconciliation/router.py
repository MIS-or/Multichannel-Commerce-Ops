from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.modules.alerts import AlertService, get_alert_service
from app.modules.audit import AuditAction, AuditService
from app.modules.auth import Permission, UserContext, require_permission
from app.modules.channels import ChannelService, get_channel_service
from app.modules.ledger import LedgerService, get_ledger_service
from app.modules.orders.router import get_order_service
from app.modules.orders.service import OrderService
from app.modules.reconciliation.repository import ReconciliationRepository
from app.modules.reconciliation.schemas import ReconciliationRead, ReconciliationRequest
from app.modules.reconciliation.service import ReconciliationService

router = APIRouter(prefix="/reconciliations", tags=["reconciliation"])


def get_reconciliation_repository(
    session: AsyncSession = Depends(get_session),
) -> ReconciliationRepository:
    return ReconciliationRepository(session)


def get_reconciliation_service(
    session: AsyncSession = Depends(get_session),
    repository: ReconciliationRepository = Depends(get_reconciliation_repository),
    channel_service: ChannelService = Depends(get_channel_service),
    order_service: OrderService = Depends(get_order_service),
    ledger_service: LedgerService = Depends(get_ledger_service),
    alert_service: AlertService = Depends(get_alert_service),
) -> ReconciliationService:
    return ReconciliationService(
        session=session,
        repository=repository,
        channel_service=channel_service,
        order_service=order_service,
        ledger_service=ledger_service,
        alert_service=alert_service,
    )


@router.post("", response_model=ReconciliationRead, status_code=status.HTTP_201_CREATED)
async def run_reconciliation(
    payload: ReconciliationRequest,
    service: Annotated[ReconciliationService, Depends(get_reconciliation_service)],
    user: Annotated[UserContext, Depends(require_permission(Permission.RECONCILIATION_WRITE))],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> ReconciliationRead:
    result = await service.reconcile(payload)
    audit = AuditService(session)
    await audit.record_event(
        actor_id=user.user_id,
        actor_role=user.role.value,
        action=AuditAction.RECONCILIATION_RUN,
        entity_type="reconciliation_run",
        entity_id=str(result.id),
        after_state=result.model_dump(mode="json"),
        reason=f"Triggered reconciliation for source {result.source_system}",
    )
    return result



@router.get("", response_model=list[ReconciliationRead])
async def list_reconciliations(
    service: Annotated[ReconciliationService, Depends(get_reconciliation_service)],
    _user: Annotated[UserContext, Depends(require_permission(Permission.RECONCILIATION_READ))],
) -> list[ReconciliationRead]:
    return await service.list_history()


@router.get("/{reconciliation_id}", response_model=ReconciliationRead)
async def get_reconciliation(
    reconciliation_id: int,
    service: Annotated[ReconciliationService, Depends(get_reconciliation_service)],
    _user: Annotated[UserContext, Depends(require_permission(Permission.RECONCILIATION_READ))],
) -> ReconciliationRead:
    return await service.get(reconciliation_id)
