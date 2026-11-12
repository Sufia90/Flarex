import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  createExperiment,
  deleteExperiment,
  getExperiment,
  listExperiments,
  searchExperiments,
  updateExperiment,
} from '../services/experiments'
import type {
  ExperimentCreateInput,
  ExperimentSearchFilters,
  ExperimentUpdateInput,
} from '../services/experiments'
import type { Experiment, PaginatedList } from '../types'

export const experimentsQueryKey = ['experiments'] as const

export const experimentListQueryKey = (page: number, pageSize: number) =>
  [...experimentsQueryKey, 'list', page, pageSize] as const

export const experimentQueryKey = (experimentId: string) =>
  [...experimentsQueryKey, 'detail', experimentId] as const

export const experimentSearchQueryKey = (filters: ExperimentSearchFilters) =>
  [...experimentsQueryKey, 'search', filters] as const

export function useExperiments(page = 1, pageSize = 20) {
  return useQuery<PaginatedList<Experiment>, Error>({
    queryKey: experimentListQueryKey(page, pageSize),
    queryFn: ({ signal }) => listExperiments(page, pageSize, signal),
  })
}

export function useExperiment(experimentId: string, enabled = true) {
  return useQuery<Experiment, Error>({
    queryKey: experimentQueryKey(experimentId),
    queryFn: ({ signal }) => getExperiment(experimentId, signal),
    enabled: enabled && experimentId !== '',
  })
}

export function useSearchExperiments(filters: ExperimentSearchFilters, enabled = true) {
  return useQuery<PaginatedList<Experiment>, Error>({
    queryKey: experimentSearchQueryKey(filters),
    queryFn: ({ signal }) => searchExperiments(filters, signal),
    enabled,
  })
}

export function useCreateExperiment() {
  const queryClient = useQueryClient()
  return useMutation<Experiment, Error, ExperimentCreateInput>({
    mutationFn: (payload) => createExperiment(payload),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: experimentsQueryKey })
    },
  })
}

export function useUpdateExperiment() {
  const queryClient = useQueryClient()
  return useMutation<Experiment, Error, { experimentId: string; payload: ExperimentUpdateInput }>({
    mutationFn: ({ experimentId, payload }) => updateExperiment(experimentId, payload),
    onSuccess: (data) => {
      void queryClient.invalidateQueries({ queryKey: experimentsQueryKey })
      void queryClient.invalidateQueries({ queryKey: experimentQueryKey(data.id) })
    },
  })
}

export function useDeleteExperiment() {
  const queryClient = useQueryClient()
  return useMutation<void, Error, string>({
    mutationFn: (experimentId) => deleteExperiment(experimentId).then(() => undefined),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: experimentsQueryKey })
    },
  })
}
