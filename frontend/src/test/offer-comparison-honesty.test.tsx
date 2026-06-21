// Offer comparison data-honesty (Applications review 2026-06-21 #7). The backend
// returns the student's must-haves as a FLAT list with no per-offer satisfaction
// data, so the table must NOT claim a per-offer "Likely met" verdict inferred
// from a fitness score. It shows the honest "Your must-haves" list instead.
import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'

const { COMPARISON } = vi.hoisted(() => ({
  COMPARISON: {
    offers: [
      {
        application_id: 'a1', offer_id: 'o1', program_name: 'MS Computer Science',
        institution_name: 'University A', degree_type: 'masters', decision_state: 'admitted',
        cost: { tuition: 50000, scholarship: 10000, currency: 'USD', net_cost: 40000 },
        fit: { fitness: 0.82, confidence: 0.7 }, // would have shown a fabricated "✓ Likely met"
        outcomes: { median_salary: 90000, placement_rate: 0.9 }, location: 'CA',
        response_deadline: null, conditions: null,
      },
      {
        application_id: 'a2', offer_id: 'o2', program_name: 'MS Data Science',
        institution_name: 'University B', degree_type: 'masters', decision_state: 'admitted',
        cost: { tuition: 60000, scholarship: 0, currency: 'USD', net_cost: 60000 },
        fit: { fitness: 0.3, confidence: 0.5 }, // would have shown "Review below"
        outcomes: { median_salary: 70000, placement_rate: 0.7 }, location: 'NY',
        response_deadline: null, conditions: null,
      },
    ],
    indicators: { best_value: 'o1', best_fit: 'o1', most_affordable: 'o1' },
    must_have_constraints: [{ need: 'Funding', signal: 'strong_preference' }],
    count: 2,
  },
}))

vi.mock('../api/offers', () => ({
  getOffersComparison: vi.fn().mockResolvedValue(COMPARISON),
}))

import OfferComparisonTable from '../pages/student/apply/offer/OfferComparisonTable'

function renderTable() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter>
        <OfferComparisonTable />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

describe('OfferComparisonTable — must-haves honesty', () => {
  it('does not fabricate a per-offer "must-haves met" verdict', async () => {
    renderTable()
    // Wait for the data to render.
    await screen.findByText('University A')
    // The fabricated per-offer verdicts must be gone.
    expect(screen.queryByText(/Likely met/i)).not.toBeInTheDocument()
    expect(screen.queryByText(/Review below/i)).not.toBeInTheDocument()
    // The honest flat list of the student's needs stays.
    expect(screen.getByText('Your must-haves')).toBeInTheDocument()
    expect(screen.getByText(/Funding/)).toBeInTheDocument()
  })
})
