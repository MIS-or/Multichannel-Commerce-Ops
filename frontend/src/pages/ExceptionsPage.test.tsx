import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import * as api from '../lib/api'
import { ToastProvider } from '../components/Toast'
import { ExceptionsPage } from './ExceptionsPage'

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

describe('ExceptionsPage', () => {
  let queryClient: QueryClient

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
      },
    })
    vi.clearAllMocks()
  })

  it('renders page header and metrics with mock exceptions', async () => {
    const mockExceptions = [
      {
        id: 101,
        domain: 'inventory_variance',
        severity: 'critical',
        status: 'open',
        reference_id: 'SKU-RED-SHIRT-M',
        channel_code: 'shopee_vn',
        title: 'Negative Physical Stock Detected',
        description: 'Physical warehouse count indicates -3 units.',
        variance_amount: 3,
        payload_snapshot: {},
        assigned_to: null,
        root_cause: null,
        resolution_notes: null,
        created_at: '2026-10-03T10:00:00Z',
        updated_at: '2026-10-03T10:00:00Z',
        resolved_at: null,
      },
    ]

    vi.mocked(api.apiRequest).mockResolvedValueOnce(mockExceptions)

    render(
      <QueryClientProvider client={queryClient}>
        <ToastProvider>
          <ExceptionsPage />
        </ToastProvider>
      </QueryClientProvider>
    )

    expect(screen.getByText('Operational Exceptions')).toBeInTheDocument()

    await waitFor(() => {
      expect(screen.getByText('Negative Physical Stock Detected')).toBeInTheDocument()
    })

    expect(screen.getByText('SKU-RED-SHIRT-M', { exact: false })).toBeInTheDocument()
    expect(screen.getByText('CRITICAL')).toBeInTheDocument()
    expect(screen.getByText('OPEN')).toBeInTheDocument()
  })

  it('shows empty state when no exceptions exist', async () => {
    vi.mocked(api.apiRequest).mockResolvedValueOnce([])

    render(
      <QueryClientProvider client={queryClient}>
        <ToastProvider>
          <ExceptionsPage />
        </ToastProvider>
      </QueryClientProvider>
    )

    await waitFor(() => {
      expect(screen.getByText('No open exceptions')).toBeInTheDocument()
    })
  })
})

