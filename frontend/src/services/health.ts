import { apiClient } from '../api/client'
import { endpoints } from '../api/endpoints'
import type { HealthResponse } from '../types'

export function getHealth(signal?: AbortSignal): Promise<HealthResponse> {
  return apiClient.get<HealthResponse>(endpoints.health, { signal })
}
