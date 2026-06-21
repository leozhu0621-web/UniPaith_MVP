import apiClient from './client'
import { toArrayData } from './normalize'

export const createApplication = (programId: string) =>
  apiClient.post('/applications', { program_id: programId }).then(r => r.data)

export const listMyApplications = () =>
  apiClient.get('/applications/me').then(r => toArrayData<any>(r.data))

export const getMyApplication = (appId: string) =>
  apiClient.get(`/applications/me/${appId}`).then(r => r.data)

export const submitApplication = (appId: string) =>
  apiClient.post(`/applications/me/${appId}/submit`).then(r => r.data)

export const withdrawApplication = (appId: string) =>
  apiClient.delete(`/applications/me/${appId}`)

export const getChecklist = (appId: string) =>
  apiClient.get(`/students/me/applications/${appId}/checklist`).then(r => r.data)

export const generateChecklist = (appId: string) =>
  apiClient.post(`/students/me/applications/${appId}/checklist`).then(r => r.data)

export const getReadiness = (appId: string) =>
  apiClient.get(`/students/me/applications/${appId}/readiness`).then(r => r.data)

// --- Spec 15 workspace ---

export const patchApplication = (
  appId: string,
  data: {
    submission_mode?: 'internal' | 'external'
    intent_picker?: string | null
    intent_rationale?: string | null
  },
) => apiClient.patch(`/applications/me/${appId}`, data).then(r => r.data)

export const guardrailScan = (appId: string) =>
  apiClient.post(`/applications/me/${appId}/guardrail-scan`).then(r => r.data)

export const checkReadiness = (appId: string) =>
  apiClient.post(`/applications/me/${appId}/check-readiness`).then(r => r.data)

export const toggleChecklistItem = (appId: string, itemKey: string, completed: boolean) =>
  apiClient
    .patch(`/applications/me/${appId}/checklist`, { item_key: itemKey, completed })
    .then(r => r.data)
