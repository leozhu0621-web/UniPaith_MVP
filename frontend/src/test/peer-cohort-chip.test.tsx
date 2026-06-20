// Discover review 2026-06-14 #5 — privacy-safe peer-cohort chip.
// The chip renders only when a k-anonymized count is present (the backend has
// already suppressed anything below the floor), and clicking it opens Peers.
import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import MatchCard from '../pages/student/match/MatchCard'
import type { MatchResultDual } from '../types'

const baseMatch = {
  program_id: 'p1',
  program_name: 'CS Masters',
  institution_name: 'Foo University',
  band_label: 'target',
} as unknown as MatchResultDual

function renderCard(extra: Partial<React.ComponentProps<typeof MatchCard>>) {
  return render(
    <MemoryRouter>
      <MatchCard
        match={baseMatch}
        saved={false}
        comparing={false}
        onSave={() => {}}
        onCompare={() => {}}
        onView={() => {}}
        {...extra}
      />
    </MemoryRouter>,
  )
}

describe('MatchCard peer-cohort chip', () => {
  it('shows "N open to connect" and fires onPeersClick', () => {
    const onPeersClick = vi.fn()
    renderCard({ peerCount: 4, onPeersClick })
    const chip = screen.getByRole('button', { name: /open to connect/i })
    expect(chip.textContent).toContain('4')
    fireEvent.click(chip)
    expect(onPeersClick).toHaveBeenCalledOnce()
  })

  it('renders no chip when there is no count (suppressed / not opted in)', () => {
    renderCard({ peerCount: undefined })
    expect(screen.queryByText(/open to connect/i)).toBeNull()
  })

  it('renders no chip for a zero count', () => {
    renderCard({ peerCount: 0 })
    expect(screen.queryByText(/open to connect/i)).toBeNull()
  })
})
