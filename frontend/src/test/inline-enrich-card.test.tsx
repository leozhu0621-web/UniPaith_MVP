/**
 * InlineChatEnrichCard — the inline Prompt-Library widget that surfaces inside
 * the Uni conversation thread after the most recent assistant message.
 *
 * Tests verify:
 *  1. Widget card renders in the thread when there is an assistant message and
 *     getEnrichNext returns an item.
 *  2. Widget does NOT render while Uni is streaming (avoids flicker).
 *  3. Widget renders nothing (gracefully absent) when getEnrichNext returns no
 *     items (profile complete — EnrichWidget self-hides).
 */
import { describe, expect, it, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { MemoryRouter } from 'react-router-dom'

// ── API mocks ────────────────────────────────────────────────────────────────

const mockGetEnrichNext = vi.fn()
vi.mock('../api/enrichment', () => ({
  getEnrichNext: (...args: unknown[]) => mockGetEnrichNext(...args),
  setEnrichValue: vi.fn().mockResolvedValue({}),
}))

vi.mock('../api/discovery', () => ({
  listSessions: vi.fn().mockResolvedValue([
    { id: 's1', track: 'discovery', started_at: '2026-06-20T00:00:00Z', status: 'active' },
  ]),
  getSession: vi.fn().mockResolvedValue({
    id: 's1',
    track: 'discovery',
    started_at: '2026-06-20T00:00:00Z',
    messages: [
      {
        id: 'm1',
        session_id: 's1',
        role: 'assistant',
        content: "What's important to you in choosing a school?",
        extracted_signals: null,
        created_at: '2026-06-20T00:00:00Z',
      },
    ],
  }),
  startUnifiedSession: vi.fn().mockResolvedValue({ id: 's1', track: 'discovery', started_at: '' }),
  appendMessage: vi.fn().mockResolvedValue({
    student_message: { id: 'm2', session_id: 's1', role: 'student', content: 'hi', created_at: '' },
    assistant_message: null,
  }),
  streamDiscoveryMessage: vi.fn(),
  streamDiscoveryOpener: vi.fn(),
  getCompletionMap: vi.fn().mockResolvedValue({ profile: '0', goals: '0', needs: '0', identity: '0' }),
  getHandoffVerdict: vi.fn().mockResolvedValue({
    should_handoff: false, handoff_target: null, reason: '', completion: {},
  }),
}))

vi.mock('../api/livingProfile', () => ({
  getLivingProfile: vi.fn().mockResolvedValue({ narrative: '', lightsUp: [], goals: [], needs: [], gaps: [] }),
  updateSignal: vi.fn(),
}))
vi.mock('../stores/auth-store', () => ({
  useAuthStore: (sel: (s: { user: { email: string; uni_guided: boolean } }) => unknown) =>
    sel({ user: { email: 'leo@unipaith.co', uni_guided: false } }),
}))
vi.mock('../stores/toast-store', () => ({ showToast: vi.fn() }))

import UniConversation from '../pages/student/discover/UniConversation'

function renderConversation() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter>
        <UniConversation />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

// ── Tests ────────────────────────────────────────────────────────────────────

describe('InlineChatEnrichCard in UniConversation', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders the enrich widget card when getEnrichNext returns an item', async () => {
    mockGetEnrichNext.mockResolvedValue({
      items: [
        {
          field: 'target_degree_level',
          type: 'string',
          tier: 'essential',
          ask_kind: 'choice',
          question: 'What degree level are you targeting?',
          options: ["Bachelor's", "Master's", 'PhD'],
          action: 'ask',
          current_value: null,
          confidence: null,
        },
      ],
      essentials_present: false,
    })

    renderConversation()

    // The widget question should appear in the thread
    await waitFor(() => {
      expect(
        screen.getByText('What degree level are you targeting?'),
      ).toBeInTheDocument()
    })

    // The "needed to match" badge appears for essential-tier items in inline mode
    expect(screen.getByText('needed to match')).toBeInTheDocument()

    // Choice options are rendered as buttons
    expect(screen.getByRole('button', { name: "Bachelor's" })).toBeInTheDocument()
  })

  it('renders nothing when getEnrichNext returns no items (profile complete)', async () => {
    mockGetEnrichNext.mockResolvedValue({ items: [], essentials_present: true })

    renderConversation()

    // Wait for conversation to settle
    await waitFor(() => {
      expect(
        screen.getByText("What's important to you in choosing a school?"),
      ).toBeInTheDocument()
    })

    // No enrich question or option buttons should appear
    expect(screen.queryByText('needed to match')).not.toBeInTheDocument()
  })

  it('does NOT show the "Enrich your profile" eyebrow when inline', async () => {
    mockGetEnrichNext.mockResolvedValue({
      items: [
        {
          field: 'gpa',
          type: 'number',
          tier: 'high_value',
          ask_kind: 'number',
          question: 'What is your GPA?',
          options: null,
          action: 'ask',
          current_value: null,
          confidence: null,
        },
      ],
      essentials_present: true,
    })

    renderConversation()

    await waitFor(() => {
      expect(screen.getByText('What is your GPA?')).toBeInTheDocument()
    })

    // The default eyebrow header must be absent in inline/thread mode
    expect(screen.queryByText('Enrich your profile')).not.toBeInTheDocument()
  })
})
