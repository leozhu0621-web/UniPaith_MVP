// Scholarships UI (Spec 2026-06-14) — real CareerOneStop data in Resources ›
// Financial. Verifies the matched list renders, a card shows real verbatim
// amount + an apply link, and searching swaps to the search query.
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'

vi.mock('../api/scholarships', () => ({
  searchScholarships: vi.fn(),
  getScholarshipMatches: vi.fn(),
}))
import { searchScholarships, getScholarshipMatches } from '../api/scholarships'
import ScholarshipsBlock from '../pages/student/explore/resources/ScholarshipsBlock'

const sample = (over = {}) => ({
  id: 'u1',
  external_id: '9999696',
  name: 'AACT Research Award',
  organization: 'American Academy of Clinical Toxicology',
  purpose: 'To fund clinical research.',
  level_of_study: "Bachelor's Degree",
  award_type: 'Grant',
  award_amount: '$1,000 $5,000',
  deadline: 'November',
  url: 'https://www.careeronestop.org/x?scholarshipId=9999696',
  source: 'careeronestop_scholarship_finder',
  ...over,
})

function renderBlock() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(<QueryClientProvider client={qc}><ScholarshipsBlock /></QueryClientProvider>)
}

beforeEach(() => {
  vi.mocked(getScholarshipMatches).mockResolvedValue([sample()] as never)
  vi.mocked(searchScholarships).mockResolvedValue({ items: [sample({ id: 's1', name: 'Engineering Merit Award' })], total: 1, page: 1 } as never)
})

describe('ScholarshipsBlock', () => {
  it('shows the matched list with real verbatim amount + an apply link', async () => {
    renderBlock()
    expect(await screen.findByText('AACT Research Award')).toBeTruthy()
    expect(screen.getByText('$1,000 $5,000')).toBeTruthy() // verbatim, unparsed
    const apply = screen.getByRole('link', { name: /apply \/ details/i })
    expect(apply.getAttribute('href')).toContain('scholarshipId=9999696')
    expect(apply.getAttribute('target')).toBe('_blank')
  })

  it('switches to search results when a query is submitted', async () => {
    renderBlock()
    await screen.findByText('AACT Research Award')
    fireEvent.change(screen.getByLabelText('Search scholarships'), { target: { value: 'engineering' } })
    fireEvent.click(screen.getByRole('button', { name: 'Search' }))
    await waitFor(() => expect(screen.getByText('Engineering Merit Award')).toBeTruthy())
    expect(searchScholarships).toHaveBeenCalledWith(expect.objectContaining({ q: 'engineering' }))
  })
})
