import type { BaseRecord, VerificationStatus } from './common'

export type RelationshipType = 'used_in' | 'housed_in' | 'part_of' | 'supports' | 'produced_by'

export interface ExperimentHardwareRelationship extends BaseRecord {
  experiment_id: string
  hardware_id: string
  relationship_type: RelationshipType
  role: string | null
  evidence: string | null
  source_id: string | null
  verification_status: VerificationStatus
  notes: string | null
}

export type SourceType = 'nasa_report' | 'paper' | 'dataset' | 'website' | 'other'

export interface Source extends BaseRecord {
  source_type: SourceType
  title: string
  nasa_report_id: string | null
  doi: string | null
  url: string | null
  publisher: string | null
  publication_date: string | null
  access_date: string | null
  page_section: string | null
  description: string | null
  verification_status: VerificationStatus
}

export interface MediaReference extends BaseRecord {
  file_path: string | null
  external_url: string | null
  media_type: string | null
  caption: string | null
  description: string | null
  experiment_id: string | null
  hardware_id: string | null
  original_source_url: string | null
  credit: string | null
  license: string | null
}
