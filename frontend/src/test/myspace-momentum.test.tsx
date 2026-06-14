import { describe, expect, it, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'

vi.mock('../api/students', () => ({ getOnboarding: vi.fn() }))
import { getOnboarding } from '../api/students'
import MomentumBand from '../pages/student/myspace/home/MomentumBand'

const onboarding = vi.mocked(getOnboarding)

function renderBand(props: React.ComponentProps<typeof MomentumBand>) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={qc}><MemoryRouter><MomentumBand {...props} /></MemoryRouter></QueryClientProvider>,
  )
}

const stage = { savedCount: 1, appCount: 0, hasDecision: false, hasOffer: false }
const week = { saved: [], runs: [], apps: [] }

describe('MomentumBand', () => {
  it('shows the setup ring + a next step while onboarding < 100%', async () => {
    onboarding.mockResolvedValue({ completion_percentage: 40, steps_completed: ['basic_profile'], next_step: null } as any)
    renderBand({ stage, week })
    expect(await screen.findByText('Set up your space')).toBeTruthy()
    expect(screen.getByText('Match')).toBeTruthy() // journey map still renders
  })
  it('hides the ring at 100% but still renders the journey map', async () => {
    onboarding.mockResolvedValue({ completion_percentage: 100, steps_completed: [], next_step: null } as any)
    renderBand({ stage, week })
    await waitFor(() => expect(screen.getByText('Match')).toBeTruthy())
    expect(screen.queryByText('Set up your space')).toBeNull()
  })
})
