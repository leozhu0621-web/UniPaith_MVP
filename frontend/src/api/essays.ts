import apiClient from './client'

export const createEssay = (data: { program_id: string; essay_type: string; content: string; prompt_text?: string }) =>
  apiClient.post('/students/me/essays', data).then(r => r.data)

export const listEssays = (programId?: string) =>
  apiClient.get('/students/me/essays', { params: { program_id: programId } }).then(r => r.data)

export const getEssay = (essayId: string) =>
  apiClient.get(`/students/me/essays/${essayId}`).then(r => r.data)

export const updateEssay = (essayId: string, data: { content?: string; prompt_text?: string }) =>
  apiClient.put(`/students/me/essays/${essayId}`, data).then(r => r.data)

export const finalizeEssay = (essayId: string) =>
  apiClient.post(`/students/me/essays/${essayId}/finalize`).then(r => r.data)

export const requestEssayFeedback = (essayId: string, feedbackType = 'general') =>
  apiClient.post(`/students/me/essays/${essayId}/feedback`, { feedback_type: feedbackType }).then(r => r.data)
