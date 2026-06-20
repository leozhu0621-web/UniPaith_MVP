import { describe, expect, it, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
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
    narrative: 'You light up around hands-on problems.',
    lightsUp: ['curiosity'],
    goals: [],
    needs: [],
    gaps: [],
  }),
  updateSignal: vi.fn(),
}))
vi.mock('../stores/auth-store', () => ({
  useAuthStore: (sel: (s: { user: { email: string; uni_guided: boolean } }) => unknown) =>
    sel({ user: { email: 'leo@unipaith.co', uni_guided: true } }),
}))
vi.mock('../stores/toast-store', () => ({ showToast: vi.fn() }))
vi.mock('../api/enrichment', () => ({
  getEnrichNext: vi.fn().mockResolvedValue({ items: [], essentials_present: true }),
  setEnrichValue: vi.fn().mockResolvedValue({}),
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

describe('DiscoverHomePage — Uni guided workspace', () => {
  it('renders the Uni conversation and the journey rail', async () => {
    renderHome()
    expect(await screen.findByText(/I'm Uni/)).toBeInTheDocument()
    expect(screen.getByPlaceholderText(/Tell Uni what's on your mind/i)).toBeInTheDocument()
    // Rail stages (unique to the rail; "About you" is also echoed in the mobile bar)
    expect(screen.getByText('Your goals')).toBeInTheDocument()
    expect(screen.getByText('What you need')).toBeInTheDocument()
    expect(screen.getByText('Your matches')).toBeInTheDocument()
  })

  it('shows the living profile (rail on lg, its own column on xl)', async () => {
    renderHome()
    // The living profile renders in both responsive slots — inside the rail (shown
    // at lg, xl:hidden) and as its own right column (hidden xl:block). jsdom has no
    // breakpoints, so both copies are in the DOM; assert it's present at least once.
    expect((await screen.findAllByText(/You light up around hands-on problems/)).length).toBeGreaterThan(0)
    expect(screen.getAllByText('What Uni knows about you').length).toBeGreaterThan(0)
    expect(screen.getAllByText('What lights you up').length).toBeGreaterThan(0)
  })

  it('drops the old track/layer/strategy chrome', () => {
    renderHome()
    expect(screen.queryByRole('button', { name: /generate strategy/i })).not.toBeInTheDocument()
    expect(screen.queryByText("Let's figure out what you're looking for")).not.toBeInTheDocument()
  })

  it('offers counselor-style ways-in (gentle quick replies)', async () => {
    renderHome()
    await screen.findByText(/I'm Uni/)
    expect(screen.getByText("I'm not sure where to start")).toBeInTheDocument()
    expect(screen.getByText('Could you give an example?')).toBeInTheDocument()
  })
})
