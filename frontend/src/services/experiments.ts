import { apiClient, withQuery } from '../api/client'
import { endpoints } from '../api/endpoints'
import type { DeleteResponse, Experiment, PaginatedList } from '../types'

export type ExperimentSearchFilters = {
  query?: string
  research_category?: string
  fuel_material?: string
  hardware_id?: string
  gravity_condition?: string
  mission_applicability?: string
  fire_safety_relevance?: string
  data_completeness?: string
  page?: number
  page_size?: number
}

export type ExperimentCreateInput = { name: string } & Partial<
  Omit<Experiment, 'id' | 'name' | 'schema_version' | 'created_at' | 'updated_at' | 'status'>
>

export type ExperimentUpdateInput = Partial<
  Omit<Experiment, 'id' | 'schema_version' | 'created_at' | 'updated_at' | 'status'>
>

export function listExperiments(
  page = 1,
  pageSize = 20,
  signal?: AbortSignal,
): Promise<PaginatedList<Experiment>> {
  return apiClient.get<PaginatedList<Experiment>>(
    withQuery(endpoints.experiments.list, { page, page_size: pageSize }),
    { signal },
  )
}

export function searchExperiments(
  filters: ExperimentSearchFilters,
  signal?: AbortSignal,
): Promise<PaginatedList<Experiment>> {
  return apiClient.get<PaginatedList<Experiment>>(withQuery(endpoints.experiments.search, filters), { signal })
}

export function getExperiment(experimentId: string, signal?: AbortSignal): Promise<Experiment> {
  return apiClient.get<Experiment>(endpoints.experiments.byId(experimentId), { signal })
}

export function createExperiment(payload: ExperimentCreateInput, signal?: AbortSignal): Promise<Experiment> {
  return apiClient.post<Experiment>(endpoints.experiments.list, payload, { signal })
}

export function updateExperiment(
  experimentId: string,
  payload: ExperimentUpdateInput,
  signal?: AbortSignal,
): Promise<Experiment> {
  return apiClient.put<Experiment>(endpoints.experiments.byId(experimentId), payload, { signal })
}

export function deleteExperiment(experimentId: string, signal?: AbortSignal): Promise<DeleteResponse> {
  return apiClient.delete<DeleteResponse>(endpoints.experiments.byId(experimentId), { signal })
}
