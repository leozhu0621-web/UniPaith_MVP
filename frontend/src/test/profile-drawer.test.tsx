import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { MemoryRouter } from 'react-router-dom'

import ProfileDrawer from '../pages/student/discover/ProfileDrawer'
import * as livingProfile from '../api/livingProfile'
import type { LivingProfile } from '../api/livingProfile'

const PROFILE: LivingProfile = {
  narrative: 'You light up around hands-on problems and care about doing work that matters.',
  lightsUp: ['curiosity', 'building things'],
  goals: [{ kind: 'goal', id: 'g1', label: 'study marine biology', meta: 'academic' }],
  needs: [{ kind: 'need', id: 'n1', label: 'strong financial aid', meta: 'safety' }],
  gaps: [
    {
      key: 'identity',
      invitation: 'what matters most to you',
      prompt: "I'd like to talk about what matters most to me.",
    },
  ],
}

function renderDrawer(ui: React.ReactNode) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  // ProfileDrawer renders a <Link to="/s/profile"> (full-profile link), so it
  // needs a Router context — as it always has in the app.
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter>{ui}</MemoryRouter>
    </QueryClientProvider>,
  )
}

describe('ProfileDrawer', () => {
  beforeEach(() => vi.restoreAllMocks())

  it('shows the narrative, the three sections, and a gap invitation', async () => {
    vi.spyOn(livingProfile, 'getLivingProfile').mockResolvedValue(PROFILE)
    renderDrawer(<ProfileDrawer isOpen onClose={() => {}} />)

    expect(await screen.findByText(/You light up around hands-on problems/i)).toBeInTheDocument()
    expect(screen.getByText('What lights you up')).toBeInTheDocument()
    expect(screen.getByText("Where you're headed")).toBeInTheDocument()
    expect(screen.getByText('What you need to thrive')).toBeInTheDocument()
    expect(screen.getByText(/what matters most to you/i)).toBeInTheDocument()
  })

  it('accepting a gap invitation dispatches its prompt and closes', async () => {
    vi.spyOn(livingProfile, 'getLivingProfile').mockResolvedValue(PROFILE)
    const onAsk = vi.fn()
    const onClose = vi.fn()
    renderDrawer(<ProfileDrawer isOpen onClose={onClose} onAsk={onAsk} />)

    const invite = await screen.findByText(/what matters most to you/i)
    fireEvent.click(invite)
    expect(onAsk).toHaveBeenCalledWith("I'd like to talk about what matters most to me.")
    expect(onClose).toHaveBeenCalledOnce()
  })

  it('edits a goal chip inline via updateSignal', async () => {
    vi.spyOn(livingProfile, 'getLivingProfile').mockResolvedValue(PROFILE)
    const spy = vi.spyOn(livingProfile, 'updateSignal').mockResolvedValue({ id: 'g1' } as never)
    renderDrawer(<ProfileDrawer isOpen onClose={() => {}} />)

    fireEvent.click(await screen.findByLabelText('Tweak: study marine biology'))
    const input = screen.getByLabelText('Edit what Uni noticed') as HTMLInputElement
    fireEvent.change(input, { target: { value: 'study marine ecology' } })
    fireEvent.keyDown(input, { key: 'Enter' })

    await waitFor(() =>
      expect(spy).toHaveBeenCalledWith({ kind: 'goal', id: 'g1', value: 'study marine ecology' }),
    )
  })
})
