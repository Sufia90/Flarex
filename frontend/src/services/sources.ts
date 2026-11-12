import { apiClient, withQuery } from '../api/client'
import { endpoints } from '../api/endpoints'
import type { DeleteResponse, PaginatedList, Source, SourceType, VerificationStatus } from '../types'

export type SourceSearchFilters = {
  query?: string
  source_type?: SourceType
  verification_status?: VerificationStatus
  nasa_report_id?: string
  publisher?: string
  page?: number
  page_size?: number
}

export type SourceCreateInput = { id: string; title: string } & Partial<
  Omit<Source, 'id' | 'title' | 'schema_version' | 'created_at' | 'updated_at' | 'status'>
>

export type SourceUpdateInput = Partial<
  Omit<Source, 'id' | 'schema_version' | 'created_at' | 'updated_at' | 'status'>
>

export function listSources(
  page = 1,
  pageSize = 20,
  signal?: AbortSignal,
): Promise<PaginatedList<Source>> {
  return apiClient.get<PaginatedList<Source>>(
    withQuery(endpoints.sources.list, { page, page_size: pageSize }),
    { signal },
  )
}

export function searchSources(
  filters: SourceSearchFilters,
  signal?: AbortSignal,
): Promise<PaginatedList<Source>> {
  return apiClient.get<PaginatedList<Source>>(withQuery(endpoints.sources.search, filters), { signal })
}

export function getSource(sourceId: string, signal?: AbortSignal): Promise<Source> {
  return apiClient.get<Source>(endpoints.sources.byId(sourceId), { signal })
}

export function createSource(payload: SourceCreateInput, signal?: AbortSignal): Promise<Source> {
  return apiClient.post<Source>(endpoints.sources.list, payload, { signal })
}

export function updateSource(
  sourceId: string,
  payload: SourceUpdateInput,
  signal?: AbortSignal,
): Promise<Source> {
  return apiClient.put<Source>(endpoints.sources.byId(sourceId), payload, { signal })
}

export function deleteSource(sourceId: string, signal?: AbortSignal): Promise<DeleteResponse> {
  return apiClient.delete<DeleteResponse>(endpoints.sources.byId(sourceId), { signal })
}

export function setSourceVerification(
  sourceId: string,
  verificationStatus: VerificationStatus,
  signal?: AbortSignal,
): Promise<Source> {
  return apiClient.post<Source>(
    endpoints.sources.verification(sourceId),
    { verification_status: verificationStatus },
    { signal },
  )
}
