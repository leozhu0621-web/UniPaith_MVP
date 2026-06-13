import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { MemoryRouter, Route, Routes } from 'react-router-dom'

vi.mock('../api/matching', () => ({
  getMatches: vi.fn().mockResolvedValue([
    {
      program_id: 'p1',
      program_name: 'Marine Biology, B.S.',
      institution_name: 'Univ. of Maine',
      fitness_score: '0.88',
      confidence_score: '0.8',
      rationale_text: 'Coastal field station + strong aid.',
      band_label: 'target',
      tuition: 18000,
      acceptance_rate: 0.7,
    },
    {
      program_id: 'p2',
      program_name: 'Marine Science, B.S.',
      institution_name: 'UNC Wilmington',
      fitness_score: '0.82',
      confidence_score: '0.6',
      rationale_text: 'Top program; aid likely.',
      band_label: 'reach',
    },
    {
      program_id: 'p3',
      program_name: 'Environmental Sci',
      institution_name: 'UNH',
      fitness_score: '0.79',
      confidence_score: '0.8',
      rationale_text: 'In-state aid, hands-on labs.',
      band_label: 'safer',
    },
    {
      program_id: 'p4',
      program_name: 'Should not show',
      institution_name: 'X',
      fitness_score: '0.7',
      confidence_score: '0.5',
      rationale_text: '',
      band_label: null,
    },
  ]),
}))

import FirstLookCard from '../pages/student/discover/FirstLookCard'
import type { HandoffVerdict } from '../types'

const READY: HandoffVerdict = {
  should_handoff: true,
  handoff_target: 'recommendation',
  reason: 'ok',
  completion: {},
}
const NOT_READY: HandoffVerdict = {
  should_handoff: false,
  handoff_target: null,
  reason: 'keep going',
  completion: {},
}

function renderCard(ui: React.ReactNode) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter initialEntries={['/s']}>
        <Routes>
          <Route path="/s" element={ui} />
          <Route path="/s/explore" element={<div>EXPLORE PAGE</div>} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

describe('FirstLookCard', () => {
  it('shows the top 3 matches and goes deeper to Match', async () => {
    renderCard(<FirstLookCard verdict={READY} />)
    expect(await screen.findByText(/Marine Biology, B\.S\./)).toBeInTheDocument()
    expect(screen.getByText(/Marine Science, B\.S\./)).toBeInTheDocument()
    expect(screen.getByText(/Environmental Sci/)).toBeInTheDocument()
    expect(screen.queryByText(/Should not show/)).not.toBeInTheDocument()
    // Grounded cost/selectivity line from the catalog.
    expect(screen.getByText(/\$18,000\/yr · 70% admit · target fit/)).toBeInTheDocument()
    fireEvent.click(screen.getByText(/Go deeper in Discover/i))
    expect(await screen.findByText('EXPLORE PAGE')).toBeInTheDocument()
  })

  it('renders nothing in auto variant when not ready', () => {
    const { container } = renderCard(<FirstLookCard verdict={NOT_READY} variant="auto" />)
    expect(container.querySelector('[data-testid="first-look-card"]')).toBeNull()
  })

  it('shows an honest look-anytime note in the always variant when not ready', () => {
    renderCard(<FirstLookCard verdict={NOT_READY} variant="always" />)
    expect(screen.getByText(/the more we talk, the sharper your matches get/i)).toBeInTheDocument()
  })

  it('lets the student keep talking', () => {
    const onKeepTalking = vi.fn()
    renderCard(<FirstLookCard verdict={READY} onKeepTalking={onKeepTalking} />)
    fireEvent.click(screen.getByText('Keep talking'))
    expect(onKeepTalking).toHaveBeenCalledOnce()
  })
})
