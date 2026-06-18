/**
 * Spec 09 — Program Match unit tests (presentational + API contracts).
 *
 * Covers the spec §12 checklist that's testable without a live backend:
 * DualRing renders both scores; band badges map correctly; probability bands
 * render honest ranges and the "not enough data yet" state; the new match
 * API clients are wired.
 */
import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import DualRing from '../pages/student/match/DualRing'
import ProbabilityBands from '../pages/student/match/ProbabilityBands'
import BandBadge from '../components/ui/BandBadge'
import * as matching from '../api/matching'
import type { ProbabilityBands as Bands } from '../types'

describe('DualRing', () => {
  it('renders both the fitness and confidence scores', () => {
    render(<DualRing fitness={0.82} confidence={0.74} />)
    expect(screen.getByText('Fitness · 82%')).toBeInTheDocument()
    expect(screen.getByText('Confidence · 74%')).toBeInTheDocument()
  })

  it('exposes both scores to assistive tech even in compact mode', () => {
    render(<DualRing fitness={0.5} confidence={0.3} compact onClick={() => {}} />)
    expect(
      screen.getByLabelText(/fitness 50%, confidence 30%/i),
    ).toBeInTheDocument()
  })
})

describe('BandBadge', () => {
  it('maps reach / target / safer to their labels', () => {
    const { rerender } = render(<BandBadge band="reach" />)
    expect(screen.getByText('Reach')).toBeInTheDocument()
    rerender(<BandBadge band="target" />)
    expect(screen.getByText('Target')).toBeInTheDocument()
    rerender(<BandBadge band="safer" />)
    expect(screen.getByText('Safer')).toBeInTheDocument()
  })
})

describe('ProbabilityBands (§4A)', () => {
  const bands: Bands = {
    admit: { low: 0.35, high: 0.5, label: 'target' },
    scholarship: { low: 0.15, high: 0.25 },
    waitlist: { approx: 0.1 },
    drivers: [
      { signal: 'Historical admit rate', direction: 'up' },
      { signal: 'High selectivity', direction: 'down' },
    ],
  }

  it('renders admit / scholarship / waitlist as ranges with drivers', () => {
    render(<ProbabilityBands bands={bands} />)
    expect(screen.getByText('Admit')).toBeInTheDocument()
    expect(screen.getByText('Scholarship')).toBeInTheDocument()
    expect(screen.getByText('Waitlist')).toBeInTheDocument()
    // A range, never a single point.
    expect(screen.getByText('35%–50%')).toBeInTheDocument()
    expect(screen.getByText('~10%')).toBeInTheDocument()
    expect(screen.getByText('Historical admit rate')).toBeInTheDocument()
  })

  // Discover review 2026-06-14 — the no-data copy now branches on `reason` so a
  // student can tell whose side the gap is on (program history vs own profile).
  it('explains a missing-program-history gap when reason=no_history', () => {
    render(<ProbabilityBands bands={null} reason="no_history" />)
    expect(screen.getByText(/no admissions history yet/i)).toBeInTheDocument()
  })

  it('explains a sparse-profile gap when reason=not_match_ready', () => {
    render(<ProbabilityBands bands={null} reason="not_match_ready" />)
    expect(screen.getByText(/add more to your profile/i)).toBeInTheDocument()
  })

  it('falls back to the generic line with no reason', () => {
    render(<ProbabilityBands bands={null} />)
    expect(screen.getByText(/Not enough data yet/i)).toBeInTheDocument()
  })
})

describe('match API clients', () => {
  it('exposes getMatches, refreshMatches, and getMatchProbability', () => {
    expect(typeof matching.getMatches).toBe('function')
    expect(typeof matching.refreshMatches).toBe('function')
    expect(typeof matching.getMatchProbability).toBe('function')
  })
})
