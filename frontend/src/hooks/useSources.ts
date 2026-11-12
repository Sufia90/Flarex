import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  createSource,
  deleteSource,
  getSource,
  listSources,
  searchSources,
  setSourceVerification,
  updateSource,
} from '../services/sources'
import type {
  SourceCreateInput,
  SourceSearchFilters,
  SourceUpdateInput,
} from '../services/sources'
import type { PaginatedList, Source, VerificationStatus } from '../types'

export const sourcesQueryKey = ['sources'] as const

export const sourceListQueryKey = (page: number, pageSize: number) =>
  [...sourcesQueryKey, 'list', page, pageSize] as const

export const sourceQueryKey = (sourceId: string) =>
  [...sourcesQueryKey, 'detail', sourceId] as const

export const sourceSearchQueryKey = (filters: SourceSearchFilters) =>
  [...sourcesQueryKey, 'search', filters] as const

export function useSources(page = 1, pageSize = 20) {
  return useQuery<PaginatedList<Source>, Error>({
    queryKey: sourceListQueryKey(page, pageSize),
    queryFn: ({ signal }) => listSources(page, pageSize, signal),
  })
}

export function useSource(sourceId: string, enabled = true) {
  return useQuery<Source, Error>({
    queryKey: sourceQueryKey(sourceId),
    queryFn: ({ signal }) => getSource(sourceId, signal),
    enabled: enabled && sourceId !== '',
  })
}

export function useSearchSources(filters: SourceSearchFilters, enabled = true) {
  return useQuery<PaginatedList<Source>, Error>({
    queryKey: sourceSearchQueryKey(filters),
    queryFn: ({ signal }) => searchSources(filters, signal),
    enabled,
  })
}

export function useCreateSource() {
  const queryClient = useQueryClient()
  return useMutation<Source, Error, SourceCreateInput>({
    mutationFn: (payload) => createSource(payload),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: sourcesQueryKey })
    },
  })
}

export function useUpdateSource() {
  const queryClient = useQueryClient()
  return useMutation<Source, Error, { sourceId: string; payload: SourceUpdateInput }>({
    mutationFn: ({ sourceId, payload }) => updateSource(sourceId, payload),
    onSuccess: (data) => {
      void queryClient.invalidateQueries({ queryKey: sourcesQueryKey })
      void queryClient.invalidateQueries({ queryKey: sourceQueryKey(data.id) })
    },
  })
}

export function useDeleteSource() {
  const queryClient = useQueryClient()
  return useMutation<void, Error, string>({
    mutationFn: (sourceId) => deleteSource(sourceId).then(() => undefined),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: sourcesQueryKey })
    },
  })
}

export function useSetSourceVerification() {
  const queryClient = useQueryClient()
  return useMutation<Source, Error, { sourceId: string; verificationStatus: VerificationStatus }>({
    mutationFn: ({ sourceId, verificationStatus }) => setSourceVerification(sourceId, verificationStatus),
    onSuccess: (data) => {
      void queryClient.invalidateQueries({ queryKey: sourcesQueryKey })
      void queryClient.invalidateQueries({ queryKey: sourceQueryKey(data.id) })
    },
  })
}
