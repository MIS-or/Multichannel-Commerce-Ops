import { useState } from 'react'
import { RefreshCw, ArrowUpRight, X, ChevronRight } from 'lucide-react'

import { Button } from '../components/Button'
import { ConfirmDialog } from '../components/ConfirmDialog'
import { EmptyState } from '../components/EmptyState'
import { ErrorState } from '../components/ErrorState'
import { PageHeader } from '../components/PageHeader'
import { Skeleton, TableRowSkeleton } from '../components/Skeleton'
import { useToast } from '../components/Toast'
import {
  type Rule,
  type RuleExecutionLog,
  useEvaluateRule,
  useRuleLogs,
  useRules,
  useUpdateRule,
} from '../features/automation/api'
import { formatDateTime } from '../utils'

type AutomationTab = 'workflows' | 'designer'

// ─── Trigger label map ────────────────────────────────────────────────────────
const TRIGGER_META: Record<
  string,
  { label: string; short: string; color: string; dot: string }
> = {
  inventory_variance_detected: {
    label: 'Lệch tồn kho (Variance)',
    short: 'Variance',
    color: 'text-blue-700 bg-blue-50 border-blue-200',
    dot: 'bg-blue-500',
  },
  settlement_discrepancy_detected: {
    label: 'Lệch tiền sàn (Settlement)',
    short: 'Settlement',
    color: 'text-violet-700 bg-violet-50 border-violet-200',
    dot: 'bg-violet-500',
  },
  order_ingested: {
    label: 'Đơn hàng mới (Order)',
    short: 'Order',
    color: 'text-emerald-700 bg-emerald-50 border-emerald-200',
    dot: 'bg-emerald-500',
  },
  exception_created: {
    label: 'Ngoại lệ phát sinh',
    short: 'Exception',
    color: 'text-amber-700 bg-amber-50 border-amber-200',
    dot: 'bg-amber-500',
  },
}

// ─── Action type label map ────────────────────────────────────────────────────
const ACTION_LABELS: Record<string, string> = {
  create_exception: 'Tạo ngoại lệ',
  create_alert: 'Tạo cảnh báo',
  trigger_webhook: 'Gọi webhook',
  auto_assign_exception: 'Tự phân công',
}

// ─── Operator label map ───────────────────────────────────────────────────────
const OPERATOR_LABELS: Record<string, string> = {
  '>': '>',
  '>=': '≥',
  '<': '<',
  '<=': '≤',
  '==': '=',
  '!=': '≠',
  in: 'trong',
  not_in: 'ngoài',
  contains: 'chứa',
}

