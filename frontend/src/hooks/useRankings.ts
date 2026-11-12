import { useMutation } from '@tanstack/react-query'
import { createRanking } from '../services/rankings'
import type { RankingRequest, RankingResult } from '../types'

export function useCreateRanking() {
  return useMutation<RankingResult, Error, RankingRequest>({
    mutationFn: (request) => createRanking(request),
  })
}
