import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  createHardware,
  deleteHardware,
  getHardware,
  listHardware,
  searchHardware,
  updateHardware,
} from '../services/hardware'
import type {
  HardwareCreateInput,
  HardwareSearchFilters,
  HardwareUpdateInput,
} from '../services/hardware'
import type { Hardware, PaginatedList } from '../types'

export const hardwareQueryKey = ['hardware'] as const

export const hardwareListQueryKey = (page: number, pageSize: number) =>
  [...hardwareQueryKey, 'list', page, pageSize] as const

export const hardwareDetailQueryKey = (hardwareId: string) =>
  [...hardwareQueryKey, 'detail', hardwareId] as const

export const hardwareSearchQueryKey = (filters: HardwareSearchFilters) =>
  [...hardwareQueryKey, 'search', filters] as const

export function useHardware(page = 1, pageSize = 20) {
  return useQuery<PaginatedList<Hardware>, Error>({
    queryKey: hardwareListQueryKey(page, pageSize),
    queryFn: ({ signal }) => listHardware(page, pageSize, signal),
  })
}

export function useHardwareItem(hardwareId: string, enabled = true) {
  return useQuery<Hardware, Error>({
    queryKey: hardwareDetailQueryKey(hardwareId),
    queryFn: ({ signal }) => getHardware(hardwareId, signal),
    enabled: enabled && hardwareId !== '',
  })
}

export function useSearchHardware(filters: HardwareSearchFilters, enabled = true) {
  return useQuery<PaginatedList<Hardware>, Error>({
    queryKey: hardwareSearchQueryKey(filters),
    queryFn: ({ signal }) => searchHardware(filters, signal),
    enabled,
  })
}

export function useCreateHardware() {
  const queryClient = useQueryClient()
  return useMutation<Hardware, Error, HardwareCreateInput>({
    mutationFn: (payload) => createHardware(payload),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: hardwareQueryKey })
    },
  })
}

export function useUpdateHardware() {
  const queryClient = useQueryClient()
  return useMutation<Hardware, Error, { hardwareId: string; payload: HardwareUpdateInput }>({
    mutationFn: ({ hardwareId, payload }) => updateHardware(hardwareId, payload),
    onSuccess: (data) => {
      void queryClient.invalidateQueries({ queryKey: hardwareQueryKey })
      void queryClient.invalidateQueries({ queryKey: hardwareDetailQueryKey(data.id) })
    },
  })
}

export function useDeleteHardware() {
  const queryClient = useQueryClient()
  return useMutation<void, Error, string>({
    mutationFn: (hardwareId) => deleteHardware(hardwareId).then(() => undefined),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: hardwareQueryKey })
    },
  })
}