function TriggerBadge({ trigger }: { trigger: string }) {
  const meta = TRIGGER_META[trigger]
  if (!meta) {
    return (
      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-medium bg-gray-100 text-gray-600 border border-gray-200">
        {trigger}
      </span>
    )
  }
  return (
    <span
      className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-medium border ${meta.color}`}
    >
      <span className={`w-1.5 h-1.5 rounded-full flex-shrink-0 ${meta.dot}`} />
      {meta.label}
    </span>
  )
}

function StatusPill({ status }: { status: string }) {
  const s = status.toLowerCase()
  if (s === 'success')
    return (
      <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[11px] font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
        Thành công
      </span>
    )
  if (s === 'failed')
    return (
      <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[11px] font-semibold bg-red-50 text-red-700 border border-red-200">
        Thất bại
      </span>
    )
  return (
    <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[11px] font-medium bg-gray-100 text-gray-500 border border-gray-200">
      Bỏ qua
    </span>
  )
}

// ─── Rule detail slide-over panel ────────────────────────────────────────────
function RuleDetailPanel({
  rule,
  onClose,
  onToggle,
  onEvaluate,
}: {
  rule: Rule
  onClose: () => void
  onToggle: (r: Rule) => void
  onEvaluate: (r: Rule) => void
}) {
  return (
    <div
      className="fixed inset-0 z-50 flex"
      role="dialog"
      aria-modal="true"
      aria-label={`Chi tiết quy tắc: ${rule.name}`}
    >
      {/* backdrop */}
      <div
        className="flex-1 bg-black/30 backdrop-blur-[2px]"
        onClick={onClose}
      />
      {/* panel */}
      <div className="w-full max-w-md bg-white shadow-2xl flex flex-col animate-[slideInRight_0.2s_ease-out]">
        {/* header */}
        <div className="px-6 py-5 border-b border-border flex items-start justify-between gap-4">
          <div className="space-y-1 flex-1 min-w-0">
            <div className="flex items-center gap-2 flex-wrap">
              <span className="text-[10px] font-mono font-semibold px-1.5 py-0.5 rounded bg-gray-100 text-gray-600 tracking-wider">
                P{rule.priority}
              </span>
              <span
                className={`text-[10px] font-semibold px-2 py-0.5 rounded-full border ${rule.is_active ? 'bg-emerald-50 text-emerald-700 border-emerald-200' : 'bg-gray-100 text-gray-500 border-gray-200'}`}
              >
                {rule.is_active ? 'Đang hoạt động' : 'Tạm dừng'}
              </span>
            </div>
            <h2 className="text-base font-bold text-gray-900 leading-snug truncate">
              {rule.name}
            </h2>
            {rule.description && (
              <p className="text-xs text-text-secondary leading-relaxed">
                {rule.description}
              </p>
            )}
          </div>
          <button
            onClick={onClose}
            className="flex-shrink-0 w-8 h-8 rounded-lg flex items-center justify-center text-gray-400 hover:text-gray-700 hover:bg-gray-100 transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* body */}
        <div className="flex-1 overflow-y-auto px-6 py-5 space-y-6 text-sm">
          {/* Trigger */}
          <section>
            <h3 className="text-[10px] uppercase tracking-widest font-semibold text-text-muted mb-2">
              Sự kiện kích hoạt
            </h3>
            <TriggerBadge trigger={rule.trigger_event} />
          </section>

          {/* Conditions */}
          <section>
            <h3 className="text-[10px] uppercase tracking-widest font-semibold text-text-muted mb-2">
              Điều kiện ({rule.conditions.length || 'Luôn khớp'})
            </h3>
            {rule.conditions.length === 0 ? (
              <p className="text-xs text-text-secondary italic">
                Không có điều kiện — quy tắc luôn được kích hoạt.
              </p>
            ) : (
              <div className="space-y-2">
                {rule.conditions.map((c, i) => (
                  <div
                    key={i}
                    className="flex items-center gap-2 px-3 py-2 bg-gray-50 rounded-lg border border-border text-xs font-mono"
                  >
                    <span className="text-gray-700 font-medium">
                      {String(c.field)}
                    </span>
                    <span className="text-gray-400">
                      {OPERATOR_LABELS[String(c.operator)] || String(c.operator)}
                    </span>
                    <span className="text-primary-700 font-semibold">
                      {JSON.stringify(c.value)}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </section>

          {/* Actions */}
          <section>
            <h3 className="text-[10px] uppercase tracking-widest font-semibold text-text-muted mb-2">
              Hành động thực thi ({rule.actions.length})
            </h3>
            <div className="space-y-2">
              {rule.actions.map((a, i) => {
                const label =
                  ACTION_LABELS[String(a.action_type)] || String(a.action_type)
                return (
                  <div
                    key={i}
                    className="flex items-center justify-between px-3 py-2.5 bg-primary-50 border border-primary-200 rounded-lg"
                  >
                    <span className="text-xs font-semibold text-primary-800">
                      {label}
                    </span>
                    {a.params && (
                      <span className="text-[10px] font-mono text-primary-500 truncate max-w-[120px]">
                        {JSON.stringify(a.params)}
                      </span>
                    )}
                  </div>
                )
              })}
            </div>
          </section>

          {/* Metadata */}
          <section>
            <h3 className="text-[10px] uppercase tracking-widest font-semibold text-text-muted mb-2">
              Thông tin
            </h3>
            <dl className="grid grid-cols-2 gap-x-4 gap-y-2 text-xs">
              <dt className="text-text-secondary">ID</dt>
              <dd className="font-mono text-gray-800">#{rule.id}</dd>
              <dt className="text-text-secondary">Tạo lúc</dt>
              <dd className="text-gray-800">{formatDateTime(rule.created_at)}</dd>
              <dt className="text-text-secondary">Cập nhật</dt>
              <dd className="text-gray-800">{formatDateTime(rule.updated_at)}</dd>
            </dl>
          </section>
        </div>

        {/* footer */}
        <div className="px-6 py-4 border-t border-border flex items-center justify-between gap-3">
          <button
            onClick={() => onEvaluate(rule)}
            disabled={!rule.is_active}
            className="text-xs font-medium text-primary-600 hover:text-primary-800 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
          >
            Chạy thử quy tắc
          </button>
          <Button
            variant={rule.is_active ? 'danger' : 'primary'}
            size="sm"
            onClick={() => onToggle(rule)}
          >
            {rule.is_active ? 'Tạm dừng' : 'Kích hoạt'}
          </Button>
        </div>
      </div>
    </div>
  )
}

// ─── Log detail modal ─────────────────────────────────────────────────────────
function LogDetailModal({
  log,
  allRules,
  onClose,
}: {
  log: RuleExecutionLog
  allRules: Rule[]
  onClose: () => void
}) {
  const matchedRule = allRules.find((r) => r.id === log.rule_id)
  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40 backdrop-blur-[2px]"
      role="dialog"
      aria-modal="true"
    >
      <div className="bg-white rounded-2xl border border-border shadow-2xl w-full max-w-lg max-h-[88vh] flex flex-col">
        {/* header */}
        <div className="px-6 py-4 border-b border-border flex items-center justify-between">
          <div>
            <h3 className="text-sm font-bold text-gray-900">
              Execution Log #{log.id}
            </h3>
            <p className="text-xs text-text-secondary mt-0.5">
              {matchedRule?.name ?? `Rule #${log.rule_id}`} ·{' '}
              {formatDateTime(log.executed_at)}
            </p>
          </div>
          <button
            onClick={onClose}
            className="w-8 h-8 rounded-lg flex items-center justify-center text-gray-400 hover:text-gray-700 hover:bg-gray-100 transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto px-6 py-5 space-y-5">
          {/* Summary row */}
          <div className="flex flex-wrap gap-2">
            <TriggerBadge trigger={log.trigger_event} />
            <StatusPill status={log.status} />
            {log.matched ? (
              <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[11px] font-medium bg-emerald-50 text-emerald-700 border border-emerald-200">
                Điều kiện khớp
              </span>
            ) : (
              <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[11px] font-medium bg-gray-100 text-gray-500 border border-gray-200">
                Không khớp
              </span>
            )}
          </div>

          {/* Payload */}
          <div>
            <p className="text-[10px] uppercase tracking-widest font-semibold text-text-muted mb-2">
              Snapshot dữ liệu đầu vào
            </p>
            <pre className="p-4 bg-gray-950 text-gray-100 rounded-xl text-[11px] font-mono leading-relaxed overflow-x-auto">
              {JSON.stringify(log.payload_snapshot, null, 2)}
            </pre>
          </div>

          {/* Actions taken */}
          <div>
            <p className="text-[10px] uppercase tracking-widest font-semibold text-text-muted mb-2">
              Hành động điều phối
            </p>
            {log.actions_taken && log.actions_taken.length > 0 ? (
              <pre className="p-4 bg-gray-950 text-emerald-300 rounded-xl text-[11px] font-mono leading-relaxed overflow-x-auto">
                {JSON.stringify(log.actions_taken, null, 2)}
              </pre>
            ) : (
              <p className="text-xs text-text-secondary italic">
                Không có hành động được thực thi.
              </p>
            )}
          </div>

          {/* Error */}
          {log.error_message && (
            <div>
              <p className="text-[10px] uppercase tracking-widest font-semibold text-red-500 mb-2">
                Chi tiết lỗi
              </p>
              <div className="px-4 py-3 bg-red-50 border border-red-200 text-red-700 text-xs rounded-xl">
                {log.error_message}
              </div>
            </div>
          )}
        </div>

        <div className="px-6 py-4 border-t border-border flex justify-end">
          <Button variant="secondary" size="sm" onClick={onClose}>
            Đóng
          </Button>
        </div>
      </div>
    </div>
  )
}

