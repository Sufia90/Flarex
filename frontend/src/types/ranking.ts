export type RankingCriterion =
  | 'hardware_experiment_associations'
  | 'experiment_documentation_completeness'
  | 'experiment_measurement_coverage'

export type RankingStatus = 'ranked' | 'insufficient_evidence'

export interface RankingItem {
  rank: number | null
  item_id: string
  item_name: string | null
  metric_value: number
  metric_max: number | null
  metric_breakdown: Record<string, number>
  evidence_ids: string[]
  data_completeness: string | null
  verification_status: string | null
  explanation: string
  limitations: string[]
}

export interface RankingResult {
  ranking_id: string | null
  criterion: RankingCriterion
  title: string
  question: string
  methodology: string
  metric_name: string
  metric_description: string
  metric_max: number | null
  status: RankingStatus
  eligible_item_ids: string[]
  items: RankingItem[]
  source_ids: string[]
  explanation: string
  limitations: string[]
}

export interface RankingRequest {
  criterion: RankingCriterion
  item_ids: string[] | null
  limit: number
}
