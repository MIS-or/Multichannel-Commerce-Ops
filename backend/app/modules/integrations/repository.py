from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import col

from app.modules.integrations.models import SyncRun, SyncStatus, SyncType


class SyncRunRepository:
    """Persistence repository for connector sync run telemetry and cursor state."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, run: SyncRun) -> SyncRun:
        self._session.add(run)
        await self._session.flush()
        return run

    async def update(self, run: SyncRun) -> SyncRun:
        self._session.add(run)
        await self._session.flush()
        return run

    async def get_by_id(self, run_id: int) -> SyncRun | None:
        return await self._session.get(SyncRun, run_id)

    async def get_last_successful_cursor(
        self, channel_code: str, sync_type: SyncType
    ) -> str | None:
        statement = (
            select(SyncRun)
            .where(
                col(SyncRun.channel_code) == channel_code,
                col(SyncRun.sync_type) == sync_type,
                col(SyncRun.status) == SyncStatus.SUCCESS,
                col(SyncRun.cursor_value).is_not(None),
            )
            .order_by(col(SyncRun.completed_at).desc(), col(SyncRun.id).desc())
            .limit(1)
        )
        result = await self._session.execute(statement)
        run = result.scalar_one_or_none()
        return run.cursor_value if run else None

    async def list_runs(
        self,
        *,
        channel_code: str | None = None,
        sync_type: SyncType | None = None,
        limit: int = 50,
    ) -> Sequence[SyncRun]:
        statement = select(SyncRun)
        if channel_code is not None:
            statement = statement.where(col(SyncRun.channel_code) == channel_code)
        if sync_type is not None:
            statement = statement.where(col(SyncRun.sync_type) == sync_type)
        statement = statement.order_by(col(SyncRun.started_at).desc()).limit(limit)

        result = await self._session.execute(statement)
        return result.scalars().all()
