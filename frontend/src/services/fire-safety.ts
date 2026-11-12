import { apiClient, withQuery } from '../api/client'
import { endpoints } from '../api/endpoints'
import type {
  FireSafetyCategory,
  FireSafetyEvidenceStatus,
  FireSafetyInsight,
  FireSafetySummary,
  PaginatedList,
} from '../types'

export type FireSafetyInsightFilters = {
  category?: FireSafetyCategory
  evidence_status?: FireSafetyEvidenceStatus
  experiment_id?: string
  hardware_id?: string
  mission?: string
  page?: number
  page_size?: number
}

export function listFireSafetyInsights(
  filters: FireSafetyInsightFilters = {},
  signal?: AbortSignal,
): Promise<PaginatedList<FireSafetyInsight>> {
  return apiClient.get<PaginatedList<FireSafetyInsight>>(
    withQuery(endpoints.fireSafety.insights, filters),
    { signal },
  )
}

export function getPreventionInsights(
  page = 1,
  pageSize = 20,
  signal?: AbortSignal,
): Promise<PaginatedList<FireSafetyInsight>> {
  return apiClient.get<PaginatedList<FireSafetyInsight>>(
    withQuery(endpoints.fireSafety.prevention, { page, page_size: pageSize }),
    { signal },
  )
}

export function getDetectionInsights(
  page = 1,
  pageSize = 20,
  signal?: AbortSignal,
): Promise<PaginatedList<FireSafetyInsight>> {
  return apiClient.get<PaginatedList<FireSafetyInsight>>(
    withQuery(endpoints.fireSafety.detection, { page, page_size: pageSize }),
    { signal },
  )
}

export function getSuppressionInsights(
  page = 1,
  pageSize = 20,
  signal?: AbortSignal,
): Promise<PaginatedList<FireSafetyInsight>> {
  return apiClient.get<PaginatedList<FireSafetyInsight>>(
    withQuery(endpoints.fireSafety.suppression, { page, page_size: pageSize }),
    { signal },
  )
}

export function getFireSafetySummary(signal?: AbortSignal): Promise<FireSafetySummary> {
  return apiClient.get<FireSafetySummary>(endpoints.fireSafety.summary, { signal })
}

export function getInsightsForExperiment(
  experimentId: string,
  signal?: AbortSignal,
): Promise<FireSafetyInsight[]> {
  return apiClient.get<FireSafetyInsight[]>(endpoints.fireSafety.byExperiment(experimentId), { signal })
}

export function getInsightsForHardware(
  hardwareId: string,
  signal?: AbortSignal,
): Promise<FireSafetyInsight[]> {
  return apiClient.get<FireSafetyInsight[]>(endpoints.fireSafety.byHardware(hardwareId), { signal })
}
