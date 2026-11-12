export type VerificationStatus = 'confirmed' | 'partially_documented' | 'unverified' | 'verification_failed'

export type DataCompleteness = 'complete' | 'partially_complete' | 'incomplete' | 'not_yet_verified'

export type MissingValue = 'missing' | 'unknown' | 'not_reported' | 'not_applicable'

export interface BaseRecord {
  id: string
  schema_version: string
  created_at: string | null
  updated_at: string | null
  status: string
}

export interface DataQuality {
  completeness: DataCompleteness
  verification_status: VerificationStatus
  missing_fields: string[]
  notes: string | null
}

export interface ApiErrorResponse {
  detail: string
}

export interface PaginatedList<T> {
  total: number
  page: number
  page_size: number
  total_pages: number
  items: T[]
}

export interface DeleteResponse {
  message: string
  deleted_id: string
}

export interface HealthResponse {
  status: string
  service: string
}