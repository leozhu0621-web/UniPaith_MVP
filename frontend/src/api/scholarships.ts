// Scholarships (Spec 2026-06-14) — real CareerOneStop (U.S. DOL) scholarships,
// served from the external_scholarships catalog. award_amount + deadline are
// verbatim source text (a range / a month) — render as-is, never parse.
import apiClient from './client'

export interface Scholarship {
  id: string
  external_id: string
  name: string
  organization: string | null
  purpose: string | null
  level_of_study: string | null
  award_type: string | null
  award_amount: string | null
  deadline: string | null
  url: string | null
  source: string
}

export interface ScholarshipSearch {
  items: Scholarship[]
  total: number
  page: number
}

export interface ScholarshipSearchParams {
  q?: string
  level?: string
  award_type?: string
  page?: number
  page_size?: number
}

export const searchScholarships = (params: ScholarshipSearchParams = {}) =>
  apiClient
    .get('/scholarships', { params })
    .then(r => r.data as ScholarshipSearch)

/** "For your level" — filtered by the student's study level (real signal only). */
export const getScholarshipMatches = (limit = 20) =>
  apiClient
    .get('/scholarships/matches', { params: { limit } })
    .then(r => (r.data as { items: Scholarship[] }).items ?? [])
