/**
 * Spec 43 — Major-Specific Field Catalog API client.
 *
 * The student-facing major-specific readiness surface: the 15-track field
 * catalog (for the form renderer), per-track signal subdocuments (validated +
 * §5 provenance), and the §4.18 inference summary. Mirrors
 * unipaith-backend/src/unipaith/api/major_specific.py.
 */
import apiClient from './client'
import type {
  CatalogResponse,
  MajorSpecificSummary,
  TrackSignals,
  TrackSignalsOut,
  TracksResponse,
} from '../types/majorSpecific'

const BASE = '/students/me/major-specific'

export const getCatalog = (): Promise<CatalogResponse> =>
  apiClient.get(`${BASE}/catalog`).then(r => r.data)

export const getTracks = (): Promise<TracksResponse> =>
  apiClient.get(`${BASE}/tracks`).then(r => r.data)

export const upsertTrack = (trackKey: string, signals: TrackSignals): Promise<TrackSignalsOut> =>
  apiClient.put(`${BASE}/tracks/${trackKey}`, { signals }).then(r => r.data)

export const getSummary = (): Promise<MajorSpecificSummary> =>
  apiClient.get(`${BASE}/summary`).then(r => r.data)
