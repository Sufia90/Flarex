import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  createRelationship,
  deleteRelationship,
  getRelationship,
  getRelationshipsByExperiment,
  getRelationshipsByHardware,
  listRelationships,
  searchRelationships,
  updateRelationship,
} from '../services/relationships'
import type {
  RelationshipCreateInput,
  RelationshipSearchFilters,
  RelationshipUpdateInput,
} from '../services/relationships'
import type { ExperimentHardwareRelationship, PaginatedList } from '../types'

export const relationshipsQueryKey = ['relationships'] as const

export const relationshipListQueryKey = (page: number, pageSize: number) =>
  [...relationshipsQueryKey, 'list', page, pageSize] as const

export const relationshipDetailQueryKey = (relationshipId: string) =>
  [...relationshipsQueryKey, 'detail', relationshipId] as const

export const relationshipSearchQueryKey = (filters: RelationshipSearchFilters) =>
  [...relationshipsQueryKey, 'search', filters] as const

export const relationshipsByExperimentQueryKey = (experimentId: string) =>
  [...relationshipsQueryKey, 'by-experiment', experimentId] as const

export const relationshipsByHardwareQueryKey = (hardwareId: string) =>
  [...relationshipsQueryKey, 'by-hardware', hardwareId] as const

export function useRelationships(page = 1, pageSize = 20) {
  return useQuery<PaginatedList<ExperimentHardwareRelationship>, Error>({
    queryKey: relationshipListQueryKey(page, pageSize),
    queryFn: ({ signal }) => listRelationships(page, pageSize, signal),
  })
}

export function useRelationship(relationshipId: string, enabled = true) {
  return useQuery<ExperimentHardwareRelationship, Error>({
    queryKey: relationshipDetailQueryKey(relationshipId),
    queryFn: ({ signal }) => getRelationship(relationshipId, signal),
    enabled: enabled && relationshipId !== '',
  })
}

export function useSearchRelationships(filters: RelationshipSearchFilters, enabled = true) {
  return useQuery<PaginatedList<ExperimentHardwareRelationship>, Error>({
    queryKey: relationshipSearchQueryKey(filters),
    queryFn: ({ signal }) => searchRelationships(filters, signal),
    enabled,
  })
}

export function useRelationshipsByExperiment(experimentId: string, enabled = true) {
  return useQuery<PaginatedList<ExperimentHardwareRelationship>, Error>({
    queryKey: relationshipsByExperimentQueryKey(experimentId),
    queryFn: ({ signal }) => getRelationshipsByExperiment(experimentId, signal),
    enabled: enabled && experimentId !== '',
  })
}

export function useRelationshipsByHardware(hardwareId: string, enabled = true) {
  return useQuery<PaginatedList<ExperimentHardwareRelationship>, Error>({
    queryKey: relationshipsByHardwareQueryKey(hardwareId),
    queryFn: ({ signal }) => getRelationshipsByHardware(hardwareId, signal),
    enabled: enabled && hardwareId !== '',
  })
}

export function useCreateRelationship() {
  const queryClient = useQueryClient()
  return useMutation<ExperimentHardwareRelationship, Error, RelationshipCreateInput>({
    mutationFn: (payload) => createRelationship(payload),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: relationshipsQueryKey })
    },
  })
}

export function useUpdateRelationship() {
  const queryClient = useQueryClient()
  return useMutation<
    ExperimentHardwareRelationship,
    Error,
    { relationshipId: string; payload: RelationshipUpdateInput }
  >({
    mutationFn: ({ relationshipId, payload }) => updateRelationship(relationshipId, payload),
    onSuccess: (data) => {
      void queryClient.invalidateQueries({ queryKey: relationshipsQueryKey })
      void queryClient.invalidateQueries({ queryKey: relationshipDetailQueryKey(data.id) })
    },
  })
}

export function useDeleteRelationship() {
  const queryClient = useQueryClient()
  return useMutation<void, Error, string>({
    mutationFn: (relationshipId) => deleteRelationship(relationshipId).then(() => undefined),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: relationshipsQueryKey })
    },
  })
}
