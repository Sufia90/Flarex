export type ApiErrorKind = 'network' | 'timeout' | 'http' | 'malformed'

export class ApiError extends Error {
  readonly kind: ApiErrorKind
  readonly status: number | null
  readonly detail: string | null

  constructor(kind: ApiErrorKind, message: string, status: number | null = null, detail: string | null = null) {
    super(message)
    this.name = 'ApiError'
    this.kind = kind
    this.status = status
    this.detail = detail
  }
}

export function isApiError(value: unknown): value is ApiError {
  return value instanceof ApiError
}

export function apiErrorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    return error.message
  }
  if (error instanceof Error) {
    return error.message
  }
  return 'An unknown error occurred.'
}

export async function httpErrorFromResponse(response: Response): Promise<ApiError> {
  let detail: string | null = null
  try {
    const data: unknown = await response.json()
    if (data !== null && typeof data === 'object' && 'detail' in data) {
      const raw = (data as { detail?: unknown }).detail
      if (typeof raw === 'string') {
        detail = raw
      } else if (raw !== undefined) {
        detail = JSON.stringify(raw)
      }
    }
  } catch {
    detail = null
  }
  const message = detail ?? `Request failed with status ${response.status}.`
  return new ApiError('http', message, response.status, detail)
}
