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

export const respondToOffer = (appId: string, response: string, declineReason?: string) =>
  apiClient.post(`/applications/me/${appId}/offer/respond`, { response, decline_reason: declineReason }).then(r => r.data)

export const getChecklist = (appId: string) =>
  apiClient.get(`/students/me/applications/${appId}/checklist`).then(r => r.data)

export const generateChecklist = (appId: string) =>
  apiClient.post(`/students/me/applications/${appId}/checklist`).then(r => r.data)

export const getReadiness = (appId: string) =>
  apiClient.get(`/students/me/applications/${appId}/readiness`).then(r => r.data)