// ─── Main Page ────────────────────────────────────────────────────────────────
export function AutomationPage() {
  const [activeTab, setActiveTab] = useState<AutomationTab>('workflows')
  const [searchQuery, setSearchQuery] = useState('')
  const [triggerFilter, setTriggerFilter] = useState<string>('all')

  const [selectedRule, setSelectedRule] = useState<Rule | null>(null)
  const [toggleTarget, setToggleTarget] = useState<Rule | null>(null)
  const [evaluateTarget, setEvaluateTarget] = useState<Rule | null>(null)
  const [selectedLog, setSelectedLog] = useState<RuleExecutionLog | null>(null)
  const [iframeKey, setIframeKey] = useState(0)

  const { addToast } = useToast()

  const {
    data: rules,
    isLoading: isRulesLoading,
    error: rulesError,
    refetch: refetchRules,
  } = useRules()

  const {
    data: logs,
    isLoading: isLogsLoading,
    error: logsError,
    refetch: refetchLogs,
  } = useRuleLogs({ limit: 100 })

  const updateMutation = useUpdateRule()
  const evaluateMutation = useEvaluateRule()

  const handleRefresh = async () => {
    await Promise.all([refetchRules(), refetchLogs()])
  }

  const handleConfirmToggle = async () => {
    if (!toggleTarget) return
    const nextActive = !toggleTarget.is_active
    try {
      await updateMutation.mutateAsync({
        id: toggleTarget.id,
        payload: { is_active: nextActive },
      })
      addToast({
        type: 'success',
        message: `Đã ${nextActive ? 'kích hoạt' : 'tạm dừng'} quy tắc "${toggleTarget.name}"`,
      })
      setToggleTarget(null)
      setSelectedRule(null)
    } catch (err) {
      addToast({
        type: 'error',
        message: err instanceof Error ? err.message : 'Không thể cập nhật trạng thái.',
      })
    }
  }

  const handleConfirmEvaluate = async () => {
    if (!evaluateTarget) return
    try {
      const sampleCtx: Record<string, unknown> = {
        severity: 'critical',
        variance_amount: 25000,
        total_amount: 1500000,
        channel_code: 'shopee_vn',
        sku: 'BAG-CNV',
      }
      const res = await evaluateMutation.mutateAsync({
        trigger_event: evaluateTarget.trigger_event,
        context: sampleCtx,
      })
      addToast({
        type: 'success',
        message: `Chạy thử xong: ${res.matched_count}/${res.evaluated_count} quy tắc khớp.`,
      })
      setEvaluateTarget(null)
      void refetchLogs()
    } catch (err) {
      addToast({
        type: 'error',
        message: err instanceof Error ? err.message : 'Chạy thử thất bại.',
      })
    }
  }

  // ── Error state
  if (rulesError || logsError) {
    const errObj = rulesError || logsError
    return (
      <div className="p-6 max-w-[1440px] w-full">
        <PageHeader
          eyebrow="Automation"
          title="Automation &amp; Workflows"
          subtitle="Quản trị quy tắc tự động hóa nội bộ kết hợp n8n Visual Designer."
        />
        <div className="mt-6">
          <ErrorState
            title="Không thể tải dữ liệu tự động hóa"
            message={errObj instanceof Error ? errObj.message : 'Lỗi kết nối máy chủ.'}
            onRetry={() => { void handleRefresh() }}
          />
        </div>
      </div>
    )
  }

  const allRules = rules ?? []
  const allLogs = logs ?? []

  // ── Metrics
  const activeCount = allRules.filter((r) => r.is_active).length
  const totalExec = allLogs.length
  const successExec = allLogs.filter((l) => l.status === 'success').length
  const failedExec = allLogs.filter((l) => l.status === 'failed').length
  const successRate = totalExec > 0 ? Math.round((successExec / totalExec) * 100) : 100

  // ── Filter
  const filteredRules = allRules.filter((r) => {
    const q = searchQuery.toLowerCase()
    const matchSearch =
      r.name.toLowerCase().includes(q) ||
      (r.description ?? '').toLowerCase().includes(q)
    const matchTrigger = triggerFilter === 'all' || r.trigger_event === triggerFilter
    return matchSearch && matchTrigger
  })

  const triggerOptions = [
    { value: 'all', label: 'Tất cả sự kiện' },
    { value: 'inventory_variance_detected', label: 'Lệch tồn kho' },
    { value: 'settlement_discrepancy_detected', label: 'Lệch tiền sàn' },
    { value: 'order_ingested', label: 'Đơn hàng mới' },
    { value: 'exception_created', label: 'Ngoại lệ' },
  ]

  return (
    <div className="p-6 max-w-[1440px] w-full">
      {/* ── Page header */}
      <PageHeader
        eyebrow="Operations Engine"
        title="Automation &amp; Workflows"
        subtitle="Quản trị quy tắc tự động hóa nội bộ (Native Rules) kết hợp n8n Visual DAG Designer."
        action={
          <div className="flex items-center gap-2">
            <Button
              variant="secondary"
              size="sm"
              onClick={() => { void handleRefresh() }}
            >
              <RefreshCw className="w-3.5 h-3.5" />
              Làm mới
            </Button>
            {activeTab === 'designer' && (
              <a
                href="/n8n/"
                target="_blank"
                rel="noreferrer"
                className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-border bg-white text-xs font-medium text-gray-700 hover:bg-gray-50 hover:border-gray-300 transition-colors shadow-xs"
              >
                <ArrowUpRight className="w-3.5 h-3.5" />
                Toàn màn hình
              </a>
            )}
          </div>
        }
      />

      {/* ── Tab bar */}
      <div className="border-b border-border flex items-center justify-between -mt-2 mb-6">
        <div className="flex">
          {(
            [
              { key: 'workflows', label: 'Workflows Management', count: `${activeCount}/${allRules.length}` },
              { key: 'designer', label: 'Workflow Designer (n8n Canvas)', count: 'Embedded' },
            ] as const
          ).map((tab) => (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              className={`group flex items-center gap-2 px-4 py-3 text-sm font-semibold border-b-2 transition-all cursor-pointer ${
                activeTab === tab.key
                  ? 'border-primary-600 text-primary-700'
                  : 'border-transparent text-gray-500 hover:text-gray-800 hover:border-gray-300'
              }`}
            >
              {tab.label}
              <span
                className={`text-[10px] px-1.5 py-0.5 rounded font-mono font-semibold transition-colors ${
                  activeTab === tab.key
                    ? 'bg-primary-100 text-primary-700'
                    : 'bg-gray-100 text-gray-500 group-hover:bg-gray-200'
                }`}
              >
                {tab.count}
              </span>
            </button>
          ))}
        </div>

        <div className="hidden sm:flex items-center gap-1.5 pb-3 text-xs text-text-secondary">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
          Automation Engine — Live
        </div>
      </div>

      {/* ══════════════════════════════════════════════════════════════
          TAB 1: Workflows Management
      ══════════════════════════════════════════════════════════════ */}
      {activeTab === 'workflows' && (
        <div className="space-y-6">
          {/* ── KPI strip */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            {[
              {
                label: 'Quy tắc đang chạy',
                value: isRulesLoading ? '—' : `${activeCount} / ${allRules.length}`,
                sub: 'trên tổng số quy tắc',
              },
              {
                label: 'Tổng lượt thực thi',
                value: isLogsLoading ? '—' : totalExec,
                sub: 'sự kiện đã xử lý',
              },
              {
                label: 'Tỷ lệ thành công',
                value: isLogsLoading ? '—' : `${successRate}%`,
                sub: `${successExec} thành công · ${failedExec} thất bại`,
              },
              {
                label: 'Kiến trúc điều phối',
                value: 'Hybrid',
                sub: 'FastAPI Rules + n8n DAG',
              },
            ].map(({ label, value, sub }) => (
              <div
                key={label}
                className="bg-white border border-border rounded-xl px-5 py-4 shadow-xs"
              >
                <p className="text-xs font-medium text-text-secondary mb-2">{label}</p>
                <p className="text-2xl font-bold tabular-nums text-gray-900 leading-none">
                  {value}
                </p>
                <p className="text-[11px] text-text-muted mt-1.5">{sub}</p>
              </div>
            ))}
          </div>

          {/* ── Rules table */}
          <div className="bg-white rounded-xl border border-border shadow-xs overflow-hidden">
            {/* toolbar */}
            <div className="px-5 py-4 border-b border-border flex flex-col sm:flex-row sm:items-center justify-between gap-3">
              <div>
                <h2 className="text-sm font-bold text-gray-900">
                  Danh sách quy tắc tự động hóa
                </h2>
                <p className="text-xs text-text-secondary mt-0.5">
                  Bật/tắt, kiểm thử và xem chi tiết từng bộ quy tắc vận hành.
                </p>
              </div>
              <div className="flex flex-wrap items-center gap-2">
                <input
                  type="text"
                  placeholder="Tìm quy tắc…"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-44 px-3 py-1.5 bg-gray-50 border border-border rounded-lg text-xs text-gray-800 placeholder-gray-400 focus:outline-none focus:ring-1 focus:ring-primary-600 focus:bg-white transition-colors"
                />
                <select
                  value={triggerFilter}
                  onChange={(e) => setTriggerFilter(e.target.value)}
                  className="px-2.5 py-1.5 bg-gray-50 border border-border rounded-lg text-xs text-gray-700 focus:outline-none focus:ring-1 focus:ring-primary-600"
                >
                  {triggerOptions.map((o) => (
                    <option key={o.value} value={o.value}>
                      {o.label}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            {/* body */}
            {isRulesLoading ? (
              <div className="p-5 space-y-3">
                <Skeleton className="h-16 w-full rounded-lg" />
                <Skeleton className="h-16 w-full rounded-lg" />
                <Skeleton className="h-16 w-full rounded-lg" />
              </div>
            ) : filteredRules.length === 0 ? (
              <div className="py-14">
                <EmptyState
                  title="Không tìm thấy quy tắc"
                  description="Thay đổi bộ lọc hoặc kiểm tra lại cấu hình sự kiện."
                />
              </div>
            ) : (
              <div className="divide-y divide-border">
                {filteredRules.map((rule) => {
                  const trigMeta = TRIGGER_META[rule.trigger_event]
                  return (
                    <div
                      key={rule.id}
                      className="group px-5 py-4 flex items-center justify-between gap-4 hover:bg-gray-50/70 transition-colors"
                    >
                      {/* left: info */}
                      <div className="flex-1 min-w-0 space-y-1.5">
                        <div className="flex flex-wrap items-center gap-2">
                          <span className="text-[10px] font-mono font-bold text-gray-500 bg-gray-100 px-1.5 py-0.5 rounded">
                            P{rule.priority}
                          </span>
                          <span className="text-sm font-semibold text-gray-900 truncate">
                            {rule.name}
                          </span>
                          {trigMeta && (
                            <span
                              className={`hidden sm:inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-medium border ${trigMeta.color}`}
                            >
                              <span className={`w-1.5 h-1.5 rounded-full ${trigMeta.dot}`} />
                              {trigMeta.short}
                            </span>
                          )}
                          <span
                            className={`text-[10px] font-semibold px-2 py-0.5 rounded-full border ${rule.is_active ? 'bg-emerald-50 text-emerald-700 border-emerald-200' : 'bg-gray-100 text-gray-400 border-gray-200'}`}
                          >
                            {rule.is_active ? 'Đang chạy' : 'Đã dừng'}
                          </span>
                        </div>

                        {rule.description && (
                          <p className="text-xs text-text-secondary truncate max-w-prose">
                            {rule.description}
                          </p>
                        )}

                        {/* conditions summary */}
                        <div className="flex flex-wrap items-center gap-1.5 text-[11px]">
                          <span className="text-text-muted font-mono">IF</span>
                          {rule.conditions.length === 0 ? (
                            <span className="italic text-text-muted">luôn khớp</span>
                          ) : (
                            rule.conditions.map((c, i) => (
                              <span
                                key={i}
                                className="font-mono px-1.5 py-0.5 rounded bg-gray-100 text-gray-700"
                              >
                                {String(c.field)}{' '}
                                {OPERATOR_LABELS[String(c.operator)] || String(c.operator)}{' '}
                                {JSON.stringify(c.value)}
                              </span>
                            ))
                          )}
                          <span className="text-text-muted font-mono ml-1">→</span>
                          {rule.actions.map((a, i) => (
                            <span
                              key={i}
                              className="px-1.5 py-0.5 rounded bg-primary-50 text-primary-700 font-medium"
                            >
                              {ACTION_LABELS[String(a.action_type)] || String(a.action_type)}
                            </span>
                          ))}
                        </div>
                      </div>

                      {/* right: controls */}
                      <div className="flex items-center gap-3 flex-shrink-0">
                        {/* toggle switch */}
                        <button
                          type="button"
                          role="switch"
                          aria-checked={rule.is_active}
                          aria-label={`Bật/tắt quy tắc ${rule.name}`}
                          onClick={() => setToggleTarget(rule)}
                          className={`relative inline-flex h-5 w-9 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-primary-600 focus:ring-offset-1 ${
                            rule.is_active ? 'bg-primary-600' : 'bg-gray-300'
                          }`}
                        >
                          <span
                            aria-hidden="true"
                            className={`pointer-events-none inline-block h-4 w-4 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out ${
                              rule.is_active ? 'translate-x-4' : 'translate-x-0'
                            }`}
                          />
                        </button>

                        {/* detail button */}
                        <button
                          onClick={() => setSelectedRule(rule)}
                          className="flex items-center gap-1 text-xs font-medium text-gray-400 hover:text-primary-600 transition-colors group-hover:opacity-100"
                          title="Xem chi tiết"
                        >
                          Chi tiết
                          <ChevronRight className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </div>
                  )
                })}
              </div>
            )}
          </div>

          {/* ── Execution log table */}
          <div className="bg-white rounded-xl border border-border shadow-xs overflow-hidden">
            <div className="px-5 py-4 border-b border-border flex items-center justify-between">
              <div>
                <h2 className="text-sm font-bold text-gray-900">
                  Execution Telemetry — Lịch sử thực thi
                </h2>
                <p className="text-xs text-text-secondary mt-0.5">
                  Lưu vết chi tiết từng sự kiện được đánh giá, kết quả so khớp và hành động điều phối.
                </p>
              </div>
              <span className="text-[11px] font-mono text-text-muted">
                {allLogs.length} bản ghi
              </span>
            </div>

            {isLogsLoading ? (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <tbody className="divide-y divide-border">
                    <TableRowSkeleton cols={8} />
                    <TableRowSkeleton cols={8} />
                    <TableRowSkeleton cols={8} />
                  </tbody>
                </table>
              </div>
            ) : allLogs.length === 0 ? (
              <div className="py-14">
                <EmptyState
                  title="Chưa có lịch sử thực thi"
                  description="Khi sự kiện kích hoạt, lịch sử chạy sẽ được ghi tại đây."
                />
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead className="bg-gray-50/80 border-b border-border">
                    <tr className="text-[11px] font-semibold text-text-secondary uppercase tracking-wider">
                      <th className="py-3 px-5 whitespace-nowrap">Run ID</th>
                      <th className="py-3 px-4 whitespace-nowrap">Quy tắc</th>
                      <th className="py-3 px-4 whitespace-nowrap">Sự kiện</th>
                      <th className="py-3 px-4 whitespace-nowrap">Trạng thái</th>
                      <th className="py-3 px-4 whitespace-nowrap">Khớp</th>
                      <th className="py-3 px-4 whitespace-nowrap">Hành động</th>
                      <th className="py-3 px-4 whitespace-nowrap">Thời gian</th>
                      <th className="py-3 px-4 text-right whitespace-nowrap"></th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-border">
                    {allLogs.map((log) => {
                      const matchedRule = allRules.find((r) => r.id === log.rule_id)
                      return (
                        <tr key={log.id} className="hover:bg-gray-50/60 transition-colors">
                          <td className="py-3 px-5 font-mono text-gray-400 whitespace-nowrap">
                            #{log.id}
                          </td>
                          <td className="py-3 px-4 font-medium text-gray-800 whitespace-nowrap max-w-[160px] truncate">
                            {matchedRule?.name ?? `Rule #${log.rule_id}`}
                          </td>
                          <td className="py-3 px-4 whitespace-nowrap">
                            <TriggerBadge trigger={log.trigger_event} />
                          </td>
                          <td className="py-3 px-4 whitespace-nowrap">
                            <StatusPill status={log.status} />
                          </td>
                          <td className="py-3 px-4 whitespace-nowrap">
                            {log.matched ? (
                              <span className="text-emerald-600 font-medium">Khớp</span>
                            ) : (
                              <span className="text-gray-400">—</span>
                            )}
                          </td>
                          <td className="py-3 px-4 font-mono text-[11px] text-gray-500 whitespace-nowrap">
                            {log.actions_taken?.length > 0
                              ? `${log.actions_taken.length} action`
                              : '—'}
                          </td>
                          <td className="py-3 px-4 text-text-secondary whitespace-nowrap">
                            {formatDateTime(log.executed_at)}
                          </td>
                          <td className="py-3 px-4 text-right">
                            <button
                              onClick={() => setSelectedLog(log)}
                              className="text-[11px] font-medium text-gray-400 hover:text-primary-600 transition-colors"
                            >
                              Xem
                            </button>
                          </td>
                        </tr>
                      )
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      )}

      {/* ══════════════════════════════════════════════════════════════
          TAB 2: n8n Designer
      ══════════════════════════════════════════════════════════════ */}
      {activeTab === 'designer' && (
        <div className="space-y-4">
          {/* top bar */}
          <div className="bg-white border border-border rounded-xl px-5 py-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4 shadow-xs">
            <div>
              <div className="flex items-center gap-2.5 mb-1">
                <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                <h2 className="text-sm font-bold text-gray-900">
                  Visual DAG Workflow Designer (n8n Engine)
                </h2>
                <span className="text-[10px] px-2 py-0.5 rounded font-mono font-medium bg-emerald-50 text-emerald-700 border border-emerald-200">
                  Reverse Proxy: /n8n/
                </span>
              </div>
              <p className="text-xs text-text-secondary">
                Không gian thiết kế luồng kéo thả dành cho System Architect &amp; Integration Engineer. MCO kích hoạt webhook tới n8n khi phát hiện ngoại lệ nghiêm trọng hoặc đơn VIP.
              </p>
            </div>
            <div className="flex items-center gap-2 flex-shrink-0">
              <button
                onClick={() => setIframeKey((k) => k + 1)}
                className="px-3 py-1.5 text-xs font-medium rounded-lg border border-border bg-white text-gray-700 hover:bg-gray-50 hover:border-gray-300 transition-colors shadow-xs cursor-pointer"
              >
                Tải lại canvas
              </button>
              <a
                href="/n8n/"
                target="_blank"
                rel="noreferrer"
                className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-primary-600 hover:bg-primary-700 text-white text-xs font-semibold transition-colors shadow-xs"
              >
                <ArrowUpRight className="w-3.5 h-3.5" />
                Toàn màn hình
              </a>
            </div>
          </div>

          {/* iframe */}
          <div className="bg-white rounded-xl border border-border shadow-xs overflow-hidden">
            <iframe
              key={iframeKey}
              src="/n8n/"
              title="n8n Workflow Designer Canvas"
              className="w-full h-[800px] border-0"
              allow="clipboard-read; clipboard-write"
            />
          </div>
        </div>
      )}

      {/* ── Rule detail slide-over */}
      {selectedRule && (
        <RuleDetailPanel
          rule={selectedRule}
          onClose={() => setSelectedRule(null)}
          onToggle={(r) => {
            setSelectedRule(null)
            setToggleTarget(r)
          }}
          onEvaluate={(r) => {
            setSelectedRule(null)
            setEvaluateTarget(r)
          }}
        />
      )}

      {/* ── Confirm: toggle */}
      {toggleTarget && (
        <ConfirmDialog
          title={toggleTarget.is_active ? 'Tạm Dừng Luồng Tự Động?' : 'Kích Hoạt Luồng Tự Động?'}
          description={
            <div className="space-y-2">
              <p>
                Xác nhận{' '}
                <strong className={toggleTarget.is_active ? 'text-rose-600' : 'text-emerald-600'}>
                  {toggleTarget.is_active ? 'tạm dừng' : 'kích hoạt'}
                </strong>{' '}
                quy tắc <strong>"{toggleTarget.name}"</strong>?
              </p>
              <p className="text-xs text-text-secondary">
                {toggleTarget.is_active
                  ? 'Khi dừng, các sự kiện thuộc nhóm này sẽ không kích hoạt hành động phân loại ngoại lệ hoặc gửi webhook.'
                  : 'Khi kích hoạt, hệ thống sẽ tự động phản ứng theo điều kiện đã thiết lập.'}
              </p>
            </div>
          }
          confirmLabel={toggleTarget.is_active ? 'Xác Nhận Tắt' : 'Kích Hoạt Ngay'}
          variant={toggleTarget.is_active ? 'danger' : 'primary'}
          loading={updateMutation.isPending}
          onConfirm={() => { void handleConfirmToggle() }}
          onCancel={() => setToggleTarget(null)}
        />
      )}

      {/* ── Confirm: evaluate */}
      {evaluateTarget && (
        <ConfirmDialog
          title={`Chạy thử: ${evaluateTarget.name}`}
          description={
            <div className="space-y-2">
              <p>
                Hệ thống sẽ mô phỏng sự kiện{' '}
                <strong>{evaluateTarget.trigger_event}</strong> với dữ liệu giả lập chuẩn để kiểm thử điều kiện và hành động.
              </p>
              <p className="text-xs text-text-secondary">
                Kết quả sẽ được ghi vào Execution Telemetry bên dưới.
              </p>
            </div>
          }
          confirmLabel="Bắt đầu chạy thử"
          variant="primary"
          loading={evaluateMutation.isPending}
          onConfirm={() => { void handleConfirmEvaluate() }}
          onCancel={() => setEvaluateTarget(null)}
        />
      )}

      {/* ── Log detail modal */}
      {selectedLog && (
        <LogDetailModal
          log={selectedLog}
          allRules={allRules}
          onClose={() => setSelectedLog(null)}
        />
      )}
    </div>
  )
}
