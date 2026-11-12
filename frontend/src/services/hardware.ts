import { apiClient, withQuery } from '../api/client'
import { endpoints } from '../api/endpoints'
import type { DeleteResponse, Hardware, PaginatedList } from '../types'

export type HardwareSearchFilters = {
  query?: string
  name?: string
  hardware_type?: string
  parent_hardware_id?: string
  facility_classification?: string
  supported_measurements?: string
  related_experiment_ids?: string
  page?: number
  page_size?: number
}

export type HardwareCreateInput = { name: string; hardware_type: string } & Partial<
  Omit<Hardware, 'id' | 'name' | 'hardware_type' | 'schema_version' | 'created_at' | 'updated_at' | 'status'>
>

export type HardwareUpdateInput = Partial<
  Omit<Hardware, 'id' | 'schema_version' | 'created_at' | 'updated_at' | 'status'>
>

export function listHardware(
  page = 1,
  pageSize = 20,
  signal?: AbortSignal,
): Promise<PaginatedList<Hardware>> {
  return apiClient.get<PaginatedList<Hardware>>(
    withQuery(endpoints.hardware.list, { page, page_size: pageSize }),
    { signal },
  )
}

export function searchHardware(
  filters: HardwareSearchFilters,
  signal?: AbortSignal,
): Promise<PaginatedList<Hardware>> {
  return apiClient.get<PaginatedList<Hardware>>(withQuery(endpoints.hardware.search, filters), { signal })
}

export function getHardware(hardwareId: string, signal?: AbortSignal): Promise<Hardware> {
  return apiClient.get<Hardware>(endpoints.hardware.byId(hardwareId), { signal })
}

export function createHardware(payload: HardwareCreateInput, signal?: AbortSignal): Promise<Hardware> {
  return apiClient.post<Hardware>(endpoints.hardware.list, payload, { signal })
}

export function updateHardware(
  hardwareId: string,
  payload: HardwareUpdateInput,
  signal?: AbortSignal,
): Promise<Hardware> {
  return apiClient.put<Hardware>(endpoints.hardware.byId(hardwareId), payload, { signal })
}

export function deleteHardware(hardwareId: string, signal?: AbortSignal): Promise<DeleteResponse> {
  return apiClient.delete<DeleteResponse>(endpoints.hardware.byId(hardwareId), { signal })
}
