import apiClient from './client'
import type {
  Application,
  ApplicationOffer,
  OfferDecisionResult,
  OffersComparison,
} from '../types'

// Spec 18 · Decisions & Offers

export const getOffersComparison = () =>
  apiClient.get('/applications/me/offers/comparison').then(r => r.data as OffersComparison)

export interface RecordOfferPayload {
  offer_type?: string
  decision_date?: string | null
  response_deadline?: string | null
  scholarship_amount?: number | null
  scholarship_currency?: string | null
  tuition_amount?: number | null
  tuition_estimate?: number | null
  total_cost_estimate?: number | null
  conditions?: Record<string, unknown> | null
  start_term?: { season?: string | null; year?: number | null } | null
  next_step_actions?: { action: string; by_date?: string | null }[] | null
}

export const recordExternalOffer = (appId: string, body: RecordOfferPayload) =>
  apiClient.post(`/applications/me/${appId}/offers`, body).then(r => r.data as ApplicationOffer)

export const respondToOfferV2 = (
  appId: string,
  offerId: string,
  response: 'accepted' | 'declined',
  declineReason?: string,
) =>
  apiClient
    .patch(`/applications/me/${appId}/offers/${offerId}`, {
      response,
      decline_reason: declineReason,
    })
    .then(r => r.data as OfferDecisionResult)

export const withdrawDecision = (appId: string) =>
  apiClient.post(`/applications/me/${appId}/withdraw`).then(r => r.data as Application)

export const bulkWithdraw = (applicationIds: string[]) =>
  apiClient
    .post('/applications/me/withdraw-bulk', { application_ids: applicationIds })
    .then(r => r.data as { withdrawn_count: number })
