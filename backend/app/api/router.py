from fastapi import APIRouter

from app.modules.alerts.router import router as alerts_router
from app.modules.audit.router import router as audit_router
from app.modules.exceptions.router import router as exceptions_router
from app.modules.integrations.router import router as integrations_router
from app.modules.inventory.router import router as inventory_router
from app.modules.jobs.router import router as jobs_router
from app.modules.orders.router import router as orders_router
from app.modules.reconciliation.router import router as reconciliation_router
from app.modules.reports.router import router as reports_router
from app.modules.rules.router import router as rules_router

api_router = APIRouter()
api_router.include_router(alerts_router)
api_router.include_router(orders_router)
api_router.include_router(inventory_router)
api_router.include_router(reports_router)
api_router.include_router(reconciliation_router)
api_router.include_router(exceptions_router)
api_router.include_router(rules_router)
api_router.include_router(integrations_router)
api_router.include_router(audit_router)
api_router.include_router(jobs_router, prefix="/jobs")


