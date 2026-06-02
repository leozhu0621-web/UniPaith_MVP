// Spec 54 §9 — the realtime client (SSE + WebSocket), reconnecting, cache-first.
//
// One client, two transports:
//   • SSE (EventSource) — notifications bell, feed "new posts", chat token
//     streaming (§57 §1, §19).
//   • WebSocket — messaging (§17 / §29): typing + read receipts.
//
// Contract (the rest lands with spec 57's endpoints):
//   • One reconnecting connection with exponential backoff + full jitter.
//   • On an event, the consumer PATCHES the Query cache (qc.setQueryData) —
//     never a full refetch — via `useRealtime` (see hooks/useRealtime.ts).
//
// Dependency-free: native EventSource / WebSocket. Native EventSource can't set
// an Authorization header (§14 open question — recommends
// @microsoft/fetch-event-source for bearer SSE); until that dep is adopted, a
// token is appended as `?access_token=` so the seam is ready. Nothing connects
// on its own — `useRealtime({ enabled })` defaults to off — so this is inert
// until 57 wires real endpoints.

export type RealtimeKind = 'sse' | 'ws'
export type RealtimeStatus = 'idle' | 'connecting' | 'open' | 'closed' | 'error'

export interface RealtimeMessage<T = unknown> {
  type: string
  data: T
}

export type RealtimeListener = (msg: RealtimeMessage) => void
export type StatusListener = (status: RealtimeStatus) => void

export interface BackoffOptions {
  baseMs?: number
  factor?: number
  maxMs?: number
  jitter?: boolean
}

/**
 * Exponential backoff with optional full jitter. Pure → unit-testable.
 * attempt 0 → ~base, capped at maxMs. Jitter spreads reconnects so a fleet of
 * clients doesn't stampede the server after an outage.
 */
export function computeBackoff(attempt: number, opts: BackoffOptions = {}): number {
  const base = opts.baseMs ?? 1000
  const factor = opts.factor ?? 2
  const max = opts.maxMs ?? 30_000
  const ceiling = Math.min(max, base * factor ** Math.max(0, attempt))
  if (opts.jitter === false) return ceiling
  return Math.round(Math.random() * ceiling)
}

// A minimal connection the client drives. Native EventSource/WebSocket are
// adapted to it; tests inject a fake. This is the only IO seam.
export interface RealtimeConnection {
  close(): void
}

export interface ConnectionHandlers {
  onOpen: () => void
  onMessage: (raw: string) => void
  onError: () => void
  onClose: () => void
}

export type ConnectionFactory = (
  handlers: ConnectionHandlers,
  url: string,
  kind: RealtimeKind,
) => RealtimeConnection

export interface RealtimeOptions {
  url: string
  /** Defaults to 'ws' for ws:// or wss:// urls, otherwise 'sse'. */
  kind?: RealtimeKind
  /** Appended as ?access_token= for EventSource (no custom-header support). */
  token?: string | null
  backoff?: BackoffOptions
  /** Test seam: build the underlying connection. Defaults to native ES/WS. */
  connectionFactory?: ConnectionFactory
}

function inferKind(url: string): RealtimeKind {
  return /^wss?:\/\//i.test(url) ? 'ws' : 'sse'
}

function withToken(url: string, token: string | null | undefined): string {
  if (!token) return url
  const sep = url.includes('?') ? '&' : '?'
  return `${url}${sep}access_token=${encodeURIComponent(token)}`
}

const defaultConnectionFactory: ConnectionFactory = (handlers, url, kind) => {
  if (kind === 'ws') {
    const ws = new WebSocket(url)
    ws.onopen = () => handlers.onOpen()
    ws.onmessage = (e: MessageEvent) => handlers.onMessage(String(e.data))
    ws.onerror = () => handlers.onError()
    ws.onclose = () => handlers.onClose()
    return { close: () => ws.close() }
  }
  const es = new EventSource(url)
  es.onopen = () => handlers.onOpen()
  es.onmessage = (e: MessageEvent) => handlers.onMessage(String(e.data))
  // EventSource auto-reconnects; we drive reconnection ourselves for unified
  // backoff, so on error we close and schedule our own retry.
  es.onerror = () => handlers.onError()
  return { close: () => es.close() }
}

function parseMessage(raw: string): RealtimeMessage {
  try {
    const obj = JSON.parse(raw) as { type?: string; data?: unknown }
    if (obj && typeof obj === 'object' && typeof obj.type === 'string') {
      return { type: obj.type, data: obj.data ?? null }
    }
    return { type: 'message', data: obj }
  } catch {
    return { type: 'message', data: raw }
  }
}

export class RealtimeClient {
  status: RealtimeStatus = 'idle'

  private readonly url: string
  private readonly kind: RealtimeKind
  private readonly token: string | null
  private readonly backoff: BackoffOptions
  private readonly factory: ConnectionFactory

  private conn: RealtimeConnection | null = null
  private attempt = 0
  private closedByUser = false
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null
  private readonly listeners = new Set<RealtimeListener>()
  private readonly statusListeners = new Set<StatusListener>()

  constructor(opts: RealtimeOptions) {
    this.url = opts.url
    this.kind = opts.kind ?? inferKind(opts.url)
    this.token = opts.token ?? null
    this.backoff = opts.backoff ?? {}
    this.factory = opts.connectionFactory ?? defaultConnectionFactory
  }

  subscribe(listener: RealtimeListener): () => void {
    this.listeners.add(listener)
    return () => this.listeners.delete(listener)
  }

  onStatus(listener: StatusListener): () => void {
    this.statusListeners.add(listener)
    return () => this.statusListeners.delete(listener)
  }

  connect(): void {
    this.closedByUser = false
    this.open()
  }

  disconnect(): void {
    this.closedByUser = true
    if (this.reconnectTimer !== null) {
      clearTimeout(this.reconnectTimer)
      this.reconnectTimer = null
    }
    this.conn?.close()
    this.conn = null
    this.setStatus('closed')
  }

  private open(): void {
    this.setStatus('connecting')
    const url = this.kind === 'sse' ? withToken(this.url, this.token) : this.url
    this.conn = this.factory(
      {
        onOpen: () => {
          this.attempt = 0
          this.setStatus('open')
        },
        onMessage: (raw) => this.dispatch(parseMessage(raw)),
        onError: () => {
          this.setStatus('error')
          this.scheduleReconnect()
        },
        onClose: () => {
          if (!this.closedByUser) this.scheduleReconnect()
        },
      },
      url,
      this.kind,
    )
  }

  private scheduleReconnect(): void {
    if (this.closedByUser) return
    this.conn?.close()
    this.conn = null
    const delay = computeBackoff(this.attempt++, this.backoff)
    this.reconnectTimer = setTimeout(() => this.open(), delay)
  }

  private dispatch(msg: RealtimeMessage): void {
    for (const l of this.listeners) l(msg)
  }

  private setStatus(status: RealtimeStatus): void {
    this.status = status
    for (const l of this.statusListeners) l(status)
  }
}
