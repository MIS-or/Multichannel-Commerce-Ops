import { useState } from 'react'
import {
  ChevronRight,
  RefreshCw,
  ArrowRight,
} from 'lucide-react'
import { useNavigate } from 'react-router-dom'

import { PageHeader } from '../components/PageHeader'
import { MetricCard } from '../components/MetricCard'
import { Panel } from '../components/Panel'
import { ChannelBadge, SeverityBadge, InventoryStatusBadge } from '../components/Badge'
import { MetricCardSkeleton, ChartSkeleton, Skeleton } from '../components/Skeleton'
import { ErrorState } from '../components/ErrorState'
import { ApiError } from '../lib/api'
import { ChannelProfitChart } from '../features/dashboard/ChannelProfitChart'
import { ChannelRevenueChart } from '../features/dashboard/ChannelRevenueChart'
import { useDailyReport, useOperationsHealth } from '../features/dashboard/api'
import { useInventory } from '../features/inventory/api'
import { useAlerts } from '../features/alerts/api'
import { useReconciliations } from '../features/reconciliation/api'
import { formatVND, formatDateTime } from '../utils'

function getInventoryStatus(current: number, threshold: number): 'out' | 'low' | 'healthy' {
  if (current === 0) return 'out'
  if (current <= threshold) return 'low'
  return 'healthy'
}

