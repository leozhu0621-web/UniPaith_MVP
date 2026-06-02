import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, renderHook, screen, waitFor, fireEvent } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { MemoryRouter } from 'react-router-dom'
import type { ReactNode } from 'react'

import FrontendStandardsPage from '../pages/public/FrontendStandardsPage'
import * as buildApi from '../api/build'
import type { FrontendStandards } from '../types/build'
import { qk } from '../api/queryKeys'
import { useOptimisticMutation } from '../hooks/useOptimisticMutation'
import {
  computeBackoff,
  RealtimeClient,
  type ConnectionFactory,
  type ConnectionHandlers,
  type RealtimeMessage,
} from '../lib/realtime'
import {
  track,
  setAnalyticsConsent,
  configureAnalytics,
  flushAnalytics,
  __resetAnalytics,
  type QueuedEvent,
} from '../lib/analytics'

// Spec 54 — frontend engineering standards. Covers the /goal/frontend page
// (the four async states + the primary filter action, per §11) and the net-new
// primitives the spec calls for: the query-key factory (§3), the optimistic
// mutation helper (§4), the realtime client (§9) and the analytics bus (§10).

// ── §3 · query-key factory ──────────────────────────────────────────────────
describe('Spec 54 §3 — query-key factory', () => {
  it('mints stable keys with the full param set', () => {
    expect(qk.buildFrontendStandards()).toEqual(['build-frontend-standards'])
    expect(qk.buildOverview()).toEqual(['build-overview'])
    expect(qk.program('p1')).toEqual(['program', 'p1'])
    expect(qk.recommendations(true)).toEqual(['recommendations', { refresh: true }])
    // params object carries the full filter set so combinations never collide
    expect(qk.pipelineApplications({ stage: 'review', view: 'all' })).toEqual([
      'pipeline-applications',
      { stage: 'review', view: 'all' },
    ])
    // roots match the legacy literals → adopting qk is drop-in
    expect(qk.profile()).toEqual(['profile'])
  })
})

// ── §4 · optimistic mutation ────────────────────────────────────────────────
describe('Spec 54 §4 — useOptimisticMutation', () => {
  function wrapper(qc: QueryClient) {
    return ({ children }: { children: ReactNode }) => (
      <QueryClientProvider client={qc}>{children}</QueryClientProvider>
    )
  }

  it('applies the optimistic patch then rolls back on error', async () => {
    const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
    qc.setQueryData(['saved'], ['a'])
    // A deferred promise so the pending (optimistic) state is observable before
    // the rejection rolls it back — otherwise the transition is too fast to see.
    let reject!: (e: unknown) => void
    const pending = new Promise<void>((_, rej) => {
      reject = rej
    })
    const { result } = renderHook(
      () =>
        useOptimisticMutation<void, string, string[]>({
          mutationFn: () => pending,
          queryKey: ['saved'],
          optimisticUpdate: (cur, v) => [...(cur ?? []), v],
        }),
      { wrapper: wrapper(qc) },
    )

    result.current.mutate('b')
    // While the mutation is pending, the optimistic value is applied.
    await waitFor(() => expect(qc.getQueryData(['saved'])).toEqual(['a', 'b']))
    // On rejection, the cache rolls back to the snapshot.
    reject(new Error('boom'))
    await waitFor(() => expect(result.current.isError).toBe(true))
    expect(qc.getQueryData(['saved'])).toEqual(['a'])
  })

  it('keeps the optimistic value on success', async () => {
    const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
    qc.setQueryData(['saved'], ['a'])
    const { result } = renderHook(
      () =>
        useOptimisticMutation<void, string, string[]>({
          mutationFn: () => Promise.resolve(),
          queryKey: ['saved'],
          optimisticUpdate: (cur, v) => [...(cur ?? []), v],
        }),
      { wrapper: wrapper(qc) },
    )
    result.current.mutate('b')
    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(qc.getQueryData(['saved'])).toEqual(['a', 'b'])
  })
})

