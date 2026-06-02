// Spec 56 §6 — saved-search client. Authed student endpoints under
// /students/me/saved-searches. The stored `query` is the durable half of a
// search (q + chips + filters + sort), so it round-trips back into the Explore
// URL via the same encoders DiscoverySearch uses.
import apiClient from './client'
import type { ConstraintChip, SearchFilters, SortOption } from '../types/search'
import type { ProgramSummary } from '../types'

export type SavedSearchEntity = 'program' | 'scholarship' | 'school'

export interface SavedQueryPayload {
  query?: string | null
  chips?: ConstraintChip[]
  filters?: SearchFilters | null
  sort?: SortOption
}

export interface SavedSearch {
  id: string
  name: string
  entity_type: SavedSearchEntity
  query: SavedQueryPayload
  alert_enabled: boolean
  last_run_at: string | null
  last_match_count: number | null
  last_alerted_at: string | null
  created_at: string
  updated_at: string
}

export interface SavedSearchRunResult {
  count: number
  results: ProgramSummary[]
}

export interface CreateSavedSearchBody {
  name: string
  entity_type?: SavedSearchEntity
  query: SavedQueryPayload
  alert_enabled?: boolean
}

export interface UpdateSavedSearchBody {
  name?: string
  query?: SavedQueryPayload
  alert_enabled?: boolean
}

export const listSavedSearches = (): Promise<SavedSearch[]> =>
  apiClient.get('/students/me/saved-searches').then(r => r.data)

export const createSavedSearch = (body: CreateSavedSearchBody): Promise<SavedSearch> =>
  apiClient.post('/students/me/saved-searches', body).then(r => r.data)

export const updateSavedSearch = (
  id: string,
  body: UpdateSavedSearchBody,
): Promise<SavedSearch> =>
  apiClient.patch(`/students/me/saved-searches/${id}`, body).then(r => r.data)

export const deleteSavedSearch = (id: string): Promise<void> =>
  apiClient.delete(`/students/me/saved-searches/${id}`).then(() => undefined)

export const runSavedSearch = (id: string): Promise<SavedSearchRunResult> =>
  apiClient.post(`/students/me/saved-searches/${id}/run`).then(r => r.data)
