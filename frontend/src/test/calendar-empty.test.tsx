import { describe, expect, it, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'

vi.mock('../api/calendar', () => ({
  getCalendar: vi.fn(),
  createReminder: vi.fn(),
  createWorkBlock: vi.fn(),
  patchCalendarItem: vi.fn(),
}))
vi.mock('../api/interviews', () => ({ getMyInterviews: vi.fn(), declineInterview: vi.fn() }))

import { getCalendar } from '../api/calendar'
import { getMyInterviews } from '../api/interviews'
import CalendarPage from '../pages/student/CalendarPage'

beforeEach(() => {
  vi.mocked(getMyInterviews).mockResolvedValue([])
  // jsdom has no matchMedia; CalendarPage reads it for its mobile default view.
  if (!window.matchMedia) {
    window.matchMedia = vi.fn().mockReturnValue({
      matches: false, addEventListener: vi.fn(), removeEventListener: vi.fn(),
      addListener: vi.fn(), removeListener: vi.fn(), onchange: null, media: '', dispatchEvent: vi.fn(),
    }) as unknown as typeof window.matchMedia
  }
})

function renderCal() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(<QueryClientProvider client={qc}><MemoryRouter><CalendarPage /></MemoryRouter></QueryClientProvider>)
}

describe('CalendarPage empty state', () => {
  it('shows a smart empty state with an Add-a-reminder CTA when the timeline is empty', async () => {
    vi.mocked(getCalendar).mockResolvedValue([])
    renderCal()
    expect(await screen.findByText('Your calendar is clear')).toBeTruthy()
    expect(screen.getByText('Add a reminder')).toBeTruthy()
  })
})