// ── §9 · realtime client ────────────────────────────────────────────────────
describe('Spec 54 §9 — realtime client', () => {
  it('computes exponential backoff with a cap', () => {
    expect(computeBackoff(0, { jitter: false })).toBe(1000)
    expect(computeBackoff(1, { jitter: false })).toBe(2000)
    expect(computeBackoff(2, { jitter: false })).toBe(4000)
    expect(computeBackoff(10, { jitter: false, maxMs: 5000 })).toBe(5000)
    // jittered values stay within [0, ceiling]
    const v = computeBackoff(3, { baseMs: 100, factor: 2 }) // ceiling = 800
    expect(v).toBeGreaterThanOrEqual(0)
    expect(v).toBeLessThanOrEqual(800)
  })

  it('opens, dispatches parsed messages, and closes on disconnect', () => {
    let handlers: ConnectionHandlers | null = null
    let closed = false
    const factory: ConnectionFactory = (h) => {
      handlers = h
      return { close: () => (closed = true) }
    }
    const client = new RealtimeClient({ url: 'sse://x', kind: 'sse', connectionFactory: factory })
    const got: RealtimeMessage[] = []
    client.subscribe((m) => got.push(m))

    client.connect()
    expect(client.status).toBe('connecting')
    handlers!.onOpen()
    expect(client.status).toBe('open')

    handlers!.onMessage(JSON.stringify({ type: 'notification', data: { id: 1 } }))
    expect(got).toEqual([{ type: 'notification', data: { id: 1 } }])
    // non-JSON falls back to a {type:'message'} envelope
    handlers!.onMessage('hello')
    expect(got[1]).toEqual({ type: 'message', data: 'hello' })

    client.disconnect()
    expect(closed).toBe(true)
    expect(client.status).toBe('closed')
  })

  it('reconnects with backoff after an error', () => {
    vi.useFakeTimers()
    let calls = 0
    let handlers: ConnectionHandlers | null = null
    const factory: ConnectionFactory = (h) => {
      handlers = h
      calls += 1
      return { close: () => {} }
    }
    const client = new RealtimeClient({
      url: 'sse://x',
      kind: 'sse',
      connectionFactory: factory,
      backoff: { jitter: false, baseMs: 10, factor: 2 },
    })
    client.connect()
    expect(calls).toBe(1)
    handlers!.onError() // schedules a reconnect at backoff(0) = 10ms
    vi.advanceTimersByTime(20)
    expect(calls).toBe(2)
    client.disconnect()
    vi.useRealTimers()
  })
})

// ── §10 · analytics bus ─────────────────────────────────────────────────────
describe('Spec 54 §10 — analytics bus', () => {
  beforeEach(() => __resetAnalytics())

  it('drops events while consent is off', async () => {
    const sent: QueuedEvent[] = []
    configureAnalytics({ transport: (b) => void sent.push(...b), batchSize: 1 })
    track('signup')
    await flushAnalytics()
    expect(sent).toHaveLength(0)
  })

  it('delivers batched events once consent is granted', async () => {
    const sent: QueuedEvent[] = []
    configureAnalytics({ transport: (b) => void sent.push(...b), batchSize: 1 })
    setAnalyticsConsent(true)
    track('program_saved', { id: 'p1' })
    await Promise.resolve()
    expect(sent.map((e) => e.event)).toContain('program_saved')
    expect(sent[0].props.id).toBe('p1')
  })

  it('drops the buffer when consent is revoked', async () => {
    const sent: QueuedEvent[] = []
    configureAnalytics({ transport: (b) => void sent.push(...b), batchSize: 99 })
    setAnalyticsConsent(true)
    track('login') // buffered (batchSize 99)
    setAnalyticsConsent(false) // revoke → buffer dropped
    setAnalyticsConsent(true)
    await flushAnalytics()
    expect(sent).toHaveLength(0)
  })
})

