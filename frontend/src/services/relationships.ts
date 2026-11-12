import { apiClient, withQuery } from '../api/client'
import { endpoints } from '../api/endpoints'
import type { DeleteResponse, ExperimentHardwareRelationship, PaginatedList } from '../types'

export type RelationshipSearchFilters = {
  query?: string
  experiment_id?: string
  hardware_id?: string
  relationship_type?: string
  verification_status?: string
  role?: string
  page?: number
  page_size?: number
}

export type RelationshipCreateInput = { experiment_id: string; hardware_id: string } & Partial<
  Omit<
    ExperimentHardwareRelationship,
    'id' | 'experiment_id' | 'hardware_id' | 'schema_version' | 'created_at' | 'updated_at' | 'status'
  >
>

export type RelationshipUpdateInput = Partial<
  Omit<ExperimentHardwareRelationship, 'id' | 'schema_version' | 'created_at' | 'updated_at' | 'status'>
>

export function listRelationships(
  page = 1,
  pageSize = 20,
  signal?: AbortSignal,
): Promise<PaginatedList<ExperimentHardwareRelationship>> {
  return apiClient.get<PaginatedList<ExperimentHardwareRelationship>>(
    withQuery(endpoints.relationships.list, { page, page_size: pageSize }),
    { signal },
  )
}

export function searchRelationships(
  filters: RelationshipSearchFilters,
  signal?: AbortSignal,
): Promise<PaginatedList<ExperimentHardwareRelationship>> {
  return apiClient.get<PaginatedList<ExperimentHardwareRelationship>>(
    withQuery(endpoints.relationships.search, filters),
    { signal },
  )
}

export function getRelationship(relationshipId: string, signal?: AbortSignal): Promise<ExperimentHardwareRelationship> {
  return apiClient.get<ExperimentHardwareRelationship>(endpoints.relationships.byId(relationshipId), { signal })
}

export function getRelationshipsByExperiment(
  experimentId: string,
  signal?: AbortSignal,
): Promise<ExperimentHardwareRelationship[]> {
  return apiClient.get<ExperimentHardwareRelationship[]>(endpoints.relationships.byExperiment(experimentId), { signal })
}

export function getRelationshipsByHardware(
  hardwareId: string,
  signal?: AbortSignal,
): Promise<ExperimentHardwareRelationship[]> {
  return apiClient.get<ExperimentHardwareRelationship[]>(endpoints.relationships.byHardware(hardwareId), { signal })
}

export function createRelationship(
  payload: RelationshipCreateInput,
  signal?: AbortSignal,
): Promise<ExperimentHardwareRelationship> {
  return apiClient.post<ExperimentHardwareRelationship>(endpoints.relationships.list, payload, { signal })
}

export function updateRelationship(
  relationshipId: string,
  payload: RelationshipUpdateInput,
  signal?: AbortSignal,
): Promise<ExperimentHardwareRelationship> {
  return apiClient.put<ExperimentHardwareRelationship>(endpoints.relationships.byId(relationshipId), payload, {
    signal,
  })
}

export function deleteRelationship(relationshipId: string, signal?: AbortSignal): Promise<DeleteResponse> {
  return apiClient.delete<DeleteResponse>(endpoints.relationships.byId(relationshipId), { signal })
}
