import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { ToastProvider } from '../components/Toast'
import * as api from '../lib/api'
import { AutomationPage } from './AutomationPage'

vi.mock('../lib/api', () => ({
  apiRequest: vi.fn(),
  ApiError: class ApiError extends Error {
    status: number
    code: string
    constructor(status: number, code: string, message: string) {
      super(message)
      this.status = status
      this.code = code
    }
  },
}))

describe('AutomationPage', () => {
  let queryClient: QueryClient

  const mockRules = [
    {
      id: 1,
      name: 'Auto-Triage Critical Inventory Discrepancy',
      description: 'Create an operational exception when inventory variance severity is CRITICAL.',
      trigger_event: 'inventory_variance_detected',
      conditions: [{ field: 'severity', operator: 'equals', value: 'critical' }],
      actions: [{ action_type: 'create_exception' }],
      is_active: true,
      priority: 10,
      created_at: '2026-10-01T09:56:00Z',
      updated_at: '2026-10-01T09:56:00Z',
    },
    {
      id: 2,
      name: 'Alert Finance on Settlement Discrepancy',
      description: 'Dispatch alert to internal channel when settlement payout diff > 20k.',
      trigger_event: 'settlement_discrepancy_detected',
      conditions: [{ field: 'variance_amount', operator: 'greater_than_or_equal', value: 20000 }],
      actions: [{ action_type: 'create_alert' }],
      is_active: false,
      priority: 20,
      created_at: '2026-10-01T09:56:00Z',
      updated_at: '2026-10-01T09:56:00Z',
    },
  ]

  const mockLogs = [
    {
      id: 101,
      rule_id: 1,
      trigger_event: 'inventory_variance_detected',
      matched: true,
      status: 'success',
      payload_snapshot: { sku: 'BAG-CNV', variance: 12 },
      actions_taken: [{ action_type: 'create_exception', status: 'executed' }],
      error_message: null,
      executed_at: '2026-10-03T11:00:00Z',
    },
  ]

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
      },
    })
    vi.clearAllMocks()

    vi.mocked(api.apiRequest).mockImplementation((path: string) => {
      if (path.includes('/rules/logs')) {
        return Promise.resolve(mockLogs)
      }
      if (path.includes('/rules')) {
        return Promise.resolve(mockRules)
      }
      return Promise.resolve(null)
    })
  })

  it('renders Automation page with 2 tabs and metrics summary', async () => {
    render(
      <QueryClientProvider client={queryClient}>
        <ToastProvider>
          <AutomationPage />
        </ToastProvider>
      </QueryClientProvider>,
    )

    expect(screen.getByText('Automation & Workflows')).toBeInTheDocument()
    expect(screen.getByText('Workflows Management')).toBeInTheDocument()
    expect(screen.getByText('Workflow Designer (n8n Canvas)')).toBeInTheDocument()

    await waitFor(() => {
      expect(
        screen.getAllByText('Auto-Triage Critical Inventory Discrepancy')[0],
      ).toBeInTheDocument()
      expect(
        screen.getByText('Alert Finance on Settlement Discrepancy'),
      ).toBeInTheDocument()
    })
  })

  it('opens ConfirmDialog when clicking the toggle switch', async () => {
    render(
      <QueryClientProvider client={queryClient}>
        <ToastProvider>
          <AutomationPage />
        </ToastProvider>
      </QueryClientProvider>,
    )

    await waitFor(() => {
      expect(
        screen.getAllByText('Auto-Triage Critical Inventory Discrepancy')[0],
      ).toBeInTheDocument()
    })

    const switches = screen.getAllByRole('switch')
    expect(switches.length).toBe(2)

    // Click the active switch (Rule 1)
    fireEvent.click(switches[0])

    // Verify ConfirmDialog opens
    expect(screen.getByText('Tạm Dừng Luồng Tự Động?')).toBeInTheDocument()
    expect(screen.getByText('Xác Nhận Tắt')).toBeInTheDocument()
  })

  it('switches to Workflow Designer tab and renders n8n iframe', () => {
    render(
      <QueryClientProvider client={queryClient}>
        <ToastProvider>
          <AutomationPage />
        </ToastProvider>
      </QueryClientProvider>,
    )

    const designerTab = screen.getByText('Workflow Designer (n8n Canvas)')
    fireEvent.click(designerTab)

    expect(
      screen.getByText('Visual DAG Workflow Designer (n8n Engine)'),
    ).toBeInTheDocument()

    const iframe = screen.getByTitle('n8n Workflow Designer Canvas')
    expect(iframe).toBeInTheDocument()
    expect(iframe).toHaveAttribute('src', '/n8n/')
  })
})
