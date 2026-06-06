import { describe, expect, it, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { MemoryRouter } from 'react-router-dom'

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
  getHandoffVerdict: vi.fn().mockResolvedValue({
    should_handoff: false,
    handoff_target: null,
    reason: '',
    completion: {},
  }),
}))
vi.mock('../api/livingProfile', () => ({
  getLivingProfile: vi.fn().mockResolvedValue({
    narrative: 'You light up around hands-on problems.',
    lightsUp: ['curiosity'],
    goals: [],
    needs: [],
    gaps: [],
  }),
  updateSignal: vi.fn(),
}))
vi.mock('../stores/auth-store', () => ({
  useAuthStore: (sel: (s: { user: { email: string } }) => unknown) =>
    sel({ user: { email: 'leo@unipaith.co' } }),
}))
vi.mock('../stores/toast-store', () => ({ showToast: vi.fn() }))

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

describe('DiscoverHomePage — Uni redesign', () => {
  it('renders the Uni conversation and the quiet profile link', async () => {
    renderHome()
    expect(screen.getByText('Discover · with Uni')).toBeInTheDocument()
    expect(await screen.findByText(/I'm Uni/)).toBeInTheDocument()
    expect(screen.getByText('Your profile')).toBeInTheDocument()
    expect(screen.getByPlaceholderText(/Tell Uni what's on your mind/i)).toBeInTheDocument()
  })

  it('drops the old track/layer/strategy chrome', () => {
    renderHome()
    expect(screen.queryByRole('button', { name: /generate strategy/i })).not.toBeInTheDocument()
    expect(screen.queryByText("Let's figure out what you're looking for")).not.toBeInTheDocument()
  })

  it('offers counselor-style ways-in (gentle quick replies)', () => {
    renderHome()
    expect(screen.getByText("I'm not sure where to start")).toBeInTheDocument()
    expect(screen.getByText('Could you give an example?')).toBeInTheDocument()
  })

  it('opens the living-profile drawer from the trigger', async () => {
    renderHome()
    await screen.findByText(/I'm Uni/)
    fireEvent.click(screen.getByText('Your profile'))
    expect(await screen.findByText('What lights you up')).toBeInTheDocument()
    expect(screen.getByText(/You light up around hands-on problems/)).toBeInTheDocument()
  })
})
