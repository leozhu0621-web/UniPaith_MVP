import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { MemoryRouter } from 'react-router-dom'

vi.mock('../api/livingProfile', () => ({
  getLivingProfile: vi
    .fn()
    .mockResolvedValue({ narrative: '', lightsUp: [], goals: [], needs: [], gaps: [] }),
  updateSignal: vi.fn(),
}))

import JourneyRail from '../pages/student/discover/JourneyRail'
import type { JourneyStage } from '../pages/student/discover/useJourneyState'

const STAGES: JourneyStage[] = [
  { key: 'profile', label: 'About you', state: 'done', pct: 0.8 },
  { key: 'goals', label: 'Your goals', state: 'current', pct: 0.2 },
  { key: 'needs', label: 'What you need', state: 'locked', pct: 0 },
]

function renderRail(props: Record<string, unknown> = {}) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter>
        <JourneyRail stages={STAGES} matchesUnlocked={false} {...props} />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

describe('JourneyRail', () => {
  it('renders the three stages + the matches item (locked)', () => {
    renderRail()
    expect(screen.getByText('About you')).toBeInTheDocument()
    expect(screen.getByText('Your goals')).toBeInTheDocument()
    expect(screen.getByText('What you need')).toBeInTheDocument()
    expect(screen.getByText('Your matches')).toBeInTheDocument()
    expect(screen.getByText('unlocks soon')).toBeInTheDocument()
  })

  it('revisits a done stage on click', () => {
    const onRevisit = vi.fn()
    renderRail({ onRevisit })
    fireEvent.click(screen.getByText('About you'))
    expect(onRevisit).toHaveBeenCalledWith('profile')
  })

  it('does not revisit a locked stage', () => {
    const onRevisit = vi.fn()
    renderRail({ onRevisit })
    fireEvent.click(screen.getByText('What you need'))
    expect(onRevisit).not.toHaveBeenCalled()
  })
})
