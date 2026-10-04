import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import * as api from '../lib/api'
import { ToastProvider } from '../components/Toast'
import { IntegrationsPage } from './IntegrationsPage'

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

describe('IntegrationsPage', () => {
  let queryClient: QueryClient

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
      },
    })
    vi.clearAllMocks()
  })

  it('renders connector health and sync telemetry', async () => {
    const mockHealth = {
      connectors: [
        {
          channel_code: 'odoo_erp',
          is_healthy: true,
          latency_ms: 12,
          message: 'Odoo ERP XML-RPC ping successful',
          details: {},
        },
        {
          channel_code: 'shopee_vn',
          is_healthy: true,
          latency_ms: 35,
          message: 'Shopee Open API connected',
          details: {},
        },
      ],
      healthy_count: 2,
      total_count: 2,
    }

    const mockSyncRuns = [
      {
        id: 1,
        channel_code: 'shopee_vn',
        sync_type: 'orders',
        status: 'success',
        records_fetched: 25,
        records_processed: 25,
        records_failed: 0,
        cursor_value: '2026-10-03T10:00:00Z',
        error_details: null,
        duration_ms: 180,
        started_at: '2026-10-03T10:00:00Z',
        completed_at: '2026-10-03T10:00:01Z',
      },
    ]

    vi.mocked(api.apiRequest).mockImplementation((path: string) => {
      if (path.includes('/integrations/health')) {
        return Promise.resolve(mockHealth)
      }
      if (path.includes('/integrations/sync-runs')) {
        return Promise.resolve(mockSyncRuns)
      }
      return Promise.resolve(null)
    })


    render(
      <QueryClientProvider client={queryClient}>
        <ToastProvider>
          <IntegrationsPage />
        </ToastProvider>
      </QueryClientProvider>
    )


    expect(screen.getByText('Integrations & Sync Telemetry')).toBeInTheDocument()

    await waitFor(() => {
      expect(screen.getByText('ODOO ERP')).toBeInTheDocument()
      expect(screen.getByText('SHOPEE VN')).toBeInTheDocument()
    })

    expect(screen.getByText('12 ms')).toBeInTheDocument()
    expect(screen.getByText('#1')).toBeInTheDocument()
    expect(screen.getByText('SUCCESS')).toBeInTheDocument()
  })
})
