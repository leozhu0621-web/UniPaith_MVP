/**
 * Text→interactive pass · ApplicationsPage rows.
 * Each row carries ONE inline action button derived from its bucket/offer
 * state, and clicking it routes to the owned destination without bubbling the
 * whole-row navigate. Inform-only states (under review, decided-no-offer) keep
 * the prose "Next:" line and no action button.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import type { ReactElement } from 'react'
import { MemoryRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import type { Application } from '../types'

const nav = vi.fn()
vi.mock('react-router-dom', async (orig) => ({
  ...(await orig() as object),
  useNavigate: () => nav,
}))

const listMyApplications = vi.fn()
vi.mock('../api/applications', () => ({
  listMyApplications: () => listMyApplications(),
}))

// Costs & aid tab is lazy-imported by the page; stub it so the module graph
// resolves without pulling its own data deps into this list-focused test.
vi.mock('../pages/student/myspace/applications/CostsAidTab', () => ({
  default: () => null,
}))

import ApplicationsPage from '../pages/student/ApplicationsPage'

const baseApp = (overrides: Partial<Application> = {}): Application =>
  ({
    id: 'app-1',
    student_id: 's1',
    program_id: 'p1',
    status: 'draft',
    match_score: 0.8,
    match_reasoning_text: null,
    submitted_at: null,
    decision: null,
    decision_at: null,
    decision_notes: null,
    completeness_status: null,
    missing_items: null,
    submission_mode: 'internal',
    readiness_pct: 0,
    intent_picker: null,
    intent_rationale: null,
    fit_band: 'medium',
    guardrail_blockers: null,
    offer: null,
    student_decision: null,
    decision_state: null,
    created_at: '2026-01-01',
    updated_at: '2026-01-01',
    program: {
      id: 'p1',
      program_name: 'MS Computer Science',
      institution_name: 'University of Foo',
      degree_type: 'masters',
    } as Application['program'],
    ...overrides,
  }) as Application

function wrap(ui: ReactElement) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <MemoryRouter>
      <QueryClientProvider client={client}>{ui}</QueryClientProvider>
    </MemoryRouter>,
  )
}

async function renderWith(apps: Application[]) {
  listMyApplications.mockResolvedValue(apps)
  wrap(<ApplicationsPage />)
  // The list title appears once data resolves.
  await screen.findAllByText('MS Computer Science')
}

describe('ApplicationsPage row action', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    nav.mockReset()
  })

  it('a fresh draft shows "Start" routing to the checklist tab', async () => {
    await renderWith([baseApp({ readiness_pct: 0 })])
    const btn = screen.getByRole('button', { name: 'Start' })
    fireEvent.click(btn)
    expect(nav).toHaveBeenCalledWith('/s/applications/app-1?tab=checklist')
  })

  it('a partly-done draft shows "Resume"', async () => {
    await renderWith([baseApp({ readiness_pct: 60 })])
    const btn = screen.getByRole('button', { name: 'Resume' })
    fireEvent.click(btn)
    expect(nav).toHaveBeenCalledWith('/s/applications/app-1?tab=checklist')
  })

  it('a 100%-ready draft shows "Submit" routing to the checklist tab', async () => {
    await renderWith([baseApp({ readiness_pct: 100 })])
    const btn = screen.getByRole('button', { name: 'Submit' })
    fireEvent.click(btn)
    expect(nav).toHaveBeenCalledWith('/s/applications/app-1?tab=checklist')
  })

  it('an admitted application with an offer shows "View offer" (inform + view)', async () => {
    await renderWith([
      baseApp({
        status: 'decision_made',
        decision: 'admitted',
        readiness_pct: 100,
        offer: {
          id: 'o1',
          application_id: 'app-1',
          offer_type: 'full_admission',
          tuition_amount: 48000,
          scholarship_amount: 0,
          financial_package_total: null,
          conditions: null,
          response_deadline: '2027-04-15',
          status: 'sent',
          student_response: null,
          response_at: null,
        } as Application['offer'],
      }),
    ])
    const btn = screen.getByRole('button', { name: 'View offer' })
    fireEvent.click(btn)
    expect(nav).toHaveBeenCalledWith('/s/applications/app-1?tab=offer')
    // Inform-only: no accept/decline control lives on the list row.
    expect(screen.queryByRole('button', { name: /Accept/i })).toBeNull()
    expect(screen.queryByRole('button', { name: /Decline/i })).toBeNull()
  })

  it('an under-review application keeps the prose next step and no action button', async () => {
    await renderWith([baseApp({ status: 'under_review', readiness_pct: 100 })])
    expect(screen.getByText(/Next: Under review/i)).toBeTruthy()
    expect(screen.queryByRole('button', { name: 'Submit' })).toBeNull()
    expect(screen.queryByRole('button', { name: 'Resume' })).toBeNull()
  })
})
