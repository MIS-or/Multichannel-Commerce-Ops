from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.audit import AuditAction, AuditService
from app.modules.exceptions import (
    ExceptionCreate,
    ExceptionDomain,
    ExceptionService,
    ExceptionSeverity,
    RootCauseCategory,
)


@pytest.mark.asyncio
async def test_audit_service_record_and_list(session: AsyncSession) -> None:
    audit_service = AuditService(session)

    log1 = await audit_service.record_event(
        actor_id="usr_admin_1",
        actor_role="admin",
        action=AuditAction.RULE_CREATED,
        entity_type="automation_rule",
        entity_id="1",
        after_state={"name": "Auto Assign High Severity", "is_active": True},
        reason="Initial setup",
    )
    assert log1.id is not None
    assert log1.actor_id == "usr_admin_1"
    assert log1.action == AuditAction.RULE_CREATED.value

    log2 = await audit_service.record_event(
        actor_id="usr_ops_2",
        actor_role="operations",
        action=AuditAction.EXCEPTION_ASSIGNED,
        entity_type="operational_exception",
        entity_id="101",
        before_state={"assigned_to": None},
        after_state={"assigned_to": "alice"},
        reason="Assigned to specialist",
    )
    assert log2.id is not None
    assert log2.action == AuditAction.EXCEPTION_ASSIGNED.value

    # List all logs
    all_logs = await audit_service.list_logs()
    assert len(all_logs) == 2
    assert all_logs[0].id == log2.id  # Newest first

    # Filter by action
    rule_logs = await audit_service.list_logs(action=AuditAction.RULE_CREATED.value)
    assert len(rule_logs) == 1
    assert rule_logs[0].entity_id == "1"

    # Filter by entity_type
    exc_logs = await audit_service.list_logs(entity_type="operational_exception")
    assert len(exc_logs) == 1
    assert exc_logs[0].actor_id == "usr_ops_2"

    # Count logs
    total = await audit_service.count_logs()
    assert total == 2


@pytest.mark.asyncio
async def test_exception_lifecycle_records_audit_trail(session: AsyncSession) -> None:
    audit_service = AuditService(session)
    exc_service = ExceptionService(session=session, audit_service=audit_service)

    # 1. Create exception
    exc = await exc_service.create_exception(
        ExceptionCreate(
            domain=ExceptionDomain.INVENTORY_VARIANCE,
            severity=ExceptionSeverity.HIGH,
            reference_id="SKU-AUDIT-01",
            channel_code="shopee",
            title="Variance on SKU-AUDIT-01",
            description="Test audit trail",
        )
    )
    assert exc.id is not None

    # 2. Assign
    assigned = await exc_service.assign(
        exc.id,
        "bob_warehouse",
        actor_id="usr_lead_01",
        actor_role="operations",
    )
    assert assigned.assigned_to == "bob_warehouse"

    # 3. Resolve
    resolved = await exc_service.resolve(
        exc.id,
        root_cause=RootCauseCategory.PHYSICAL_INVENTORY_SHRINKAGE,
        resolution_notes="Found damaged items in aisle 4",
        actor_id="usr_bob_02",
        actor_role="operations",
    )
    assert resolved.status.value == "resolved"

    # 4. Check audit logs
    logs = await audit_service.list_logs(
        entity_type="operational_exception",
        entity_id=str(exc.id),
    )
    assert len(logs) == 2  # assign and resolve
    actions = [entry.action for entry in logs]
    assert AuditAction.EXCEPTION_RESOLVED.value in actions
    assert AuditAction.EXCEPTION_ASSIGNED.value in actions

    resolve_log = next(
        entry for entry in logs if entry.action == AuditAction.EXCEPTION_RESOLVED.value
    )
    assert resolve_log.actor_id == "usr_bob_02"
    assert resolve_log.after_state is not None
    assert (
        resolve_log.after_state["root_cause"]
        == RootCauseCategory.PHYSICAL_INVENTORY_SHRINKAGE.value
    )
    assert resolve_log.reason == "Found damaged items in aisle 4"

