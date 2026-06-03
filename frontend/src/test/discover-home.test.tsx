import { describe, expect, it, vi } from 'vitest'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { MemoryRouter } from 'react-router-dom'
import { useConfirmStore } from '../stores/confirm-store'

vi.mock('../api/discovery', () => ({
  getCompletionMap: vi
    .fn()
    .mockResolvedValue({ profile: '0', goals: '0', needs: '0', identity: '0' }),
  listSessions: vi.fn().mockResolvedValue([]),
  getSession: vi.fn().mockResolvedValue(null),
  startSession: vi.fn().mockResolvedValue({ id: 's1' }),
  appendMessage: vi.fn().mockResolvedValue({
    student_message: { id: 'm1', session_id: 's1', role: 'student', content: 'hi', created_at: '' },
    assistant_message: {
      id: 'm2',
      session_id: 's1',
      role: 'assistant',
      content: 'Hello',
      extracted_signals: {},
      created_at: '',
    },
  }),
  getPersonalitySignals: vi.fn().mockResolvedValue([]),
  getHandoffVerdict: vi.fn().mockResolvedValue({ should_handoff: false, handoff_target: null }),
}))
vi.mock('../api/strategy', () => ({
  generateStrategy: vi.fn().mockResolvedValue({}),
}))
vi.mock('../api/students', () => ({
  getProfile: vi.fn().mockResolvedValue({}),
  listAcademics: vi.fn().mockResolvedValue([]),
}))
vi.mock('../api/goals', () => ({
  listGoals: vi.fn().mockResolvedValue([]),
}))
vi.mock('../api/needs', () => ({
  listNeeds: vi.fn().mockResolvedValue([]),
}))
vi.mock('../api/identity', () => ({
  getIdentity: vi.fn().mockRejectedValue(new Error('no identity')),
}))
vi.mock('../stores/auth-store', () => ({
  useAuthStore: (sel: (s: { user: { email: string } }) => unknown) =>
    sel({ user: { email: 'test@unipaith.co' } }),
}))

import DiscoverHomePage from '../pages/student/DiscoverHomePage'

function renderHome(route = '/s') {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter initialEntries={[route]}>
        <DiscoverHomePage />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

describe('DiscoverHomePage (spec 19)', () => {
  it('renders the spec eyebrow, H1, and three track cards', () => {
    renderHome()
    expect(screen.getByText('Discover')).toBeInTheDocument()
    expect(screen.getByText("Let's figure out what you're looking for")).toBeInTheDocument()
    expect(screen.getByText('Profile')).toBeInTheDocument()
    expect(screen.getByText('Goals')).toBeInTheDocument()
    expect(screen.getByText('Needs')).toBeInTheDocument()
  })

  it('shows profile layer dots on the Profile track card', () => {
    renderHome('/s?layer=basic')
    expect(screen.getByText(/Layer: Basic/)).toBeInTheDocument()
  })

  it('shows the Generate strategy CTA disabled until tracks reach threshold', () => {
    renderHome()
    const cta = screen.getByRole('button', { name: /generate strategy/i })
    expect(cta).toBeDisabled()
  })

  it('enables Generate strategy when all tracks meet threshold', async () => {
    const { getCompletionMap } = await import('../api/discovery')
    vi.mocked(getCompletionMap).mockResolvedValue({
      profile: '0.6',
      goals: '0.55',
      needs: '0.5',
      identity: '0.4',
    })
    renderHome()
    await waitFor(() => {
      expect(screen.getByRole('button', { name: /generate strategy/i })).not.toBeDisabled()
    })
  })

  it('renders basic-layer suggested prompt chips in empty chat', () => {
    renderHome('/s?layer=basic')
    expect(screen.getByText('I love board games')).toBeInTheDocument()
    expect(screen.getByText('Word puzzles I guess')).toBeInTheDocument()
  })

  it('asks before switching track when the composer has a draft', () => {
    useConfirmStore.getState().settle(false) // clear any prior pending confirm
    renderHome()
    const textarea = screen.getByPlaceholderText(/tell me about your life/i)
    fireEvent.change(textarea, { target: { value: 'draft message' } })
    fireEvent.click(screen.getByRole('button', { name: /Goals.*SMART/i }))
    // Switching tracks with a draft opens the styled confirm (Spec 78 §6),
    // not a native window.confirm.
    expect(useConfirmStore.getState().current?.title).toBe('Discard your message?')
    useConfirmStore.getState().settle(false)
  })
})
