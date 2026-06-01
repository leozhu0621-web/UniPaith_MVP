import apiClient from './client'
import type {
  Prospect,
  ProspectImportResult,
  ProspectList,
  ProspectToSegmentResult,
  RecruitmentFair,
  RecruitmentSummary,
  RecruitmentTrip,
  Territory,
  TerritoryDashboard,
  TerritoryOptimize,
} from '../types'

// Spec 40 · Recruitment CRM (Pre-Applicant) — /institutions/me/recruitment

const BASE = '/institutions/me/recruitment'

// ── summary ───────────────────────────────────────────────────────────────

export const getRecruitmentSummary = () =>
  apiClient.get(`${BASE}/summary`).then(r => r.data as RecruitmentSummary)

// ── prospects ─────────────────────────────────────────────────────────────

export interface ProspectFilters {
  stage?: string
  source?: string
  territory_id?: string
  owner_user_id?: string
  search?: string
}

export const listProspects = (filters: ProspectFilters = {}) => {
  const params = Object.fromEntries(
    Object.entries(filters).filter(([, v]) => v != null && v !== ''),
  )
  return apiClient.get(`${BASE}/prospects`, { params }).then(r => r.data as ProspectList)
}

export const createProspect = (payload: Partial<Prospect>) =>
  apiClient.post(`${BASE}/prospects`, payload).then(r => r.data as Prospect)

export const getProspect = (id: string) =>
  apiClient.get(`${BASE}/prospects/${id}`).then(r => r.data as Prospect)

export const updateProspect = (id: string, payload: Partial<Prospect>) =>
  apiClient.patch(`${BASE}/prospects/${id}`, payload).then(r => r.data as Prospect)

export interface ImportRow {
  name: string
  email?: string | null
  phone?: string | null
  city?: string | null
  region?: string | null
  country?: string | null
  interests?: string[]
  consent_outreach?: boolean
}

export const importProspects = (payload: {
  source?: string
  source_detail?: string | null
  territory_id?: string | null
  rows: ImportRow[]
}) => apiClient.post(`${BASE}/prospects/import`, payload).then(r => r.data as ProspectImportResult)

export const convertProspect = (id: string, applicationId?: string | null) =>
  apiClient
    .post(`${BASE}/prospects/${id}/convert`, { application_id: applicationId ?? null })
    .then(r => r.data as Prospect)

export const prospectsToSegment = (payload: { prospect_ids: string[]; list_name: string }) =>
  apiClient
    .post(`${BASE}/prospects/to-segment`, payload)
    .then(r => r.data as ProspectToSegmentResult)

// ── travel calendar ───────────────────────────────────────────────────────

export const listTrips = () =>
  apiClient.get(`${BASE}/trips`).then(r => r.data as RecruitmentTrip[])

export const createTrip = (payload: Record<string, unknown>) =>
  apiClient.post(`${BASE}/trips`, payload).then(r => r.data as RecruitmentTrip)

export const updateTrip = (id: string, payload: Record<string, unknown>) =>
  apiClient.patch(`${BASE}/trips/${id}`, payload).then(r => r.data as RecruitmentTrip)

export const addTripVisit = (tripId: string, payload: Record<string, unknown>) =>
  apiClient.post(`${BASE}/trips/${tripId}/visits`, payload).then(r => r.data as RecruitmentTrip)

export const updateTripVisit = (
  tripId: string,
  visitId: string,
  payload: Record<string, unknown>,
) =>
  apiClient
    .patch(`${BASE}/trips/${tripId}/visits/${visitId}`, payload)
    .then(r => r.data as RecruitmentTrip)

// ── fairs ─────────────────────────────────────────────────────────────────

export const listFairs = () =>
  apiClient.get(`${BASE}/fairs`).then(r => r.data as RecruitmentFair[])

export const createFair = (payload: Record<string, unknown>) =>
  apiClient.post(`${BASE}/fairs`, payload).then(r => r.data as RecruitmentFair)

export const updateFair = (id: string, payload: Record<string, unknown>) =>
  apiClient.patch(`${BASE}/fairs/${id}`, payload).then(r => r.data as RecruitmentFair)

export interface CaptureLead {
  name: string
  email?: string | null
  phone?: string | null
  interests?: string[]
  consent_outreach?: boolean
}

export const captureLeads = (
  fairId: string,
  payload: { leads: CaptureLead[]; territory_id?: string | null; trip_visit_id?: string | null },
) =>
  apiClient
    .post(`${BASE}/fairs/${fairId}/capture`, payload)
    .then(r => r.data as { captured: number; deduped: number; suppressed: number; fair_id: string })

// ── territories ───────────────────────────────────────────────────────────

export const listTerritories = () =>
  apiClient.get(`${BASE}/territories`).then(r => r.data as Territory[])

export const getTerritoryDashboard = () =>
  apiClient.get(`${BASE}/territories/dashboard`).then(r => r.data as TerritoryDashboard)

export const createTerritory = (payload: Record<string, unknown>) =>
  apiClient.post(`${BASE}/territories`, payload).then(r => r.data as Territory)

export const updateTerritory = (id: string, payload: Record<string, unknown>) =>
  apiClient.patch(`${BASE}/territories/${id}`, payload).then(r => r.data as Territory)

export const optimizeTerritory = (id: string) =>
  apiClient.post(`${BASE}/territories/${id}/optimize`).then(r => r.data as TerritoryOptimize)
