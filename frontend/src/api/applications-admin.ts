import apiClient from './client'
import type {
  Application,
  BatchOperationResult,
  BatchReleaseItem,
  BatchReleaseResult,
  InstitutionDecision,
  OfferLetter,
  OfferStatus,
  ReleaseDecisionResult,
  ReleaseOfferTerms,
} from '../types'

export async function getApplicationsByProgram(programId: string): Promise<Application[]> {
  const { data } = await apiClient.get(`/applications/programs/${programId}`)
  return data
}

export async function reviewApplication(applicationId: string): Promise<Application> {
  const { data } = await apiClient.get(`/applications/review/${applicationId}`)
  return data
}

export async function makeDecision(applicationId: string, payload: {
  decision: 'admitted' | 'conditional_admission' | 'rejected' | 'waitlisted' | 'deferred'
  decision_notes?: string | null
}): Promise<Application> {
  const { data } = await apiClient.post(`/applications/review/${applicationId}/decision`, payload)
  return data
}

// --- Spec 34 · Decisions & Offers (institution) ---

/** Release a decision (and offer for accepts/conditionals) in one audited,
 *  notified action (spec 34 §3). The unified replacement for makeDecision + createOffer. */
export async function releaseDecision(applicationId: string, payload: {
  decision: InstitutionDecision
  decision_notes?: string | null
  offer?: ReleaseOfferTerms | null
  message?: string | null
  notify?: boolean
}): Promise<ReleaseDecisionResult> {
  const { data } = await apiClient.post(`/applications/review/${applicationId}/release`, payload)
  return data
}

export async function getOfferStatus(applicationId: string): Promise<OfferStatus> {
  const { data } = await apiClient.get(`/applications/review/${applicationId}/offer-status`)
  return data
}

export async function extendOfferDeadline(offerId: string, responseDeadline: string): Promise<OfferLetter> {
  const { data } = await apiClient.post(`/applications/offers/${offerId}/extend-deadline`, { response_deadline: responseDeadline })
  return data
}

export async function rescindOffer(offerId: string): Promise<OfferLetter> {
  const { data } = await apiClient.post(`/applications/offers/${offerId}/rescind`)
  return data
}

export async function batchReleaseDecisionV2(items: BatchReleaseItem[], notify = true): Promise<BatchReleaseResult> {
  const { data } = await apiClient.post('/applications/batch-release-decision', { items, notify })
  return data
}

export async function updateApplicationStatus(applicationId: string, status: string): Promise<Application> {
  const { data } = await apiClient.patch(`/applications/review/${applicationId}/status`, { status })
  return data
}

export async function createOffer(applicationId: string, payload: {
  offer_type: 'full_admission' | 'conditional' | 'partial' | 'transfer_credit_offer' | 'waitlist_to_admit'
  tuition_amount?: number | null; scholarship_amount?: number;
  scholarship_currency?: string;
  tuition_estimate?: number | null;
  total_cost_estimate?: number | null;
  assistantship_details?: Record<string, any> | null;
  financial_package_total?: number | null;
  conditions?: Record<string, any> | null;
  response_deadline?: string | null;
  start_term?: { season?: string | null; year?: number | null };
  next_step_actions?: { action: string; by_date?: string | null }[] | null
}): Promise<OfferLetter> {
  const { data } = await apiClient.post(`/applications/review/${applicationId}/offer`, payload)
  return data
}

// --- Batch Operations ---

export async function batchRequestMissingItems(applicationIds: string[], items: string[]): Promise<BatchOperationResult> {
  const { data } = await apiClient.post('/applications/batch/request-items', { application_ids: applicationIds, items })
  return data
}

export async function batchUpdateStatus(applicationIds: string[], status: string): Promise<BatchOperationResult> {
  const { data } = await apiClient.post('/applications/batch/status', { application_ids: applicationIds, status })
  return data
}

export async function batchReleaseDecision(applicationIds: string[], decision: string, decisionNotes?: string): Promise<BatchOperationResult> {
  const { data } = await apiClient.post('/applications/batch/decision', { application_ids: applicationIds, decision, decision_notes: decisionNotes })
  return data
}
