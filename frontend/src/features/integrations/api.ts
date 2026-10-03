import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { z } from 'zod'

import { apiRequest } from '../../lib/api'

export const connectorHealthStatusSchema = z.object({
  channel_code: z.string(),
  is_healthy: z.boolean(),
  latency_ms: z.number().nullable().optional(),
  message: z.string(),
  details: z.record(z.string(), z.any()).optional().default({}),
})

export const integrationHealthResponseSchema = z.object({
  connectors: z.array(connectorHealthStatusSchema),
  healthy_count: z.number(),
  total_count: z.number(),
})

export const syncTypeSchema = z.enum(['orders', 'inventory', 'settlement', 'settlements'])
export const syncStatusSchema = z.enum(['running', 'success', 'partial', 'partial_failure', 'failed'])

export const syncRunReadSchema = z.object({
  id: z.number(),
  channel_code: z.string(),
  sync_type: syncTypeSchema,
  status: syncStatusSchema,
  records_fetched: z.number(),
  records_processed: z.number(),
  records_failed: z.number(),
  cursor_value: z.string().nullable().optional(),
  error_details: z.record(z.string(), z.any()).nullable().optional(),
  duration_ms: z.number(),
  started_at: z.string(),
  completed_at: z.string().nullable().optional(),
})

const syncRunsListSchema = z.array(syncRunReadSchema)

export const syncTriggerResponseSchema = z.object({
  sync_run: syncRunReadSchema,
  message: z.string(),
})

export type ConnectorHealthStatus = z.infer<typeof connectorHealthStatusSchema>
export type IntegrationHealthResponse = z.infer<typeof integrationHealthResponseSchema>
export type SyncType = z.infer<typeof syncTypeSchema>
export type SyncStatus = z.infer<typeof syncStatusSchema>
export type SyncRun = z.infer<typeof syncRunReadSchema>
export type SyncTriggerResponse = z.infer<typeof syncTriggerResponseSchema>

export interface SyncRunFilterParams {
  channel_code?: string
  sync_type?: SyncType
  limit?: number
}

export function useIntegrationHealth() {
  return useQuery({
    queryKey: ['integrations', 'health'],
    queryFn: ({ signal }) =>
      apiRequest('/integrations/health', integrationHealthResponseSchema, { signal }),
    refetchInterval: 15000,
  })
}

export function useSyncRuns(params?: SyncRunFilterParams) {
  return useQuery({
    queryKey: ['integrations', 'sync-runs', params],
    queryFn: ({ signal }) => {
      const searchParams = new URLSearchParams()
      if (params?.channel_code && params.channel_code !== 'all') {
        searchParams.set('channel_code', params.channel_code)
      }
      if (params?.sync_type) {
        searchParams.set('sync_type', params.sync_type)
      }
      if (params?.limit) {
        searchParams.set('limit', String(params.limit))
      }
      const qs = searchParams.toString()
      const path = `/integrations/sync-runs${qs ? `?${qs}` : ''}`
      return apiRequest(path, syncRunsListSchema, { signal })
    },
    refetchInterval: 10000,
  })
}

export function useTriggerSync() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({
      channel_code,
      sync_type,
      cursor,
      max_retries = 3,
    }: {
      channel_code: string
      sync_type: SyncType
      cursor?: string
      max_retries?: number
    }) =>
      apiRequest(`/integrations/${channel_code}/sync`, syncTriggerResponseSchema, {
        method: 'POST',
        body: JSON.stringify({ sync_type, cursor, max_retries }),
      }),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['integrations'] })
      await queryClient.invalidateQueries({ queryKey: ['orders'] })
      await queryClient.invalidateQueries({ queryKey: ['inventory'] })
      await queryClient.invalidateQueries({ queryKey: ['reconciliation'] })
    },
  })
}
