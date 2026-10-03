from __future__ import annotations

import logging
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import SessionFactory, get_session
from app.modules.auth import Permission, UserContext, require_permission
from app.modules.jobs.models import JobStatus, JobType
from app.modules.jobs.schemas import JobFilter, JobRunRead, JobStatsResponse, JobSubmitRequest
from app.modules.jobs.service import JobService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="", tags=["jobs"])


async def _run_job_in_background(job_id: int) -> None:
    try:
        async with SessionFactory() as session:
            service = JobService(session)
            await service.execute_job(job_id)
    except Exception as exc:
        logger.exception("Background task execution failed for job %s: %s", job_id, exc)


@router.post(
    "",
    response_model=JobRunRead,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Enqueue a new background operational job",
)
async def submit_job(
    request: JobSubmitRequest,
    background_tasks: BackgroundTasks,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[UserContext, Depends(require_permission(Permission.JOBS_WRITE))],
) -> JobRunRead:
    service = JobService(session)
    job = await service.submit_job(
        request,
        actor_id=current_user.user_id,
        actor_role=current_user.role.value,
    )

    if request.run_in_background:
        background_tasks.add_task(_run_job_in_background, job.id)

    return job


@router.get(
    "/stats",
    response_model=JobStatsResponse,
    summary="Get aggregated statistics of background jobs",
)
async def get_job_stats(
    session: Annotated[AsyncSession, Depends(get_session)],
    _: Annotated[UserContext, Depends(require_permission(Permission.JOBS_READ))],
) -> JobStatsResponse:
    service = JobService(session)
    return await service.get_stats()


@router.get(
    "",
    response_model=list[JobRunRead],
    summary="List background operational jobs",
)
async def list_jobs(
    session: Annotated[AsyncSession, Depends(get_session)],
    _: Annotated[UserContext, Depends(require_permission(Permission.JOBS_READ))],
    job_status: Annotated[JobStatus | None, Query(alias="status")] = None,
    job_type: Annotated[JobType | None, Query(alias="type")] = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[JobRunRead]:
    filter_params = JobFilter(
        status=job_status,
        job_type=job_type,
        limit=limit,
        offset=offset,
    )
    service = JobService(session)
    return await service.list_jobs(filter_params)


@router.get(
    "/{job_id}",
    response_model=JobRunRead,
    summary="Get details of a background job",
)
async def get_job(
    job_id: int,
    session: Annotated[AsyncSession, Depends(get_session)],
    _: Annotated[UserContext, Depends(require_permission(Permission.JOBS_READ))],
) -> JobRunRead:
    service = JobService(session)
    return await service.get_job(job_id)


@router.post(
    "/{job_id}/execute",
    response_model=JobRunRead,
    summary="Trigger immediate synchronous execution of a job",
)
async def execute_job(
    job_id: int,
    session: Annotated[AsyncSession, Depends(get_session)],
    _: Annotated[UserContext, Depends(require_permission(Permission.JOBS_WRITE))],
) -> JobRunRead:
    service = JobService(session)
    return await service.execute_job(job_id)


@router.post(
    "/{job_id}/cancel",
    response_model=JobRunRead,
    summary="Cancel a pending job",
)
async def cancel_job(
    job_id: int,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[UserContext, Depends(require_permission(Permission.JOBS_WRITE))],
    reason: str | None = None,
) -> JobRunRead:
    service = JobService(session)
    return await service.cancel_job(
        job_id,
        actor_id=current_user.user_id,
        actor_role=current_user.role.value,
        reason=reason,
    )


@router.post(
    "/{job_id}/retry",
    response_model=JobRunRead,
    summary="Requeue a failed or cancelled job",
)
async def retry_job(
    job_id: int,
    background_tasks: BackgroundTasks,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[UserContext, Depends(require_permission(Permission.JOBS_WRITE))],
    run_in_background: bool = Query(default=False),
) -> JobRunRead:
    service = JobService(session)
    job = await service.retry_job(
        job_id,
        actor_id=current_user.user_id,
        actor_role=current_user.role.value,
    )
    if run_in_background:
        background_tasks.add_task(_run_job_in_background, job.id)
    return job
