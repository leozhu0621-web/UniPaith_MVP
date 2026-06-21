import { describe, expect, it, vi, beforeEach } from 'vitest'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter, useLocation } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import StrategyTab from '../pages/student/profile/StrategyTab'
import type { StudentStrategy } from '../types'

vi.mock('../api/strategy', () => ({
  activateStrategy: vi.fn(),
  generateStrategy: vi.fn(),
  getActiveStrategy: vi.fn(),
  listStrategyVersions: vi.fn(),
  updateStrategy: vi.fn(),
}))

vi.mock('../api/applications', () => ({
  listMyApplications: vi.fn(),
}))

vi.mock('../api/saved-lists', () => ({
  listSaved: vi.fn(),
}))

vi.mock('../lib/analytics', () => ({
  track: vi.fn(),
}))

vi.mock('../stores/toast-store', () => ({
  showToast: vi.fn(),
}))

import { generateStrategy, getActiveStrategy, listStrategyVersions } from '../api/strategy'
import { listMyApplications } from '../api/applications'
import { listSaved } from '../api/saved-lists'
import { track } from '../lib/analytics'

function makeStrategy(overrides: Partial<StudentStrategy> = {}): StudentStrategy {
  return {
    id: 'strategy-1',
    student_id: 'student-1',
    version: 3,
    status: 'active',
    career_target: 'Computational social scientist',
    target_degree: 'PhD in Sociology',
    academic_path: [{ step: 'Finish advanced statistics', options: ['Bayesian modeling'], rationale: 'Needed for research fit.' }],
    financial_path: [],
    geographic_path: [{ region: 'US Northeast', rationale: 'Closest to research labs.', constraints: ['Cold weather'] }],
    narrative: 'Use social science research and quantitative methods to evaluate civic technology.',
    generated_at: '2025-01-10T12:00:00Z',
    generated_from_session_ids: ['session-a', 'session-b'],
    is_stub: false,
    created_at: '2025-01-10T12:00:00Z',
    updated_at: '2025-01-10T12:00:00Z',
    ...overrides,
  }
}

function LocationProbe() {
  const location = useLocation()
  return <output data-testid="location">{location.pathname + location.search}</output>
}

function renderStrategyTab(initialEntry = '/s/profile?tab=strategy') {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <MemoryRouter initialEntries={[initialEntry]}>
      <QueryClientProvider client={client}>
        <StrategyTab />
        <LocationProbe />
      </QueryClientProvider>
    </MemoryRouter>,
  )
}

describe('StrategyTab living document', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(listMyApplications).mockResolvedValue([])
    vi.mocked(listSaved).mockResolvedValue([])
    vi.mocked(generateStrategy).mockResolvedValue(makeStrategy({ id: 'draft-generated', status: 'draft' }))
  })

  it('surfaces stale strategy, evidence gaps, draft risk, and Uni handoff', async () => {
    const active = makeStrategy()
    vi.mocked(getActiveStrategy).mockResolvedValue(active)
    vi.mocked(listStrategyVersions).mockResolvedValue([
      makeStrategy({ id: 'draft-1', version: 4, status: 'draft' }),
      makeStrategy({ id: 'archived-1', version: 2, status: 'archived' }),
    ])

    renderStrategyTab()

    expect(await screen.findByRole('region', { name: /strategy living document/i })).toBeTruthy()
    expect(screen.getByText('Computational social scientist -> PhD in Sociology')).toBeTruthy()
    expect(screen.getByText('Review freshness')).toBeTruthy()
    expect(screen.getByText('5/6 anchors')).toBeTruthy()
    expect(screen.getByText('Financial path missing')).toBeTruthy()
    expect(screen.getByText('1 draft waiting')).toBeTruthy()
    expect(screen.getAllByText(/Generated from 2 discovery sessions/i).length).toBeGreaterThan(0)

    fireEvent.click(screen.getByRole('button', { name: /Develop with Uni/i }))

    await waitFor(() => {
      expect(screen.getByTestId('location').textContent).toBe(
        '/s?intent=strategy&source_task=strategy%3Arefine&return_to=%2Fs%2Fprofile%3Ftab%3Dstrategy&artifact_destination=strategy_draft',
      )
    })
    expect(track).toHaveBeenCalledWith('strategy_refine_clicked', expect.objectContaining({
      surface: 'profile_strategy',
      active_strategy_id: 'strategy-1',
    }))
    expect(track).toHaveBeenCalledWith('uni_chat_handoff_started', expect.objectContaining({
      intent: 'strategy',
      source_task: 'strategy:refine',
      artifact_destination: 'strategy_draft',
    }))
  })

  it('keeps the first-draft path actionable when no active strategy exists', async () => {
    vi.mocked(getActiveStrategy).mockResolvedValue(null)
    vi.mocked(listStrategyVersions).mockResolvedValue([])

    renderStrategyTab()

    expect(await screen.findByRole('heading', { name: 'No active strategy' })).toBeTruthy()
    expect(screen.getByText('0/6 anchors')).toBeTruthy()

    fireEvent.click(screen.getByRole('button', { name: /Generate first draft/i }))

    await waitFor(() => {
      expect(generateStrategy).toHaveBeenCalledTimes(1)
    })
  })
})
