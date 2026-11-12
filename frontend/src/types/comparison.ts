export type ComparabilityStatus = 'comparable' | 'partially_comparable' | 'not_comparable' | 'insufficient_data'

export type ComparisonCategory =
  | 'experiment'
  | 'hardware'
  | 'measurement'
  | 'fuel_material'
  | 'oxygen_condition'
  | 'pressure_condition'
  | 'temperature_condition'
  | 'airflow_condition'
  | 'gravity_condition'

export interface ComparedValue {
  item_id: string
  value: boolean | number | string | null
  unit: string | null
  measurement_kind: string | null
  measurement_method: string | null
  sensor: string | null
  time_point: string | null
  source_id: string | null
  verification_status: string | null
  missing_reason: string | null
}

export interface ParameterComparison {
  parameter_name: string
  category: ComparisonCategory
  status: ComparabilityStatus
  reason: string
  values: ComparedValue[]
  units: string[]
  conditions_note: string | null
}

export interface ConditionComparison {
  condition_name: string
  status: ComparabilityStatus
  reason: string
  values: ComparedValue[]
}

export interface ExperimentComparison {
  comparison_id: string | null
  category: ComparisonCategory
  experiment_ids: string[]
  parameters: ParameterComparison[]
  conditions: ConditionComparison[]
  similarities: string[]
  differences: string[]
  missing_information: string[]
  incompatible_items: string[]
  source_ids: string[]
  explanation: string
  limitations: string[]
  methodology: string
}

export interface HardwareComparison {
  comparison_id: string | null
  category: ComparisonCategory
  hardware_ids: string[]
  hardware_types: string[]
  same_hardware_type: boolean
  fields: ParameterComparison[]
  shared_measurements: string[]
  unique_measurements: Record<string, string[]>
  similarities: string[]
  differences: string[]
  missing_information: string[]
  source_ids: string[]
  explanation: string
  limitations: string[]
  methodology: string
}

export interface MeasurementComparison {
  comparison_id: string | null
  category: ComparisonCategory
  measurement_ids: string[]
  parameters: ParameterComparison[]
  similarities: string[]
  differences: string[]
  missing_information: string[]
  incompatible_items: string[]
  source_ids: string[]
  explanation: string
  limitations: string[]
  methodology: string
}

export interface ExperimentComparisonRequest {
  experiment_ids: string[]
  parameters: string[] | null
  include_conditions: boolean
}

export interface HardwareComparisonRequest {
  hardware_ids: string[]
  fields: string[] | null
}

export interface MeasurementComparisonRequest {
  measurement_ids: string[]
  parameter_names: string[] | null
}
