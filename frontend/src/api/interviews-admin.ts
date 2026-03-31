import apiClient from './client'
import type { Interview, InterviewScore } from '../types'

export async function proposeInterview(payload: {
  application_id: string; interviewer_id: string; interview_type: string;
  proposed_times: string[]; duration_minutes?: number; location_or_link?: string | null
}): Promise<Interview> {
  const { data } = await apiClient.post('/interviews', payload)
  return data
}

export async function getInterviewsByApplication(applicationId: string): Promise<Interview[]> {
  const { data } = await apiClient.get(`/interviews/application/${applicationId}`)
  return data
}

export async function completeInterview(interviewId: string): Promise<Interview> {
  const { data } = await apiClient.post(`/interviews/${interviewId}/complete`)
  return data
}

export async function scoreInterview(interviewId: string, payload: {
  criterion_scores: Record<string, number>; total_weighted_score: number;
  interviewer_notes?: string | null; recommendation?: string | null;
  rubric_id?: string | null
}): Promise<InterviewScore> {
  const { data } = await apiClient.post(`/interviews/${interviewId}/score`, payload)
  return data
}
