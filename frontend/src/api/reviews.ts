import apiClient from './client'
import type { BatchOperationResult, Rubric, ApplicationScore, ReviewAssignment, AIReviewSummary, PipelineData } from '../types'

export async function getRubrics(programId?: string): Promise<Rubric[]> {
  const params = programId ? { program_id: programId } : {}
  const { data } = await apiClient.get('/reviews/rubrics', { params })
  return data
}

export async function createRubric(payload: {
  rubric_name: string
  criteria: { name: string; weight: number; description?: string }[]
  program_id?: string | null
}): Promise<Rubric> {
  const { data } = await apiClient.post('/reviews/rubrics', payload)
  return data
}

export async function assignReviewer(applicationId: string): Promise<ReviewAssignment[]> {
  const { data } = await apiClient.post(`/reviews/applications/${applicationId}/assign`)
  return data
}

export async function scoreApplication(applicationId: string, payload: {
  rubric_id: string
  criterion_scores: Record<string, number>
  reviewer_notes?: string | null
}): Promise<ApplicationScore> {
  const { data } = await apiClient.post(`/reviews/applications/${applicationId}/score`, payload)
  return data
}

export async function getScores(applicationId: string): Promise<ApplicationScore[]> {
  const { data } = await apiClient.get(`/reviews/applications/${applicationId}/scores`)
  return data
}

export async function getAISummary(applicationId: string): Promise<AIReviewSummary> {
  const { data } = await apiClient.get(`/reviews/applications/${applicationId}/ai-summary`)
  return data
}

export async function getPipeline(programId: string): Promise<PipelineData> {
  const { data } = await apiClient.get(`/reviews/pipeline/${programId}`)
  return data
}

// --- Batch Operations ---

export async function batchAssignReviewers(applicationIds: string[], reviewerId?: string): Promise<BatchOperationResult> {
  const { data } = await apiClient.post('/reviews/batch/assign', { application_ids: applicationIds, reviewer_id: reviewerId })
  return data
}
