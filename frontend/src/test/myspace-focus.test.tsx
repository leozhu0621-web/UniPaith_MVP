import { describe, expect, it, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import TodaysFocus from '../pages/student/myspace/home/TodaysFocus'
import { AlertTriangle } from 'lucide-react'

const nav = vi.fn()
vi.mock('react-router-dom', async (orig) => ({ ...(await orig() as object), useNavigate: () => nav }))

describe('TodaysFocus', () => {
  it('renders the top action and navigates on click', () => {
    render(
      <MemoryRouter>
        <TodaysFocus action={{ key: 'k', icon: AlertTriangle, title: 'Respond to your offer', sub: 'MIT', urgency: 'warning', chip: 'offer in', to: '/s/applications/1?tab=offer' }} onboardingComplete={false} />
      </MemoryRouter>,
    )
    expect(screen.getByText('Respond to your offer')).toBeTruthy()
    // Two navigable targets (title + "Go: …"); click the title by exact name.
    fireEvent.click(screen.getByRole('button', { name: 'Respond to your offer' }))
    expect(nav).toHaveBeenCalledWith('/s/applications/1?tab=offer')
  })

  it('shows the caught-up state with a setup CTA when no action and onboarding incomplete', () => {
    render(<MemoryRouter><TodaysFocus action={null} onboardingComplete={false} /></MemoryRouter>)
    expect(screen.getByText(/caught up/i)).toBeTruthy()
    expect(screen.getByText(/Keep building your profile/i)).toBeTruthy()
  })

  it('caught-up CTA points to Uni when onboarding is complete', () => {
    render(<MemoryRouter><TodaysFocus action={null} onboardingComplete /></MemoryRouter>)
    expect(screen.getByText(/Talk to Uni/i)).toBeTruthy()
  })
})
