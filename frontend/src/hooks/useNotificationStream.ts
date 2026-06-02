// Spec 57 §5 — bind the SSE notification stream to the Query cache.
//
// Opens GET /me/stream via the reconnecting realtime client and, on each typed
// event, PATCHES the cache (qc.setQueryData) instead of refetching:
//   • connected / notification.unread_count → set the unread-count query
//   • notification.created                  → prepend to the notifications list
//   • notification.read / read_all          → flip is_read in the list
// Cross-tab / cross-device read-state sync is automatic: the backend echoes
// read events to *every* open stream for the user (each tab has its own SSE
// connection), so a mark-read in one tab patches the others (§5).

import type { QueryClient } from '@tanstack/react-query'

import { qk } from '../api/queryKeys'
import { useAuthStore } from '../stores/auth-store'
import type { Notification } from '../types'
import type { RealtimeMessage, RealtimeStatus } from '../lib/realtime'
import { useRealtime } from './useRealtime'

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'

function patchList(
  qc: QueryClient,
  fn: (old: Notification[]) => Notification[],
): void {
  qc.setQueriesData<Notification[] | undefined>({ queryKey: qk.notifications() }, (old) =>
    Array.isArray(old) ? fn(old) : old,
  )
}

function setUnread(qc: QueryClient, count: number): void {
  qc.setQueryData(qk.notificationsUnread(), { count })
}

export function handleNotificationEvent(msg: RealtimeMessage, qc: QueryClient): void {
  switch (msg.type) {
    case 'connected': {
      const d = msg.data as { unread?: number } | null
      if (d && typeof d.unread === 'number') setUnread(qc, d.unread)
      break
    }
    case 'notification.unread_count': {
      const d = msg.data as { count?: number } | null
      if (d && typeof d.count === 'number') setUnread(qc, d.count)
      break
    }
    case 'notification.created': {
      const n = msg.data as Notification | null
      if (n && n.id) {
        patchList(qc, (old) => (old.some((x) => x.id === n.id) ? old : [n, ...old]))
      }
      break
    }
    case 'notification.read': {
      const d = msg.data as { id?: string } | null
      if (d && d.id) {
        patchList(qc, (old) => old.map((x) => (x.id === d.id ? { ...x, is_read: true } : x)))
      }
      break
    }
    case 'notification.read_all': {
      patchList(qc, (old) => old.map((x) => ({ ...x, is_read: true })))
      break
    }
    default:
      break
  }
}

export function useNotificationStream(enabled = true): { status: RealtimeStatus } {
  const token = useAuthStore((s) => s.accessToken)
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated)

  return useRealtime({
    url: `${API_BASE}/me/stream`,
    kind: 'sse',
    enabled: enabled && isAuthenticated && Boolean(token),
    token,
    onMessage: handleNotificationEvent,
  })
}
