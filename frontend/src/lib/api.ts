import { z } from 'zod'

const errorEnvelopeSchema = z.object({
  error: z.object({
    code: z.string(),
    message: z.string(),
    request_id: z.string().optional(),
    details: z.unknown().optional(),
  }),
})

export class ApiError extends Error {
  readonly status: number
  readonly code: string
  readonly requestId?: string

  constructor(status: number, code: string, message: string, requestId?: string) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.code = code
    this.requestId = requestId
  }
}

export function resolveApiBaseUrl(raw?: string): string {
  const trimmed = raw?.trim()
  return trimmed && trimmed.length > 0 ? trimmed.replace(/\/$/, '') : '/api/v1'
}

export const API_BASE_URL = resolveApiBaseUrl(
  import.meta.env.VITE_API_BASE_URL as string | undefined,
)

export async function apiRequest<T>(
  path: string,
  schema: z.ZodType<T>,
  init?: RequestInit,
): Promise<T> {
  const normalizedPath = path.startsWith('/') ? path : `/${path}`
  const url = `${API_BASE_URL}${normalizedPath}`
  const response = await fetch(url, {
    ...init,
    headers: {
      Accept: 'application/json',
      ...(init?.body ? { 'Content-Type': 'application/json' } : {}),
      ...init?.headers,
    },
  })

  const contentType = response.headers.get('content-type') || ''
  const isJson = contentType.includes('application/json')
  const payload: unknown = isJson ? await response.json().catch(() => null) : null

  if (!response.ok) {
    const headerRequestId = response.headers.get('x-request-id') || undefined
    if (payload && typeof payload === 'object') {
      const parsed = errorEnvelopeSchema.safeParse(payload)
      if (parsed.success) {
        throw new ApiError(
          response.status,
          parsed.data.error.code,
          parsed.data.error.message,
          parsed.data.error.request_id || headerRequestId,
        )
      }
    }
    throw new ApiError(
      response.status,
      'HTTP_ERROR',
      `Request to ${url} failed with status ${response.status}`,
      headerRequestId,
    )
  }

  if (!isJson) {
    throw new ApiError(
      response.status,
      'INVALID_RESPONSE',
      `Expected JSON response from ${url}, but received content-type '${contentType}'`,
    )
  }

  if (payload === null || payload === undefined) {
    throw new ApiError(
      response.status,
      'EMPTY_RESPONSE',
      `Received empty response payload from ${url}`,
    )
  }

  return schema.parse(payload)
}