// ── §12 / page · /goal/frontend ─────────────────────────────────────────────
const FRONTEND: FrontendStandards = {
  summary: {
    live_router_count: 42,
    live_route_count: 557,
    doc_claimed_api_modules: 37,
    doc_claimed_routers: 22,
    doc_claimed_stores: 6,
    doc_claimed_hooks: 3,
    state_rule_count: 4,
    build_task_count: 4,
    build_tasks_done: 2,
    build_tasks_partial: 1,
    build_tasks_planned: 1,
    perf_budget_count: 3,
    acceptance_count: 2,
    live_is_source_of_truth: true,
  },
  the_standard: 'A buildable engineering spec for the real frontend.',
  state_rules: [
    { kind: 'Server state', tool: 'TanStack Query v5', where: 'api/<domain>.ts', rule: 'Never copy into Zustand.' },
    { kind: 'Global UI / auth', tool: 'Zustand', where: 'stores/', rule: 'Small, synchronous.' },
    { kind: 'URL state', tool: 'react-router', where: 'useSearchParams', rule: 'tab, filters, q.' },
    { kind: 'Local', tool: 'useState', where: 'component', rule: 'Transient toggles only.' },
  ],
  state_build_rule: 'A screen reads data only through an api/<domain>.ts function.',
  query_key: { rule: 'Keys come from one factory.', example: "qk.program = (id) => ['program', id]", stale_time: 'staleTime per resource.' },
  mutation: { shape: 'useMutation({ onMutate, onError, onSettled })', rule: 'Standardized as useOptimisticMutation.', surfaces: ['Saved (13)', 'Inbox mark-read (17)'] },
  parity: {
    statement: 'Every typed api module maps to a backend router.',
    live_router_count: 42,
    live_route_count: 557,
    doc_claimed_api_modules: 37,
    doc_claimed_routers: 22,
  },
  routing: ['Heavy sub-trees are React.lazy + Suspense.', 'Every route carries errorElement.'],
  error_handling: { interceptor: 'client.ts maps status → action.', ai_fallback: 'AI surfaces fall back, never 5xx.' },
  perf_budgets: [
    { metric: 'LCP', target: '< 2.5 s', note: '4G mid-device.' },
    { metric: 'INP', target: '< 200 ms', note: 'Interaction to Next Paint.' },
    { metric: 'CLS', target: '< 0.1', note: 'Reserved metrics.' },
  ],
  perf_tactics: ['Lighthouse-CI soft → hard.', 'Lazy-load recharts.'],
  realtime: { summary: 'One reconnecting client.', transports: ['SSE — notifications.', 'WebSocket — messaging.'], status: 'Shipped; inert until spec 57.' },
  analytics: { summary: 'A typed event bus.', rules: ['Consent-gated (46).', 'Batched + best-effort.'] },
  testing: ['Vitest + Testing Library + MSW.', 'Type-parity test catches drift.'],
  build_tasks: [
    { key: 'optimistic-mutation', title: 'useOptimisticMutation', status: 'done', evidence: 'Helper shipped + tested.', artifact: 'src/hooks/useOptimisticMutation.ts', fe_verifiable: true },
    { key: 'query-keys', title: 'queryKeys factory', status: 'partial', evidence: 'Factory shipped; migration in progress.', artifact: 'src/api/queryKeys.ts', fe_verifiable: true },
    { key: 'type-parity', title: 'OpenAPI type parity', status: 'planned', evidence: 'Tooling chosen.', artifact: 'src/types/api-generated.ts', fe_verifiable: true },
    { key: 'error-boundaries', title: 'Error boundaries', status: 'done', evidence: 'Root + per-route.', artifact: null, fe_verifiable: false },
  ],
  acceptance: ['No server data in Zustand.', 'Every route error-boundaried.'],
  open_questions: [{ question: 'Bearer SSE transport', recommendation: 'fetch-event-source.' }],
}

function renderPage(ui: React.ReactElement, route = '/goal/frontend') {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter initialEntries={[route]}>{ui}</MemoryRouter>
    </QueryClientProvider>,
  )
}

describe('Spec 54 — /goal/frontend page (four states + filter)', () => {
  beforeEach(() => vi.restoreAllMocks())

  it('loading: shows skeletons, not a blank flash', () => {
    vi.spyOn(buildApi, 'getFrontendStandards').mockReturnValue(new Promise(() => {}))
    const { container } = renderPage(<FrontendStandardsPage />)
    // The hero (static lede) renders immediately; the stat band shows skeletons.
    expect(screen.getByText(/The build spec behind the React app/i)).toBeInTheDocument()
    expect(container.querySelectorAll('.animate-pulse').length).toBeGreaterThan(0)
  })

  it('success: renders parity, build tasks and a live-verified badge', async () => {
    vi.spyOn(buildApi, 'getFrontendStandards').mockResolvedValue(FRONTEND)
    renderPage(<FrontendStandardsPage />)

    await waitFor(() => expect(screen.getByText('useOptimisticMutation')).toBeInTheDocument())
    expect(screen.getByText('queryKeys factory')).toBeInTheDocument()
    // The live backend parity numbers appear (stat band + parity card).
    expect(screen.getAllByText('42').length).toBeGreaterThan(0)
    expect(screen.getAllByText('557').length).toBeGreaterThan(0)
    // import.meta.glob confirmed real artifacts in the bundle → ≥1 verified badge.
    expect(screen.getAllByText(/Verified in bundle/i).length).toBeGreaterThan(0)
    // The doc-vs-live drift note renders.
    expect(screen.getByText(/drafted at 37 api modules/i)).toBeInTheDocument()
  })

  it('filters the build checklist by status', async () => {
    vi.spyOn(buildApi, 'getFrontendStandards').mockResolvedValue(FRONTEND)
    renderPage(<FrontendStandardsPage />)

    await waitFor(() => expect(screen.getByText('queryKeys factory')).toBeInTheDocument())
    // Filter to Done → the partial/planned tasks drop out.
    fireEvent.click(screen.getByRole('button', { name: 'Done' }))
    await waitFor(() => expect(screen.queryByText('queryKeys factory')).not.toBeInTheDocument())
    expect(screen.getByText('useOptimisticMutation')).toBeInTheDocument()
  })

  it('error: shows an error state with retry', async () => {
    vi.spyOn(buildApi, 'getFrontendStandards').mockRejectedValue(new Error('nope'))
    renderPage(<FrontendStandardsPage />)
    await waitFor(() =>
      expect(screen.getByText(/couldn't load the frontend standards/i)).toBeInTheDocument(),
    )
    expect(screen.getByRole('button', { name: 'Retry' })).toBeInTheDocument()
  })
})
