from __future__ import annotations

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.audit.models import AuditAction, AuditLog
from app.modules.audit.repository import AuditRepository


class AuditService:
    """Service handling audit recording and retrieval across operations."""

    def __init__(self, session: AsyncSession) -> None:
        self.repository = AuditRepository(session)

    async def record_event(
        self,
        *,
        actor_id: str,
        actor_role: str,
        action: AuditAction | str,
        entity_type: str,
        entity_id: str,
        before_state: dict[str, Any] | None = None,
        after_state: dict[str, Any] | None = None,
        reason: str | None = None,
        ip_address: str | None = None,
    ) -> AuditLog:
        action_str = action.value if isinstance(action, AuditAction) else str(action)
        entry = AuditLog(
            actor_id=actor_id,
            actor_role=actor_role,
            action=action_str,
            entity_type=entity_type,
            entity_id=entity_id,
            before_state=before_state,
            after_state=after_state,
            reason=reason,
            ip_address=ip_address,
        )
        return await self.repository.create(entry)

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
        return await self.repository.list_logs(
            actor_id=actor_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            limit=limit,
            offset=offset,
        )

    async def count_logs(
        self,
        *,
        actor_id: str | None = None,
        action: str | None = None,
        entity_type: str | None = None,
        entity_id: str | None = None,
    ) -> int:
        return await self.repository.count_logs(
            actor_id=actor_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
        )
