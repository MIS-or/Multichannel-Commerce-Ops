from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.audit import AuditAction, AuditService
from app.modules.jobs import (
    JobFilter,
    JobService,
    JobStatus,
    JobSubmitRequest,
    JobType,
)
from app.shared.errors import BusinessRuleError, NotFoundError


@pytest.mark.asyncio
async def test_job_submit_and_lifecycle(session: AsyncSession) -> None:
    service = JobService(session)
    audit_service = AuditService(session)

    # 1. Submit Job
    req = JobSubmitRequest(
        job_type=JobType.CHANNEL_SYNC,
        payload={"channel_code": "shopee", "sync_type": "orders"},
        max_retries=3,
        run_in_background=False,
    )
    job = await service.submit_job(req, actor_id="usr_ops_1", actor_role="operations")

    assert job.id is not None
    assert job.job_type == JobType.CHANNEL_SYNC.value
    assert job.status == JobStatus.PENDING.value
    assert job.retry_count == 0
    assert job.enqueued_by == "usr_ops_1"

    # Check audit log
    logs = await audit_service.list_logs(action=AuditAction.JOB_SUBMITTED.value)
    assert len(logs) >= 1
    assert logs[0].entity_id == str(job.id)

    # 2. Cancel Job
    cancelled_job = await service.cancel_job(
        job.id, actor_id="usr_ops_1", actor_role="operations", reason="Operator cancelled"
    )
    assert cancelled_job.status == JobStatus.CANCELLED.value
    assert cancelled_job.error_message == "Operator cancelled"

    # 3. Cannot cancel again
    with pytest.raises(BusinessRuleError):
        await service.cancel_job(job.id)

    # 4. Retry Job
    retried_job = await service.retry_job(job.id, actor_id="usr_ops_1", actor_role="operations")
    assert retried_job.status == JobStatus.PENDING.value
    assert retried_job.error_message is None

    # 5. Cannot retry when already pending
    with pytest.raises(BusinessRuleError):
        await service.retry_job(job.id)


@pytest.mark.asyncio
async def test_job_stats_and_filtering(session: AsyncSession) -> None:
    service = JobService(session)

    # Submit 3 jobs
    await service.submit_job(
        JobSubmitRequest(job_type=JobType.CHANNEL_SYNC, payload={"channel": "tiktok"})
    )
    job2 = await service.submit_job(
        JobSubmitRequest(job_type=JobType.SETTLEMENT_RECONCILIATION, payload={"channel": "shopee"})
    )
    await service.submit_job(
        JobSubmitRequest(job_type=JobType.INVENTORY_VARIANCE_CHECK, payload={})
    )

    # Cancel one
    await service.cancel_job(job2.id)

    # Stats
    stats = await service.get_stats()
    assert stats.total >= 3
    assert stats.pending >= 2
    assert stats.cancelled >= 1

    # Filter by job_type
    recon_jobs = await service.list_jobs(
        JobFilter(job_type=JobType.SETTLEMENT_RECONCILIATION)
    )
    assert len(recon_jobs) == 1
    assert recon_jobs[0].job_type == JobType.SETTLEMENT_RECONCILIATION.value

    # Filter by status
    pending_jobs = await service.list_jobs(JobFilter(status=JobStatus.PENDING))
    assert len(pending_jobs) >= 2


@pytest.mark.asyncio
async def test_job_execution(session: AsyncSession) -> None:
    service = JobService(session)

    # Submit settlement reconciliation job
    job = await service.submit_job(
        JobSubmitRequest(
            job_type=JobType.SETTLEMENT_RECONCILIATION,
            payload={"channel_code": "shopee", "sample_size": 25},
            run_in_background=False,
        )
    )

    # Execute synchronously
    completed_job = await service.execute_job(job.id)
    assert completed_job.status == JobStatus.COMPLETED.value
    assert completed_job.result is not None
    assert completed_job.result.get("entries_reconciled") == 25
    assert completed_job.completed_at is not None
    assert completed_job.duration_ms is not None


@pytest.mark.asyncio
async def test_job_not_found(session: AsyncSession) -> None:
    service = JobService(session)
    with pytest.raises(NotFoundError):
        await service.get_job(999999)
