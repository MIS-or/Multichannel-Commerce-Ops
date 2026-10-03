from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.modules.alerts.models import AlertSeverity, AlertType


class AlertRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    type: AlertType
    severity: AlertSeverity
    dedup_key: str
    message: str
    resolved: bool
    created_at: datetime
    resolved_at: datetime | None
    notified_at: datetime | None


class LowStockAlertRequest(BaseModel):
    product_id: int | None = None
    sku: str
    name: str = ""
    current_stock: int
    reorder_threshold: int
