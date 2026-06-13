// Spec 54 §10 — a typed, consent-gated, batched analytics event bus.
//
// Emits the product funnel events (signup, discover_message_sent,
// program_saved, application_started, decision_viewed, …) that feed product
// metrics and the §56 ranking signals. Three invariants:
//
//   1. Typed     — `track()` autocompletes the known funnel events; props are
//                  a flat scalar bag.
//   2. Consent   — gated on analytics consent (§46). No event is buffered or
//                  sent while consent is off; revoking consent drops the buffer.
//   3. Resilient — analytics must NEVER break the app. Delivery is best-effort,
//                  batched, and every failure is swallowed.
//
// No sink is configured by default → events are dropped silently until the app
// calls `configureAnalytics({ endpoint })` (or injects a transport in tests).

// Known funnel events, while still allowing ad-hoc names (the `& {}` keeps
// literal autocomplete without closing the type).
export type AnalyticsEvent =
  | 'signup'
  | 'login'
  | 'discover_message_sent'
  | 'program_viewed'
  | 'program_saved'
  | 'application_started'
  | 'application_submitted'
  | 'decision_viewed'
  | 'search_performed'
  // Onboarding funnel (UX overhaul Ship C §3) — fired by the wizard. Consent
  // gating unchanged: no consent, no event.
  | 'onboarding_started'
  | 'onboarding_step_completed'
  | 'onboarding_completed'
  | 'onboarding_skipped'
  // Ship C tour + journey checklist (fired by Coachmark / JourneyChecklistCard).
  | 'coachmark_dismissed'
  | 'onboarding_checklist_step_clicked'
  | (string & {})

export type AnalyticsProps = Record<string, string | number | boolean | null | undefined>

export interface QueuedEvent {
  event: string
  props: AnalyticsProps
  ts: number
}

export type AnalyticsTransport = (events: QueuedEvent[]) => void | Promise<void>

interface AnalyticsConfig {
  endpoint: string | null
  batchSize: number
  flushIntervalMs: number
  transport: AnalyticsTransport | null
}

let consent = false
let queue: QueuedEvent[] = []
let timer: ReturnType<typeof setInterval> | null = null
let lifecycleBound = false

const config: AnalyticsConfig = {
  endpoint: null,
  batchSize: 20,
  flushIntervalMs: 10_000,
  transport: null,
}

/** Grant or revoke analytics consent (§46). Revoking drops anything buffered. */
export function setAnalyticsConsent(granted: boolean): void {
  consent = granted
  if (!granted) {
    queue = []
    clearTimer()
  }
}

export function getAnalyticsConsent(): boolean {
  return consent
}

/** Point the bus at a sink (and tune batching). Call once at app start. */
export function configureAnalytics(opts: Partial<AnalyticsConfig>): void {
  Object.assign(config, opts)
}

/** Enqueue a funnel event. No-op unless consent is granted. */
export function track(event: AnalyticsEvent, props: AnalyticsProps = {}): void {
  if (!consent) return
  queue.push({ event, props, ts: Date.now() })
  if (queue.length >= config.batchSize) {
    void flushAnalytics()
  } else {
    ensureTimer()
  }
}

/** Send everything buffered now. Safe to call repeatedly; never throws. */
export async function flushAnalytics(): Promise<void> {
  if (queue.length === 0) return
  const batch = queue
  queue = []
  try {
    await deliver(batch)
  } catch {
    // Swallow — analytics is fire-and-forget and must not surface to the user.
  }
}

function deliver(batch: QueuedEvent[]): void | Promise<void> {
  if (config.transport) return config.transport(batch)
  if (!config.endpoint) return // no sink → drop silently
  const body = JSON.stringify({ events: batch })
  if (typeof navigator !== 'undefined' && typeof navigator.sendBeacon === 'function') {
    navigator.sendBeacon(config.endpoint, body)
    return
  }
  if (typeof fetch !== 'undefined') {
    return fetch(config.endpoint, {
      method: 'POST',
      body,
      headers: { 'Content-Type': 'application/json' },
      keepalive: true,
    }).then(() => undefined)
  }
}

function ensureTimer(): void {
  if (typeof window === 'undefined') return
  if (timer === null) {
    timer = setInterval(() => void flushAnalytics(), config.flushIntervalMs)
  }
  if (!lifecycleBound) {
    lifecycleBound = true
    // Flush the tail on the way out so the last events aren't lost.
    window.addEventListener('pagehide', () => void flushAnalytics())
    document.addEventListener('visibilitychange', () => {
      if (document.visibilityState === 'hidden') void flushAnalytics()
    })
  }
}

function clearTimer(): void {
  if (timer !== null) {
    clearInterval(timer)
    timer = null
  }
}

/** Test-only: reset all module state. */
export function __resetAnalytics(): void {
  consent = false
  queue = []
  clearTimer()
  config.endpoint = null
  config.batchSize = 20
  config.flushIntervalMs = 10_000
  config.transport = null
}
