/**
 * Phase A — Discovery API client.
 *
 * Backs Stage 1 (Discovery) journey. Plan 2's LLM stack is the producer of
 * `assistant`-role messages and `extracted_signals`; the Phase B Discover
 * page wires the chat UI through `appendMessage` and reads progress through
 * `getCompletionMap`.
 */
import apiClient from './client'
import type {
  AppendMessageResponse,
  CompletionMap,
  DiscoveryLayer,
  DiscoveryMessage,
  DiscoveryRole,
  DiscoverySession,
  DiscoverySessionDetail,
  DiscoveryStatus,
  DiscoveryTrack,
} from '../types'

const BASE = '/students/me/discovery'

export const startSession = (
  track: DiscoveryTrack,
  layer?: DiscoveryLayer,
): Promise<DiscoverySession> =>
  apiClient.post(`${BASE}/sessions`, { track, layer }).then(r => r.data)

export const listSessions = (params?: {
  track?: DiscoveryTrack
  status?: DiscoveryStatus
}): Promise<DiscoverySession[]> =>
  apiClient.get(`${BASE}/sessions`, { params }).then(r => r.data)

export const getSession = (sessionId: string): Promise<DiscoverySessionDetail> =>
  apiClient.get(`${BASE}/sessions/${sessionId}`).then(r => r.data)

export const updateSession = (
  sessionId: string,
  body: {
    status?: DiscoveryStatus
    completion_pct?: string | number
    exit_signal?: Record<string, unknown>
  },
): Promise<DiscoverySession> =>
  apiClient.patch(`${BASE}/sessions/${sessionId}`, body).then(r => r.data)

export const appendMessage = (
  sessionId: string,
  body: {
    role: DiscoveryRole
    content: string
    extracted_signals?: Record<string, unknown>
  },
): Promise<AppendMessageResponse> =>
  apiClient.post(`${BASE}/sessions/${sessionId}/messages`, body).then(r => r.data)

export const getCompletionMap = (): Promise<CompletionMap> =>
  apiClient.get(`${BASE}/completion`).then(r => r.data)

// Re-export types so importers don't have to dig into the types barrel.
export type {
  AppendMessageResponse,
  CompletionMap,
  DiscoveryLayer,
  DiscoveryMessage,
  DiscoveryRole,
  DiscoverySession,
  DiscoverySessionDetail,
  DiscoveryStatus,
  DiscoveryTrack,
}
