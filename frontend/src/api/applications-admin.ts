import apiClient from './client'
import type { Application, OfferLetter } from '../types'

export async function getApplicationsByProgram(programId: string): Promise<Application[]> {
  const { data } = await apiClient.get(`/applications/programs/${programId}`)
  return data
}

export async function reviewApplication(applicationId: string): Promise<Application> {
  const { data } = await apiClient.get(`/applications/review/${applicationId}`)
  return data
}

export async function makeDecision(applicationId: string, payload: {
  decision: 'admitted' | 'rejected' | 'waitlisted' | 'deferred'
  decision_notes?: string | null
}): Promise<Application> {
  const { data } = await apiClient.post(`/applications/review/${applicationId}/decision`, payload)
  return data
}

export async function createOffer(applicationId: string, payload: {
  offer_type: 'full_admission' | 'conditional' | 'waitlist_offer'
  tuition_amount?: number | null; scholarship_amount?: number;
  assistantship_details?: Record<string, any> | null;
  financial_package_total?: number | null;
  conditions?: Record<string, any> | null;
  response_deadline?: string | null
}): Promise<OfferLetter> {
  const { data } = await apiClient.post(`/applications/review/${applicationId}/offer`, payload)
  return data
}
