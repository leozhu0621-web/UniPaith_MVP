import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import SavedListPage from '../pages/student/SavedListPage'

vi.mock('../api/saved-lists', () => ({
  listSaved: vi.fn().mockResolvedValue([]),
  listSavedTagSuggestions: vi.fn().mockResolvedValue([]),
  unsaveProgram: vi.fn(),
  patchSavedProgram: vi.fn(),
  startApplicationFromSaved: vi.fn(),
}))

vi.mock('../api/events', () => ({
  getMyFollows: vi.fn().mockResolvedValue([]),
  unfollowInstitution: vi.fn().mockResolvedValue(undefined),
}))

vi.mock('../stores/compare-store', () => ({
  MAX_COMPARE: 4,
  useCompareStore: () => ({
    items: [],
    hydrated: true,
    rejectedFull: false,
    compareRunTick: 0,
    hydrate: vi.fn(),
    add: vi.fn(),
    remove: vi.fn(),
    clear: vi.fn(),
    has: () => false,
    isFull: () => false,
    requestCompareRun: vi.fn(),
  }),
}))

function renderPage() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter>
        <SavedListPage />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

describe('SavedListPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('shows spec empty state copy and Open Match CTA', async () => {
    renderPage()
    expect(await screen.findByText('Your shortlist')).toBeTruthy()
    expect(screen.getByText(/Save programs from Match or Discovery/)).toBeTruthy()
    expect(screen.getByRole('button', { name: /Open Match/i })).toBeTruthy()
  })

  it('renders Programs and Schools tabs', async () => {
    renderPage()
    expect(await screen.findByRole('button', { name: /Programs \(0\)/i })).toBeTruthy()
    expect(screen.getByRole('button', { name: /Schools \(0\)/i })).toBeTruthy()
  })

  it('shows shortlist helper copy', async () => {
    renderPage()
    expect(
      await screen.findByText(/Curate programs you are serious about/i),
    ).toBeTruthy()
  })
})
