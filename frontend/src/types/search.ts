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
  | 'deadline'
  | 'recently_added'

export interface InterpretResponse {
  chips: ConstraintChip[]
  interpretation: string
  degraded: boolean
}

export interface SearchRequestPayload {
  query?: string | null
  chips: ConstraintChip[]
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
