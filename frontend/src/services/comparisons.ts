import { apiClient } from '../api/client'
import { endpoints } from '../api/endpoints'
import type {
  ExperimentComparison,
  ExperimentComparisonRequest,
  HardwareComparison,
  HardwareComparisonRequest,
  MeasurementComparison,
  MeasurementComparisonRequest,
} from '../types'

export function compareExperiments(
  request: ExperimentComparisonRequest,
  signal?: AbortSignal,
): Promise<ExperimentComparison> {
  return apiClient.post<ExperimentComparison>(endpoints.comparisons.experiments, request, { signal })
}

export function compareHardware(
  request: HardwareComparisonRequest,
  signal?: AbortSignal,
): Promise<HardwareComparison> {
  return apiClient.post<HardwareComparison>(endpoints.comparisons.hardware, request, { signal })
}

export function compareMeasurements(
  request: MeasurementComparisonRequest,
  signal?: AbortSignal,
): Promise<MeasurementComparison> {
  return apiClient.post<MeasurementComparison>(endpoints.comparisons.measurements, request, { signal })
}
