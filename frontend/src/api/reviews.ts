import apiClient from './client'
import type { AIPacketSummary, BatchOperationResult, CohortComparisonData, IntegritySignal, IntegrityResolution, IntegrityAction, InstitutionMatchRationale, PrioritizedApplication, Rubric, ApplicationScore, ReviewAssignment, AIReviewSummary, PipelineData, ReviewPacket, ReviewSynthesis, ReviewAssistantAnswer, ReviewCalibration } from '../types'

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

// --- AI Packet Summary ---

export async function getAIPacketSummary(applicationId: string, rubricId?: string): Promise<AIPacketSummary> {
  const params = rubricId ? { rubric_id: rubricId } : undefined
  const { data } = await apiClient.get(`/reviews/applications/${applicationId}/ai-packet`, { params })
  return data
}

export async function regenerateAIPacketSummary(applicationId: string, rubricId?: string): Promise<AIPacketSummary> {
  const params = rubricId ? { rubric_id: rubricId } : undefined
  const { data } = await apiClient.post(`/reviews/applications/${applicationId}/ai-packet/regenerate`, null, { params })
  return data
}

// --- Asymmetric match rationale (institution full view, spec 06 §3/§5.5) ---

export async function getMatchRationaleFull(applicationId: string): Promise<InstitutionMatchRationale> {
  const { data } = await apiClient.get(`/reviews/applications/${applicationId}/match-rationale`)
  return data
}

// --- Integrity Signals ---

export async function scanIntegrity(applicationId: string): Promise<IntegritySignal[]> {
  const { data } = await apiClient.post(`/reviews/applications/${applicationId}/integrity-scan`)
  return data
}

export async function getIntegritySignals(applicationId?: string, signalStatus?: string): Promise<IntegritySignal[]> {
  const params: Record<string, string> = {}
  if (applicationId) params.application_id = applicationId
  if (signalStatus) params.signal_status = signalStatus
  const { data } = await apiClient.get('/reviews/integrity-signals', { params })
  return data
}

export async function resolveIntegritySignal(
  signalId: string,
  resolution?: IntegrityResolution,
  notes?: string,
): Promise<{ id: string; status: string; resolution: string | null }> {
  const params: Record<string, string> = {}
  if (resolution) params.resolution = resolution
  if (notes) params.notes = notes
  const { data } = await apiClient.post(`/reviews/integrity-signals/${signalId}/resolve`, null, {
    params: Object.keys(params).length ? params : undefined,
  })
  return data
}

// --- Priority Queue ---

export async function getReviewPriorityQueue(programId?: string): Promise<PrioritizedApplication[]> {
  const params = programId ? { program_id: programId } : undefined
  const { data } = await apiClient.get('/reviews/priority-queue', { params })
  return data
}

// --- AI Rubric Pre-fill ---

export async function getAIPrefill(applicationId: string, rubricId: string): Promise<{
  application_id: string; rubric_id: string;
  prefill: Record<string, { suggested_score: number | null; suggested_note: string }>;
  overall_note: string; recommended_score: number | null
}> {
  const { data } = await apiClient.post(`/reviews/applications/${applicationId}/ai-prefill`, null, { params: { rubric_id: rubricId } })
  return data
}

// --- Cohort Comparison ---

export async function getCohortComparison(applicationIds: string[]): Promise<CohortComparisonData> {
  const { data } = await apiClient.get('/reviews/cohort-compare', { params: { application_ids: applicationIds.join(',') } })
  return data
}

// --- Batch Operations ---

export async function batchAssignReviewers(applicationIds: string[], reviewerId?: string): Promise<BatchOperationResult> {
  const { data } = await apiClient.post('/reviews/batch/assign', { application_ids: applicationIds, reviewer_id: reviewerId })
  return data
}

// --- Spec 32 · Review Workspace ---

export async function getReviewPacket(applicationId: string, opts?: { rubricId?: string; reveal?: boolean }): Promise<ReviewPacket> {
  const params: Record<string, string> = {}
  if (opts?.rubricId) params.rubric_id = opts.rubricId
  if (opts?.reveal) params.reveal = 'true'
  const { data } = await apiClient.get(`/reviews/applications/${applicationId}/review-packet`, { params })
  return data
}

export async function synthesizeReviews(applicationId: string, rubricId?: string): Promise<ReviewSynthesis> {
  const params = rubricId ? { rubric_id: rubricId } : undefined
  const { data } = await apiClient.post(`/reviews/applications/${applicationId}/synthesize`, null, { params })
  return data
}

export async function reviewAssistantChat(applicationId: string, question: string): Promise<ReviewAssistantAnswer> {
  const { data } = await apiClient.post(`/reviews/applications/${applicationId}/assistant-chat`, { question })
  return data
}

export async function revealApplicantIdentity(applicationId: string, reason?: string): Promise<{ revealed: boolean }> {
  const { data } = await apiClient.post(`/reviews/applications/${applicationId}/reveal-identity`, { reason: reason ?? null })
  return data
}

export async function actOnIntegritySignal(signalId: string, action: IntegrityAction, notes?: string): Promise<{ id: string; status: string; action: string; rejected_application: boolean }> {
  const { data } = await apiClient.post(`/reviews/integrity-signals/${signalId}/action`, { action, notes: notes ?? null })
  return data
}

export async function getReviewCalibration(programId?: string): Promise<ReviewCalibration> {
  const params = programId ? { program_id: programId } : undefined
  const { data } = await apiClient.get('/reviews/calibration', { params })
  return data
}
