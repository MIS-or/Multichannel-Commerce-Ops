from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import col

from app.modules.rules.models import Rule, RuleExecutionLog, TriggerEvent


class RuleRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_active_by_trigger(self, trigger_event: TriggerEvent) -> Sequence[Rule]:
        query = (
            select(Rule)
            .where(col(Rule.trigger_event) == trigger_event, col(Rule.is_active) == True)  # noqa: E712
            .order_by(col(Rule.priority).asc(), col(Rule.id).asc())
        )
        result = await self._session.execute(query)
        return result.scalars().all()

    async def get_by_id(self, rule_id: int) -> Rule | None:
        return await self._session.get(Rule, rule_id)

    async def list_all(self, *, active_only: bool = False) -> Sequence[Rule]:
        query = select(Rule)
        if active_only:
            query = query.where(col(Rule.is_active) == True)  # noqa: E712
        query = query.order_by(col(Rule.priority).asc(), col(Rule.id).asc())
        result = await self._session.execute(query)
        return result.scalars().all()

    async def create(self, rule: Rule) -> Rule:
        self._session.add(rule)
        await self._session.flush()
        return rule

    async def update(self, rule: Rule) -> Rule:
        self._session.add(rule)
        await self._session.flush()
        return rule

    async def delete(self, rule: Rule) -> None:
        await self._session.delete(rule)
        await self._session.flush()

    async def log_execution(self, log: RuleExecutionLog) -> RuleExecutionLog:
        self._session.add(log)
        await self._session.flush()
        return log

    async def list_logs(
        self, *, rule_id: int | None = None, limit: int = 50
    ) -> Sequence[RuleExecutionLog]:
        query = select(RuleExecutionLog)
        if rule_id is not None:
            query = query.where(col(RuleExecutionLog.rule_id) == rule_id)
        query = query.order_by(col(RuleExecutionLog.executed_at).desc()).limit(limit)
        result = await self._session.execute(query)
        return result.scalars().all()
