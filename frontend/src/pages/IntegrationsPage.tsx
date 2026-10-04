import { useState } from 'react'
import { Play, RefreshCw } from 'lucide-react'

import {
  ChannelBadge,
  SyncStatusBadge,
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
  type SyncType,
  useIntegrationHealth,
  useSyncRuns,
  useTriggerSync,
} from '../features/integrations/api'
import { formatDateTime } from '../utils'

const CHANNEL_OPTIONS = [
  { value: 'shopee_vn', label: 'Shopee Vietnam' },
  { value: 'tiktok_shop_vn', label: 'TikTok Shop Vietnam' },
  { value: 'odoo_erp', label: 'Odoo ERP (Physical SoT)' },
]

const SYNC_TYPES: Array<{ value: SyncType; label: string }> = [
  { value: 'orders', label: 'Orders Synchronization' },
  { value: 'inventory', label: 'Inventory Snapshots' },
  { value: 'settlement', label: 'Settlement Payouts' },
]

export function IntegrationsPage() {
  const [selectedChannel, setSelectedChannel] = useState<string>('shopee_vn')
  const [selectedSyncType, setSelectedSyncType] = useState<SyncType>('orders')
  const [filterChannel, setFilterChannel] = useState<string>('all')

  const { addToast } = useToast()

  const {
    data: healthData,
    isLoading: isHealthLoading,
    error: healthError,
    refetch: refetchHealth,
  } = useIntegrationHealth()

  const {
    data: syncRuns,
    isLoading: isRunsLoading,
    error: runsError,
    refetch: refetchRuns,
  } = useSyncRuns({
    channel_code: filterChannel,
    limit: 50,
  })

  const triggerMutation = useTriggerSync()

  const handleTriggerSync = async () => {
    try {
      const response = await triggerMutation.mutateAsync({
        channel_code: selectedChannel,
        sync_type: selectedSyncType,
        max_retries: 3,
      })
      addToast({
        type: 'success',
        message: `Sync initiated: ${response.message} (Fetched: ${response.sync_run.records_fetched}, Processed: ${response.sync_run.records_processed})`,
      })
      void refetchRuns()
    } catch (err) {
      addToast({
        type: 'error',
        message: err instanceof Error ? err.message : 'Sync execution failed.',
      })
    }
  }

  const hasError = healthError || runsError

  if (hasError) {
    const errorObj = healthError || runsError
    return (
      <div className="p-6 max-w-[1440px] w-full">
        <PageHeader
          title="Integrations & Sync Telemetry"
          subtitle="Real-time connector health and automated pipeline synchronization."
        />
        <ErrorState
          title="Failed to load integration telemetry"
          description={errorObj instanceof Error ? errorObj.message : 'Please check your connection and retry.'}
          requestId={errorObj instanceof ApiError ? errorObj.requestId : undefined}
          onRetry={() => {
            void refetchHealth()
            void refetchRuns()
          }}
        />
      </div>
    )
  }

  return (
    <div className="p-6 max-w-[1440px] w-full">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
        <PageHeader
          title="Integrations & Sync Telemetry"
          subtitle="Real-time connector health and automated pipeline synchronization."
        />
        <div className="flex items-center gap-2 self-start sm:self-auto">
          <Button
            variant="secondary"
            size="sm"
            onClick={() => {
              void refetchHealth()
              void refetchRuns()
            }}
          >
            <RefreshCw className="w-3.5 h-3.5 mr-1" />
            Refresh Telemetry
          </Button>
        </div>
      </div>

      {/* Health Overview KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-6">
        <MetricCard
          label="Active Connectors"
          value={
            isHealthLoading
              ? '...'
              : `${healthData?.healthy_count ?? 0} / ${healthData?.total_count ?? 0}`
          }
          description="Đầu mối kết nối trực tiếp (Shopee, TikTok Shop, Odoo SoT)"
          accent="info"
        />
        <MetricCard
          label="Sync Pipelines"
          value="Automated"
          valueClassName="text-emerald-600 font-bold"
          description="Đồng bộ Đơn hàng, Tồn kho snapshot và Đối soát payout"
          accent="success"
        />
        <MetricCard
          label="Recent Sync Runs"
          value={isRunsLoading ? '...' : (syncRuns?.length ?? 0)}
          valueClassName="font-bold font-mono"
          description="Lịch sử các tiến trình đồng bộ gần nhất được ghi nhận"
          accent="default"
        />
      </div>

      {/* Connectors Health Status Cards */}
      <div className="mb-6">
        <h3 className="text-sm font-bold text-gray-900 mb-3">
          Channel & ERP Connection Health
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {isHealthLoading ? (
            Array.from({ length: 3 }).map((_, i) => (
              <div key={i} className="h-28 bg-white border border-border rounded-xl p-4 animate-pulse" />
            ))
          ) : !healthData?.connectors || healthData.connectors.length === 0 ? (
            <div className="col-span-3">
              <EmptyState title="No connectors configured" />
            </div>
          ) : (
            healthData.connectors.map((c) => (
              <div
                key={c.channel_code}
                className="bg-white border border-border rounded-xl p-4 shadow-xs flex flex-col justify-between"
              >
                <div>
                  <div className="flex items-center justify-between gap-2 mb-2">
                    <span className="text-xs font-bold text-gray-900">
                      {c.channel_code.replace(/_/g, ' ').toUpperCase()}
                    </span>

                    <span
                      className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-[11px] font-semibold ${
                        c.is_healthy
                          ? 'bg-emerald-50 text-emerald-700'
                          : 'bg-red-50 text-red-700'
                      }`}
                    >
                      <span className={`w-1.5 h-1.5 rounded-full flex-shrink-0 ${c.is_healthy ? 'bg-emerald-500' : 'bg-red-500'}`} />
                      {c.is_healthy ? 'Online' : 'Offline'}
                    </span>
                  </div>
                  <p className="text-xs text-text-secondary leading-snug">{c.message}</p>
                </div>

                <div className="flex items-center justify-between text-[11px] text-text-muted mt-3 pt-2 border-t border-border">
                  <span>Latency:</span>
                  <span className="font-mono-data font-semibold text-gray-800">
                    {c.latency_ms !== null && c.latency_ms !== undefined
                      ? `${c.latency_ms} ms`
                      : 'N/A'}
                  </span>
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Manual Sync Trigger Control Box */}
      <div className="bg-white border border-border rounded-xl p-5 shadow-xs mb-6">
        <h3 className="text-sm font-bold text-gray-900 mb-1">
          Trigger Manual Channel Synchronization
        </h3>
        <p className="text-xs text-text-secondary mb-4">
          Execute an on-demand batch pull and canonical normalization pipeline with automatic exponential backoff retry.
        </p>

        <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-3">
          <div className="flex-1">
            <label className="block text-[11px] font-semibold text-gray-600 mb-1">Target Channel</label>
            <select
              value={selectedChannel}
              onChange={(e) => setSelectedChannel(e.target.value)}
              className="w-full text-xs px-3 py-2 border border-border rounded-lg bg-gray-50 focus:bg-white focus:outline-none focus:ring-2 focus:ring-primary-600"
            >
              {CHANNEL_OPTIONS.map((ch) => (
                <option key={ch.value} value={ch.value}>
                  {ch.label}
                </option>
              ))}
            </select>
          </div>

          <div className="flex-1">
            <label className="block text-[11px] font-semibold text-gray-600 mb-1">Pipeline Type</label>
            <select
              value={selectedSyncType}
              onChange={(e) => setSelectedSyncType(e.target.value as SyncType)}
              className="w-full text-xs px-3 py-2 border border-border rounded-lg bg-gray-50 focus:bg-white focus:outline-none focus:ring-2 focus:ring-primary-600"
            >
              {SYNC_TYPES.map((st) => (
                <option key={st.value} value={st.value}>
                  {st.label}
                </option>
              ))}
            </select>
          </div>

          <div className="sm:self-end">
            <Button
              variant="primary"
              size="md"
              onClick={() => {
                void handleTriggerSync()
              }}
              disabled={triggerMutation.isPending}
              className="w-full sm:w-auto"
            >
              {triggerMutation.isPending ? (
                <>
                  <RefreshCw className="w-4 h-4 mr-1.5 animate-spin" />
                  Running Sync...
                </>
              ) : (
                <>
                  <Play className="w-4 h-4 mr-1.5" />
                  Start Pipeline
                </>
              )}
            </Button>
          </div>
        </div>
      </div>

      {/* Sync Execution History */}
      <div className="bg-white border border-border rounded-xl overflow-hidden shadow-xs">
        <div className="p-4 border-b border-border flex items-center justify-between gap-3 flex-wrap">
          <div>
            <h3 className="text-sm font-bold text-gray-900">Sync Execution Logs &amp; Telemetry</h3>
          </div>

          <div className="flex items-center gap-2">
            <span className="text-xs text-text-secondary">Filter Channel:</span>
            <select
              value={filterChannel}
              onChange={(e) => setFilterChannel(e.target.value)}
              className="text-xs px-2.5 py-1 border border-border rounded-lg bg-white focus:outline-none"
            >
              <option value="all">All Channels</option>
              <option value="shopee_vn">Shopee VN</option>
              <option value="tiktok_shop_vn">TikTok Shop VN</option>
              <option value="odoo_erp">Odoo ERP</option>
            </select>
          </div>
        </div>

        {isRunsLoading ? (
          <table className="w-full">
            <tbody className="divide-y divide-border">
              {Array.from({ length: 5 }).map((_, i) => (
                <TableRowSkeleton key={i} cols={6} />
              ))}
            </tbody>
          </table>
        ) : !syncRuns || syncRuns.length === 0 ? (
          <EmptyState
            title="No sync runs recorded"
            description="Trigger a manual synchronization above to begin populating operational logs."
          />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse text-xs">
              <thead>
                <tr className="bg-gray-50 border-b border-border text-[11px] font-semibold text-gray-500 uppercase tracking-wider">
                  <th className="py-3 px-4">Run ID & Channel</th>
                  <th className="py-3 px-4">Sync Type</th>
                  <th className="py-3 px-4">Status</th>
                  <th className="py-3 px-4">Records (Fetch / Proc / Fail)</th>
                  <th className="py-3 px-4">Duration</th>
                  <th className="py-3 px-4">Started At</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {syncRuns.map((run) => (
                  <tr key={run.id} className="hover:bg-gray-50/80 transition-colors">
                    {/* Run ID & Channel */}
                    <td className="py-3 px-4">
                      <div className="font-semibold text-gray-900">#{run.id}</div>
                      <div className="mt-0.5">
                        <ChannelBadge channel={run.channel_code} />
                      </div>
                    </td>

                    {/* Sync Type */}
                    <td className="py-3 px-4 font-medium text-gray-700 uppercase">
                      {run.sync_type}
                    </td>

                    {/* Status */}
                    <td className="py-3 px-4">
                      <SyncStatusBadge status={run.status} />
                    </td>

                    {/* Records stats */}
                    <td className="py-3 px-4 font-mono-data">
                      <span className="text-gray-900 font-semibold">{run.records_fetched}</span>
                      <span className="text-gray-400"> / </span>
                      <span className="text-emerald-600 font-semibold">{run.records_processed}</span>
                      <span className="text-gray-400"> / </span>
                      <span
                        className={`font-semibold ${
                          run.records_failed > 0 ? 'text-red-600' : 'text-gray-500'
                        }`}
                      >
                        {run.records_failed}
                      </span>
                    </td>

                    {/* Duration */}
                    <td className="py-3 px-4 font-mono-data text-gray-700">
                      {run.duration_ms} ms
                    </td>

                    {/* Started At */}
                    <td className="py-3 px-4 text-text-muted font-mono-data text-[11px]">
                      {formatDateTime(run.started_at)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}
