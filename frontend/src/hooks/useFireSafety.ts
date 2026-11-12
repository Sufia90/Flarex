import { useQuery } from '@tanstack/react-query'
import {
  getDetectionInsights,
  getFireSafetySummary,
  getInsightsForExperiment,
  getInsightsForHardware,
  getPreventionInsights,
  getSuppressionInsights,
  listFireSafetyInsights,
} from '../services/fire-safety'
import type { FireSafetyInsightFilters } from '../services/fire-safety'
import type { FireSafetyInsight, FireSafetySummary, PaginatedList } from '../types'

export const fireSafetyQueryKey = ['fire-safety'] as const

export const fireSafetyInsightsQueryKey = (filters: FireSafetyInsightFilters) =>
  [...fireSafetyQueryKey, 'insights', filters] as const

export const fireSafetySummaryQueryKey = [...fireSafetyQueryKey, 'summary'] as const

export const fireSafetyCategoryQueryKey = (category: string, page: number, pageSize: number) =>
  [...fireSafetyQueryKey, category, page, pageSize] as const

export const insightsForExperimentQueryKey = (experimentId: string) =>
  [...fireSafetyQueryKey, 'experiments', experimentId] as const

export const insightsForHardwareQueryKey = (hardwareId: string) =>
  [...fireSafetyQueryKey, 'hardware', hardwareId] as const

export function useFireSafetyInsights(filters: FireSafetyInsightFilters = {}) {
  return useQuery<PaginatedList<FireSafetyInsight>, Error>({
    queryKey: fireSafetyInsightsQueryKey(filters),
    queryFn: ({ signal }) => listFireSafetyInsights(filters, signal),
  })
}

export function usePreventionInsights(page = 1, pageSize = 20) {
  return useQuery<PaginatedList<FireSafetyInsight>, Error>({
    queryKey: fireSafetyCategoryQueryKey('prevention', page, pageSize),
    queryFn: ({ signal }) => getPreventionInsights(page, pageSize, signal),
  })
}

export function useDetectionInsights(page = 1, pageSize = 20) {
  return useQuery<PaginatedList<FireSafetyInsight>, Error>({
    queryKey: fireSafetyCategoryQueryKey('detection', page, pageSize),
    queryFn: ({ signal }) => getDetectionInsights(page, pageSize, signal),
  })
}

export function useSuppressionInsights(page = 1, pageSize = 20) {
  return useQuery<PaginatedList<FireSafetyInsight>, Error>({
    queryKey: fireSafetyCategoryQueryKey('suppression', page, pageSize),
    queryFn: ({ signal }) => getSuppressionInsights(page, pageSize, signal),
  })
}

export function useFireSafetySummary() {
  return useQuery<FireSafetySummary, Error>({
    queryKey: fireSafetySummaryQueryKey,
    queryFn: ({ signal }) => getFireSafetySummary(signal),
  })
}

export function useInsightsForExperiment(experimentId: string, enabled = true) {
  return useQuery<FireSafetyInsight[], Error>({
    queryKey: insightsForExperimentQueryKey(experimentId),
    queryFn: ({ signal }) => getInsightsForExperiment(experimentId, signal),
    enabled: enabled && experimentId !== '',
  })
}

export function useInsightsForHardware(hardwareId: string, enabled = true) {
  return useQuery<FireSafetyInsight[], Error>({
    queryKey: insightsForHardwareQueryKey(hardwareId),
    queryFn: ({ signal }) => getInsightsForHardware(hardwareId, signal),
    enabled: enabled && hardwareId !== '',
  })
}
