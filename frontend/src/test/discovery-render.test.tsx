import { describe, expect, it, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { MemoryRouter } from 'react-router-dom'

// Mock the network layer so DiscoverySearch mounts without a backend — this is
// a render smoke test (catches mount/hook crashes the unit tests can't see).
vi.mock('../api/search', () => ({
  interpretQuery: vi.fn().mockResolvedValue({ chips: [], interpretation: '', degraded: false }),
  searchProgramsTyped: vi
    .fn()
    .mockResolvedValue({ results: [], total: 0, page: 1, page_size: 24, total_pages: 1 }),
  getCompareSet: vi.fn().mockResolvedValue({ items: [], max: 4 }),
  addToCompare: vi.fn().mockResolvedValue({ items: [], max: 4 }),
  removeFromCompare: vi.fn().mockResolvedValue({ items: [], max: 4 }),
}))
vi.mock('../api/saved-lists', () => ({
  listSaved: vi.fn().mockResolvedValue([]),
  saveProgram: vi.fn().mockResolvedValue({}),
  unsaveProgram: vi.fn().mockResolvedValue({}),
}))

import DiscoverySearch from '../pages/student/explore/discovery/DiscoverySearch'

function renderDS() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter initialEntries={['/s/explore']}>
        <DiscoverySearch />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

describe('DiscoverySearch (render smoke)', () => {
  it('renders the search box and genre tiles in the empty state', () => {
    renderDS()
    expect(
      screen.getByPlaceholderText('What kind of program are you looking for?'),
    ).toBeInTheDocument()
    expect(screen.getByText('Or browse')).toBeInTheDocument()
    expect(screen.getByText('Computer Science')).toBeInTheDocument()
    // Empty state shows genre tiles, not a results count.
    expect(screen.queryByTestId('results-count')).not.toBeInTheDocument()
  })
})
