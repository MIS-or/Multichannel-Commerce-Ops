import { useMemo, useState } from 'react'
import { CheckCircle2, Filter } from 'lucide-react'


import {
  ExceptionStatusBadge,
  SeverityBadge,
} from '../components/Badge'
import { Button } from '../components/Button'
import { EmptyState } from '../components/EmptyState'
import { ErrorState } from '../components/ErrorState'
import { MetricCard } from '../components/MetricCard'
import { PageHeader } from '../components/PageHeader'
import { TableRowSkeleton } from '../components/Skeleton'
import { useToast } from '../components/Toast'
import { ApiError } from '../lib/api'
import {
  type OperationalException,
  type RootCauseCategory,
  useAssignException,
  useExceptions,
  useIgnoreException,
  useResolveException,
} from '../features/exceptions/api'
import { formatCurrency, formatDateTime } from '../utils'

const STATUS_FILTERS = [
  { value: 'all', label: 'All' },
  { value: 'open', label: 'Open' },
  { value: 'investigating', label: 'Investigating' },
  { value: 'resolved', label: 'Resolved' },
  { value: 'ignored', label: 'Ignored' },
]

const DOMAIN_OPTIONS = [
  { value: 'all', label: 'All Domains' },
  { value: 'inventory_variance', label: 'Inventory Variance' },
  { value: 'settlement_discrepancy', label: 'Settlement Discrepancy' },
  { value: 'order_sync_failed', label: 'Order Sync Failed' },
  { value: 'data_normalization', label: 'Data Normalization' },
]

const ROOT_CAUSES: Array<{ value: RootCauseCategory; label: string }> = [
  { value: 'platform_fee_overcharge', label: 'Platform Fee Overcharge' },
  { value: 'physical_inventory_shrinkage', label: 'Physical Inventory Shrinkage' },
  { value: 'channel_sync_delay', label: 'Channel Sync Delay' },
  { value: 'malformed_external_payload', label: 'Malformed External Payload' },
  { value: 'operator_data_entry_error', label: 'Operator Data Entry Error' },
  { value: 'other', label: 'Other Root Cause' },
]