export function DashboardPage() {
  const navigate = useNavigate()
  const [selectedDate, setSelectedDate] = useState<string>('')

  const reportQuery = useDailyReport(selectedDate || undefined)
  const healthQuery = useOperationsHealth()
  const inventoryQuery = useInventory()
  const alertsQuery = useAlerts(false)
  const reconciliationsQuery = useReconciliations()

  const loading = reportQuery.isLoading || inventoryQuery.isLoading
  const error = reportQuery.error ?? inventoryQuery.error

  const handleRefresh = async () => {
    await Promise.all([
      reportQuery.refetch(),
      healthQuery.refetch(),
      inventoryQuery.refetch(),
      alertsQuery.refetch(),
      reconciliationsQuery.refetch(),
    ])
  }

  if (error) {
    return (
      <div className="p-6 max-w-[1440px] w-full">
        <ErrorState
          title="Failed to load dashboard data"
          message={error.message}
          requestId={error instanceof ApiError ? error.requestId : undefined}
          onRetry={() => {
            void handleRefresh()
          }}
        />
      </div>
    )
  }

  const report = reportQuery.data
  const activeAlerts = alertsQuery.data ?? []
  const reconciliations = reconciliationsQuery.data ?? []
  const inventory = inventoryQuery.data ?? []

  const atRiskInventory = inventory.filter(
    (i) => getInventoryStatus(i.current_stock, i.reorder_threshold) !== 'healthy'
  )

  const revenue = report?.totals.revenue ?? 0
  const cogs = report?.totals.cogs ?? 0
  const grossProfit = report?.totals.gross_profit ?? 0
  const orders = report?.totals.orders ?? 0
  const margin = revenue > 0 ? ((grossProfit / revenue) * 100).toFixed(1) : '0.0'

  const health = healthQuery.data
  const isActionRequired = health
    ? health.critical_exceptions > 0 || health.failed_syncs_24h > 0 || health.critical_alerts > 0
    : false

  return (
    <div className="p-6 max-w-[1440px] w-full">
      <PageHeader
        title="Dashboard"
        subtitle="Multichannel commerce performance and operational health."
        action={
          <div className="flex items-center gap-2">
            <div className="flex items-center gap-1.5 px-3 py-1.5 bg-white border border-border rounded-lg text-sm text-gray-700">
              <span className="text-text-secondary text-xs">Date:</span>
              <input
                type="date"
                value={selectedDate || report?.date || ''}
                onChange={(e) => setSelectedDate(e.target.value)}
                className="font-medium bg-transparent border-0 p-0 text-sm text-gray-800 focus:outline-none cursor-pointer"
              />
            </div>
            <button
              onClick={() => {
                void handleRefresh()
              }}
              className="w-8 h-8 flex items-center justify-center rounded-lg border border-border bg-white text-gray-500 hover:text-gray-700 hover:bg-gray-50 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary-600 cursor-pointer"
              aria-label="Refresh data"
              title="Refresh data"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${reportQuery.isFetching || healthQuery.isFetching ? 'animate-spin' : ''}`} />
            </button>
          </div>
        }
      />

      {/* Operations Health Cockpit */}
      <div className="mb-6 bg-white border border-border rounded-xl p-5 shadow-xs">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-border gap-3">
          <div>
            <div className="flex items-center gap-2.5 mb-1">
              <span className={`w-2 h-2 rounded-full flex-shrink-0 ${healthQuery.isLoading ? 'bg-gray-400' : isActionRequired ? 'bg-rose-500 animate-pulse' : 'bg-emerald-500 animate-pulse'}`} />
              <h2 className="text-sm font-bold text-gray-900 tracking-tight">Operations &amp; Multi-System Telemetry</h2>
              <span className={`px-2 py-0.5 rounded text-[10px] font-semibold border ${healthQuery.isLoading ? 'bg-gray-100 text-gray-600 border-gray-200' : isActionRequired ? 'bg-rose-50 text-rose-700 border-rose-200' : 'bg-emerald-50 text-emerald-700 border-emerald-200'}`}>
                {healthQuery.isLoading ? 'Đang đồng bộ…' : isActionRequired ? 'Cần xử lý' : 'Đồng bộ tốt'}
              </span>
            </div>
            <p className="text-xs text-text-secondary">Trạng thái vận hành thời gian thực — connector đa sàn, lệch tồn kho ERP, đối soát payout và hàng chờ ngoại lệ.</p>
          </div>
          <div className="text-[11px] text-text-muted font-mono">Tự động cập nhật mỗi 30 giây</div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 mt-4">
          {/* Connector Health */}
          <button
            onClick={() => {
              void navigate('/integrations')
            }}
            className="group text-left bg-gray-50/60 hover:bg-white border border-border hover:border-gray-300 rounded-lg p-3.5 transition-all cursor-pointer shadow-none hover:shadow-xs"
          >
            <div className="flex items-center justify-between text-xs mb-1.5">
              <span className="font-semibold text-gray-500 text-[10px] uppercase tracking-wider">Connectors &amp; Sync</span>
              <ArrowRight className="w-3.5 h-3.5 text-gray-400 group-hover:text-primary-600 group-hover:translate-x-0.5 transition-all" />
            </div>
            <div className="text-xl font-bold font-mono text-gray-900 mb-1">
              {health?.healthy_integrations ?? 0}/{health?.total_integrations ?? 0}{' '}
              <span className="text-xs font-sans font-medium text-emerald-600">online</span>
            </div>
            <div className="text-xs">
              {health && health.failed_syncs_24h > 0 ? (
                <span className="text-rose-600 font-medium">
                  {health.failed_syncs_24h} lần đồng bộ lỗi (24h qua)
                </span>
              ) : (
                <span className="text-text-secondary">Tất cả pipeline chạy ổn định</span>
              )}
            </div>
          </button>

          {/* Operational Exceptions */}
          <button
            onClick={() => {
              void navigate('/exceptions')
            }}
            className="group text-left bg-gray-50/60 hover:bg-white border border-border hover:border-gray-300 rounded-lg p-3.5 transition-all cursor-pointer shadow-none hover:shadow-xs"
          >
            <div className="flex items-center justify-between text-xs mb-1.5">
              <span className="font-semibold text-gray-500 text-[10px] uppercase tracking-wider">Ngoại lệ đang mở</span>
              <ArrowRight className="w-3.5 h-3.5 text-gray-400 group-hover:text-amber-600 group-hover:translate-x-0.5 transition-all" />
            </div>
            <div className="text-xl font-bold font-mono text-gray-900 mb-1">
              {health?.open_exceptions ?? 0}{' '}
              <span className="text-xs font-sans font-normal text-text-muted">mục chưa xử lý</span>
            </div>
            <div className="text-xs">
              {health && health.critical_exceptions > 0 ? (
                <span className="text-rose-600 font-medium">
                  {health.critical_exceptions} mục nghiêm trọng — cần xử lý ngay
                </span>
              ) : (
                <span className="text-text-secondary">0 mục nghiêm trọng đang chờ</span>
              )}
            </div>
          </button>

          {/* Inventory Alignment */}
          <button
            onClick={() => {
              void navigate('/inventory')
            }}
            className="group text-left bg-gray-50/60 hover:bg-white border border-border hover:border-gray-300 rounded-lg p-3.5 transition-all cursor-pointer shadow-none hover:shadow-xs"
          >
            <div className="flex items-center justify-between text-xs mb-1.5">
              <span className="font-semibold text-gray-500 text-[10px] uppercase tracking-wider">Lệch tồn kho</span>
              <ArrowRight className="w-3.5 h-3.5 text-gray-400 group-hover:text-indigo-600 group-hover:translate-x-0.5 transition-all" />
            </div>
            <div className="text-xl font-bold font-mono text-gray-900 mb-1">
              {health?.inventory_mismatches ?? 0}{' '}
              <span className="text-xs font-sans font-normal text-text-muted">SKU có sai lệch</span>
            </div>
            <div className="text-xs text-text-secondary truncate">
              ERP nguồn thực vs snapshot từng kênh
            </div>
          </button>

          {/* Settlement Discrepancy */}
          <button
            onClick={() => {
              void navigate('/reconciliation')
            }}
            className="group text-left bg-gray-50/60 hover:bg-white border border-border hover:border-gray-300 rounded-lg p-3.5 transition-all cursor-pointer shadow-none hover:shadow-xs"
          >
            <div className="flex items-center justify-between text-xs mb-1.5">
              <span className="font-semibold text-gray-500 text-[10px] uppercase tracking-wider">Đối soát thanh toán</span>
              <ArrowRight className="w-3.5 h-3.5 text-gray-400 group-hover:text-emerald-600 group-hover:translate-x-0.5 transition-all" />
            </div>
            <div className="text-xl font-bold font-mono text-gray-900 mb-1">
              {health?.settlement_mismatches ?? 0}{' '}
              <span className="text-xs font-sans font-normal text-text-muted">lần lệch payout</span>
            </div>
            <div className="text-xs text-text-secondary truncate">
              {health?.pending_reconciliations ?? 0} phiên đối soát đang chờ kiểm tra
            </div>
          </button>
        </div>
      </div>

      {/* KPI Row */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        {loading ? (
          Array.from({ length: 4 }).map((_, i) => <MetricCardSkeleton key={i} />)
        ) : (
          <>
            <MetricCard
              label="Doanh thu"
              value={formatVND(revenue, true)}
              description="Tổng tiền khách hàng thanh toán trên tất cả kênh bán"
              subValue={formatVND(revenue)}
              accent="info"
            />
            <MetricCard
              label="Giá vốn hàng bán (COGS)"
              value={formatVND(cogs, true)}
              description="Chi phí nhập hàng tương ứng với các đơn đã bán"
              subValue={formatVND(cogs)}
              accent="warning"
            />
            <MetricCard
              label="Lợi nhuận gộp"
              value={formatVND(grossProfit, true)}
              description={`Biên lợi nhuận gộp: ${margin}% — Doanh thu trừ đi giá vốn`}
              accent={Number(margin) >= 20 ? 'success' : Number(margin) >= 10 ? 'warning' : 'danger'}
            />
            <MetricCard
              label="Số đơn hàng"
              value={orders.toString()}
              description="Tổng đơn đã ghi nhận trên tất cả kênh trong ngày"
              accent="default"
            />
          </>
        )}
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 mb-6">
        <Panel
          title="Revenue by Channel"
          subtitle="Fixed channel colors keep comparisons familiar across visits."
        >
          {loading ? (
            <ChartSkeleton />
          ) : report && report.channels.length > 0 ? (
            <ChannelRevenueChart channels={report.channels} />
          ) : (
            <div className="py-12 text-center text-sm text-text-secondary">
              No revenue data available for this date.
            </div>
          )}
        </Panel>

        <Panel
          title="Gross Profit by Channel"
          subtitle="Positive and negative values diverge around zero."
        >
          {loading ? (
            <ChartSkeleton />
          ) : report && report.channels.length > 0 ? (
            <ChannelProfitChart channels={report.channels} />
          ) : (
            <div className="py-12 text-center text-sm text-text-secondary">
              No profit data available for this date.
            </div>
          )}
        </Panel>
      </div>

      {/* Channel Breakdown Table */}
      {report && report.channels.length > 0 && (
        <Panel title="Channel Performance Summary" className="mb-6" noPadding>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-border bg-gray-50">
                  <th className="px-4 py-3 text-left text-[12px] font-semibold text-text-secondary uppercase tracking-wide">
                    Channel
                  </th>
                  <th className="px-4 py-3 text-right text-[12px] font-semibold text-text-secondary uppercase tracking-wide">
                    Orders
                  </th>
                  <th className="px-4 py-3 text-right text-[12px] font-semibold text-text-secondary uppercase tracking-wide">
                    Revenue
                  </th>
                  <th className="px-4 py-3 text-right text-[12px] font-semibold text-text-secondary uppercase tracking-wide">
                    COGS
                  </th>
                  <th className="px-4 py-3 text-right text-[12px] font-semibold text-text-secondary uppercase tracking-wide">
                    Gross Profit
                  </th>
                  <th className="px-4 py-3 text-right text-[12px] font-semibold text-text-secondary uppercase tracking-wide">
                    Margin
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {report.channels.map((ch) => {
                  const chMargin = ch.revenue > 0 ? ((ch.gross_profit / ch.revenue) * 100).toFixed(1) : '0.0'
                  return (
                    <tr key={ch.channel} className="hover:bg-gray-50 transition-colors">
                      <td className="px-4 py-3.5">
                        <div className="flex items-center gap-2">
                          <ChannelBadge channel={ch.channel} />
                          <span className="text-sm font-medium text-gray-800">{ch.channel_name}</span>
                        </div>

                      </td>
                      <td className="px-4 py-3.5 text-right">
                        <span className="text-sm tabular-nums text-gray-700">{ch.orders}</span>
                      </td>
                      <td className="px-4 py-3.5 text-right">
                        <span className="text-sm font-medium tabular-nums text-gray-800">{formatVND(ch.revenue)}</span>
                      </td>
                      <td className="px-4 py-3.5 text-right">
                        <span className="text-sm tabular-nums text-gray-700">{formatVND(ch.cogs)}</span>
                      </td>
                      <td className="px-4 py-3.5 text-right">
                        <span className={`text-sm font-semibold tabular-nums ${ch.gross_profit >= 0 ? 'text-success-700' : 'text-critical-600'}`}>
                          {formatVND(ch.gross_profit)}
                        </span>
                      </td>
                      <td className="px-4 py-3.5 text-right">
                        <span className="text-xs font-medium text-text-secondary tabular-nums">{chMargin}%</span>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        </Panel>
      )}

      {/* Operational Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 mb-6">
        {/* Inventory Health */}
        <Panel
          title="Inventory Health"
          subtitle="Products approaching or below reorder threshold."
          action={
            <button
              onClick={() => {
                void navigate('/inventory')
              }}
              className="flex items-center gap-1 text-xs text-primary-600 hover:text-primary-700 font-medium focus-visible:outline-none cursor-pointer"
            >
              View inventory <ChevronRight className="w-3.5 h-3.5" />
            </button>
          }

          noPadding
        >
          {inventoryQuery.isLoading ? (
            <div className="px-5 pb-5 space-y-2">
              {Array.from({ length: 3 }).map((_, i) => (
                <Skeleton key={i} className="h-10 rounded-lg" />
              ))}
            </div>
          ) : atRiskInventory.length === 0 ? (
            <div className="px-5 py-8 text-center">
              <p className="text-sm text-success-600 font-medium">All stock levels healthy.</p>
            </div>
          ) : (
            <div className="divide-y divide-border">
              {atRiskInventory.map((item) => {
                const status = getInventoryStatus(item.current_stock, item.reorder_threshold)
                return (
                  <div key={item.sku} className="flex items-center justify-between px-5 py-3 gap-3">
                    <div className="min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="font-mono-data text-xs text-gray-800 font-medium">{item.sku}</span>
                        <InventoryStatusBadge status={status} />
                      </div>
                      <p className="text-xs text-text-secondary mt-0.5 truncate">{item.name}</p>
                    </div>
                    <div className="text-right flex-shrink-0">
                      <div
                        className={`text-sm font-bold tabular-nums ${
                          status === 'out' ? 'text-critical-600' : 'text-warning-600'
                        }`}
                      >
                        {item.current_stock} units
                      </div>
                      <div className="text-[11px] text-text-muted">threshold: {item.reorder_threshold}</div>
                    </div>
                  </div>
                )
              })}
            </div>
          )}
        </Panel>

        {/* Reconciliation Status */}
        <Panel
          title="Reconciliation Status"
          subtitle="Latest reconciliation run per source."
          action={
            <button
              onClick={() => {
                void navigate('/reconciliation')
              }}
              className="flex items-center gap-1 text-xs text-primary-600 hover:text-primary-700 font-medium focus-visible:outline-none cursor-pointer"
            >
              View reconciliation <ChevronRight className="w-3.5 h-3.5" />
            </button>
          }
          noPadding
        >
          {reconciliationsQuery.isLoading ? (
            <div className="px-5 pb-5 space-y-2">
              {Array.from({ length: 3 }).map((_, i) => (
                <Skeleton key={i} className="h-14 rounded-lg" />
              ))}
            </div>
          ) : reconciliations.length === 0 ? (
            <div className="px-5 py-8 text-center text-sm text-text-secondary">
              No reconciliation runs recorded yet.
            </div>
          ) : (
            <div className="divide-y divide-border">
              {reconciliations.slice(0, 3).map((r) => (
                <div key={r.id} className="flex items-center justify-between px-5 py-3 gap-3">
                  <div className="min-w-0">
                    <div className="flex items-center gap-2 mb-0.5">
                      <span className="text-sm font-medium text-gray-800 capitalize">{r.source_system}</span>
                      <span
                        className={`inline-flex items-center gap-0.5 text-[11px] font-semibold px-1.5 py-0.5 rounded-md ${
                          r.status === 'success'
                            ? 'bg-success-50 text-success-700'
                            : r.status === 'mismatch'
                            ? 'bg-critical-50 text-critical-600'
                            : 'bg-gray-100 text-gray-600'
                        }`}
                      >
                        {r.status === 'success' ? 'Success' : r.status === 'mismatch' ? 'Mismatch' : 'Failed'}
                      </span>
                    </div>
                    <p className="text-xs text-text-secondary">
                      {r.records_checked.toLocaleString()} records checked
                      {r.mismatches_found > 0 && (
                        <span className="text-critical-600 font-medium ml-1">
                          • {r.mismatches_found} mismatches
                        </span>
                      )}
                    </p>
                  </div>
                  {r.completed_at && (
                    <div className="text-[11px] text-text-muted text-right flex-shrink-0">
                      {formatDateTime(r.completed_at)}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </Panel>
      </div>

      {/* Active Alerts */}
      <Panel
        title="Active Alerts"
        subtitle="Operational issues requiring attention."
        action={
          <button
            onClick={() => {
              void navigate('/alerts')
            }}
            className="flex items-center gap-1 text-xs text-primary-600 hover:text-primary-700 font-medium focus-visible:outline-none cursor-pointer"
          >
            View all alerts <ChevronRight className="w-3.5 h-3.5" />
          </button>
        }

        noPadding
      >
        {alertsQuery.isLoading ? (
          <div className="px-5 pb-5 space-y-2">
            {Array.from({ length: 3 }).map((_, i) => (
              <Skeleton key={i} className="h-14 rounded-lg" />
            ))}
          </div>
        ) : activeAlerts.length === 0 ? (
          <div className="px-5 py-8 text-center">
            <p className="text-sm text-success-600 font-medium">No active alerts. Everything looks good.</p>
          </div>
        ) : (
          <div className="divide-y divide-border">
            {activeAlerts.map((alert) => (
              <div key={alert.id} className="flex items-start gap-3 px-5 py-3.5">
                <div className="flex-shrink-0 mt-0.5">
                  <SeverityBadge severity={alert.severity} />
                </div>
                <div className="min-w-0 flex-1">
                  <div className="text-xs font-semibold text-gray-700 mb-0.5 capitalize">
                    {alert.type.replace(/_/g, ' ')}
                  </div>
                  <p className="text-sm text-gray-600 leading-snug">{alert.message}</p>
                </div>
                <div className="text-[11px] text-text-muted flex-shrink-0 mt-0.5">
                  {formatDateTime(alert.created_at)}
                </div>
              </div>
            ))}
          </div>
        )}
      </Panel>
    </div>
  )
}
