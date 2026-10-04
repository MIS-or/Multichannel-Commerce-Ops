import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { z } from 'zod'

import { ApiError, apiRequest, resolveApiBaseUrl } from './api'

describe('resolveApiBaseUrl', () => {
  it('defaults to /api/v1 when undefined or empty string', () => {
    expect(resolveApiBaseUrl(undefined)).toBe('/api/v1')
    expect(resolveApiBaseUrl('')).toBe('/api/v1')
    expect(resolveApiBaseUrl('   ')).toBe('/api/v1')
  })

  it('strips trailing slashes when a custom URL is provided', () => {
    expect(resolveApiBaseUrl('http://localhost:8000/api/v1/')).toBe('http://localhost:8000/api/v1')
    expect(resolveApiBaseUrl('/api/v1')).toBe('/api/v1')
  })
})

describe('apiRequest', () => {
  const dummySchema = z.object({
    id: z.number(),
    name: z.string(),
  })

  beforeEach(() => {
    vi.restoreAllMocks()
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('parses valid JSON response successfully', async () => {
    const mockData = { id: 1, name: 'Item 1' }
    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      headers: new Headers({ 'content-type': 'application/json' }),
      json: () => Promise.resolve(mockData),
    })

    const result = await apiRequest('/items/1', dummySchema)
    expect(result).toEqual(mockData)
  })

  it('throws ApiError with INVALID_RESPONSE when response is HTML instead of JSON', async () => {
    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      headers: new Headers({ 'content-type': 'text/html; charset=utf-8' }),
      json: () => Promise.reject(new SyntaxError('Unexpected token <')),
    })

    await expect(apiRequest('/items/1', dummySchema)).rejects.toThrow(ApiError)
    await expect(apiRequest('/items/1', dummySchema)).rejects.toThrow(/Expected JSON response/)
  })

  it('throws ApiError with EMPTY_RESPONSE when JSON payload is null', async () => {
    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      headers: new Headers({ 'content-type': 'application/json' }),
      json: () => Promise.resolve(null),
    })

    await expect(apiRequest('/items/1', dummySchema)).rejects.toThrow(ApiError)
    await expect(apiRequest('/items/1', dummySchema)).rejects.toThrow(/Received empty response payload/)
  })

  it('extracts error code and message from backend RFC error envelope', async () => {
    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 404,
      headers: new Headers({
        'content-type': 'application/json',
        'x-request-id': 'req-test-123',
      }),
      json: () =>
        Promise.resolve({
          error: {
            code: 'ORDER_NOT_FOUND',
            message: 'Order 999 not found',
          },
        }),
    })

    try {
      await apiRequest('/orders/999', dummySchema)
      expect.unreachable('Should have thrown ApiError')
    } catch (err) {
      expect(err).toBeInstanceOf(ApiError)
      const apiErr = err as ApiError
      expect(apiErr.status).toBe(404)
      expect(apiErr.code).toBe('ORDER_NOT_FOUND')
      expect(apiErr.message).toBe('Order 999 not found')
      expect(apiErr.requestId).toBe('req-test-123')
    }
  })
})
