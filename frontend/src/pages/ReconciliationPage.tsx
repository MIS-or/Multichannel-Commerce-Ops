import { useMemo, useState } from 'react'
import { ArrowRight, ListChecks, Play, RefreshCw } from 'lucide-react'
import { useNavigate } from 'react-router-dom'

import { ReconciliationStatusBadge } from '../components/Badge'
import { Button } from '../components/Button'
import { ConfirmDialog } from '../components/ConfirmDialog'
import { EmptyState } from '../components/EmptyState'
import { ErrorState } from '../components/ErrorState'
import { MetricCard } from '../components/MetricCard'
import { PageHeader } from '../components/PageHeader'
import { TableRowSkeleton } from '../components/Skeleton'
import { useToast } from '../components/Toast'
import { ApiError } from '../lib/api'
import { useReconciliations, useRunReconciliation } from '../features/reconciliation/api'
import { formatDateTime } from '../utils'

const CHANNELS = ['Shopee', 'TikTok', 'Website'] as const

export function ReconciliationPage() {
  const navigate = useNavigate()
  const { data: reconciliations, isLoading, error, refetch, isRefetching } = useReconciliations()
  const runMutation = useRunReconciliation()
  const { addToast } = useToast()

  const [isModalOpen, setIsModalOpen] = useState(false)
  const [selectedChannel, setSelectedChannel] = useState<string>('Shopee')

  // Computed reconciliation KPI summary metrics
  const summaryMetrics = useMemo(() => {
    if (!reconciliations) return { total: 0, successful: 0, totalChecked: 0, totalMismatches: 0 }
    return {
      total: reconciliations.length,
      successful: reconciliations.filter((r) => r.status === 'success').length,
      totalChecked: reconciliations.reduce((acc, r) => acc + (r.records_checked || 0), 0),
      totalMismatches: reconciliations.reduce((acc, r) => acc + (r.mismatches_found || 0), 0),
    }
  }, [reconciliations])

  const handleRunReconciliation = async () => {
    try {
      // Create sample order snapshots for reconciliation based on channel
      const sampleOrders = [
        { external_order_id: `${selectedChannel.toUpperCase().slice(0, 3)}-ORD-101`, total_amount: 125000 },
        { external_order_id: `${selectedChannel.toUpperCase().slice(0, 3)}-ORD-102`, total_amount: 350000 },
      ]

      const result = await runMutation.mutateAsync({
        source_system: selectedChannel,
        orders: sampleOrders,
      })

      setIsModalOpen(false)
      addToast({
        type: result.status === 'success' ? 'success' : 'info',
        message: `Reconciliation for ${selectedChannel} finished with status: ${result.status}`,
      })
      void navigate(`/reconciliation/${result.id}`)
    } catch (err) {
      addToast({
        type: 'error',
        message: err instanceof Error ? err.message : 'Failed to trigger reconciliation.',
      })
    }
  }

  if (error) {
    return (
      <div className="p-6 max-w-[1440px] w-full">
        <PageHeader
          title="Reconciliation"
          subtitle="Verify source orders against MCO order and ledger records."
        />
        <ErrorState
          title="Failed to load reconciliation history"
          description={error instanceof Error ? error.message : 'Please check your connection and retry.'}
          requestId={error instanceof ApiError ? error.requestId : undefined}
          onRetry={() => {
            void refetch()
          }}
        />
      </div>
    )
  }

  return (
    <div className="p-6 max-w-[1440px] w-full">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
        <PageHeader
          title="Reconciliation"
          subtitle="Verify source orders against MCO order and ledger records."
        />
        <div className="flex items-center gap-2">
          <Button
            variant="secondary"
            size="sm"
            onClick={() => {
              void refetch()
            }}
            disabled={isRefetching}
          >
            <RefreshCw className={`w-3.5 h-3.5 mr-1.5 ${isRefetching ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
          <Button
            variant="primary"
            size="sm"
            onClick={() => setIsModalOpen(true)}
          >
            <Play className="w-3.5 h-3.5 mr-1.5" />
            Run Reconciliation
          </Button>
        </div>
      </div>

      {/* Reconciliation KPI Overview */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <MetricCard
          label="Tổng phiên đối soát"
          value={isLoading ? '...' : summaryMetrics.total}
          description="Lịch sử đối soát đơn hàng và payout dòng tiền"
          accent="info"
        />
        <MetricCard
          label="Khớp hoàn toàn"
          value={isLoading ? '...' : summaryMetrics.successful}
          valueClassName="text-emerald-600 font-bold font-mono"
          description="Phiên đối soát không phát hiện sai lệch số liệu"
          accent="success"
        />
        <MetricCard
          label="Lệch phát hiện"
          value={isLoading ? '...' : summaryMetrics.totalMismatches}
          valueClassName={
            summaryMetrics.totalMismatches > 0
              ? 'text-red-600 font-bold font-mono'
              : 'text-gray-900 font-bold font-mono'
          }
          description="Số đơn hoặc giao dịch có sai lệch cần tạo ngoại lệ"
          accent={summaryMetrics.totalMismatches > 0 ? 'danger' : 'default'}
        />
        <MetricCard
          label="Đơn đã kiểm tra"
          value={isLoading ? '...' : summaryMetrics.totalChecked.toLocaleString()}
          valueClassName="font-bold font-mono"
          description="Tổng số bản ghi giao dịch đã được quét đối soát"
          accent="default"
        />
      </div>

      <div className="bg-white border border-border rounded-[10px] overflow-hidden shadow-xs">
        <div className="overflow-x-auto">
          <table className="w-full min-w-[700px]">
            <thead>
              <tr className="border-b border-border bg-gray-50">
                <th className="px-4 py-3 text-left text-[12px] font-semibold text-text-secondary uppercase tracking-wide">
                  Source
                </th>
                <th className="px-4 py-3 text-left text-[12px] font-semibold text-text-secondary uppercase tracking-wide">
                  Status
                </th>
                <th className="px-4 py-3 text-left text-[12px] font-semibold text-text-secondary uppercase tracking-wide">
                  Started At
                </th>
                <th className="px-4 py-3 text-left text-[12px] font-semibold text-text-secondary uppercase tracking-wide">
                  Completed At
                </th>
                <th className="px-4 py-3 text-right text-[12px] font-semibold text-text-secondary uppercase tracking-wide">
                  Records
                </th>
                <th className="px-4 py-3 text-right text-[12px] font-semibold text-text-secondary uppercase tracking-wide">
                  Mismatches
                </th>
                <th className="px-4 py-3 text-right text-[12px] font-semibold text-text-secondary uppercase tracking-wide">
                  Action
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {isLoading ? (
                Array.from({ length: 4 }).map((_, i) => <TableRowSkeleton key={i} cols={7} />)
              ) : !reconciliations || reconciliations.length === 0 ? (
                <tr>
                  <td colSpan={7}>
                    <EmptyState
                      icon={ListChecks}
                      title="No reconciliation runs yet."
                      description="Click 'Run Reconciliation' to compare source system data with MCO ledgers."
                    />
                  </td>
                </tr>
              ) : (
                reconciliations.map((r) => (
                  <tr
                    key={r.id}
                    className="table-row-hover hover:bg-gray-50 cursor-pointer transition-colors"
                    onClick={() => {
                      void navigate(`/reconciliation/${r.id}`)
                    }}
                  >
                    <td className="px-4 py-3.5">
                      <span className="text-sm font-semibold text-gray-800">{r.source_system}</span>
                    </td>
                    <td className="px-4 py-3.5">
                      <ReconciliationStatusBadge status={r.status} />
                    </td>
                    <td className="px-4 py-3.5">
                      <span className="text-sm text-gray-700 font-mono-data">
                        {formatDateTime(r.started_at)}
                      </span>
                    </td>
                    <td className="px-4 py-3.5">
                      <span className="text-sm text-gray-700 font-mono-data">
                        {r.completed_at ? formatDateTime(r.completed_at) : <span className="text-text-muted">—</span>}
                      </span>
                    </td>
                    <td className="px-4 py-3.5 text-right">
                      <span className="text-sm tabular-nums text-gray-700 font-medium">
                        {r.records_checked.toLocaleString()}
                      </span>
                    </td>
                    <td className="px-4 py-3.5 text-right">
                      {r.status === 'failed' ? (
                        <span className="text-sm text-text-muted">—</span>
                      ) : (
                        <span
                          className={`text-sm font-bold tabular-nums ${
                            r.mismatches_found > 0 ? 'text-critical-600' : 'text-gray-700'
                          }`}
                        >
                          {r.mismatches_found}
                        </span>
                      )}
                    </td>
                    <td className="px-4 py-3.5 text-right">
                      <button
                        onClick={(e) => {
                          e.stopPropagation()
                          void navigate(`/reconciliation/${r.id}`)
                        }}
                        className="inline-flex items-center gap-1 text-xs text-primary-600 hover:text-primary-700 font-medium focus-visible:outline-none"
                      >
                        View detail
                        <ArrowRight className="w-3 h-3" />
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Trigger Dialog */}
      {isModalOpen && (
        <ConfirmDialog
          title="Run Reconciliation"
          description={
            <div className="space-y-3 pt-2">
              <p className="text-sm text-gray-600">
                Select a channel source system to reconcile orders, revenue entries, and inventory cost snapshots.
              </p>
              <div className="flex gap-2">
                {CHANNELS.map((ch) => (
                  <button
                    key={ch}
                    type="button"
                    onClick={() => setSelectedChannel(ch)}
                    className={`px-3 py-1.5 rounded-lg border text-sm font-medium transition-colors ${
                      selectedChannel === ch
                        ? 'border-primary-600 bg-primary-50 text-primary-700'
                        : 'border-border bg-white text-gray-700 hover:bg-gray-50'
                    }`}
                  >
                    {ch}
                  </button>
                ))}
              </div>
            </div>
          }
          confirmLabel="Start Run"
          cancelLabel="Cancel"
          loading={runMutation.isPending}
          onConfirm={() => {
            void handleRunReconciliation()
          }}
          onCancel={() => setIsModalOpen(false)}
        />
      )}
    </div>
  )
}
