import type React from "react"
import type { AlertSeverity } from "../types"
import { CHANNEL_COLORS, CHANNEL_LABELS } from "../utils"

export type BadgeVariant = "neutral" | "primary" | "success" | "warning" | "critical" | "info"
export type BadgeSize = "sm" | "md"

const variantClasses: Record<BadgeVariant, string> = {
  neutral: "bg-gray-100 text-gray-700",
  primary: "bg-primary-50 text-primary-700",
  success: "bg-success-50 text-success-700",
  warning: "bg-warning-50 text-warning-600",
  critical: "bg-critical-50 text-critical-600",
  info: "bg-info-50 text-info-600",
}

const sizeClasses: Record<BadgeSize, string> = {
  sm: "px-1.5 py-0.5 text-[11px]",
  md: "px-2 py-0.5 text-xs",
}

export interface BadgeProps {
  variant?: BadgeVariant
  size?: BadgeSize
  children: React.ReactNode
  className?: string
}

export function Badge({ variant = "neutral", size = "md", children, className = "" }: BadgeProps) {
  return (
    <span
      className={`inline-flex items-center gap-1 font-medium rounded-md whitespace-nowrap ${variantClasses[variant]} ${sizeClasses[size]} ${className}`}
    >
      {children}
    </span>
  )
}

export function SeverityBadge({ severity }: { severity: string }) {
  const norm = severity.toLowerCase() as AlertSeverity
  const map: Record<AlertSeverity, { variant: BadgeVariant; label: string }> = {
    critical: { variant: "critical", label: "CRITICAL" },
    warning: { variant: "warning", label: "WARNING" },
    info: { variant: "info", label: "INFO" },
  }
  const item = map[norm] ?? { variant: "neutral", label: severity.toUpperCase() }
  return <Badge variant={item.variant} size="sm">{item.label}</Badge>
}

export function AlertStatusBadge({ status }: { status: string }) {
  const norm = status.toLowerCase()
  return norm === "active" ? (
    <Badge variant="critical" size="sm">Active</Badge>
  ) : (
    <Badge variant="success" size="sm">Resolved</Badge>
  )
}

export function OrderStatusBadge({ status }: { status: string }) {
  const norm = status.toLowerCase()
  const map: Record<string, { variant: BadgeVariant; label: string }> = {
    paid: { variant: "success", label: "Paid" },
    completed: { variant: "success", label: "Completed" },
    processing: { variant: "primary", label: "Processing" },
    pending: { variant: "neutral", label: "Pending" },
    cancelled: { variant: "critical", label: "Cancelled" },
  }
  const item = map[norm] ?? { variant: "neutral", label: status }
  return <Badge variant={item.variant}>{item.label}</Badge>
}

export function ChannelBadge({ channel }: { channel: string }) {
  const key = channel.toLowerCase()
  const color = CHANNEL_COLORS[key] || "#6366F1"
  const label = CHANNEL_LABELS[key] || channel
  return (
    <span
      className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-md text-xs font-medium whitespace-nowrap"
      style={{ backgroundColor: `${color}18`, color }}
    >
      <span className="w-1.5 h-1.5 rounded-full flex-shrink-0" style={{ backgroundColor: color }} />
      {label}
    </span>
  )
}

export function ReconciliationStatusBadge({ status }: { status: string }) {
  const norm = status.toLowerCase()
  const map: Record<string, { variant: BadgeVariant; label: string }> = {
    success: { variant: "success", label: "Success" },
    mismatch: { variant: "critical", label: "Mismatch" },
    failed: { variant: "critical", label: "Failed" },
    running: { variant: "info", label: "Running" },
  }
  const item = map[norm] ?? { variant: "neutral", label: status }
  return <Badge variant={item.variant}>{item.label}</Badge>
}

export function InventoryStatusBadge({ status }: { status: string }) {
  const norm = status.toLowerCase()
  const map: Record<string, { variant: BadgeVariant; label: string }> = {
    healthy: { variant: "success", label: "Healthy" },
    low: { variant: "warning", label: "Low Stock" },
    out: { variant: "critical", label: "Out of Stock" },
  }
  const item = map[norm] ?? { variant: "neutral", label: status }
  return <Badge variant={item.variant} size="sm">{item.label}</Badge>
}

export function ExceptionStatusBadge({ status }: { status: string }) {
  const norm = status.toLowerCase()
  const map: Record<string, { variant: BadgeVariant; label: string }> = {
    open: { variant: "critical", label: "OPEN" },
    investigating: { variant: "warning", label: "INVESTIGATING" },
    resolved: { variant: "success", label: "RESOLVED" },
    ignored: { variant: "neutral", label: "IGNORED" },
  }
  const item = map[norm] ?? { variant: "neutral", label: status.toUpperCase() }
  return <Badge variant={item.variant} size="sm">{item.label}</Badge>
}

export function SyncStatusBadge({ status }: { status: string }) {
  const norm = status.toLowerCase()
  const map: Record<string, { variant: BadgeVariant; label: string }> = {
    success: { variant: "success", label: "SUCCESS" },
    running: { variant: "info", label: "RUNNING" },
    partial: { variant: "warning", label: "PARTIAL" },
    partial_failure: { variant: "warning", label: "PARTIAL" },
    failed: { variant: "critical", label: "FAILED" },
  }
  const item = map[norm] ?? { variant: "neutral", label: status.toUpperCase() }
  return <Badge variant={item.variant} size="sm">{item.label}</Badge>
}

