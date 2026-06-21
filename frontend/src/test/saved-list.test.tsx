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

  it('shows spec empty state copy and Open Discover CTA', async () => {
    renderPage()
    expect(await screen.findByText('Saved')).toBeTruthy()
    expect(screen.getByText(/No saved programs yet/)).toBeTruthy()
    expect(screen.getByRole('button', { name: /Open Discover/i })).toBeTruthy()
  })

  it('renders Programs and Schools tabs', async () => {
    renderPage()
    expect(await screen.findByRole('tab', { name: /Programs \(0\)/i })).toBeTruthy()
    expect(screen.getByRole('tab', { name: /Schools \(0\)/i })).toBeTruthy()
  })

  it('shows the saved header', async () => {
    // The descriptive sub-tagline was removed app-wide (maturity pass); the
    // header is a plain noun (UX-QA voice rule 1) now followed by a live count
    // of the active sub-view (desktop count parity with Applications).
    renderPage()
    expect(
      (await screen.findAllByRole('heading', { name: /^saved\b/i })).length,
    ).toBeGreaterThan(0)
  })
})
