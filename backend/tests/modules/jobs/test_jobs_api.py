from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.main import app
from app.modules.auth import (
    ROLE_PERMISSIONS,
    UserContext,
    UserRole,
    get_current_user,
)


@pytest.mark.asyncio
async def test_jobs_api_rbac_enforcement(session: AsyncSession) -> None:
    app.dependency_overrides[get_session] = lambda: session

    viewer_user = UserContext(
        user_id="usr_viewer_1",
        email="viewer@mco.internal",
        full_name="Viewer",
        role=UserRole.VIEWER,
        permissions=ROLE_PERMISSIONS[UserRole.VIEWER],
    )
    app.dependency_overrides[get_current_user] = lambda: viewer_user

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://testserver"
    ) as client:
        # Viewer does not have JOBS_WRITE permission
        resp = await client.post(
            "/api/v1/jobs",
            json={
                "job_type": "channel_sync",
                "payload": {"channel_code": "shopee"},
                "run_in_background": False,
            },
        )
        assert resp.status_code == 403
        assert resp.json()["error"]["code"] == "FORBIDDEN_INSUFFICIENT_PERMISSION"

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_jobs_api_crud_flow(session: AsyncSession) -> None:
    app.dependency_overrides[get_session] = lambda: session

    ops_user = UserContext(
        user_id="usr_ops_1",
        email="ops@mco.internal",
        full_name="Operations User",
        role=UserRole.OPERATIONS,
        permissions=ROLE_PERMISSIONS[UserRole.OPERATIONS],
    )
    app.dependency_overrides[get_current_user] = lambda: ops_user

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://testserver"
    ) as client:
        # 1. Submit Job
        submit_resp = await client.post(
            "/api/v1/jobs",
            json={
                "job_type": "settlement_reconciliation",
                "payload": {"channel_code": "tiktok", "sample_size": 10},
                "run_in_background": False,
            },
        )
        assert submit_resp.status_code == 202
        job_data = submit_resp.json()
        job_id = job_data["id"]
        assert job_data["status"] == "pending"
        assert job_data["job_type"] == "settlement_reconciliation"

        # 2. Get Job
        get_resp = await client.get(f"/api/v1/jobs/{job_id}")
        assert get_resp.status_code == 200
        assert get_resp.json()["id"] == job_id

        # 3. List Jobs
        list_resp = await client.get("/api/v1/jobs")
        assert list_resp.status_code == 200
        assert len(list_resp.json()) >= 1

        # 4. Get Stats
        stats_resp = await client.get("/api/v1/jobs/stats")
        assert stats_resp.status_code == 200
        assert stats_resp.json()["total"] >= 1

        # 5. Cancel Job
        cancel_resp = await client.post(f"/api/v1/jobs/{job_id}/cancel?reason=TestCancel")
        assert cancel_resp.status_code == 200
        assert cancel_resp.json()["status"] == "cancelled"

        # 6. Retry Job
        retry_resp = await client.post(f"/api/v1/jobs/{job_id}/retry")
        assert retry_resp.status_code == 200
        assert retry_resp.json()["status"] == "pending"

    app.dependency_overrides.clear()
