import { apiClient } from '../api/client'
import { endpoints } from '../api/endpoints'
import type { RankingRequest, RankingResult } from '../types'

export function createRanking(request: RankingRequest, signal?: AbortSignal): Promise<RankingResult> {
  return apiClient.post<RankingResult>(endpoints.rankings.create, request, { signal })
}
