/**
 * Discover For-you — strategy→matches bridge line (MatchesSection).
 *
 * The bridge names the honest relationship — matches are banded off the
 * strategy, not numerically ranked in the student view — and surfaces
 * "Refine priorities" at the seam. It only appears with an active strategy
 * AND matches present.
 */
import { render, screen, waitFor } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import { MemoryRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'

vi.mock('../api/matching', () => ({ getMatches: vi.fn(), refreshMatches: vi.fn() }))
import { getMatches } from '../api/matching'
import MatchesSection from '../pages/student/match/MatchesSection'

const matches = vi.mocked(getMatches)

function renderSection(strategyActive: boolean) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter>
        <MatchesSection savedIds={new Set()} onToggleSave={() => {}} strategyActive={strategyActive} />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

const sample = [
  { program_id: 'p1', program_name: 'MS CS', institution_name: 'MIT', fitness_score: '0.82', band_label: 'reach' },
] as any

describe('MatchesSection strategy bridge', () => {
  it('shows the bridge line with an active strategy and matches present', async () => {
    matches.mockResolvedValue(sample)
    renderSection(true)
    expect(await screen.findByText(/These matches reflect your strategy/i)).toBeTruthy()
    // The Refine priorities control is surfaced at the seam.
    expect(screen.getAllByRole('button', { name: /Refine priorities/i }).length).toBeGreaterThan(0)
  })

  it('hides the bridge line when there is no active strategy', async () => {
    matches.mockResolvedValue(sample)
    renderSection(false)
    expect(await screen.findByText('MS CS')).toBeTruthy()
    expect(screen.queryByText(/These matches reflect your strategy/i)).toBeNull()
  })

  it('hides the bridge line when there are no matches', async () => {
    matches.mockResolvedValue([])
    renderSection(true)
    await waitFor(() => expect(screen.getByText(/No matches yet/i)).toBeTruthy())
    expect(screen.queryByText(/These matches reflect your strategy/i)).toBeNull()
  })
})
