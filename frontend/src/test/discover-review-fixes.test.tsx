// Discover review fixes (2026-06-14) — pin the data-honesty + dead-end fixes.
import { describe, it, expect, vi } from 'vitest'
import { render, screen, within } from '@testing-library/react'

vi.mock('@tanstack/react-query', () => ({ useQuery: () => ({ data: undefined }) }))

import ProbabilityBands from '../pages/student/match/ProbabilityBands'
import DiscoverTabBar from '../pages/student/explore/DiscoverTabBar'
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

describe('DiscoverTabBar hides Peers when its flag is off', () => {
  const renderBar = (peersEnabled: boolean) =>
    render(
      <DiscoverTabBar tab="foryou" onChange={() => {}} onManageFollowing={() => {}} peersEnabled={peersEnabled} />,
    )

  it('shows Peers when enabled', () => {
    renderBar(true)
    const list = screen.getByRole('tablist', { name: 'Discover sections' })
    expect(within(list).getByText('Peers')).toBeTruthy()
  })
  it('omits Peers when disabled (no dead-end tab)', () => {
    renderBar(false)
    const list = screen.getByRole('tablist', { name: 'Discover sections' })
    expect(within(list).queryByText('Peers')).toBeNull()
    expect(within(list).getByText('For you')).toBeTruthy()
  })
})
