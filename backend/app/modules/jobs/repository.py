from __future__ import annotations

from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import col, select

from app.modules.jobs.models import JobRun, JobStatus
from app.modules.jobs.schemas import JobFilter


class JobRepository:
    """Persistence repository for background operational job records."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, job: JobRun) -> JobRun:
        self.session.add(job)
        await self.session.commit()
        await self.session.refresh(job)
        return job

    async def get_by_id(self, job_id: int) -> JobRun | None:
        stmt = select(JobRun).where(col(JobRun.id) == job_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_jobs(self, filter_params: JobFilter) -> list[JobRun]:
        stmt = select(JobRun).order_by(col(JobRun.created_at).desc())

        if filter_params.status:
            stmt = stmt.where(col(JobRun.status) == filter_params.status.value)
        if filter_params.job_type:
            stmt = stmt.where(col(JobRun.job_type) == filter_params.job_type.value)

        stmt = stmt.offset(filter_params.offset).limit(filter_params.limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def count_jobs(self, filter_params: JobFilter) -> int:
        stmt = select(func.count()).select_from(JobRun)
        if filter_params.status:
            stmt = stmt.where(col(JobRun.status) == filter_params.status.value)
        if filter_params.job_type:
            stmt = stmt.where(col(JobRun.job_type) == filter_params.job_type.value)

        result = await self.session.execute(stmt)
        return int(result.scalar_one() or 0)

    async def get_stats(self) -> dict[str, int]:
        stmt = (
            select(col(JobRun.status), func.count())
            .select_from(JobRun)
            .group_by(col(JobRun.status))
        )
        result = await self.session.execute(stmt)
        counts = {row[0]: int(row[1]) for row in result.all()}

        total = sum(counts.values())
        return {
            "total": total,
            "pending": counts.get(JobStatus.PENDING.value, 0),
            "running": counts.get(JobStatus.RUNNING.value, 0),
            "completed": counts.get(JobStatus.COMPLETED.value, 0),
            "failed": counts.get(JobStatus.FAILED.value, 0),
            "cancelled": counts.get(JobStatus.CANCELLED.value, 0),
        }

    async def acquire_next_pending(self) -> JobRun | None:
        """Select next pending job for execution."""
        stmt = (
            select(JobRun)
            .where(col(JobRun.status) == JobStatus.PENDING.value)
            .order_by(col(JobRun.created_at).asc())
            .limit(1)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def update(self, job: JobRun) -> JobRun:
        self.session.add(job)
        await self.session.commit()
        await self.session.refresh(job)
        return job
