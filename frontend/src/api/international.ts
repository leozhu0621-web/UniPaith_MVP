import apiClient from './client'
import type {
  IntlApplicantRow,
  IntlCountryPack,
  IntlCountryRequirement,
  IntlEnglishPolicy,
  IntlNormalizeResult,
  IntlProcessingView,
} from '../types'

// Spec 38 · International Admissions (institution processing)

// ── Per-applicant ────────────────────────────────────────────────────────────
export const getInternational = (appId: string) =>
  apiClient
    .get(`/applications/review/${appId}/international`)
    .then(r => r.data as IntlProcessingView)

export interface IntlPatch {
  credential_provider?: 'WES' | 'ECE' | 'SpanTran' | 'other'
  credential_status?: 'none' | 'requested' | 'in_progress' | 'received' | 'verified'
  credential_report_ref?: string
  credential_normalized_gpa?: number
  credential_source_scale?: string
  credential_notes?: string
  english_test?: 'TOEFL' | 'IELTS' | 'DET' | 'PTE'
  english_score?: number
  english_meets_minimum?: boolean
  english_waiver_eligible?: boolean
  english_waiver_basis?: string
  country_requirements?: IntlCountryRequirement[]
  visa_appointment_at?: string
  visa_consulate?: string
  visa_outcome?: 'pending' | 'approved' | 'denied'
}

export const updateInternational = (appId: string, patch: IntlPatch) =>
  apiClient
    .patch(`/applications/review/${appId}/international`, patch)
    .then(r => r.data as IntlProcessingView)

export const normalizeGpa = (
  appId: string,
  body?: { raw_gpa?: number; scale_hint?: string; country?: string },
) =>
  apiClient
    .post(`/applications/review/${appId}/international/normalize-gpa`, body ?? {})
    .then(r => r.data as IntlNormalizeResult)

export const suggestCountryPack = (appId: string) =>
  apiClient
    .post(`/applications/review/${appId}/international/suggest-country-pack`)
    .then(
      r => r.data as { country_name: string; requirements: IntlCountryRequirement[]; ai_used: boolean },
    )

export const generateImmigrationDoc = (appId: string, docType: 'I-20' | 'DS-2019') =>
  apiClient
    .post(`/applications/review/${appId}/immigration-doc/generate`, { doc_type: docType })
    .then(
      r =>
        r.data as {
          doc_type: string
          status: string
          sevis_id: string
          issued_at: string
          sevis_export: Record<string, unknown>
        },
    )

// ── Institution-wide ─────────────────────────────────────────────────────────
export const listInternationalApplicants = () =>
  apiClient
    .get('/institutions/me/international/applicants')
    .then(r => r.data as IntlApplicantRow[])

export const listCountryRequirements = () =>
  apiClient
    .get('/institutions/me/international/country-requirements')
    .then(r => r.data as IntlCountryPack[])

export const updateEnglishPolicy = (
  programId: string,
  body: IntlEnglishPolicy & { expected_version?: number },
) =>
  apiClient
    .patch(`/institutions/me/programs/${programId}/english-policy`, body)
    .then(r => r.data)
