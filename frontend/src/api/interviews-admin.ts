import apiClient from './client'
import type { BatchOperationResult, Interview, InterviewRubric, InterviewScore } from '../types'

export async function getInstitutionInterviews(status?: string): Promise<Interview[]> {
  const params = status ? { status } : undefined
  const { data } = await apiClient.get('/interviews/institution', { params })
  return data
}

export interface ProposeInterviewPayload {
  application_ids: string[]
  interview_type: string
  proposed_times?: string[]
  duration_minutes?: number
  location_or_link?: string | null
  async_window_end?: string | null
  notes_to_student?: string | null
  ai_draft_used?: boolean
}

// Spec 33 §5 — propose returns one interview per applicant (a list).
export async function proposeInterview(payload: ProposeInterviewPayload): Promise<Interview[]> {
  const { data } = await apiClient.post('/interviews', payload)
  return data
}

export async function getInterviewsByApplication(applicationId: string): Promise<Interview[]> {
  const { data } = await apiClient.get(`/interviews/application/${applicationId}`)
  return data
}

export async function getInterviewRubrics(programId?: string | null): Promise<InterviewRubric[]> {
  const params = programId ? { program_id: programId } : undefined
  const { data } = await apiClient.get('/interviews/rubrics', { params })
  return data
}

export async function completeInterview(interviewId: string): Promise<Interview> {
  const { data } = await apiClient.post(`/interviews/${interviewId}/complete`)
  return data
}

export async function cancelInterview(interviewId: string): Promise<Interview> {
  const { data } = await apiClient.post(`/interviews/${interviewId}/cancel`)
  return data
}

export async function markInterviewNoShow(interviewId: string): Promise<Interview> {
  const { data } = await apiClient.post(`/interviews/${interviewId}/no-show`)
  return data
}

export async function rescheduleInterview(
  interviewId: string,
  payload: {
    proposed_times?: string[]
    async_window_end?: string | null
    duration_minutes?: number
    location_or_link?: string | null
  },
): Promise<Interview> {
  const { data } = await apiClient.post(`/interviews/${interviewId}/reschedule`, payload)
  return data
}

export async function scoreInterview(
  interviewId: string,
  payload: {
    criterion_scores: Record<string, number>
    total_weighted_score: number
    interviewer_notes?: string | null
    recommendation?: string | null
    rubric_id?: string | null
  },
): Promise<InterviewScore> {
  const { data } = await apiClient.post(`/interviews/${interviewId}/score`, payload)
  return data
}

// --- AI helpers (Spec 33 §9) ---

export interface DraftInviteResponse {
  available: boolean
  draft: string | null
  tone: string | null
  length: string | null
}

export async function draftInterviewInvite(payload: {
  application_id: string
  interview_type: string
  proposed_times?: string[]
  async_window_end?: string | null
  duration_minutes?: number | null
  location_or_link?: string | null
}): Promise<DraftInviteResponse> {
  const { data } = await apiClient.post('/interviews/draft-invite', payload)
  return data
}

export interface ScorePrefillResponse {
  available: boolean
  criterion_scores: Record<string, number>
  overall_note: string | null
  recommendation: string | null
}

export async function prefillInterviewScore(
  interviewId: string,
  payload: { rubric_id?: string | null; transcript_or_notes?: string },
): Promise<ScorePrefillResponse> {
  const { data } = await apiClient.post(`/interviews/${interviewId}/score-prefill`, payload)
  return data
}

// --- Batch Operations ---

export async function batchInviteInterviews(
  applicationIds: string[],
  interviewerId: string,
  interviewType: string,
  proposedTimes: string[],
  durationMinutes?: number,
  locationOrLink?: string,
): Promise<BatchOperationResult> {
  const { data } = await apiClient.post('/interviews/batch/invite', {
    application_ids: applicationIds,
    interviewer_id: interviewerId,
    interview_type: interviewType,
    proposed_times: proposedTimes,
    duration_minutes: durationMinutes ?? 30,
    location_or_link: locationOrLink,
  })
  return data
}
