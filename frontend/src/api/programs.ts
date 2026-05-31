import apiClient from './client'
import type { NetPriceEstimate, ProgramReviewSummary, EmployerFeedbackSummary } from '../types'

export const searchPrograms = (params: {
  q?: string; country?: string; degree_type?: string; institution_id?: string;
  min_tuition?: number; max_tuition?: number;
  delivery_format?: string; campus_setting?: string; max_duration_months?: number; city?: string;
  sort_by?: string; page?: number; page_size?: number
}) => apiClient.get('/programs', { params }).then(r => r.data)

export const getProgram = (id: string) =>
  apiClient.get(`/programs/${id}`).then(r => r.data)

export const semanticSearch = (q: string, limit = 10) =>
  apiClient.get('/programs/search/semantic', { params: { q, limit } }).then(r => r.data)

export const nlpSearch = (query: string) =>
  apiClient.post('/programs/search/nlp', { query }, { timeout: 30_000 }).then(r => r.data)

export const getProgramReviews = (programId: string): Promise<ProgramReviewSummary> =>
  apiClient.get(`/programs/${programId}/reviews`).then(r => r.data)

export const getEmployerFeedback = (programId: string): Promise<EmployerFeedbackSummary> =>
  apiClient.get(`/programs/${programId}/employer-feedback`).then(r => r.data)

// Spec 11 §3.3a — personalized net price (authenticated student). Returns
// { available:false } gracefully when the program lacks cost data.
export const getNetPrice = (programId: string): Promise<NetPriceEstimate> =>
  apiClient.get(`/students/me/programs/${programId}/net-price`).then(r => r.data)
