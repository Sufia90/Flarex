export type MissionContext = 'ISS' | 'Moon' | 'Mars'

export type RelevanceLevel = 'documented' | 'potential' | 'unsupported' | 'unknown' | 'insufficient_evidence'

export interface MissionRelevanceAssessment {
  assessment_id: string | null
  subject_type: string
  subject_id: string
  subject_name: string | null
  mission: MissionContext
  relevance_level: RelevanceLevel
  relevant_conditions: string[]
  similarities: string[]
  differences: string[]
  supporting_evidence: string[]
  transferability_limitations: string[]
  missing_information: string[]
  source_ids: string[]
  evidence_status: string | null
  derived_from_experiment_ids: string[]
  explanation: string
  limitations: string[]
  methodology: string
}
