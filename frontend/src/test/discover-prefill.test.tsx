/**
 * Regression: five surfaces navigate to /s?prefill=<question> ("Ask counselor"
 * on a program / school / institution, the review CTA, the Discover search empty
 * state). DiscoverHomePage must read that param and hand the question to Uni —
 * sent as the opening student turn, with the generic opener suppressed — instead
 * of silently dropping it into a blank chat.
 */
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { render, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { MemoryRouter } from 'react-router-dom'

type StreamMsg = { id: string; session_id: string; role: string; content: string; created_at: string }
type StreamCb = {
  onStudentMessage?: (m: StreamMsg) => void
  onAssistantMessage?: (m: StreamMsg) => void
  onDelta?: (t: string) => void
  onError?: (m?: string) => void
  onDone?: () => void
}

vi.mock('../api/discovery', () => ({
  listSessions: vi.fn().mockResolvedValue([]),
  getSession: vi.fn().mockResolvedValue(null),
  startUnifiedSession: vi
    .fn()
    .mockResolvedValue({ id: 's1', track: 'discovery', started_at: '' }),
  appendMessage: vi.fn().mockResolvedValue({
    student_message: { id: 'm1', session_id: 's1', role: 'student', content: 'hi', created_at: '' },
    assistant_message: null,
  }),
  // Capture the streamed turn so we can assert the prefill reached Uni.
  streamDiscoveryMessage: vi.fn(async (_sid: string, msg: { content: string }, cb: StreamCb) => {
    cb.onStudentMessage?.({ id: 'sm', session_id: 's1', role: 'student', content: msg.content, created_at: '' })
    cb.onAssistantMessage?.({ id: 'am', session_id: 's1', role: 'assistant', content: 'Here is my take.', created_at: '' })
    cb.onDone?.()
  }),
  // If the prefill works the opener is suppressed; this must never be called.
  streamDiscoveryOpener: vi.fn(async (_cb: StreamCb, _signal?: unknown) => {}),
  getCompletionMap: vi
    .fn()
    .mockResolvedValue({ profile: '0', goals: '0', needs: '0', identity: '0' }),
  getHandoffVerdict: vi.fn().mockResolvedValue({
    should_handoff: false,
    handoff_target: null,
    reason: '',
    completion: {},
  }),
}))
vi.mock('../api/livingProfile', () => ({
  getLivingProfile: vi.fn().mockResolvedValue({
    narrative: '', lightsUp: [], goals: [], needs: [], gaps: [],
  }),
  updateSignal: vi.fn(),
}))
vi.mock('../stores/auth-store', () => ({
  useAuthStore: (sel: (s: { user: { email: string; uni_guided: boolean } }) => unknown) =>
    sel({ user: { email: 'leo@unipaith.co', uni_guided: true } }),
}))
vi.mock('../stores/toast-store', () => ({ showToast: vi.fn() }))

import DiscoverHomePage from '../pages/student/DiscoverHomePage'
import { streamDiscoveryMessage, streamDiscoveryOpener } from '../api/discovery'

const QUESTION = 'Is Computer Science at MIT a good fit for me? Why or why not?'

function renderHome(route: string) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter initialEntries={[route]}>
        <DiscoverHomePage />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

describe('DiscoverHomePage — /s?prefill cross-sell hand-off', () => {
  beforeEach(() => vi.clearAllMocks())

  it('sends the prefill question to Uni as the opening turn (and suppresses the generic opener)', async () => {
    renderHome(`/s?prefill=${encodeURIComponent(QUESTION)}`)

    await waitFor(() => expect(streamDiscoveryMessage).toHaveBeenCalled())
    const [, msg] = vi.mocked(streamDiscoveryMessage).mock.calls[0]
    expect((msg as { content: string }).content).toBe(QUESTION)

    // The question drove the turn — Uni answers it instead of a generic greeting.
    expect(streamDiscoveryOpener).not.toHaveBeenCalled()
  })

  it('does not touch Uni when there is no prefill param', async () => {
    renderHome('/s')
    // Let mount effects + session resolution settle.
    await waitFor(() => expect(streamDiscoveryOpener).toHaveBeenCalled())
    expect(streamDiscoveryMessage).not.toHaveBeenCalled()
  })
})
