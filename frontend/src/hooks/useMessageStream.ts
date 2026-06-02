// Spec 57 §2 — bind the WebSocket messaging stream to the inbox Query cache.
//
// On an instant-delivery event (messaging.message) or a read receipt, PATCH the
// affected inbox queries by invalidating them so the thread + list update the
// moment a message arrives — no polling. The WS transport (typing / read / delivery
// fan-out, ping/pong) is served by /ws/messages and fully tested server-side; the
// typing-indicator UI is the named FE follow-up.
//
// The realtime client appends the bearer token to SSE URLs only, so for the WS we
// bake ?access_token= into the URL ourselves (the endpoint reads it from there).

import type { QueryClient } from '@tanstack/react-query'

import { useAuthStore } from '../stores/auth-store'
import type { RealtimeMessage, RealtimeStatus } from '../lib/realtime'
import { useRealtime } from './useRealtime'

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'
const WS_BASE = API_BASE.replace(/^http/i, 'ws')

export function handleMessageEvent(
  msg: RealtimeMessage,
  qc: QueryClient,
  activeThreadId?: string | null,
): void {
  if (msg.type !== 'messaging.message' && msg.type !== 'messaging.read') return
  qc.invalidateQueries({ queryKey: ['inbox-threads'] })
  qc.invalidateQueries({ queryKey: ['inbox-threads-all'] })
  const convId = (msg.data as { conversation_id?: string } | null)?.conversation_id
  const target = convId ?? activeThreadId
  if (target) qc.invalidateQueries({ queryKey: ['inbox-thread', target] })
}

export function useMessageStream(
  opts: { enabled?: boolean; activeThreadId?: string | null } = {},
): { status: RealtimeStatus } {
  const { enabled = true, activeThreadId = null } = opts
  const token = useAuthStore((s) => s.accessToken)
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated)

  return useRealtime({
    url: `${WS_BASE}/ws/messages?access_token=${encodeURIComponent(token ?? '')}`,
    kind: 'ws',
    enabled: enabled && isAuthenticated && Boolean(token),
    token,
    onMessage: (msg, client) => handleMessageEvent(msg, client, activeThreadId),
  })
}
