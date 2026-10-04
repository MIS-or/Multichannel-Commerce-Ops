export type Channel = "shopee" | "tiktok" | "website"
export type OrderStatus = "pending" | "processing" | "completed" | "cancelled" | "paid"
export type AlertSeverity = "critical" | "warning" | "info"
export type AlertStatus = "active" | "resolved"
export type ReconciliationStatus = "success" | "mismatch" | "failed" | "running"
export type InventoryStatus = "healthy" | "low" | "out"

export type Page =
  | "dashboard"
  | "orders"
  | "order-detail"
  | "inventory"
  | "alerts"
  | "reconciliation"
  | "reconciliation-detail"
  | "exceptions"
  | "integrations"
  | "automation"

export interface ToastItem {
  id: number
  message: string
  type: "success" | "error" | "info"
}

// Canonical feature entity types re-exported from feature schemas
export type { Order, OrderItem, OrderDetail, OrderFilterParams } from "./features/orders/api"
export type { DailyReport } from "./features/dashboard/api"
export type { InventoryItem } from "./features/inventory/api"
export type { Alert } from "./features/alerts/api"
export type { Reconciliation, ReconciliationMismatch, RunReconciliationPayload } from "./features/reconciliation/api"
export type {
  OperationalException,
  ExceptionDomain,
  ExceptionSeverity,
  ExceptionStatus,
  RootCauseCategory,
} from "./features/exceptions/api"
export type {
  ConnectorHealthStatus,
  IntegrationHealthResponse,
  SyncRun,
  SyncType,
  SyncStatus,
} from "./features/integrations/api"
export type {
  Rule,
  RuleExecutionLog,
  TriggerEvent,
  ActionType,
} from "./features/automation/api"
