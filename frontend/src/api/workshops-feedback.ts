/**
 * Phase A — Workshop feedback (feedback-only) API client.
 *
 * The product spec is explicit: workshops do NOT generate context. The
 * backend response shape mechanically excludes any field that could carry
 * a generated essay / answer / draft. The CI test
 * `test_workshop_no_generation_contract.py` enforces this — even Plan 2's
 * LLM swap-in cannot add a `revised_text` field without breaking the build.
 */
import apiClient from './client'
import type { WorkshopDomain, WorkshopFeedbackRun } from '../types'

const BASE = '/students/me/workshops'

export interface EssayFeedbackBody {
  essay_text: string
  prompt_text?: string | null
  target_program_id?: string | null
  document_id?: string | null
}

export interface InterviewPracticeBody {
  target_program_id?: string | null
  interview_type?: 'behavioral' | 'technical' | 'general'
  focus_area?: string | null
  /**
   * When set, the workshop coach scores this response rather than
   * returning canned practice questions. The schema-level no-generation
   * guard still binds — coach output cannot include a model answer.
   */
  response_text?: string | null
  question_text?: string | null
}

export type StandardizedTest =
  | 'GRE'
  | 'GMAT'
  | 'TOEFL'
  | 'IELTS'
  | 'MCAT'
  | 'LSAT'
  | 'SAT'
  | 'ACT'

export interface TestGuidanceBody {
  test_type: StandardizedTest
  current_score?: number | null
  target_score?: number | null
}

export const requestEssayFeedback = (
  body: EssayFeedbackBody,
): Promise<WorkshopFeedbackRun> =>
  apiClient.post(`${BASE}/essay/feedback`, body).then(r => r.data)

export const requestInterviewPractice = (
  body: InterviewPracticeBody,
): Promise<WorkshopFeedbackRun> =>
  apiClient.post(`${BASE}/interview/practice`, body).then(r => r.data)

export const requestTestGuidance = (
  body: TestGuidanceBody,
): Promise<WorkshopFeedbackRun> =>
  apiClient.post(`${BASE}/test/guidance`, body).then(r => r.data)

export const listWorkshopRuns = (
  domain?: WorkshopDomain,
): Promise<WorkshopFeedbackRun[]> =>
  apiClient
    .get(`${BASE}/runs`, { params: domain ? { domain } : undefined })
    .then(r => r.data)

export type { WorkshopDomain, WorkshopFeedbackRun }
