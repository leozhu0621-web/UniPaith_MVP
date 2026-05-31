// Spec 10 — Discovery type-first program search API client.
import apiClient from './client'
import type {
  CompareListResponse,
  InterpretResponse,
  SearchRequestPayload,
  SearchResponse,
} from '../types/search'

/** Interpret a natural-language query into structured constraint chips. */
export const interpretQuery = (query: string): Promise<InterpretResponse> =>
  apiClient
    .post('/students/me/search/interpret', { query }, { timeout: 30_000 })
    .then(r => r.data)

/** Run a programs-only search from chips + sort. */
export const searchProgramsTyped = (body: SearchRequestPayload): Promise<SearchResponse> =>
  apiClient.post('/students/me/search/programs', body).then(r => r.data)

/** Current server-persisted compare set. */
export const getCompareSet = (): Promise<CompareListResponse> =>
  apiClient.get('/students/me/compare').then(r => r.data)

/** Add a program to the compare set (server caps at 4). */
export const addToCompare = (programId: string): Promise<CompareListResponse> =>
  apiClient.post('/students/me/compare/add', { program_id: programId }).then(r => r.data)

/** Remove a program from the compare set. */
export const removeFromCompare = (programId: string): Promise<CompareListResponse> =>
  apiClient.delete(`/students/me/compare/${programId}`).then(r => r.data)
