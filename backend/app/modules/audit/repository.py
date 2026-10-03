from __future__ import annotations

from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import col, select

from app.modules.audit.models import AuditLog


class AuditRepository:
    """Repository handling persistence of immutable audit logs."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, log: AuditLog) -> AuditLog:
        self.session.add(log)
        await self.session.flush()
        await self.session.refresh(log)
        return log

    async def list_logs(
        self,
        *,
        actor_id: str | None = None,
        action: str | None = None,
        entity_type: str | None = None,
        entity_id: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[AuditLog]:
        query = select(AuditLog)
        if actor_id:
            query = query.where(col(AuditLog.actor_id) == actor_id)
        if action:
            query = query.where(col(AuditLog.action) == action)
        if entity_type:
            query = query.where(col(AuditLog.entity_type) == entity_type)
        if entity_id:
            query = query.where(col(AuditLog.entity_id) == entity_id)

        query = (
            query.order_by(col(AuditLog.created_at).desc(), col(AuditLog.id).desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def count_logs(
        self,
        *,
        actor_id: str | None = None,
        action: str | None = None,
        entity_type: str | None = None,
        entity_id: str | None = None,
    ) -> int:
        query = select(func.count()).select_from(AuditLog)
        if actor_id:
            query = query.where(col(AuditLog.actor_id) == actor_id)
        if action:
            query = query.where(col(AuditLog.action) == action)
        if entity_type:
            query = query.where(col(AuditLog.entity_type) == entity_type)
        if entity_id:
            query = query.where(col(AuditLog.entity_id) == entity_id)

        result = await self.session.execute(query)
        return int(result.scalar_one())
