import apiClient from './client'

export const listRecommendations = () =>
  apiClient.get('/students/me/recommendations').then(r => r.data)

export const createRecommendation = (data: {
  recommender_name: string
  recommender_email?: string
  recommender_title?: string
  recommender_institution?: string
  relationship?: string
  due_date?: string
  notes?: string
  target_program_id?: string
}) => apiClient.post('/students/me/recommendations', data).then(r => r.data)

export const updateRecommendation = (id: string, data: any) =>
  apiClient.put(`/students/me/recommendations/${id}`, data).then(r => r.data)

export const deleteRecommendation = (id: string) =>
  apiClient.delete(`/students/me/recommendations/${id}`)

export const sendRecommendationRequest = (id: string) =>
  apiClient.post(`/students/me/recommendations/${id}/send`).then(r => r.data)
