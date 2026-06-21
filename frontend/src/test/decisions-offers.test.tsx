/**
 * Spec 18 · Decisions & Offers — UI smoke for offer panel + comparison table.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import type { ReactElement } from 'react'
import { MemoryRouter, useLocation } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import OfferPanel from '../pages/student/apply/offer/OfferPanel'
import DecisionComparison from '../pages/student/apply/offer/DecisionComparison'
import ApplicationsPage from '../pages/student/ApplicationsPage'
import type { Application } from '../types'

vi.mock('../api/offers', () => ({
  getOffersComparison: vi.fn().mockResolvedValue({
    count: 2,
    offers: [
      {
        application_id: 'a1',
        offer_id: 'o1',
        program_name: 'MS CS',
        institution_name: 'Foo U',
        decision_state: 'accepted',
        cost: { tuition: 48000, scholarship: 20000, net_cost: 76000, currency: 'USD' },
        fit: { fitness: 0.82, confidence: 0.71 },
        outcomes: { median_salary: 120000, placement_rate: 0.92 },
        location: 'Boston, US',
        response_deadline: '2027-04-15',
      },
      {
        application_id: 'a2',
        offer_id: 'o2',
        program_name: 'MS DS',
        institution_name: 'Foo U',
        decision_state: 'accepted',
        cost: { tuition: 40000, scholarship: 0, net_cost: 80000, currency: 'USD' },
        fit: { fitness: 0.75, confidence: 0.65 },
        outcomes: { median_salary: 110000, placement_rate: 0.88 },
        location: 'Boston, US',
        response_deadline: '2027-05-01',
      },
    ],
    indicators: { most_affordable: 'a1', best_fit: 'a1', best_value: 'a1' },
    must_have_constraints: [{ need: 'location', signal: 'East Coast' }],
    advisor_summary: 'MS CS has the lowest net cost ($76,000). MS CS scores highest on fit (82%).',
  }),
  respondToOfferV2: vi.fn(),
  recordExternalOffer: vi.fn(),
}))

vi.mock('../api/applications', () => ({
  listMyApplications: vi.fn(),
}))

import { listMyApplications } from '../api/applications'

const baseApp = (overrides: Partial<Application> = {}): Application =>
  ({
    id: 'app-1',
    student_id: 's1',
    program_id: 'p1',
    status: 'decision_made',
    match_score: 0.8,
    match_reasoning_text: null,
    submitted_at: '2026-01-01',
    decision: 'admitted',
    decision_at: '2026-03-01',
    decision_notes: null,
    completeness_status: 'complete',
    missing_items: null,
    submission_mode: 'external',
    readiness_pct: 100,
    intent_picker: null,
    intent_rationale: null,
    fit_band: 'high',
    guardrail_blockers: null,
    offer: null,
    student_decision: null,
    decision_state: 'accepted',
    created_at: '2026-01-01',
    updated_at: '2026-03-01',
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

function LocationProbe() {
  const location = useLocation()
  return <output data-testid="location">{location.pathname + location.search}</output>
}

function wrapAt(ui: ReactElement, initialEntry: string) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <MemoryRouter initialEntries={[initialEntry]}>
      <QueryClientProvider client={client}>
        {ui}
        <LocationProbe />
      </QueryClientProvider>
    </MemoryRouter>,
  )
}

describe('Spec 18 · OfferPanel', () => {
  beforeEach(() => vi.clearAllMocks())

  it('shows the waiting copy when no offer exists', () => {
    wrap(<OfferPanel application={baseApp({ status: 'submitted', decision: null })} />)
    expect(screen.getByText(/Decisions usually arrive within 4–8 weeks/i)).toBeTruthy()
    expect(screen.getByRole('button', { name: /Record an offer/i })).toBeTruthy()
  })

  it('renders spec copy and CTAs when an offer is present', () => {
    wrap(
      <OfferPanel
        application={baseApp({
          offer: {
            id: 'o1',
            application_id: 'app-1',
            offer_type: 'full_admission',
            tuition_amount: 48000,
            scholarship_amount: 20000,
            financial_package_total: null,
            conditions: null,
            response_deadline: '2027-04-15',
            status: 'sent',
            student_response: null,
            response_at: null,
            brief: 'Foo offered you their CS MS with a $20k merit scholarship.',
            plain_language_brief: {
              summary: 'Foo offered you their CS MS with a $20k merit scholarship.',
              key_terms: [{ label: 'Scholarship', value: '$20,000' }],
              deadlines: [],
              next_steps: [{ action: 'Confirm decision', by_date: '2027-04-15' }],
            },
          },
        })}
      />,
    )
    expect(screen.getByText(/Offer from University of Foo/i)).toBeTruthy()
    expect(screen.getByRole('button', { name: 'Accept offer' })).toBeTruthy()
    expect(screen.getByRole('button', { name: 'Decline offer' })).toBeTruthy()
    expect(screen.getByText(/Compare with my other offers/i)).toBeTruthy()
  })

  it('opens the external-offer recorder from the deep link', async () => {
    wrapAt(
      <OfferPanel application={baseApp({ status: 'submitted', decision: null, offer: null })} />,
      '/s/applications/app-1?tab=offer&recordOffer=1',
    )

    expect(await screen.findByText('Record an offer you received')).toBeTruthy()
  })
})

describe('Spec 18 · DecisionComparison', () => {
  it('renders comparison dimensions from the API', async () => {
    wrap(<DecisionComparison isOpen onClose={() => {}} />)
    expect(await screen.findByText('Compare your offers')).toBeTruthy()
    expect(await screen.findByText('Net cost')).toBeTruthy()
    expect(await screen.findByText('Fitness')).toBeTruthy()
    expect(await screen.findByText('Most affordable')).toBeTruthy()
    expect(await screen.findByText(/lowest net cost/i)).toBeTruthy()
    expect(await screen.findByText(/Your must-haves/i)).toBeTruthy()
  })
})

describe('Spec 18 · Applications offers view', () => {
  beforeEach(() => vi.clearAllMocks())

  const offer = {
    id: 'o1',
    application_id: 'a1',
    offer_type: 'full_admission',
    tuition_amount: 48000,
    scholarship_amount: 20000,
    financial_package_total: null,
    conditions: null,
    response_deadline: '2027-04-15',
    status: 'sent',
    student_response: null,
    response_at: null,
    brief: null,
    plain_language_brief: null,
  }

  it('promotes comparison and external-offer entry from the Offers room', async () => {
    vi.mocked(listMyApplications).mockResolvedValue([
      baseApp({ id: 'a1', offer: { ...offer, application_id: 'a1' } }),
      baseApp({
        id: 'a2',
        program_id: 'p2',
        program: { id: 'p2', program_name: 'MS Data Science', institution_name: 'University of Bar', degree_type: 'masters' } as Application['program'],
        offer: { ...offer, id: 'o2', application_id: 'a2', response_deadline: '2027-05-01' },
      }),
      baseApp({
        id: 'a3',
        program_id: 'p3',
        status: 'submitted',
        decision: null,
        decision_state: 'pending',
        offer: null,
        submission_mode: 'external',
        program: { id: 'p3', program_name: 'MEng Robotics', institution_name: 'University of Baz', degree_type: 'masters' } as Application['program'],
      }),
    ])

    wrapAt(<ApplicationsPage />, '/s/applications?tab=offers')

    expect(await screen.findByText('Offer decision center')).toBeTruthy()
    expect(screen.getByText('Compare cost, fit, terms, and response deadlines before deciding')).toBeTruthy()
    expect(screen.getByRole('button', { name: /Compare offers/i })).toBeTruthy()
    expect(screen.getByRole('button', { name: /Record external offer/i })).toBeTruthy()

    fireEvent.click(screen.getByRole('button', { name: /Compare offers/i }))
    expect(await screen.findByText('Compare your offers')).toBeTruthy()
  })

  it('routes external-offer entry to the chosen application Offer tab', async () => {
    vi.mocked(listMyApplications).mockResolvedValue([
      baseApp({ id: 'a1', offer: { ...offer, application_id: 'a1' } }),
      baseApp({
        id: 'a3',
        program_id: 'p3',
        status: 'submitted',
        decision: null,
        decision_state: 'pending',
        offer: null,
        submission_mode: 'external',
        program: { id: 'p3', program_name: 'MEng Robotics', institution_name: 'University of Baz', degree_type: 'masters' } as Application['program'],
      }),
    ])

    wrapAt(<ApplicationsPage />, '/s/applications?tab=offers')

    await screen.findByText('Offer decision center')
    fireEvent.click(screen.getByRole('button', { name: /Record external offer/i }))

    await waitFor(() => {
      expect(screen.getByTestId('location').textContent).toBe('/s/applications/a3?tab=offer&recordOffer=1')
    })
  })
})
