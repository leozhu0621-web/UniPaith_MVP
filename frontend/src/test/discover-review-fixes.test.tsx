// Discover review fixes (2026-06-14) — pin the data-honesty + dead-end fixes.
import { describe, it, expect, vi } from 'vitest'
import { render, screen, within } from '@testing-library/react'

vi.mock('@tanstack/react-query', () => ({ useQuery: () => ({ data: undefined }) }))

import ProbabilityBands from '../pages/student/match/ProbabilityBands'
import DiscoverTabBar, { DISCOVER_TABS } from '../pages/student/explore/DiscoverTabBar'
import { ringFromMatch, BAND_FILL } from '../pages/student/match/ringFill'

describe('ProbabilityBands no-data copy branches on reason', () => {
  it('distinguishes no admit history from a sparse profile', () => {
    const { rerender } = render(<ProbabilityBands bands={null} reason="no_history" />)
    expect(screen.getByText(/no admissions history yet/i)).toBeTruthy()
    rerender(<ProbabilityBands bands={null} reason="not_match_ready" />)
    expect(screen.getByText(/add more to your profile/i)).toBeTruthy()
    rerender(<ProbabilityBands bands={null} />)
    expect(screen.getByText(/not enough data yet/i)).toBeTruthy()
  })
})

describe('ringFromMatch (shared band-only ring)', () => {
  it('uses a raw score when present (numeral shown)', () => {
    expect(ringFromMatch(0.7, 'reach')).toEqual({ value: 0.7, fromBand: false })
  })
  it('falls back to the band fill when no raw score (numeral hidden)', () => {
    expect(ringFromMatch(null, 'target')).toEqual({ value: BAND_FILL.target, fromBand: true })
  })
  it('never fabricates a number when neither is present', () => {
    expect(ringFromMatch(null, null)).toEqual({ value: 0, fromBand: true })
  })
})

// Discover restructure (2026-06-14): For you · Academic · Financial · International;
// Peers dropped, Resources dissolved (Financial/International promoted to top tabs).
describe('DiscoverTabBar restructured tabs', () => {
  it('renders the four tabs in order, no Peers/Resources', () => {
    render(<DiscoverTabBar tab="foryou" onChange={() => {}} />)
    const list = screen.getByRole('tablist', { name: 'Discover sections' })
    const labels = within(list).getAllByRole('tab').map(t => (t.textContent ?? '').trim())
    expect(labels).toEqual(['For you', 'Academic', 'Financial', 'International'])
    expect(within(list).queryByText('Peers')).toBeNull()
    expect(within(list).queryByText('Resources')).toBeNull()
  })
  it('has the canonical top-tab list', () => {
    expect(DISCOVER_TABS).toEqual(['foryou', 'academic', 'financial', 'international'])
  })
})
