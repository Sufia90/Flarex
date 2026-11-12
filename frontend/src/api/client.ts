import { apiBaseUrl, apiConfig } from './config'
import { ApiError, httpErrorFromResponse } from './errors'

export type HttpMethod = 'GET' | 'POST' | 'PUT' | 'DELETE'

export interface RequestOptions {
  signal?: AbortSignal
}

export function withQuery(path: string, params: Record<string, string | number | boolean | undefined | null>): string {
  const search = new URLSearchParams()
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== null && value !== '') {
      search.append(key, String(value))
    }
  }
  const query = search.toString()
  return query === '' ? path : `${path}?${query}`
}

async function parseJson<T>(response: Response): Promise<T> {
  let data: unknown
  try {
    data = await response.json()
  } catch {
    throw new ApiError('malformed', 'The backend returned a response that could not be read as JSON.')
  }
  return data as T
}

async function request<T>(method: HttpMethod, path: string, body?: unknown, options: RequestOptions = {}): Promise<T> {
  const controller = new AbortController()
  let timedOut = false
  const timeoutId = setTimeout(() => {
    timedOut = true
    controller.abort()
  }, apiConfig.timeoutMs)
  if (options.signal) {
    if (options.signal.aborted) {
      controller.abort()
    } else {
      options.signal.addEventListener('abort', () => controller.abort(), { once: true })
    }
  }
  let response: Response
  try {
    response = await fetch(`${apiBaseUrl}${path}`, {
      method,
      headers: { 'Content-Type': 'application/json' },
      body: body === undefined ? undefined : JSON.stringify(body),
      signal: controller.signal,
    })
  } catch (error) {
    clearTimeout(timeoutId)
    if (error instanceof Error && error.name === 'AbortError') {
      if (timedOut) {
        throw new ApiError('timeout', `The request timed out after ${apiConfig.timeoutMs} ms.`)
      }
      throw error
    }
    throw new ApiError('network', 'The backend could not be reached. Check that it is running and reachable.')
  }
  clearTimeout(timeoutId)
  if (!response.ok) {
    throw await httpErrorFromResponse(response)
  }
  if (response.status === 204) {
    return undefined as T
  }
  return parseJson<T>(response)
}

export const apiClient = {
  get: <T>(path: string, options?: RequestOptions) => request<T>('GET', path, undefined, options),
  post: <T>(path: string, body?: unknown, options?: RequestOptions) => request<T>('POST', path, body, options),
  put: <T>(path: string, body?: unknown, options?: RequestOptions) => request<T>('PUT', path, body, options),
  delete: <T>(path: string, options?: RequestOptions) => request<T>('DELETE', path, undefined, options),
}
