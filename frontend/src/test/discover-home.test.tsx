import { describe, expect, it, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { MemoryRouter } from 'react-router-dom'

// Mock the discovery + strategy API so DiscoverHomePage mounts without a
// backend — render smoke test for the spec-19 surface (H1 copy, track
// selector, gated CTA).
vi.mock('../api/discovery', () => ({
  getCompletionMap: vi
    .fn()
    .mockResolvedValue({ profile: '0', goals: '0', needs: '0', identity: '0' }),
  listSessions: vi.fn().mockResolvedValue([]),
  getSession: vi.fn().mockResolvedValue(null),
  startSession: vi.fn().mockResolvedValue({ id: 's1' }),
  appendMessage: vi.fn().mockResolvedValue({ student_message: {}, assistant_message: null }),
  getPersonalitySignals: vi.fn().mockResolvedValue([]),
}))
vi.mock('../api/strategy', () => ({
  generateStrategy: vi.fn().mockResolvedValue({}),
}))
vi.mock('../stores/auth-store', () => ({
  useAuthStore: (sel: (s: { user: { email: string } }) => unknown) =>
    sel({ user: { email: 'test@unipaith.co' } }),
}))

import DiscoverHomePage from '../pages/student/DiscoverHomePage'

function renderHome() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter initialEntries={['/s']}>
        <DiscoverHomePage />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

describe('DiscoverHomePage (render smoke)', () => {
  it('renders the spec H1 and the three track cards', () => {
    renderHome()
    expect(screen.getByText("Let's figure out what you're looking for")).toBeInTheDocument()
    expect(screen.getByText('Profile')).toBeInTheDocument()
    expect(screen.getByText('Goals')).toBeInTheDocument()
    expect(screen.getByText('Needs')).toBeInTheDocument()
  })

  it('shows the Generate strategy CTA disabled until tracks reach threshold', () => {
    renderHome()
    const cta = screen.getByRole('button', { name: /generate strategy/i })
    expect(cta).toBeDisabled()
  })
})
