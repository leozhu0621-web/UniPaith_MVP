import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { MemoryRouter, Route, Routes } from 'react-router-dom'

import MatchHandoffCard from '../pages/student/discover/MatchHandoffCard'
import type { HandoffVerdict } from '../types'

const READY: HandoffVerdict = {
  should_handoff: true,
  handoff_target: 'recommendation',
  reason: 'enough signal',
  completion: { profile: 0.8, goals: 0.7, needs: 0.7 },
}
const NOT_READY: HandoffVerdict = {
  should_handoff: false,
  handoff_target: null,
  reason: 'keep going',
  completion: { profile: 0.2, goals: 0, needs: 0 },
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

describe('MatchHandoffCard', () => {
  it('offers the handoff when ready and navigates to Match', async () => {
    renderCard(<MatchHandoffCard verdict={READY} />)
    expect(screen.getByTestId('match-handoff-card')).toBeInTheDocument()
    fireEvent.click(screen.getByText(/See programs that fit me/i))
    expect(await screen.findByText('EXPLORE PAGE')).toBeInTheDocument()
  })

  it('renders nothing in auto variant when not ready', () => {
    const { container } = renderCard(<MatchHandoffCard verdict={NOT_READY} variant="auto" />)
    expect(container.querySelector('[data-testid="match-handoff-card"]')).toBeNull()
  })

  it('shows an honest confidence note in the always variant when not ready', () => {
    renderCard(<MatchHandoffCard verdict={NOT_READY} variant="always" />)
    expect(screen.getByText(/the more we talk, the sharper your matches get/i)).toBeInTheDocument()
  })

  it('lets the student keep talking', () => {
    const onKeepTalking = vi.fn()
    renderCard(<MatchHandoffCard verdict={READY} onKeepTalking={onKeepTalking} />)
    fireEvent.click(screen.getByText('Keep talking'))
    expect(onKeepTalking).toHaveBeenCalledOnce()
  })
})
