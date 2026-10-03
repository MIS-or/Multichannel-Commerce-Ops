import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { z } from 'zod'

import { apiRequest } from '../../lib/api'

export const triggerEventSchema = z.enum([
  'inventory_variance_detected',
  'settlement_discrepancy_detected',
  'exception_created',
  'order_ingested',
])

export const actionTypeSchema = z.enum([
  'create_exception',
  'create_alert',
  'trigger_webhook',
  'auto_assign_exception',
])

export const ruleConditionSchema = z.object({
  field: z.string(),
  operator: z.string(),
  value: z.any(),
})

export const ruleReadSchema = z.object({
  id: z.number(),
  name: z.string(),
  description: z.string().nullable().optional(),
  trigger_event: z.string(),
  conditions: z.array(z.record(z.string(), z.any())),
  actions: z.array(z.record(z.string(), z.any())),
  is_active: z.boolean(),
  priority: z.number(),
  created_at: z.string(),
  updated_at: z.string(),
})

export const ruleExecutionStatusSchema = z.enum(['success', 'failed', 'skipped'])

export const ruleExecutionLogReadSchema = z.object({
  id: z.number(),
  rule_id: z.number(),
  trigger_event: z.string(),
  matched: z.boolean(),
  status: z.string(),
  payload_snapshot: z.record(z.string(), z.any()).default({}),
  actions_taken: z.array(z.record(z.string(), z.any())).default([]),
  error_message: z.string().nullable().optional(),
  executed_at: z.string(),
})

export const ruleEvaluateResponseSchema = z.object({
  evaluated_count: z.number(),
  matched_count: z.number(),
  logs: z.array(ruleExecutionLogReadSchema),
})

export type Rule = z.infer<typeof ruleReadSchema>
export type RuleExecutionLog = z.infer<typeof ruleExecutionLogReadSchema>
export type TriggerEvent = z.infer<typeof triggerEventSchema>
export type ActionType = z.infer<typeof actionTypeSchema>
export type RuleEvaluateResponse = z.infer<typeof ruleEvaluateResponseSchema>

export interface RuleUpdatePayload {
  name?: string
  description?: string
  is_active?: boolean
  priority?: number
  conditions?: Array<{ field: string; operator: string; value: unknown }>
  actions?: Array<Record<string, unknown>>
}

export function useRules(activeOnly = false) {
  return useQuery({
    queryKey: ['rules', { activeOnly }],
    queryFn: ({ signal }) =>
      apiRequest(
        `/rules${activeOnly ? '?active_only=true' : ''}`,
        z.array(ruleReadSchema),
        { signal },
      ),
    refetchInterval: 15000,
  })
}

export function useRuleLogs(params?: { ruleId?: number; limit?: number }) {
  return useQuery({
    queryKey: ['rules', 'logs', params],
    queryFn: ({ signal }) => {
      const searchParams = new URLSearchParams()
      if (params?.ruleId) searchParams.set('rule_id', String(params.ruleId))
      if (params?.limit) searchParams.set('limit', String(params.limit))
      const qs = searchParams.toString()
      return apiRequest(
        `/rules/logs${qs ? `?${qs}` : ''}`,
        z.array(ruleExecutionLogReadSchema),
        { signal },
      )
    },
    refetchInterval: 10000,
  })
}

export function useUpdateRule() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, payload }: { id: number; payload: RuleUpdatePayload }) =>
      apiRequest(`/rules/${id}`, ruleReadSchema, {
        method: 'PATCH',
        body: JSON.stringify(payload),
      }),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['rules'] })
    },
  })
}

export function useEvaluateRule() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({
      trigger_event,
      context,
    }: {
      trigger_event: string
      context: Record<string, unknown>
    }) =>
      apiRequest('/rules/evaluate', ruleEvaluateResponseSchema, {
        method: 'POST',
        body: JSON.stringify({ trigger_event, context }),
      }),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['rules', 'logs'] })
    },
  })
}
