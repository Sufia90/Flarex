import type { BaseRecord, DataQuality } from './common'

export type HardwareType = 'facility' | 'apparatus' | 'component' | 'instrument'

export interface Hardware extends BaseRecord {
  name: string
  acronym: string | null
  hardware_type: HardwareType
  description: string | null
  purpose: string | null
  facility_classification: string | null
  parent_hardware_id: string | null
  component_ids: string[]
  image_ids: string[]
  diagram_ids: string[]
  supported_measurements: string[]
  related_experiment_ids: string[]
  source_ids: string[]
  limitations: string | null
  data_quality: DataQuality
}
