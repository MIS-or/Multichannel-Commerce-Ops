from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import col

from app.modules.exceptions.models import (
    ExceptionDomain,
    ExceptionSeverity,
    ExceptionStatus,
    OperationalException,
)


class ExceptionRepository:
    """Persistence repository for operational exceptions and resolution tracking."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, exception: OperationalException) -> OperationalException:
        self._session.add(exception)
        await self._session.flush()
        return exception

    async def get_by_id(self, exception_id: int) -> OperationalException | None:
        return await self._session.get(OperationalException, exception_id)

    async def get_active_by_domain_and_reference(
        self, domain: ExceptionDomain, reference_id: str
    ) -> OperationalException | None:
        statement = select(OperationalException).where(
            col(OperationalException.domain) == domain,
            col(OperationalException.reference_id) == reference_id,
            col(OperationalException.status).in_(
                [ExceptionStatus.OPEN, ExceptionStatus.INVESTIGATING]
            ),
        )
        result = await self._session.execute(statement)
        return result.scalar_one_or_none()

    async def list_filtered(
        self,
        *,
        status: ExceptionStatus | None = None,
        domain: ExceptionDomain | None = None,
        severity: ExceptionSeverity | None = None,
        channel_code: str | None = None,
        limit: int = 100,
    ) -> list[OperationalException]:
        statement = select(OperationalException)
        if status is not None:
            statement = statement.where(col(OperationalException.status) == status)
        if domain is not None:
            statement = statement.where(col(OperationalException.domain) == domain)
        if severity is not None:
            statement = statement.where(col(OperationalException.severity) == severity)
        if channel_code is not None:
            statement = statement.where(col(OperationalException.channel_code) == channel_code)

        statement = statement.order_by(
            col(OperationalException.created_at).desc(),
            col(OperationalException.id).desc(),
        ).limit(limit)

        result = await self._session.execute(statement)
        return list(result.scalars().all())

    async def update(self, exception: OperationalException) -> OperationalException:
        self._session.add(exception)
        await self._session.flush()
        return exception
