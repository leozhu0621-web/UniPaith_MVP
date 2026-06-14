import { describe, expect, it, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'

vi.mock('../api/strategy', () => ({ getActiveStrategy: vi.fn() }))
import { getActiveStrategy } from '../api/strategy'
import StrategySnapshot from '../pages/student/myspace/home/StrategySnapshot'

const strat = vi.mocked(getActiveStrategy)

function renderSnap() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(<QueryClientProvider client={qc}><MemoryRouter><StrategySnapshot /></MemoryRouter></QueryClientProvider>)
}

describe('StrategySnapshot', () => {
  it('shows the career → degree headline for an active strategy', async () => {
    strat.mockResolvedValue({ id: '1', career_target: 'Product Manager', target_degree: "Master's in HCI", narrative: 'Build toward PM via HCI.', is_stub: false } as any)
    renderSnap()
    expect(await screen.findByText(/Product Manager/)).toBeTruthy()
    expect(screen.getByText(/Refine/)).toBeTruthy()
  })
  it('shows the smart-empty CTA when there is no strategy', async () => {
    strat.mockResolvedValue(null)
    renderSnap()
    expect(await screen.findByText(/Shape your path with Uni/i)).toBeTruthy()
  })
  it('treats a stub as empty', async () => {
    strat.mockResolvedValue({ id: '1', career_target: 'x', is_stub: true } as any)
    renderSnap()
    expect(await screen.findByText(/Shape your path with Uni/i)).toBeTruthy()
  })
})
