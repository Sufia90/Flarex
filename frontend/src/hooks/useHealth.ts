import { useQuery } from '@tanstack/react-query'
import { getHealth } from '../services/health'
import type { HealthResponse } from '../types'

export const healthQueryKey = ['health'] as const

export function useHealth() {
  return useQuery<HealthResponse, Error>({
    queryKey: healthQueryKey,
    queryFn: ({ signal }) => getHealth(signal),
    retry: false,
    staleTime: 30000,
  })
}
