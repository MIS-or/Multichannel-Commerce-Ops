import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { z } from 'zod'

import { apiRequest } from '../../lib/api'

export const exceptionDomainSchema = z.enum([
  'inventory_variance',
  'settlement_discrepancy',
  'order_sync_failed',
  'data_normalization',
])

export const exceptionSeveritySchema = z.enum([
  'low',
  'medium',
  'high',
  'critical',
])

export const exceptionStatusSchema = z.enum([
  'open',
  'investigating',
  'resolved',
  'ignored',
])

export const rootCauseCategorySchema = z.enum([
  'platform_fee_overcharge',
  'physical_inventory_shrinkage',
  'channel_sync_delay',
  'malformed_external_payload',
  'operator_data_entry_error',
  'other',
])

export const exceptionReadSchema = z.object({
  id: z.number(),
  domain: exceptionDomainSchema,
  severity: exceptionSeveritySchema,
  status: exceptionStatusSchema,
  reference_id: z.string(),
  channel_code: z.string().nullable().optional(),
  title: z.string(),
  description: z.string(),
  variance_amount: z.union([z.number(), z.string()]).nullable().optional(),
  payload_snapshot: z.record(z.string(), z.any()).optional().default({}),
  assigned_to: z.string().nullable().optional(),
  root_cause: rootCauseCategorySchema.nullable().optional(),
  resolution_notes: z.string().nullable().optional(),
  created_at: z.string(),
  updated_at: z.string(),
  resolved_at: z.string().nullable().optional(),
})

const exceptionsListSchema = z.array(exceptionReadSchema)

export type ExceptionDomain = z.infer<typeof exceptionDomainSchema>
export type ExceptionSeverity = z.infer<typeof exceptionSeveritySchema>
export type ExceptionStatus = z.infer<typeof exceptionStatusSchema>
export type RootCauseCategory = z.infer<typeof rootCauseCategorySchema>
export type OperationalException = z.infer<typeof exceptionReadSchema>

export interface ExceptionFilterParams {
  status?: string
  domain?: string
  severity?: string
  channel_code?: string
  limit?: number
}

export function useExceptions(params?: ExceptionFilterParams) {
  return useQuery({
    queryKey: ['exceptions', params],
    queryFn: ({ signal }) => {
      const searchParams = new URLSearchParams()
      if (params?.status && params.status !== 'all') {
        searchParams.set('status', params.status)
      }
      if (params?.domain && params.domain !== 'all') {
        searchParams.set('domain', params.domain)
      }
      if (params?.severity && params.severity !== 'all') {
        searchParams.set('severity', params.severity)
      }
      if (params?.channel_code && params.channel_code !== 'all') {
        searchParams.set('channel_code', params.channel_code)
      }
      if (params?.limit) {
        searchParams.set('limit', String(params.limit))
      }
      const qs = searchParams.toString()
      const path = `/exceptions${qs ? `?${qs}` : ''}`
      return apiRequest(path, exceptionsListSchema, { signal })
    },
  })
}

export function useAssignException() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, assigned_to }: { id: number; assigned_to: string }) =>
      apiRequest(`/exceptions/${id}/assign`, exceptionReadSchema, {
        method: 'POST',
        body: JSON.stringify({ assigned_to }),
      }),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['exceptions'] })
    },
  })
}

export function useResolveException() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({
      id,
      root_cause,
      resolution_notes,
    }: {
      id: number
      root_cause: RootCauseCategory
      resolution_notes: string
    }) =>
      apiRequest(`/exceptions/${id}/resolve`, exceptionReadSchema, {
        method: 'POST',
        body: JSON.stringify({ root_cause, resolution_notes }),
      }),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['exceptions'] })
      await queryClient.invalidateQueries({ queryKey: ['alerts'] })
      await queryClient.invalidateQueries({ queryKey: ['reconciliation'] })
    },
  })
}

export function useIgnoreException() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, reason }: { id: number; reason: string }) =>
      apiRequest(`/exceptions/${id}/ignore`, exceptionReadSchema, {
        method: 'POST',
        body: JSON.stringify({ reason }),
      }),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['exceptions'] })
    },
  })
}
