from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.modules.auth import (
    ALL_PERMISSIONS,
    ROLE_PERMISSIONS,
    Permission,
    UnauthorizedError,
    UserContext,
    UserRole,
    get_current_user,
    get_strict_user,
)


def test_role_permissions_matrix() -> None:
    # 1. Admin has every permission
    admin_perms = ROLE_PERMISSIONS[UserRole.ADMIN]
    assert admin_perms == ALL_PERMISSIONS
    assert Permission.INTEGRATIONS_WRITE in admin_perms
    assert Permission.RULES_WRITE in admin_perms

    # 2. Operations has operational read/writes
    ops_perms = ROLE_PERMISSIONS[UserRole.OPERATIONS]
    assert Permission.INTEGRATIONS_WRITE in ops_perms
    assert Permission.EXCEPTIONS_WRITE in ops_perms
    assert Permission.INVENTORY_WRITE in ops_perms
    assert Permission.RECONCILIATION_WRITE in ops_perms

    # 3. Finance has financial perms but NOT integrations write or rules write
    fin_perms = ROLE_PERMISSIONS[UserRole.FINANCE]
    assert Permission.RECONCILIATION_WRITE in fin_perms
    assert Permission.EXCEPTIONS_WRITE in fin_perms
    assert Permission.REPORTS_READ in fin_perms
    assert Permission.INTEGRATIONS_WRITE not in fin_perms
    assert Permission.RULES_WRITE not in fin_perms

    # 4. Viewer has read-only perms, zero write perms
    viewer_perms = ROLE_PERMISSIONS[UserRole.VIEWER]
    assert Permission.REPORTS_READ in viewer_perms
    assert Permission.EXCEPTIONS_READ in viewer_perms
    assert Permission.INTEGRATIONS_READ in viewer_perms
    assert Permission.EXCEPTIONS_WRITE not in viewer_perms
    assert Permission.INTEGRATIONS_WRITE not in viewer_perms
    assert Permission.RECONCILIATION_WRITE not in viewer_perms
    assert Permission.RULES_WRITE not in viewer_perms


def test_user_context_evaluation() -> None:
    viewer = UserContext(
        user_id="usr_v",
        email="viewer@mco.internal",
        full_name="Viewer User",
        role=UserRole.VIEWER,
        permissions=ROLE_PERMISSIONS[UserRole.VIEWER],
    )
    assert viewer.has_permission(Permission.REPORTS_READ) is True
    assert viewer.has_permission(Permission.EXCEPTIONS_WRITE) is False
    assert viewer.has_role(UserRole.VIEWER) is True
    assert viewer.has_role(UserRole.ADMIN) is False

    admin = UserContext(
        user_id="usr_a",
        email="admin@mco.internal",
        full_name="Admin User",
        role=UserRole.ADMIN,
        permissions=ROLE_PERMISSIONS[UserRole.ADMIN],
    )
    # Admin has all permissions and satisfies any role requirement
    assert admin.has_permission(Permission.RULES_WRITE) is True
    assert admin.has_role(UserRole.FINANCE) is True
    assert admin.has_role(UserRole.OPERATIONS) is True


@pytest.mark.asyncio
async def test_get_current_user_resolution() -> None:
    # Header: X-User-Role
    user = await get_current_user(x_user_role="finance")
    assert user.role == UserRole.FINANCE
    assert user.has_permission(Permission.RECONCILIATION_WRITE) is True

    # Header: X-API-Key
    key_user = await get_current_user(x_api_key="mco-operations-key-dev")
    assert key_user.role == UserRole.OPERATIONS
    assert key_user.has_permission(Permission.INTEGRATIONS_WRITE) is True

    # Header: Bearer token
    bearer_user = await get_current_user(authorization="Bearer viewer")
    assert bearer_user.role == UserRole.VIEWER

    # Fallback to system default when no headers provided
    default_user = await get_current_user()
    assert default_user.role == UserRole.ADMIN

    # Invalid header values raise UnauthorizedError
    with pytest.raises(UnauthorizedError):
        await get_current_user(x_user_role="invalid_role")

    with pytest.raises(UnauthorizedError):
        await get_current_user(x_api_key="invalid_key")

    with pytest.raises(UnauthorizedError):
        await get_current_user(authorization="Bearer non_existent")


@pytest.mark.asyncio
async def test_get_strict_user_requires_credentials() -> None:
    with pytest.raises(UnauthorizedError):
        await get_strict_user()

    valid_user = await get_strict_user(x_user_role="operations")
    assert valid_user.role == UserRole.OPERATIONS


@pytest.mark.asyncio
async def test_api_endpoint_rbac_enforcement() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # 1. Viewer can read integrations health
        res = await ac.get("/api/v1/integrations/health", headers={"X-User-Role": "viewer"})
        assert res.status_code == 200

        # 2. Viewer CANNOT trigger integration sync -> 403 Forbidden
        res = await ac.post(
            "/api/v1/integrations/shopee_vn/sync",
            headers={"X-User-Role": "viewer"},
            json={"sync_type": "orders"},
        )
        assert res.status_code == 403
        data = res.json()
        assert data["error"]["code"] == "FORBIDDEN_INSUFFICIENT_PERMISSION"

        # 3. Finance CANNOT trigger integration sync -> 403 Forbidden
        res = await ac.post(
            "/api/v1/integrations/shopee_vn/sync",
            headers={"X-User-Role": "finance"},
            json={"sync_type": "orders"},
        )
        assert res.status_code == 403

        # 4. Viewer CANNOT create a rule -> 403 Forbidden
        res = await ac.post(
            "/api/v1/rules",
            headers={"X-User-Role": "viewer"},
            json={
                "name": "Test Rule",
                "trigger_event": "inventory_variance_detected",
                "conditions": [],
                "actions": [],
            },
        )
        assert res.status_code == 403

        # 5. Viewer CANNOT resolve an exception -> 403 Forbidden
        res = await ac.post(
            "/api/v1/exceptions/999999/resolve",
            headers={"X-User-Role": "viewer"},
            json={"resolution_notes": "test"},
        )
        assert res.status_code == 403

        # 6. Operations CAN manage exceptions
        # (returns 404 because ID 999999 not found, but NOT 403 Forbidden)
        res = await ac.post(
            "/api/v1/exceptions/999999/resolve",
            headers={"X-User-Role": "operations"},
            json={
                "root_cause": "operator_data_entry_error",
                "resolution_notes": "Resolved discrepancy manually",
            },
        )
        assert res.status_code == 404

        # 7. Default / Admin has access without headers
        res = await ac.get("/api/v1/integrations/health")
        assert res.status_code == 200
