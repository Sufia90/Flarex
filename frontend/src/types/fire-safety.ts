export type FireSafetyCategory = 'prevention' | 'detection' | 'suppression'

export type FireSafetyEvidenceStatus =
  | 'documented'
  | 'potential'
  | 'unsupported'
  | 'unknown'
  | 'insufficient_evidence'

export interface EvidenceReference {
  record_type: string
  record_id: string
  experiment_id: string | null
  source_ids: string[]
  verification_status: string | null
}

export interface FireSafetyInsight {
  insight_id: string
  category: FireSafetyCategory
  evidence_status: FireSafetyEvidenceStatus
  experiment_id: string | null
  experiment_name: string | null
  hardware_ids: string[]
  finding_ids: string[]
  source_ids: string[]
  documented_evidence: string[]
  derived_interpretation: string[]
  potential_applications: string[]
  limitations: string[]
  missing_information: string[]
  verification_status: string | null
  derived: boolean
  methodology: string
  explanation: string
}

export interface FireSafetySummary {
  total_experiments: number
  total_insights: number
  prevention_count: number
  detection_count: number
  suppression_count: number
  documented_count: number
  potential_count: number
  unsupported_count: number
  unknown_count: number
  insufficient_evidence_count: number
  experiments_with_evidence: number
  experiments_without_evidence: number
  limitations: string[]
  explanation: string
}

export interface FireSafetyInsightRequest {
  category: FireSafetyCategory | null
  experiment_id: string | null
  hardware_id: string | null
  evidence_status: FireSafetyEvidenceStatus | null
  page: number
  page_size: number
}
