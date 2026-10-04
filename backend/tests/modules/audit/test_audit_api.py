from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from app.database import get_session
from app.main import app
from app.modules.audit import AuditAction, AuditService
from app.modules.auth import (
    ROLE_PERMISSIONS,
    UserContext,
    UserRole,
    get_current_user,
)


@pytest.mark.asyncio
async def test_audit_logs_api_requires_permission(session) -> None:
    # 1. Override dependencies
    app.dependency_overrides[get_session] = lambda: session

    viewer_user = UserContext(
        user_id="usr_v1",
        email="viewer@mco.internal",
        full_name="Viewer",
        role=UserRole.VIEWER,
        permissions=ROLE_PERMISSIONS[UserRole.VIEWER],
    )
    app.dependency_overrides[get_current_user] = lambda: viewer_user

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://testserver"
    ) as client:
        # Viewer does not have AUDIT_READ permission
        resp = await client.get("/api/v1/audit-logs")
        assert resp.status_code == 403
        assert resp.json()["error"]["code"] == "FORBIDDEN_INSUFFICIENT_PERMISSION"

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_audit_logs_api_list_and_filter(session) -> None:
    # 1. Seed audit logs
    audit_service = AuditService(session)
    await audit_service.record_event(
        actor_id="usr_admin",
        actor_role="admin",
        action=AuditAction.SYNC_TRIGGERED,
        entity_type="sync_run",
        entity_id="10",
        reason="Manual sync test",
    )
    await audit_service.record_event(
        actor_id="usr_ops",
        actor_role="operations",
        action=AuditAction.EXCEPTION_RESOLVED,
        entity_type="operational_exception",
        entity_id="25",
        reason="Resolved inventory gap",
    )

    # 2. Authenticate as Admin
    app.dependency_overrides[get_session] = lambda: session
    admin_user = UserContext(
        user_id="usr_admin",
        email="admin@mco.internal",
        full_name="Admin",
        role=UserRole.ADMIN,
        permissions=ROLE_PERMISSIONS[UserRole.ADMIN],
    )
    app.dependency_overrides[get_current_user] = lambda: admin_user

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://testserver"
    ) as client:
        # 3. List all
        resp = await client.get("/api/v1/audit-logs")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2

        # 4. Filter by entity_type
        resp_filtered = await client.get("/api/v1/audit-logs?entity_type=sync_run")
        assert resp_filtered.status_code == 200
        filtered_data = resp_filtered.json()
        assert len(filtered_data) == 1
        assert filtered_data[0]["action"] == AuditAction.SYNC_TRIGGERED.value
        assert filtered_data[0]["actor_id"] == "usr_admin"

        # 5. Count endpoint
        resp_count = await client.get("/api/v1/audit-logs/count")
        assert resp_count.status_code == 200
        assert resp_count.json()["count"] == 2

    app.dependency_overrides.clear()
