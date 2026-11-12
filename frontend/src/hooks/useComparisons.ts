import { useMutation } from '@tanstack/react-query'
import { compareExperiments, compareHardware, compareMeasurements } from '../services/comparisons'
import type {
  ExperimentComparison,
  ExperimentComparisonRequest,
  HardwareComparison,
  HardwareComparisonRequest,
  MeasurementComparison,
  MeasurementComparisonRequest,
} from '../types'

export function useCompareExperiments() {
  return useMutation<ExperimentComparison, Error, ExperimentComparisonRequest>({
    mutationFn: (request) => compareExperiments(request),
  })
}

export function useCompareHardware() {
  return useMutation<HardwareComparison, Error, HardwareComparisonRequest>({
    mutationFn: (request) => compareHardware(request),
  })
}

export function useCompareMeasurements() {
  return useMutation<MeasurementComparison, Error, MeasurementComparisonRequest>({
    mutationFn: (request) => compareMeasurements(request),
  })
}
