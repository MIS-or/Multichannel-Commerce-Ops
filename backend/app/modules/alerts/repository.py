from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import col, select

from app.modules.alerts.models import Alert


class AlertRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, alert_id: int) -> Alert | None:
        return await self._session.get(Alert, alert_id)

    async def get_active_by_dedup_key(self, dedup_key: str) -> Alert | None:
        result = await self._session.execute(
            select(Alert).where(col(Alert.dedup_key) == dedup_key, col(Alert.resolved).is_(False))
        )
        return result.scalar_one_or_none()

    async def list_all(self, *, resolved: bool | None = None, limit: int = 100) -> list[Alert]:
        statement = select(Alert)
        if resolved is not None:
            statement = statement.where(col(Alert.resolved).is_(resolved))
        statement = statement.order_by(col(Alert.created_at).desc(), col(Alert.id).desc()).limit(
            limit
        )
        result = await self._session.execute(statement)
        return list(result.scalars().all())

    async def list_pending_notifications(self, *, limit: int = 100) -> list[Alert]:
        result = await self._session.execute(
            select(Alert)
            .where(col(Alert.resolved).is_(False), col(Alert.notified_at).is_(None))
            .order_by(col(Alert.created_at), col(Alert.id))
            .limit(limit)
        )
        return list(result.scalars().all())
