from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.audit import AuditAction, AuditService
from app.modules.exceptions.models import (
    ExceptionDomain,
    ExceptionSeverity,
    ExceptionStatus,
    OperationalException,
    RootCauseCategory,
)
from app.modules.exceptions.repository import ExceptionRepository
from app.modules.exceptions.schemas import ExceptionCreate
from app.shared.errors import BusinessRuleError, NotFoundError
from app.shared.time import utc_now

if TYPE_CHECKING:
    from app.modules.inventory import InventoryVariance
    from app.modules.reconciliation import SettlementReconciliationItem


class ExceptionService:
    """Manages the full operational exception lifecycle from detection to root cause resolution."""

    def __init__(
        self,
        session: AsyncSession,
        repository: ExceptionRepository | None = None,
        audit_service: AuditService | None = None,
    ) -> None:
        self._session = session
        self._repository = repository or ExceptionRepository(session)
        self._audit_service = audit_service or AuditService(session)

    async def create_exception(self, payload: ExceptionCreate) -> OperationalException:
        """Create or return existing active exception for the same domain and reference."""
        existing = await self._repository.get_active_by_domain_and_reference(
            payload.domain, payload.reference_id
        )
        if existing is not None:
            return existing

        now = utc_now()
        exception = OperationalException(
            domain=payload.domain,
            severity=payload.severity,
            status=ExceptionStatus.OPEN,
            reference_id=payload.reference_id,
            channel_code=payload.channel_code,
            title=payload.title,
            description=payload.description,
            variance_amount=payload.variance_amount,
            payload_snapshot=payload.payload_snapshot,
            created_at=now,
            updated_at=now,
        )
        return await self._repository.create(exception)

    async def create_from_inventory_variance(
        self, variance: InventoryVariance
    ) -> OperationalException:
        """Create operational exception from an inventory stock variance."""
        from app.modules.inventory import DiscrepancyDirection

        severity = (
            ExceptionSeverity.CRITICAL
            if variance.direction == DiscrepancyDirection.OVER_ALLOCATED
            else ExceptionSeverity.MEDIUM
        )
        title = (
            f"Stock Variance ({variance.direction}) for {variance.sku} "
            f"on {variance.channel_code}"
        )
        desc = (
            f"Channel available stock ({variance.channel_available_qty}) vs ERP physical "
            f"({variance.erp_available_qty}), variance: {variance.variance}"
        )

        return await self.create_exception(
            ExceptionCreate(
                domain=ExceptionDomain.INVENTORY_VARIANCE,
                severity=severity,
                reference_id=variance.sku,
                channel_code=variance.channel_code,
                title=title,
                description=desc,
                variance_amount=variance.variance,
                payload_snapshot=variance.model_dump(mode="json"),
            )
        )

    async def create_from_settlement_discrepancy(
        self,
        item: SettlementReconciliationItem,
        channel_code: str,
        statement_id: str,
    ) -> OperationalException:
        """Create operational exception from a settlement financial discrepancy."""
        from app.modules.reconciliation import SettlementDiscrepancyType

        severity = (
            ExceptionSeverity.CRITICAL
            if item.discrepancy_type == SettlementDiscrepancyType.GHOST_ORDER
            else ExceptionSeverity.HIGH
        )
        title = (
            f"Settlement Discrepancy ({item.discrepancy_type.value}) for order "
            f"{item.channel_order_id}"
        )

        return await self.create_exception(
            ExceptionCreate(
                domain=ExceptionDomain.SETTLEMENT_DISCREPANCY,
                severity=severity,
                reference_id=item.channel_order_id,
                channel_code=channel_code,
                title=title,
                description=item.message,
                variance_amount=item.variance,
                payload_snapshot={
                    "statement_id": statement_id,
                    **item.model_dump(mode="json"),
                },
            )
        )

    async def assign(
        self,
        exception_id: int,
        assigned_to: str,
        *,
        actor_id: str = "system",
        actor_role: str = "operations",
    ) -> OperationalException:
        """Assign an exception to an owner and advance status to INVESTIGATING if currently OPEN."""
        exception = await self.get(exception_id)
        if exception.status == ExceptionStatus.RESOLVED:
            raise BusinessRuleError(
                "CANNOT_ASSIGN_RESOLVED_EXCEPTION",
                f"Exception {exception_id} is already resolved",
            )

        before_assigned_to = exception.assigned_to
        before_status = exception.status.value

        exception.assigned_to = assigned_to
        if exception.status == ExceptionStatus.OPEN:
            exception.status = ExceptionStatus.INVESTIGATING
        exception.updated_at = utc_now()

        updated = await self._repository.update(exception)
        await self._audit_service.record_event(
            actor_id=actor_id,
            actor_role=actor_role,
            action=AuditAction.EXCEPTION_ASSIGNED,
            entity_type="operational_exception",
            entity_id=str(updated.id),
            before_state={"assigned_to": before_assigned_to, "status": before_status},
            after_state={"assigned_to": updated.assigned_to, "status": updated.status.value},
            reason=f"Assigned to {assigned_to}",
        )
        return updated

    async def resolve(
        self,
        exception_id: int,
        *,
        root_cause: RootCauseCategory,
        resolution_notes: str,
        actor_id: str = "system",
        actor_role: str = "operations",
    ) -> OperationalException:
        """Advance exception to RESOLVED with audited root cause and remediation notes."""
        exception = await self.get(exception_id)
        if exception.status == ExceptionStatus.RESOLVED:
            return exception

        before_status = exception.status.value
        now = utc_now()
        exception.status = ExceptionStatus.RESOLVED
        exception.root_cause = root_cause
        exception.resolution_notes = resolution_notes
        exception.resolved_at = now
        exception.updated_at = now

        updated = await self._repository.update(exception)
        await self._audit_service.record_event(
            actor_id=actor_id,
            actor_role=actor_role,
            action=AuditAction.EXCEPTION_RESOLVED,
            entity_type="operational_exception",
            entity_id=str(updated.id),
            before_state={"status": before_status},
            after_state={
                "status": updated.status.value,
                "root_cause": root_cause.value,
                "resolution_notes": resolution_notes,
            },
            reason=resolution_notes,
        )
        return updated

    async def ignore(
        self,
        exception_id: int,
        reason: str,
        *,
        actor_id: str = "system",
        actor_role: str = "operations",
    ) -> OperationalException:
        """Mark exception as IGNORED (e.g. recognized false positive)."""
        exception = await self.get(exception_id)
        before_status = exception.status.value
        now = utc_now()
        exception.status = ExceptionStatus.IGNORED
        exception.resolution_notes = f"IGNORED: {reason}"
        exception.resolved_at = now
        exception.updated_at = now

        updated = await self._repository.update(exception)
        await self._audit_service.record_event(
            actor_id=actor_id,
            actor_role=actor_role,
            action=AuditAction.EXCEPTION_STATUS_CHANGED,
            entity_type="operational_exception",
            entity_id=str(updated.id),
            before_state={"status": before_status},
            after_state={"status": updated.status.value},
            reason=reason,
        )
        return updated

    async def get(self, exception_id: int) -> OperationalException:
        """Retrieve an operational exception by ID or raise NotFoundError."""
        exception = await self._repository.get_by_id(exception_id)
        if exception is None:
            raise NotFoundError(
                "EXCEPTION_NOT_FOUND",
                f"Operational exception with ID {exception_id} does not exist",
                details={"exception_id": exception_id},
            )
        return exception

    async def list_exceptions(
        self,
        *,
        status: ExceptionStatus | None = None,
        domain: ExceptionDomain | None = None,
        severity: ExceptionSeverity | None = None,
        channel_code: str | None = None,
        limit: int = 100,
    ) -> list[OperationalException]:
        return await self._repository.list_filtered(
            status=status,
            domain=domain,
            severity=severity,
            channel_code=channel_code,
            limit=limit,
        )
