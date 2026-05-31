import apiClient from './client'
import { toArrayData } from './normalize'
import type { Application, GuardrailScan, OfferLetter, ReadinessCheck } from '../types'

export const createApplication = (programId: string) =>
  apiClient.post('/applications', { program_id: programId }).then(r => r.data)

export const listMyApplications = () =>
  apiClient.get('/applications/me').then(r => toArrayData<Application>(r.data))

export const getMyApplication = (appId: string) =>
  apiClient.get(`/applications/me/${appId}`).then(r => r.data as Application)

export const patchMyApplication = (
  appId: string,
  body: Partial<{
    submission_mode: 'internal' | 'external'
    intent_picker: string
    intent_rationale: string
    ready_to_submit: boolean
    checklist_item_completions: Record<string, boolean>
  }>,
) => apiClient.patch(`/applications/me/${appId}`, body).then(r => r.data as Application)

export const submitApplication = (appId: string) =>
  apiClient.post(`/applications/me/${appId}/submit`).then(r => r.data)

export const guardrailScan = (appId: string) =>
  apiClient.post(`/applications/me/${appId}/guardrail-scan`).then(r => r.data as GuardrailScan)

export const getReadiness = (appId: string) =>
  apiClient.get(`/applications/me/${appId}/readiness`).then(r => r.data as ReadinessCheck)

export const checkReadiness = (appId: string) =>
  apiClient.post(`/applications/me/${appId}/check-readiness`).then(r => r.data as ReadinessCheck)

export const getChecklist = (appId: string) =>
  apiClient.get(`/students/me/applications/${appId}/checklist`).then(r => r.data)

export const generateChecklist = (appId: string) =>
  apiClient.post(`/students/me/applications/${appId}/checklist`).then(r => r.data)

export const getMyOffer = (appId: string) =>
  apiClient.get(`/applications/me/${appId}/offer`).then(r => r.data as OfferLetter)

export const respondToOffer = (appId: string, response: string, declineReason?: string) =>
  apiClient
    .post(`/applications/me/${appId}/offer/respond`, { response, decline_reason: declineReason })
    .then(r => r.data as OfferLetter)

export const withdrawApplication = (appId: string) =>
  apiClient.delete(`/applications/me/${appId}`)
