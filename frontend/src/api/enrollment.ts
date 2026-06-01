import apiClient from './client'
import type { Enrollment, WaitlistView, YieldSnapshot } from '../types'

// Spec 35 · Enrollment Confirmation & Yield

// ── Student ──────────────────────────────────────────────────────────────

export const getMyEnrollment = (appId: string) =>
  apiClient.get(`/applications/me/${appId}/enrollment`).then(r => r.data as Enrollment)

export const confirmEnrollment = (appId: string) =>
  apiClient.post(`/applications/me/${appId}/enrollment/confirm`).then(r => r.data as Enrollment)

export const declineEnrollment = (appId: string, reason?: string) =>
  apiClient
    .post(`/applications/me/${appId}/enrollment/decline`, { reason })
    .then(r => r.data as Enrollment)

export const requestDeferral = (appId: string, toTerm?: { season?: string; year?: number }) =>
  apiClient
    .post(`/applications/me/${appId}/enrollment/defer`, { to_term: toTerm ?? null })
    .then(r => r.data as Enrollment)

export const toggleEnrollmentChecklistItem = (appId: string, key: string, complete: boolean) =>
  apiClient
    .post(`/applications/me/${appId}/enrollment/checklist-item`, { key, complete })
    .then(r => r.data as Enrollment)

// ── Institution (per-applicant) ────────────────────────────────────────────

export const getApplicantEnrollment = (appId: string) =>
  apiClient.get(`/applications/review/${appId}/enrollment`).then(r => r.data as Enrollment)

export const recordDeposit = (
  appId: string,
  depositStatus: 'none' | 'pending' | 'paid' | 'waived',
  depositAmount?: number | null,
) =>
  apiClient
    .post(`/applications/review/${appId}/enrollment/record-deposit`, {
      deposit_status: depositStatus,
      deposit_amount: depositAmount ?? null,
    })
    .then(r => r.data as Enrollment)

export const markEnrollmentConfirmed = (appId: string, final = false) =>
  apiClient
    .post(`/applications/review/${appId}/enrollment/confirm`, { final })
    .then(r => r.data as Enrollment)

export const approveDeferral = (appId: string, approved = true) =>
  apiClient
    .post(`/applications/review/${appId}/enrollment/approve-deferral`, { approved })
    .then(r => r.data as Enrollment)

// ── Institution (yield + waitlist) ──────────────────────────────────────────

export const getYield = (params?: { program_id?: string; intake_id?: string }) =>
  apiClient
    .get('/institutions/me/yield', { params })
    .then(r => r.data as YieldSnapshot)

export const getWaitlist = (programId?: string) =>
  apiClient
    .get('/institutions/me/waitlist', { params: programId ? { program_id: programId } : undefined })
    .then(r => r.data as WaitlistView)

export const offerToNextWaitlisted = (programId: string) =>
  apiClient
    .post('/institutions/me/waitlist/offer-next', { program_id: programId })
    .then(r => r.data as { promoted_application_id: string; offer_id: string | null; remaining_waitlist: number })

export const bulkOfferWaitlist = (programId: string, count: number) =>
  apiClient
    .post('/institutions/me/waitlist/bulk-offer', { program_id: programId, count })
    .then(r => r.data as { results: unknown[]; offered_count: number })
