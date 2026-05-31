import apiClient from './client'
import { toArrayData } from './normalize'
import type { ExplainMatchResponse, MatchResultDual, ProbabilityBandsResponse } from '../types'

// Spec 09 §7 — ranked matches, enriched server-side with band_label +
// probability_bands + program display fields. `refresh` recomputes the
// catalog first (applying the student's priority weights, §5.2).
export const getMatches = (refresh = false): Promise<MatchResultDual[]> =>
  apiClient
    .get('/students/me/matches', { params: { refresh } })
    .then(r => toArrayData<MatchResultDual>(r.data))

// Spec 09 §5.2 / §8 — recompute matches over the catalog, then return top-N.
export const refreshMatches = (): Promise<MatchResultDual[]> =>
  apiClient
    .post('/students/me/matches/refresh', {}, { timeout: 120_000 })
    .then(r => toArrayData<MatchResultDual>(r.data))

// Spec 09 §4A — probability bands for one program (card expand / detail load).
export const getMatchProbability = (programId: string): Promise<ProbabilityBandsResponse> =>
  apiClient.get(`/students/me/matches/${programId}/probability`).then(r => r.data)

// Untyped on purpose — legacy callers (e.g. SchoolDetailPage) consume this
// against the older `MatchResult` shape with number scores. Phase C will
// migrate consumers to MatchResultDual; until then the response carries
// both the legacy `match_score` and the new `fitness_score` /
// `confidence_score` fields, so consumers can read either.
export const getMatchDetail = (programId: string) =>
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

export type { ExplainMatchResponse, MatchResultDual, ProbabilityBandsResponse }

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
