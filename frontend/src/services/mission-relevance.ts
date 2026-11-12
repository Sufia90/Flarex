import { apiClient, withQuery } from '../api/client'
import { endpoints } from '../api/endpoints'
import type { MissionContext, MissionRelevanceAssessment } from '../types'

export function getMissionRelevanceForExperiment(
  experimentId: string,
  mission: MissionContext,
  signal?: AbortSignal,
): Promise<MissionRelevanceAssessment> {
  return apiClient.get<MissionRelevanceAssessment>(
    withQuery(endpoints.missionRelevance.byExperiment(experimentId), { mission }),
    { signal },
  )
}

export function getMissionRelevanceForHardware(
  hardwareId: string,
  mission: MissionContext,
  signal?: AbortSignal,
): Promise<MissionRelevanceAssessment> {
  return apiClient.get<MissionRelevanceAssessment>(
    withQuery(endpoints.missionRelevance.byHardware(hardwareId), { mission }),
    { signal },
  )
}
