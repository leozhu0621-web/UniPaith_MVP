// Spec 10 — Discovery type-first program search types.
import type { ProgramSummary } from '.'

export type ConstraintCategory =
  | 'degree_level'
  | 'major'
  | 'location'
  | 'budget'
  | 'format'
  | 'start_term'
  | 'duration'
  | 'selectivity'
  | 'other'

export interface ConstraintChip {
  id?: string
  category: ConstraintCategory
  value: string
  display: string
  confidence: number
  user_confirmed?: boolean
}

export type SortOption =
  | 'relevance'
  | 'fitness'
  | 'confidence'
  | 'tuition_asc'
  | 'tuition_desc'
  | 'acceptance_asc'
  | 'acceptance_desc'
  | 'salary_desc'
  | 'employment_desc'
  | 'deadline'
  | 'recently_added'

export interface InterpretResponse {
  chips: ConstraintChip[]
  interpretation: string
  degraded: boolean
}

// Spec 10 §5 — panel-level filters that coexist with chips. Mirrors the
// backend `FilterState`; all optional. Sent alongside chips on every search;
// the backend merges them (explicit filters win on conflict with a chip).
export interface SearchFilters {
  campus_setting?: string | null
  program_name?: string | null
  country?: string | null
  region?: string | null
  city?: string | null
  degree_types?: string[] | null
  delivery_formats?: string[] | null
  min_tuition?: number | null
  max_tuition?: number | null
  min_duration_months?: number | null
  max_duration_months?: number | null
  min_acceptance_rate?: number | null
  max_acceptance_rate?: number | null
  start_year?: number | null
  min_median_salary?: number | null
  min_employment_rate?: number | null
  max_payback_months?: number | null
}

export interface SearchRequestPayload {
  query?: string | null
  chips: ConstraintChip[]
  filters?: SearchFilters | null
  sort?: SortOption
  page?: number
  page_size?: number
}

export interface SearchResponse {
  results: ProgramSummary[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

export interface CompareItemDTO {
  program_id: string
  program_name: string
  institution_name: string
  degree_type?: string | null
}

export interface CompareListResponse {
  items: CompareItemDTO[]
  max: number
}
