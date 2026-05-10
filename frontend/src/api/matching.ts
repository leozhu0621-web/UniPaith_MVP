import apiClient from './client'
import { toArrayData } from './normalize'
import type { ExplainMatchResponse, MatchResultDual } from '../types'

export const getMatches = (forceRefresh = false) =>
  apiClient.get('/students/me/matches', { params: { force_refresh: forceRefresh } }).then(r => toArrayData<any>(r.data))

export const getMatchDetail = (programId: string): Promise<MatchResultDual> =>
  apiClient.get(`/students/me/matches/${programId}`).then(r => r.data)

/**
 * Phase A — generate (or return cached) rationale for a match's
 * fitness/confidence scores. Phase A returns a deterministic stub built
 * from the breakdown columns; Plan 2 will swap in an LLM-written explanation
 * that cites profile + program fields. Cached on `match_results.rationale_text`,
 * so subsequent reads via `getMatchDetail` return it inline.
 */
export const explainMatch = (programId: string): Promise<ExplainMatchResponse> =>
  apiClient.post(`/students/me/matches/${programId}/explain`).then(r => r.data)

export type { ExplainMatchResponse, MatchResultDual }

export const logEngagement = (programId: string, signalType: string, signalValue: number) =>
  apiClient.post('/students/me/engagement', { program_id: programId, signal_type: signalType, signal_value: signalValue }).then(r => r.data)

export const chatStudentAssistant = (message: string, contextProgramId?: string) =>
  apiClient
    .post('/students/me/assistant/chat', {
      message,
      context_program_id: contextProgramId,
    }, { timeout: 120_000 })
    .then(r => r.data)

// ============ CONVERSATION / PROGRAM MATCH ============

export const sendConversationTurn = (message: string, options?: { session_id?: string; entrypoint?: string; context_program_id?: string }) =>
  apiClient.post('/students/me/conversation/turn', { message, ...options }, { timeout: 120_000 }).then(r => r.data)

export const getConversationSession = () =>
  apiClient.get('/students/me/conversation/session').then(r => r.data)

export const getConversationResume = () =>
  apiClient.get('/students/me/conversation/session/resume').then(r => r.data)

export const getConversationRequirements = () =>
  apiClient.get('/students/me/conversation/requirements').then(r => r.data)

export const getConversationConfidence = () =>
  apiClient.get('/students/me/conversation/confidence').then(r => r.data)

export const getShortlistUnlock = () =>
  apiClient.get('/students/me/conversation/shortlist-unlock').then(r => r.data)

export const updateRequirement = (
  requirementId: string,
  updates: { status?: string; value?: unknown; priority?: string },
) =>
  apiClient.patch(
    `/students/me/conversation/requirements/${requirementId}`,
    updates,
  ).then(r => r.data)

export const resolveConflict = (conflictId: string, resolution: string) =>
  apiClient.post(`/students/me/conversation/conflicts/${conflictId}/resolve`, { selected_resolution: resolution }).then(r => r.data)

export const generateShortlist = () =>
  apiClient.post('/students/me/conversation/generate-shortlist', {}, { timeout: 120_000 }).then(r => r.data)
