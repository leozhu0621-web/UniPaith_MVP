import { describe, expect, it, vi, beforeEach } from 'vitest'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'

vi.mock('../api/applications', () => ({ listMyApplications: vi.fn() }))
vi.mock('../api/calendar', () => ({ getCalendar: vi.fn() }))
vi.mock('../api/saved-lists', () => ({ listSaved: vi.fn() }))
vi.mock('../api/recommendations', () => ({ listRecommendations: vi.fn(), sendRecommendationRequest: vi.fn() }))
vi.mock('../api/workshops-feedback', () => ({ listWorkshopRuns: vi.fn() }))
vi.mock('../api/inbox', () => ({ getThreads: vi.fn() }))
vi.mock('../api/intake', () => ({ listClarifications: vi.fn() }))
vi.mock('../api/students', () => ({ getProfile: vi.fn(), getOnboarding: vi.fn() }))
vi.mock('../api/strategy', () => ({ getActiveStrategy: vi.fn() }))

import { listMyApplications } from '../api/applications'
import { getCalendar } from '../api/calendar'
import { listSaved } from '../api/saved-lists'
import { listRecommendations, sendRecommendationRequest } from '../api/recommendations'
import { listWorkshopRuns } from '../api/workshops-feedback'
import { getThreads } from '../api/inbox'
import { listClarifications } from '../api/intake'
import { getProfile, getOnboarding } from '../api/students'
import { getActiveStrategy } from '../api/strategy'
import MySpaceHomePage from '../pages/student/myspace/MySpaceHomePage'

beforeEach(() => {
  vi.mocked(listMyApplications).mockResolvedValue([{ id: 'a1', status: 'draft', readiness_pct: 60, program: { program_name: 'CS' } }] as any)
  vi.mocked(getCalendar).mockResolvedValue([])
  vi.mocked(listSaved).mockResolvedValue([{ program_id: 'p1', added_at: new Date().toISOString() }] as any)
  vi.mocked(listRecommendations).mockResolvedValue([])
  vi.mocked(listWorkshopRuns).mockResolvedValue([])
  vi.mocked(getThreads).mockResolvedValue([])
  vi.mocked(listClarifications).mockResolvedValue({ clarifications: [] } as any)
  vi.mocked(getProfile).mockResolvedValue({ first_name: 'Ada' } as any)
  vi.mocked(getOnboarding).mockResolvedValue({ completion_percentage: 50, steps_completed: [], next_step: null } as any)
  vi.mocked(getActiveStrategy).mockResolvedValue(null)
})

function renderHome() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(<QueryClientProvider client={qc}><MemoryRouter><MySpaceHomePage /></MemoryRouter></QueryClientProvider>)
}

describe('MySpaceHomePage', () => {
  it('renders the greeting, momentum band, pipeline and focus without crashing', async () => {
    renderHome()
    expect(await screen.findByText(/Good (morning|afternoon|evening), Ada/)).toBeTruthy()
    await waitFor(() => expect(screen.getByText('Match')).toBeTruthy()) // journey map
    expect(screen.getByText("Today's focus")).toBeTruthy() // a draft → focus
    expect(screen.getByText('Saved')).toBeTruthy() // pipeline tile
  })

  it('nudges a waiting recommender from the dashboard', async () => {
    vi.mocked(listRecommendations).mockResolvedValue([
      { id: 'r1', recommender_name: 'Dr. Lee', status: 'requested' },
    ] as any)
    vi.mocked(sendRecommendationRequest).mockResolvedValue({} as any)
    renderHome()
    const nudge = await screen.findByRole('button', { name: /Nudge/ })
    fireEvent.click(nudge)
    await waitFor(() => expect(sendRecommendationRequest).toHaveBeenCalledWith('r1'))
  })
})
