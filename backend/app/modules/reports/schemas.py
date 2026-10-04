from datetime import date
from decimal import Decimal

from pydantic import BaseModel


class DailyTotals(BaseModel):
    orders: int
    revenue: Decimal
    cogs: Decimal
    gross_profit: Decimal


class ChannelPerformance(BaseModel):
    channel: str
    channel_name: str
    orders: int
    revenue: Decimal
    cogs: Decimal
    gross_profit: Decimal


class DailyReport(BaseModel):
    date: date
    totals: DailyTotals
    channels: list[ChannelPerformance]


class OperationsHealthSummary(BaseModel):
    healthy_integrations: int
    total_integrations: int
    failed_syncs_24h: int
    open_exceptions: int
    critical_exceptions: int
    inventory_mismatches: int
    settlement_mismatches: int
    pending_reconciliations: int
    critical_alerts: int

