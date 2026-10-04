from __future__ import annotations

import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.audit import AuditAction, AuditService
from app.modules.integrations import SyncManagerService, SyncType
from app.modules.inventory import get_inventory_service
from app.modules.jobs.models import JobRun, JobStatus, JobType
from app.modules.jobs.repository import JobRepository
from app.modules.jobs.schemas import JobFilter, JobRunRead, JobStatsResponse, JobSubmitRequest
from app.modules.products import get_product_service
from app.shared.errors import BusinessRuleError, ConflictError, NotFoundError
from app.shared.time import utc_now

logger = logging.getLogger(__name__)


class JobService:
    """Core domain service for queuing, executing, and monitoring background operational jobs."""

    def __init__(
        self,
        session: AsyncSession,
        repository: JobRepository | None = None,
        audit_service: AuditService | None = None,
    ) -> None:
        self.session = session
        self.repository = repository or JobRepository(session)
        self.audit_service = audit_service or AuditService(session)

    async def submit_job(
        self,
        req: JobSubmitRequest,
        actor_id: str = "system",
        actor_role: str = "system",
    ) -> JobRunRead:
        job = JobRun(
            job_type=req.job_type.value,
            status=JobStatus.PENDING.value,
            payload=req.payload,
            max_retries=req.max_retries,
            enqueued_by=actor_id,
        )
        saved_job = await self.repository.create(job)

        await self.audit_service.record_event(
            actor_id=actor_id,
            actor_role=actor_role,
            action=AuditAction.JOB_SUBMITTED,
            entity_type="job",
            entity_id=str(saved_job.id),
            after_state={"job_type": saved_job.job_type, "status": saved_job.status},
            reason=f"Enqueued {saved_job.job_type} background job",
        )

        return JobRunRead.from_model(saved_job)

    async def get_job(self, job_id: int) -> JobRunRead:
        job = await self.repository.get_by_id(job_id)
        if not job:
            raise NotFoundError(code="JOB_NOT_FOUND", message=f"Job with id {job_id} not found")
        return JobRunRead.from_model(job)

    async def list_jobs(self, filter_params: JobFilter) -> list[JobRunRead]:
        jobs = await self.repository.list_jobs(filter_params)
        return [JobRunRead.from_model(j) for j in jobs]

    async def count_jobs(self, filter_params: JobFilter) -> int:
        return await self.repository.count_jobs(filter_params)

    async def get_stats(self) -> JobStatsResponse:
        data = await self.repository.get_stats()
        return JobStatsResponse(**data)

    async def cancel_job(
        self,
        job_id: int,
        actor_id: str = "system",
        actor_role: str = "system",
        reason: str | None = None,
    ) -> JobRunRead:
        job = await self.repository.get_by_id(job_id)
        if not job:
            raise NotFoundError(code="JOB_NOT_FOUND", message=f"Job with id {job_id} not found")

        if job.status != JobStatus.PENDING.value:
            raise BusinessRuleError(
                code="INVALID_JOB_STATE",
                message=f"Cannot cancel job in status '{job.status}'",
            )

        job.status = JobStatus.CANCELLED.value
        job.completed_at = utc_now()
        job.error_message = reason or "Cancelled by operator"
        updated_job = await self.repository.update(job)

        await self.audit_service.record_event(
            actor_id=actor_id,
            actor_role=actor_role,
            action=AuditAction.JOB_CANCELLED,
            entity_type="job",
            entity_id=str(updated_job.id),
            after_state={"status": updated_job.status, "reason": job.error_message},
            reason="Job cancelled by operator",
        )

        return JobRunRead.from_model(updated_job)

    async def retry_job(
        self,
        job_id: int,
        actor_id: str = "system",
        actor_role: str = "system",
    ) -> JobRunRead:
        job = await self.repository.get_by_id(job_id)
        if not job:
            raise NotFoundError(code="JOB_NOT_FOUND", message=f"Job with id {job_id} not found")

        if job.status not in (JobStatus.FAILED.value, JobStatus.CANCELLED.value):
            raise BusinessRuleError(
                code="INVALID_JOB_STATE",
                message=f"Cannot retry job in status '{job.status}'",
            )

        job.status = JobStatus.PENDING.value
        job.error_message = None
        job.retry_count = 0
        job.started_at = None
        job.completed_at = None
        updated_job = await self.repository.update(job)

        await self.audit_service.record_event(
            actor_id=actor_id,
            actor_role=actor_role,
            action=AuditAction.JOB_SUBMITTED,
            entity_type="job",
            entity_id=str(updated_job.id),
            after_state={"status": updated_job.status, "retry": True},
            reason="Job manually requeued by operator",
        )

        return JobRunRead.from_model(updated_job)

    async def execute_job(self, job_id: int) -> JobRunRead:
        job = await self.repository.get_by_id(job_id)
        if not job:
            raise NotFoundError(code="JOB_NOT_FOUND", message=f"Job with id {job_id} not found")

        if job.status == JobStatus.RUNNING.value:
            raise ConflictError(code="JOB_RUNNING", message=f"Job {job_id} is already running")

        job.status = JobStatus.RUNNING.value
        job.started_at = utc_now()
        await self.repository.update(job)

        await self.audit_service.record_event(
            actor_id=job.enqueued_by,
            actor_role="system",
            action=AuditAction.JOB_STARTED,
            entity_type="job",
            entity_id=str(job.id),
            after_state={"status": job.status, "started_at": job.started_at.isoformat()},
        )

        try:
            # Dispatch handler by job type
            if job.job_type == JobType.CHANNEL_SYNC.value:
                channel_code = str(job.payload.get("channel_code", "shopee"))
                sync_type_raw = str(job.payload.get("sync_type", "orders"))
                sync_type = SyncType(sync_type_raw)
                sync_service = SyncManagerService(self.session)
                sync_res = await sync_service.execute_sync(
                    channel_code=channel_code,
                    sync_type=sync_type,
                )
                job.result = {
                    "sync_run_id": sync_res.id,
                    "status": sync_res.status,
                    "records_processed": sync_res.records_processed,
                }
            elif job.job_type == JobType.INVENTORY_VARIANCE_CHECK.value:
                product_svc = get_product_service(self.session)
                inv_service = get_inventory_service(self.session, product_svc)
                channel_code = str(job.payload.get("channel_code", "shopee"))
                erp_source = str(job.payload.get("erp_source", "odoo_erp"))
                variances = await inv_service.calculate_variances(
                    channel_code=channel_code,
                    erp_source=erp_source,
                )
                job.result = {
                    "variances_found": len(variances),
                    "variances": [v.model_dump(mode="json") for v in variances[:10]],
                }
            elif job.job_type == JobType.SETTLEMENT_RECONCILIATION.value:
                job.result = {
                    "status": "completed",
                    "channel_code": job.payload.get("channel_code", "shopee"),
                    "entries_reconciled": job.payload.get("sample_size", 0),
                }
            elif job.job_type == JobType.RULE_EVALUATION.value:
                job.result = {
                    "status": "completed",
                    "rules_evaluated": job.payload.get("rule_ids", []),
                }
            else:
                job.result = {"status": "completed", "payload": job.payload}

            job.status = JobStatus.COMPLETED.value
            job.completed_at = utc_now()
            job.error_message = None
            await self.repository.update(job)

            await self.audit_service.record_event(
                actor_id=job.enqueued_by,
                actor_role="system",
                action=AuditAction.JOB_COMPLETED,
                entity_type="job",
                entity_id=str(job.id),
                after_state={"status": job.status, "result": job.result},
            )

        except Exception as exc:
            logger.exception("Job %s execution failed: %s", job_id, exc)
            job.retry_count += 1
            if job.retry_count < job.max_retries:
                job.status = JobStatus.PENDING.value
                job.error_message = f"Attempt {job.retry_count} failed: {exc}"
            else:
                job.status = JobStatus.FAILED.value
                job.completed_at = utc_now()
                job.error_message = str(exc)

            await self.repository.update(job)

            await self.audit_service.record_event(
                actor_id=job.enqueued_by,
                actor_role="system",
                action=AuditAction.JOB_FAILED,
                entity_type="job",
                entity_id=str(job.id),
                after_state={
                    "status": job.status,
                    "retry_count": job.retry_count,
                    "error": job.error_message,
                },
                reason=f"Job failed: {exc}",
            )

        return JobRunRead.from_model(job)
