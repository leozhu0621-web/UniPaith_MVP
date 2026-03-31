import apiClient from './client'

export const generateResume = (data: { format_type: string; target_program_id?: string }) =>
  apiClient.post('/students/me/resume/generate', data).then(r => r.data)

export const listResumes = (targetProgramId?: string) =>
  apiClient.get('/students/me/resume', { params: { target_program_id: targetProgramId } }).then(r => r.data)

export const updateResume = (resumeId: string, content: any) =>
  apiClient.put(`/students/me/resume/${resumeId}`, { content }).then(r => r.data)

export const finalizeResume = (resumeId: string) =>
  apiClient.post(`/students/me/resume/${resumeId}/finalize`).then(r => r.data)

export const requestResumeFeedback = (resumeId: string, feedbackType = 'general') =>
  apiClient.post(`/students/me/resume/${resumeId}/feedback`, { feedback_type: feedbackType }).then(r => r.data)
