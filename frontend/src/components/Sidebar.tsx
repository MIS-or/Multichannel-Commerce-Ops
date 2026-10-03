import { LayoutDashboard, ShoppingBag, Package, TriangleAlert, ListChecks, ShieldAlert, RefreshCw, Zap } from "lucide-react"
import { Link, useLocation } from "react-router-dom"
import type { Page } from "../types"

interface NavItem {
  id: Page
  path: string
  label: string
  icon: typeof LayoutDashboard
}

interface NavGroup {
  title: string
  items: NavItem[]
}

const NAV_GROUPS: NavGroup[] = [
  {
    title: "OPERATIONS",
    items: [
      { id: "dashboard", path: "/", label: "Dashboard", icon: LayoutDashboard },
      { id: "orders", path: "/orders", label: "Orders", icon: ShoppingBag },
      { id: "inventory", path: "/inventory", label: "Inventory", icon: Package },
      { id: "reconciliation", path: "/reconciliation", label: "Reconciliation", icon: ListChecks },
    ],
  },
  {
    title: "CONTROL & AUTOMATION",
    items: [
      { id: "exceptions", path: "/exceptions", label: "Exceptions", icon: ShieldAlert },
      { id: "alerts", path: "/alerts", label: "Alerts", icon: TriangleAlert },
      { id: "automation", path: "/automation", label: "Automation", icon: Zap },
      { id: "integrations", path: "/integrations", label: "Integrations", icon: RefreshCw },
    ],
  },
]

export interface SystemStatusInfo {
  label: string
  color: string
}

export interface SidebarProps {
  currentPage?: Page
  onNavigate?: (page: Page) => void
  activeAlerts?: { critical: number; warning: number; total: number }
}

export function Sidebar({ currentPage, onNavigate, activeAlerts }: SidebarProps) {
  const location = useLocation()
  const currentPath = location.pathname

  // Determine active item either by currentPage prop or by react-router pathname
  const activeId = (() => {
    if (currentPage) return currentPage
    if (currentPath.startsWith("/orders")) return "orders"
    if (currentPath.startsWith("/inventory")) return "inventory"
    if (currentPath.startsWith("/alerts")) return "alerts"
    if (currentPath.startsWith("/reconciliation")) return "reconciliation"
    if (currentPath.startsWith("/exceptions")) return "exceptions"
    if (currentPath.startsWith("/integrations")) return "integrations"
    if (currentPath.startsWith("/automation")) return "automation"
    return "dashboard"
  })()

  // Dynamic system status
  const status: SystemStatusInfo = (() => {
    if (activeAlerts) {
      if (activeAlerts.critical > 0) return { label: `${activeAlerts.critical} critical issues detected`, color: "bg-critical-600" }
      if (activeAlerts.warning > 0) return { label: `${activeAlerts.warning} alerts require attention`, color: "bg-warning-600" }
      return { label: "All systems operational", color: "bg-success-600" }
    }
    return { label: "All systems operational", color: "bg-success-600" }
  })()

  return (
    <aside className="w-[240px] flex-shrink-0 h-full bg-white border-r border-border flex flex-col shadow-xs select-none">
      {/* Brand Header */}
      <div className="px-5 py-4 border-b border-border">
        <div className="flex items-center gap-2.5">
          <div className="w-7 h-7 bg-primary-600 rounded-lg flex items-center justify-center flex-shrink-0 shadow-xs">
            <span className="text-white text-xs font-bold leading-none">M</span>
          </div>
          <div>
            <div className="text-sm font-bold text-gray-900 leading-none tracking-tight">MCO</div>
            <div className="text-[10px] text-text-secondary leading-none mt-1 font-medium">Operations Platform</div>
          </div>
        </div>
      </div>

      {/* Nav groups */}
      <nav className="flex-1 px-2.5 py-3 overflow-y-auto space-y-4">
        {NAV_GROUPS.map((group) => (
          <div key={group.title}>
            <div className="text-[10px] font-semibold uppercase tracking-wider text-gray-400 px-2.5 mb-1">
              {group.title}
            </div>
            <div className="space-y-0.5">
              {group.items.map(({ id, path, label, icon: Icon }) => {
                const isActive = activeId === id
                const content = (
                  <>
                    <Icon className={`w-3.5 h-3.5 flex-shrink-0 transition-colors ${isActive ? "text-primary-600" : "text-gray-400"}`} />
                    <span className="flex-1">{label}</span>
                    {id === "alerts" && activeAlerts && activeAlerts.total > 0 && (
                      <span className={`text-[10px] font-mono font-semibold px-1.5 py-0.5 rounded-full ${activeAlerts.critical > 0 ? "bg-red-100 text-red-700" : "bg-amber-100 text-amber-700"}`}>
                        {activeAlerts.total}
                      </span>
                    )}
                  </>
                )

                const className = `w-full flex items-center gap-2.5 px-2.5 py-2 text-xs font-medium transition-all text-left cursor-pointer
                  focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary-600 focus-visible:ring-offset-1
                  ${isActive
                    ? "bg-primary-50/80 text-primary-700 font-semibold border-l-2 border-primary-600 rounded-r-lg pl-2"
                    : "text-gray-600 hover:bg-gray-50 hover:text-gray-900 rounded-lg"
                  }`

                if (onNavigate) {
                  return (
                    <button
                      key={id}
                      onClick={() => onNavigate(id)}
                      className={className}
                    >
                      {content}
                    </button>
                  )
                }

                return (
                  <Link
                    key={id}
                    to={path}
                    className={className}
                  >
                    {content}
                  </Link>
                )
              })}
            </div>
          </div>
        ))}
      </nav>

      {/* Footer telemetry */}
      <div className="px-4 py-3 border-t border-border bg-gray-50/40">
        <div className="flex items-center gap-2">
          <span className={`w-1.5 h-1.5 rounded-full flex-shrink-0 ${status.color} animate-pulse`} />
          <span className="text-[11px] text-text-muted truncate font-medium">{status.label}</span>
        </div>
      </div>
    </aside>
  )
}
