function readEnv(name: string): string | undefined {
  const value = import.meta.env[name] as string | undefined
  if (value === undefined || value.trim() === '') {
    return undefined
  }
  return value.trim()
}

function stripTrailingSlash(value: string): string {
  return value.replace(/\/+$/, '')
}

function normalizePrefix(value: string): string {
  const trimmed = stripTrailingSlash(value.trim())
  if (trimmed === '') {
    return ''
  }
  return trimmed.startsWith('/') ? trimmed : `/${trimmed}`
}

function readTimeoutMs(): number {
  const raw = readEnv('VITE_API_TIMEOUT_MS')
  const parsed = raw === undefined ? Number.NaN : Number(raw)
  if (Number.isFinite(parsed) && parsed > 0) {
    return parsed
  }
  return 10000
}

export const apiConfig = {
  baseUrl: stripTrailingSlash(readEnv('VITE_API_BASE_URL') ?? 'http://127.0.0.1:8000'),
  apiPrefix: normalizePrefix(readEnv('VITE_API_PREFIX') ?? '/api'),
  timeoutMs: readTimeoutMs(),
}

export const apiBaseUrl = `${apiConfig.baseUrl}${apiConfig.apiPrefix}`
