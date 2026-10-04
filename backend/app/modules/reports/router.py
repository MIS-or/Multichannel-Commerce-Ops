from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.modules.auth import Permission, UserContext, require_permission
from app.modules.reports.repository import ReportsRepository
from app.modules.reports.schemas import DailyReport, OperationsHealthSummary
from app.modules.reports.service import ReportsService

router = APIRouter(prefix="/reports", tags=["reports"])


def get_reports_repository(
    session: AsyncSession = Depends(get_session),
) -> ReportsRepository:
    return ReportsRepository(session)


def get_reports_service(
    repository: ReportsRepository = Depends(get_reports_repository),
) -> ReportsService:
    return ReportsService(repository)


@router.get("/daily", response_model=DailyReport)
async def daily_report(
    service: Annotated[ReportsService, Depends(get_reports_service)],
    _user: Annotated[UserContext, Depends(require_permission(Permission.REPORTS_READ))],
    report_date: date | None = Query(default=None, alias="date"),
) -> DailyReport:
    return await service.daily_report(report_date)


@router.get("/operations-health", response_model=OperationsHealthSummary)
async def operations_health(
    service: Annotated[ReportsService, Depends(get_reports_service)],
    _user: Annotated[UserContext, Depends(require_permission(Permission.REPORTS_READ))],
) -> OperationsHealthSummary:
    return await service.operations_health()
