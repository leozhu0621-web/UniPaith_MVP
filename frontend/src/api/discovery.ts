/**
 * Phase A — Discovery API client.
 *
 * Backs Stage 1 (Discovery) journey. The LLM stack is the producer of
 * `assistant`-role messages and `extracted_signals`; the Discover page wires
 * the chat UI through `appendMessage` and reads progress through
 * `getCompletionMap`. Spec 19 adds personality signals + the handoff verdict.
 */
import apiClient from './client'
import { useAuthStore } from '../stores/auth-store'
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
  HandoffVerdict,
  PersonalitySignal,
} from '../types'

const BASE = '/students/me/discovery'
const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'

export const startSession = (
  track: DiscoveryTrack,
  layer?: DiscoveryLayer,
): Promise<DiscoverySession> =>
  apiClient.post(`${BASE}/sessions`, { track, layer }).then(r => r.data)

// Redesign: one track-less Uni conversation (no Profile/Goals/Needs pick).
// `fresh` forces a brand-new discovery thread (chat-tab sessions are independent);
// omit it for the single shared track-less conversation (Discover page).
export const startUnifiedSession = (fresh = false): Promise<DiscoverySession> =>
  apiClient
    .post(`${BASE}/sessions/unified${fresh ? '?fresh=true' : ''}`)
    .then(r => r.data)

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

export interface DiscoveryStreamHandlers {
  /** Persisted student row echoed back so we can swap the optimistic bubble. */
  onStudentMessage?: (msg: DiscoveryMessage) => void
  /** Incremental assistant text chunk (Spec 77 §6 token streaming). */
  onDelta?: (text: string) => void
  /** Final persisted assistant row (content + extracted_signals). */
  onAssistantMessage?: (msg: DiscoveryMessage) => void
  onError?: (message: string) => void
  /** Terminal — stream finished cleanly. */
  onDone?: () => void
}

/**
 * Authenticated fetch for the SSE endpoints. These bypass the axios interceptor
 * (EventSource/ReadableStream can't go through axios), so the 401→refresh→retry
 * that keeps the rest of the app signed in has to live here too (todo 1.3).
 * Without it the token-sensitive Uni chat dropped to its fallback every time the
 * 1h access token lapsed. Attaches the current token, and on a 401 refreshes once
 * and retries before giving up.
 */
async function authedStreamFetch(url: string, init: RequestInit): Promise<Response> {
  const withToken = (token: string | null): RequestInit => ({
    ...init,
    headers: {
      ...(init.headers as Record<string, string> | undefined),
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
  })
  let res = await fetch(url, withToken(useAuthStore.getState().accessToken))
  if (res.status === 401) {
    try {
      const fresh = await useAuthStore.getState().refreshAccessToken()
      res = await fetch(url, withToken(fresh))
    } catch {
      /* fall through — consumeDiscoveryStream throws on !res.ok and the caller
         falls back to the non-streaming path. */
    }
  }
  return res
}

/**
 * SSE streaming counterpart to `appendMessage` (Spec 77 §6). Consumes the
 * backend `/messages/stream` Server-Sent-Events endpoint via fetch + a
 * ReadableStream reader (EventSource can't POST). Invokes the handlers as
 * frames arrive. The backend keeps a deterministic fallback (flag-off → the
 * full message as one `delta`), so callers get the same event sequence either
 * way. Throws if the connection can't be established (caller falls back to the
 * non-streaming path). Resolves a `{ gotStudentEcho }` flag so the caller knows
 * whether the turn was persisted before any mid-stream failure.
 */
export async function streamDiscoveryMessage(
  sessionId: string,
  body: { role: DiscoveryRole; content: string; extracted_signals?: Record<string, unknown> },
  handlers: DiscoveryStreamHandlers,
  signal?: AbortSignal,
): Promise<{ gotStudentEcho: boolean }> {
  const res = await authedStreamFetch(`${API_BASE}${BASE}/sessions/${sessionId}/messages/stream`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Accept: 'text/event-stream',
    },
    body: JSON.stringify(body),
    signal,
  })
  return consumeDiscoveryStream(res, handlers)
}

/**
 * Uni speaks first. Streams the proactive opener (`POST /opener/stream`) when the
 * student opens an empty conversation — same SSE contract minus `student_message`
 * (the student said nothing). Throws if the connection can't be established.
 */
export async function streamDiscoveryOpener(
  handlers: DiscoveryStreamHandlers,
  signal?: AbortSignal,
): Promise<{ gotStudentEcho: boolean }> {
  const res = await authedStreamFetch(`${API_BASE}${BASE}/opener/stream`, {
    method: 'POST',
    headers: {
      Accept: 'text/event-stream',
    },
    signal,
  })
  return consumeDiscoveryStream(res, handlers)
}

async function consumeDiscoveryStream(
  res: Response,
  handlers: DiscoveryStreamHandlers,
): Promise<{ gotStudentEcho: boolean }> {
  if (!res.ok || !res.body) throw new Error(`stream HTTP ${res.status}`)

  const reader = res.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''
  let gotStudentEcho = false

  // SSE frames are separated by a blank line; each frame has `event:`/`data:`.
  for (;;) {
    const { done, value } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })
    let sep: number
    while ((sep = buffer.indexOf('\n\n')) !== -1) {
      const frame = buffer.slice(0, sep)
      buffer = buffer.slice(sep + 2)
      let event = 'message'
      const dataLines: string[] = []
      for (const line of frame.split('\n')) {
        if (line.startsWith('event:')) event = line.slice(6).trim()
        else if (line.startsWith('data:')) dataLines.push(line.slice(5).replace(/^ /, ''))
      }
      let data: Record<string, unknown> = {}
      const raw = dataLines.join('\n')
      if (raw) {
        try {
          data = JSON.parse(raw)
        } catch {
          data = {}
        }
      }
      switch (event) {
        case 'student_message':
          gotStudentEcho = true
          handlers.onStudentMessage?.(data as unknown as DiscoveryMessage)
          break
        case 'delta':
          if (typeof data.text === 'string') handlers.onDelta?.(data.text)
          break
        case 'assistant_message':
          handlers.onAssistantMessage?.(data as unknown as DiscoveryMessage)
          break
        case 'error':
          handlers.onError?.(typeof data.message === 'string' ? data.message : 'stream error')
          break
        case 'done':
          handlers.onDone?.()
          break
      }
    }
  }
  return { gotStudentEcho }
}

export const getCompletionMap = (): Promise<CompletionMap> =>
  apiClient.get(`${BASE}/completion`).then(r => r.data)

// Spec 19 §6 — personality-layer facets for the Discover rail.
export const getPersonalitySignals = (): Promise<PersonalitySignal[]> =>
  apiClient.get(`${BASE}/personality-signals`).then(r => r.data)

// Spec 19 §7/§10 — deterministic match-ready verdict.
export const getHandoffVerdict = (): Promise<HandoffVerdict> =>
  apiClient.get(`${BASE}/handoff`).then(r => r.data)

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
  HandoffVerdict,
  PersonalitySignal,
}
