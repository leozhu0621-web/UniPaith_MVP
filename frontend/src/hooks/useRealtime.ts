// Spec 54 §9 — React binding for the realtime client.
//
// On a message the handler PATCHES the Query cache (qc.setQueryData) rather than
// refetching, so a notification / new-post / typing event updates the UI without
// a network round-trip. `enabled` defaults to false: nothing connects until
// spec 57 ships real endpoints, so adding this hook to a surface today is inert.

import { useEffect, useRef, useState } from 'react'
import { useQueryClient, type QueryClient } from '@tanstack/react-query'
import {
  RealtimeClient,
  type RealtimeKind,
  type RealtimeMessage,
  type RealtimeStatus,
} from '../lib/realtime'

export interface UseRealtimeOptions {
  url: string
  kind?: RealtimeKind
  /** Off by default — flip on once the §57 endpoint exists for this surface. */
  enabled?: boolean
  token?: string | null
  /** Patch the cache from the event. Receives the live QueryClient. */
  onMessage?: (msg: RealtimeMessage, qc: QueryClient) => void
  onStatus?: (status: RealtimeStatus) => void
}

export function useRealtime(opts: UseRealtimeOptions): { status: RealtimeStatus } {
  const qc = useQueryClient()
  const [status, setStatus] = useState<RealtimeStatus>('idle')

  // Keep the latest callbacks without forcing a reconnect when they change.
  const onMessageRef = useRef(opts.onMessage)
  const onStatusRef = useRef(opts.onStatus)
  onMessageRef.current = opts.onMessage
  onStatusRef.current = opts.onStatus

  const { url, kind, enabled = false, token = null } = opts

  useEffect(() => {
    if (!enabled) return
    const client = new RealtimeClient({ url, kind, token })
    const unsubMsg = client.subscribe((msg) => onMessageRef.current?.(msg, qc))
    const unsubStatus = client.onStatus((s) => {
      setStatus(s)
      onStatusRef.current?.(s)
    })
    client.connect()
    return () => {
      unsubMsg()
      unsubStatus()
      client.disconnect()
    }
  }, [url, kind, enabled, token, qc])

  return { status }
}