export function ExceptionsPage() {
  const [statusFilter, setStatusFilter] = useState<string>('open')
  const [domainFilter, setDomainFilter] = useState<string>('all')
  const [severityFilter, setSeverityFilter] = useState<string>('all')

  // Modals state
  const [assigningItem, setAssigningItem] = useState<OperationalException | null>(null)
  const [assigneeName, setAssigneeName] = useState<string>('')

  const [resolvingItem, setResolvingItem] = useState<OperationalException | null>(null)
  const [rootCause, setRootCause] = useState<RootCauseCategory>('platform_fee_overcharge')
  const [resolutionNotes, setResolutionNotes] = useState<string>('')

  const [ignoringItem, setIgnoringItem] = useState<OperationalException | null>(null)
  const [ignoreReason, setIgnoreReason] = useState<string>('')

  const { addToast } = useToast()

  const {
    data: exceptions,
    isLoading,
    error,
    refetch,
  } = useExceptions({
    status: statusFilter,
    domain: domainFilter,
    severity: severityFilter,
    limit: 100,
  })

  const assignMutation = useAssignException()
  const resolveMutation = useResolveException()
  const ignoreMutation = useIgnoreException()

  // KPI calculations
  const metrics = useMemo(() => {
    if (!exceptions) return { total: 0, critical: 0, investigating: 0, resolved: 0 }
    return {
      total: exceptions.length,
      critical: exceptions.filter((e) => e.severity === 'critical' && e.status !== 'resolved' && e.status !== 'ignored').length,
      investigating: exceptions.filter((e) => e.status === 'investigating').length,
      resolved: exceptions.filter((e) => e.status === 'resolved').length,
    }
  }, [exceptions])

  const handleAssign = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!assigningItem || !assigneeName.trim()) return

    try {
      await assignMutation.mutateAsync({
        id: assigningItem.id,
        assigned_to: assigneeName.trim(),
      })
      addToast({
        type: 'success',
        message: `Assigned exception #${assigningItem.id} to ${assigneeName.trim()}`,
      })
      setAssigningItem(null)
      setAssigneeName('')
    } catch (err) {
      addToast({
        type: 'error',
        message: err instanceof Error ? err.message : 'Failed to assign exception',
      })
    }
  }

  const handleResolve = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!resolvingItem || !resolutionNotes.trim()) return

    try {
      await resolveMutation.mutateAsync({
        id: resolvingItem.id,
        root_cause: rootCause,
        resolution_notes: resolutionNotes.trim(),
      })
      addToast({
        type: 'success',
        message: `Resolved exception #${resolvingItem.id} successfully`,
      })
      setResolvingItem(null)
      setResolutionNotes('')
    } catch (err) {
      addToast({
        type: 'error',
        message: err instanceof Error ? err.message : 'Failed to resolve exception',
      })
    }
  }

  const handleIgnore = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!ignoringItem || !ignoreReason.trim()) return

    try {
      await ignoreMutation.mutateAsync({
        id: ignoringItem.id,
        reason: ignoreReason.trim(),
      })
      addToast({
        type: 'info',
        message: `Ignored exception #${ignoringItem.id}`,
      })
      setIgnoringItem(null)
      setIgnoreReason('')
    } catch (err) {
      addToast({
        type: 'error',
        message: err instanceof Error ? err.message : 'Failed to ignore exception',
      })
    }
  }

  if (error) {
    return (
      <div className="p-6 max-w-[1440px] w-full">
        <PageHeader
          title="Operational Exceptions"
          subtitle="Lifecycle triage for inventory variances, settlement discrepancies, and channel sync issues."
        />
        <ErrorState
          title="Failed to load exceptions"
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
      <PageHeader
        title="Operational Exceptions"
        subtitle="Lifecycle triage for inventory variances, settlement discrepancies, and channel sync issues."
      />

      {/* KPI Summary Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <MetricCard
          label="Total Tracked"
          value={metrics.total}
          description="Tất cả ngoại lệ trong phạm vi bộ lọc đang chọn"
          accent="info"
        />
        <MetricCard
          label="Critical Severity"
          value={metrics.critical}
          valueClassName="text-red-600 font-bold font-mono"
          description="Ngoại lệ nghiêm trọng — cần can thiệp xử lý ngay"
          accent="danger"
        />
        <MetricCard
          label="Under Investigation"
          value={metrics.investigating}
          valueClassName="text-amber-600 font-bold font-mono"
          description="Đang được nhân sự vận hành / kế toán điều tra"
          accent="warning"
        />
        <MetricCard
          label="Resolved"
          value={metrics.resolved}
          valueClassName="text-emerald-600 font-bold font-mono"
          description="Đã xác định nguyên nhân gốc và chốt đóng hồ sơ"
          accent="success"
        />
      </div>

      {/* Filters and Controls */}
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3 mb-5">
        <div className="flex items-center gap-2 flex-wrap">
          {/* Status Tabs */}
          <div className="flex items-center bg-white border border-border rounded-lg overflow-hidden shadow-xs">
            {STATUS_FILTERS.map((f) => (
              <button
                key={f.value}
                onClick={() => setStatusFilter(f.value)}
                className={`px-3 py-1.5 text-xs font-medium transition-colors border-r border-border last:border-r-0 ${
                  statusFilter === f.value
                    ? 'bg-primary-50 text-primary-700'
                    : 'text-gray-600 hover:bg-gray-50'
                }`}
              >
                {f.label}
              </button>
            ))}
          </div>

          {/* Domain Dropdown */}
          <div className="flex items-center gap-1.5 bg-white border border-border rounded-lg px-2.5 py-1 text-xs shadow-xs">
            <Filter className="w-3.5 h-3.5 text-gray-400" />
            <select
              value={domainFilter}
              onChange={(e) => setDomainFilter(e.target.value)}
              className="bg-transparent text-gray-700 font-medium focus:outline-none"
            >
              {DOMAIN_OPTIONS.map((d) => (
                <option key={d.value} value={d.value}>
                  {d.label}
                </option>
              ))}
            </select>
          </div>

          {/* Severity Dropdown */}
          <div className="flex items-center gap-1.5 bg-white border border-border rounded-lg px-2.5 py-1 text-xs shadow-xs">
            <select
              value={severityFilter}
              onChange={(e) => setSeverityFilter(e.target.value)}
              className="bg-transparent text-gray-700 font-medium focus:outline-none"
            >
              <option value="all">All Severities</option>
              <option value="critical">Critical</option>
              <option value="high">High</option>
              <option value="medium">Medium</option>
              <option value="low">Low</option>
            </select>
          </div>
        </div>

        <div className="text-xs text-text-secondary self-end sm:self-auto font-medium">
          {exceptions?.length ?? 0} item{(exceptions?.length ?? 0) !== 1 ? 's' : ''}
        </div>
      </div>

      {/* Exceptions Table */}
      <div className="bg-white border border-border rounded-[10px] overflow-hidden shadow-xs">
        {isLoading ? (
          <table className="w-full">
            <tbody className="divide-y divide-border">
              {Array.from({ length: 5 }).map((_, i) => (
                <TableRowSkeleton key={i} cols={6} />
              ))}
            </tbody>
          </table>
        ) : !exceptions || exceptions.length === 0 ? (
          <EmptyState
            icon={CheckCircle2}
            title={statusFilter === 'open' ? 'No open exceptions' : 'No exceptions found'}
            description={
              statusFilter === 'open'
                ? 'All operational reconciliation discrepancies and sync issues are resolved.'
                : undefined
            }
          />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-gray-50 border-b border-border text-[11px] font-semibold text-gray-500 uppercase tracking-wider">
                  <th className="py-3 px-4">Severity & Status</th>
                  <th className="py-3 px-4">Domain & Reference</th>
                  <th className="py-3 px-4">Discrepancy Details</th>
                  <th className="py-3 px-4">Variance</th>
                  <th className="py-3 px-4">Assignee</th>
                  <th className="py-3 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border text-xs">
                {exceptions.map((item) => {
                  const varianceNum =
                    item.variance_amount !== null && item.variance_amount !== undefined
                      ? Number(item.variance_amount)
                      : null

                  return (
                    <tr key={item.id} className="hover:bg-gray-50/80 transition-colors">
                      {/* Severity & Status */}
                      <td className="py-3.5 px-4 align-top">
                        <div className="flex flex-col gap-1.5 items-start">
                          <SeverityBadge severity={item.severity} />
                          <ExceptionStatusBadge status={item.status} />
                        </div>
                      </td>

                      {/* Domain & Reference */}
                      <td className="py-3.5 px-4 align-top">
                        <div className="font-semibold text-gray-800">
                          {item.domain.replace(/_/g, ' ').toUpperCase()}
                        </div>
                        <div className="text-[11px] text-text-muted font-mono-data mt-0.5">
                          Ref: {item.reference_id}
                        </div>
                        {item.channel_code && (
                          <div className="inline-block mt-1 px-1.5 py-0.5 rounded bg-gray-100 text-gray-700 text-[10px] font-medium">
                            {item.channel_code}
                          </div>
                        )}
                      </td>

                      {/* Details */}
                      <td className="py-3.5 px-4 align-top max-w-xs">
                        <div className="font-medium text-gray-900 leading-snug">{item.title}</div>
                        <div className="text-[11px] text-text-secondary mt-1 line-clamp-2 leading-relaxed">
                          {item.description}
                        </div>
                        {item.root_cause && (
                          <div className="mt-1.5 text-[11px] text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200 inline-flex items-center gap-1.5 font-medium">
                            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 flex-shrink-0" />
                            Cause: {item.root_cause.replace(/_/g, ' ')}
                          </div>
                        )}
                        <div className="text-[10px] text-text-muted mt-1">
                          Logged: {formatDateTime(item.created_at)}
                        </div>
                      </td>

                      {/* Variance */}
                      <td className="py-3.5 px-4 align-top font-mono-data">
                        {varianceNum !== null ? (
                          <span
                            className={`font-semibold ${
                              varianceNum > 0
                                ? 'text-red-600'
                                : varianceNum < 0
                                ? 'text-amber-600'
                                : 'text-gray-700'
                            }`}
                          >
                            {item.domain === 'inventory_variance'
                              ? `${varianceNum > 0 ? '+' : ''}${varianceNum} units`
                              : formatCurrency(varianceNum)}
                          </span>
                        ) : (
                          <span className="text-gray-400">—</span>
                        )}
                      </td>

                      {/* Assignee */}
                      <td className="py-3.5 px-4 align-top">
                        {item.assigned_to ? (
                          <div className="inline-flex items-center gap-1.5 text-gray-800 font-medium bg-gray-100 px-2 py-0.5 rounded text-xs">
                            <span className="w-1.5 h-1.5 rounded-full bg-primary-600 flex-shrink-0" />
                            {item.assigned_to}
                          </div>
                        ) : (
                          <span className="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-medium bg-gray-100/80 text-gray-400 border border-gray-200/60">
                            Unassigned
                          </span>
                        )}
                      </td>

                      {/* Actions */}
                      <td className="py-3.5 px-4 align-top text-right space-x-1.5 whitespace-nowrap">
                        {item.status !== 'resolved' && item.status !== 'ignored' ? (
                          <>
                            <Button
                              variant="secondary"
                              size="sm"
                              onClick={() => {
                                setAssigningItem(item)
                                setAssigneeName(item.assigned_to || '')
                              }}
                            >
                              Assign
                            </Button>
                            <Button
                              variant="primary"
                              size="sm"
                              onClick={() => {
                                setResolvingItem(item)
                                setResolutionNotes('')
                              }}
                            >
                              Resolve
                            </Button>
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => {
                                setIgnoringItem(item)
                                setIgnoreReason('')
                              }}
                            >
                              Ignore
                            </Button>
                          </>
                        ) : (
                          <span className="text-[11px] text-text-muted font-medium">
                            {item.status === 'resolved' ? 'Closed' : 'Ignored'}
                          </span>
                        )}
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Assign Modal */}
      {assigningItem && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-xs p-4">
          <div className="bg-white rounded-xl shadow-lg border border-border max-w-md w-full p-5 animate-in fade-in zoom-in-95 duration-100">
            <h3 className="text-base font-bold text-gray-900 mb-1">
              Assign Operational Exception #{assigningItem.id}
            </h3>
            <p className="text-xs text-text-secondary mb-4">
              Assign ownership to an operations specialist or finance accountant.
            </p>
            <form onSubmit={(e) => { void handleAssign(e) }} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-gray-700 mb-1">
                  Assignee Name / Email
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Sarah Jenkins (Finance)"
                  value={assigneeName}
                  onChange={(e) => setAssigneeName(e.target.value)}
                  className="w-full text-xs px-3 py-2 border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-600"
                />
              </div>
              <div className="flex items-center justify-end gap-2 pt-2">
                <Button
                  type="button"
                  variant="secondary"
                  size="sm"
                  onClick={() => setAssigningItem(null)}
                >
                  Cancel
                </Button>
                <Button
                  type="submit"
                  variant="primary"
                  size="sm"
                  disabled={assignMutation.isPending || !assigneeName.trim()}
                >
                  {assignMutation.isPending ? 'Assigning...' : 'Save Assignment'}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Resolve Modal */}
      {resolvingItem && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-xs p-4">
          <div className="bg-white rounded-xl shadow-lg border border-border max-w-lg w-full p-5 animate-in fade-in zoom-in-95 duration-100">
            <h3 className="text-base font-bold text-gray-900 mb-1">
              Resolve Operational Exception #{resolvingItem.id}
            </h3>
            <p className="text-xs text-text-secondary mb-4">
              Document the root cause and audit trail notes to close this exception.
            </p>
            <form onSubmit={(e) => { void handleResolve(e) }} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-gray-700 mb-1">
                  Root Cause Category
                </label>
                <select
                  value={rootCause}
                  onChange={(e) => setRootCause(e.target.value as RootCauseCategory)}
                  className="w-full text-xs px-3 py-2 border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-600 bg-white"
                >
                  {ROOT_CAUSES.map((rc) => (
                    <option key={rc.value} value={rc.value}>
                      {rc.label}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-xs font-semibold text-gray-700 mb-1">
                  Resolution Notes (Minimum 5 characters)
                </label>
                <textarea
                  required
                  rows={3}
                  placeholder="Explain how the discrepancy was rectified (e.g. Filed ticket with TikTok Shop support for 15,000 VND voucher difference)..."
                  value={resolutionNotes}
                  onChange={(e) => setResolutionNotes(e.target.value)}
                  className="w-full text-xs px-3 py-2 border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-600"
                />
              </div>
              <div className="flex items-center justify-end gap-2 pt-2">
                <Button
                  type="button"
                  variant="secondary"
                  size="sm"
                  onClick={() => setResolvingItem(null)}
                >
                  Cancel
                </Button>
                <Button
                  type="submit"
                  variant="primary"
                  size="sm"
                  disabled={resolveMutation.isPending || resolutionNotes.trim().length < 5}
                >
                  {resolveMutation.isPending ? 'Resolving...' : 'Confirm Resolution'}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Ignore Modal */}
      {ignoringItem && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-xs p-4">
          <div className="bg-white rounded-xl shadow-lg border border-border max-w-md w-full p-5 animate-in fade-in zoom-in-95 duration-100">
            <h3 className="text-base font-bold text-gray-900 mb-1">
              Ignore Exception #{ignoringItem.id}
            </h3>
            <p className="text-xs text-text-secondary mb-4">
              Mark this exception as an acknowledged false positive or intentional operational variance.
            </p>
            <form onSubmit={(e) => { void handleIgnore(e) }} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-gray-700 mb-1">
                  Reason for Ignoring
                </label>
                <textarea
                  required
                  rows={2}
                  placeholder="e.g. Expected test order or promotional inventory write-down approved by warehouse manager..."
                  value={ignoreReason}
                  onChange={(e) => setIgnoreReason(e.target.value)}
                  className="w-full text-xs px-3 py-2 border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-600"
                />
              </div>
              <div className="flex items-center justify-end gap-2 pt-2">
                <Button
                  type="button"
                  variant="secondary"
                  size="sm"
                  onClick={() => setIgnoringItem(null)}
                >
                  Cancel
                </Button>
                <Button
                  type="submit"
                  variant="secondary"
                  size="sm"
                  disabled={ignoreMutation.isPending || ignoreReason.trim().length < 5}
                >
                  {ignoreMutation.isPending ? 'Saving...' : 'Ignore Exception'}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
