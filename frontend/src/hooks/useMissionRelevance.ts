import { useQuery } from '@tanstack/react-query'
import {
  getMissionRelevanceForExperiment,
  getMissionRelevanceForHardware,
} from '../services/mission-relevance'
import type { MissionContext, MissionRelevanceAssessment } from '../types'

export const missionRelevanceQueryKey = (subjectType: string, subjectId: string, mission: MissionContext) =>
  ['mission-relevance', subjectType, subjectId, mission] as const

export function useMissionRelevanceForExperiment(experimentId: string, mission: MissionContext, enabled = true) {
  return useQuery<MissionRelevanceAssessment, Error>({
    queryKey: missionRelevanceQueryKey('experiment', experimentId, mission),
    queryFn: ({ signal }) => getMissionRelevanceForExperiment(experimentId, mission, signal),
    enabled: enabled && experimentId !== '',
  })
}

export function useMissionRelevanceForHardware(hardwareId: string, mission: MissionContext, enabled = true) {
  return useQuery<MissionRelevanceAssessment, Error>({
    queryKey: missionRelevanceQueryKey('hardware', hardwareId, mission),
    queryFn: ({ signal }) => getMissionRelevanceForHardware(hardwareId, mission, signal),
    enabled: enabled && hardwareId !== '',
  })
}
