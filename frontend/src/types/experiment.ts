import type { BaseRecord, DataQuality, VerificationStatus } from './common'

export interface ExperimentalConditions {
  fuel_material: string | null
  oxygen_concentration: number | null
  oxygen_unit: string | null
  oxygen_basis: string | null
  ambient_pressure: number | null
  pressure_unit: string | null
  temperature: number | null
  temperature_unit: string | null
  airflow_velocity: number | null
  airflow_unit: string | null
  airflow_direction: string | null
  gravity_condition: string | null
  sample_geometry: string | null
  sample_dimensions: string | null
  other_conditions: Record<string, unknown> | null
}

export type MeasurementKind = 'measured' | 'derived' | 'interpreted'

export interface Measurement extends BaseRecord {
  experiment_id: string
  test_id: string | null
  parameter_name: string
  parameter_description: string | null
  value: boolean | number | string | null
  unit: string | null
  measurement_kind: MeasurementKind | null
  original_field_name: string | null
  measurement_method: string | null
  sensor: string | null
  time_point: string | null
  source_id: string | null
  verification_status: VerificationStatus
}

export type FireSafetyCategoryValue = 'prevention' | 'detection' | 'suppression'

export interface Finding extends BaseRecord {
  experiment_id: string
  title: string
  observation: string | null
  conclusion: string | null
  supporting_evidence: string[]
  measurement_ids: string[]
  limitations: string[]
  fire_safety_relevance: FireSafetyCategoryValue[]
  source_id: string | null
  verification_status: VerificationStatus
}

export type MissionApplicability = 'ISS' | 'Moon' | 'Mars'

export interface Experiment extends BaseRecord {
  nasa_investigation_id: string | null
  name: string
  acronym: string | null
  description: string | null
  scientific_objective: string | null
  research_category: string | null
  combustion_type: string | null
  fuel_material: string | null
  sample_geometry: string | null
  sample_dimensions: string | null
  hardware_ids: string[]
  related_investigation_ids: string[]
  conditions: ExperimentalConditions | null
  measurements: Measurement[]
  findings: Finding[]
  limitations: string[]
  source_ids: string[]
  media_ids: string[]
  mission_applicability: MissionApplicability[]
  transferability_note: string | null
  fire_safety_relevance: FireSafetyCategoryValue[]
  data_quality: DataQuality
}
