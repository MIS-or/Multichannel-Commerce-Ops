from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.modules.jobs.models import JobStatus, JobType


class JobSubmitRequest(BaseModel):
    """Payload to enqueue a new background operational task."""

    job_type: JobType
    payload: dict[str, Any] = Field(default_factory=dict)
    max_retries: int = Field(default=3, ge=0, le=10)
    run_in_background: bool = Field(default=True)


class JobRunRead(BaseModel):
    """Read contract for a job execution record."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    job_type: str
    status: str
    payload: dict[str, Any]
    result: dict[str, Any] | None = None
    error_message: str | None = None
    retry_count: int
    max_retries: int
    enqueued_by: str
    started_at: datetime | None = None
    completed_at: datetime | None = None
    created_at: datetime
    duration_ms: float | None = None

    @classmethod
    def from_model(cls, job: Any) -> JobRunRead:
        duration: float | None = None
        if job.started_at and job.completed_at:
            duration = round((job.completed_at - job.started_at).total_seconds() * 1000, 2)

        return cls(
            id=job.id,
            job_type=job.job_type,
            status=job.status,
            payload=job.payload,
            result=job.result,
            error_message=job.error_message,
            retry_count=job.retry_count,
            max_retries=job.max_retries,
            enqueued_by=job.enqueued_by,
            started_at=job.started_at,
            completed_at=job.completed_at,
            created_at=job.created_at,
            duration_ms=duration,
        )


class JobFilter(BaseModel):
    """Query filters for searching operational jobs."""

    status: JobStatus | None = None
    job_type: JobType | None = None
    limit: int = Field(default=50, ge=1, le=200)
    offset: int = Field(default=0, ge=0)


class JobStatsResponse(BaseModel):
    """Aggregated job telemetry counts."""

    total: int
    pending: int
    running: int
    completed: int
    failed: int
    cancelled: int
