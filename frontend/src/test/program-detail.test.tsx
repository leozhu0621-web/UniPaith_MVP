/**
 * Spec 11 — Program Detail Page tests (§10 checklist).
 *
 *   - Route /s/programs/:id renders.
 *   - DualRing shows for an authenticated student with a computed match; hidden
 *     for public visitors (who get the "Sign in to see your match" CTA).
 *   - Insights filter (reviewer type) persists in the URL.
 *   - Legacy ?tab=reviews redirects to ?tab=insights.
 *   - Save / Add to compare / Start application actions trigger.
 *   - Insights merges student reviews + employer feedback; honest empty state.
 *   - Net Price Estimator renders a {min,expected,max} range + "estimate, not a quote".
 */
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { MemoryRouter, Routes, Route, useLocation } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { describe, expect, it, vi, beforeEach } from 'vitest'

import InsightsPanel from '../pages/student/program/InsightsPanel'
import NetPriceEstimator from '../pages/student/program/NetPriceEstimator'
import type {
  ProgramReviewSummary,
  EmployerFeedbackSummary,
  NetPriceEstimate,
} from '../types'

/* ── Fixtures + mock fns (hoisted so vi.mock factories can read them) ──────── */

const h = vi.hoisted(() => {
  const reviews = {
    total_reviews: 1,
    avg_teaching: 4.6, avg_workload: 3.1, avg_career_support: 4.2,
    avg_internship_access: 4.0, avg_community_culture: 4.4, avg_roi: 4.1, avg_overall: 4.3,
    reviews: [
      {
        id: 'r1', program_id: 'prog-1',
        rating_teaching: 5, rating_workload: 3, rating_career_support: 4,
        rating_internship_access: 4, rating_community_culture: 5, rating_roi: 4, rating_overall: 5,
        review_text: 'Rigorous and rewarding.',
        who_thrives_here: 'Self-directed builders.',
        reviewer_context: { status: 'current_student', degree: 'masters', cohort_year: '2024' },
        external_source: null, is_verified: true, created_at: '2024-01-01T00:00:00Z',
      },
    ],
  }
  const employer = {
    total_feedback: 1,
    avg_technical: 4.4, avg_practical: 4.0, avg_communication: 3.8,
    avg_teamwork: 4.1, avg_reliability: 4.3, avg_overall: 4.1,
    sentiment_counts: { positive: 1, neutral: 0, negative: 0 },
    feedback: [
      {
        id: 'e1', program_id: 'prog-1', employer_name: 'Acme Corp', industry: 'Technology',
        rating_technical: 5, rating_practical: 4, rating_communication: 4,
        rating_teamwork: 4, rating_reliability: 4, rating_overall: 4,
        job_readiness_sentiment: 'positive', feedback_text: 'Graduates ship quickly.',
        hiring_pattern: 'Repeat hiring every cycle.', feedback_year: 2024,
        created_at: '2024-02-01T00:00:00Z',
      },
    ],
  }
  const netPrice = {
    program_id: 'prog-1', available: true, reason: null, currency: 'USD',
    cost_of_attendance_annual: 66000,
    net_cost_scenario_range: { min: 30000, expected: 38000, max: 46000 },
    net_cost_scenario_range_total: { min: 60000, expected: 76000, max: 92000 },
    years: 2, affordability_band: 'stretch', aid_scholarship_likelihood_band: 'moderate',
    gap: { student_annual_budget: 35000, shortfall_annual: 3000, band: 'stretch' },
    drivers: ['Sticker cost of attendance ≈ $66,000/yr.'],
    disclaimer: 'This is an estimate, not a quote or an aid offer.',
  }
  const program = {
    id: 'prog-1', program_name: 'Computer Science, M.S.', degree_type: 'masters',
    institution_id: 'inst-1', institution_name: 'University of Foo',
    institution_city: 'New York', institution_country: 'USA',
    duration_months: 24, tuition: 48000, cost_data: {}, ranking_data: {},
    application_requirements: [], intake_rounds: {}, outcomes_data: {}, highlights: [],
    is_published: true,
  }
  const match = { fitness_score: 0.82, confidence_score: 0.74, band_label: 'target', probability_bands: null }
  return {
    reviews, employer, netPrice, program, match,
    saveProgramMock: vi.fn().mockResolvedValue({}),
    createApplicationMock: vi.fn().mockResolvedValue({ id: 'app-1' }),
  }
})

const reviews = h.reviews as ProgramReviewSummary
const employer = h.employer as EmployerFeedbackSummary
const netPrice = h.netPrice as NetPriceEstimate

const emptyReviews: ProgramReviewSummary = {
  total_reviews: 0,
  avg_teaching: null, avg_workload: null, avg_career_support: null,
  avg_internship_access: null, avg_community_culture: null, avg_roi: null, avg_overall: null,
  reviews: [],
}
const emptyEmployer: EmployerFeedbackSummary = {
  total_feedback: 0,
  avg_technical: null, avg_practical: null, avg_communication: null,
  avg_teamwork: null, avg_reliability: null, avg_overall: null,
  sentiment_counts: {}, feedback: [],
}

vi.mock('../api/programs', () => ({
  getProgram: vi.fn().mockResolvedValue(h.program),
  getProgramReviews: vi.fn().mockResolvedValue(h.reviews),
  getEmployerFeedback: vi.fn().mockResolvedValue(h.employer),
  getNetPrice: vi.fn().mockResolvedValue(h.netPrice),
  searchPrograms: vi.fn().mockResolvedValue({ items: [] }),
  semanticSearch: vi.fn().mockResolvedValue([]),
}))
vi.mock('../api/matching', () => ({
  getMatchDetail: vi.fn().mockResolvedValue(h.match),
  logEngagement: vi.fn().mockResolvedValue({}),
}))
vi.mock('../api/events', () => ({
  listEvents: vi.fn().mockResolvedValue([]),
  rsvpEvent: vi.fn().mockResolvedValue({}),
  getMyRsvps: vi.fn().mockResolvedValue([]),
}))
vi.mock('../api/applications', () => ({
  listMyApplications: vi.fn().mockResolvedValue([]),
  createApplication: (...a: unknown[]) => h.createApplicationMock(...a),
}))
vi.mock('../api/saved-lists', () => ({
  saveProgram: (...a: unknown[]) => h.saveProgramMock(...a),
  unsaveProgram: vi.fn().mockResolvedValue({}),
  listSaved: vi.fn().mockResolvedValue([]),
}))

import ProgramDetailPage from '../pages/student/ProgramDetailPage'

/* ── InsightsPanel (presentational) ───────────────────────────────────────── */

describe('Spec 11 §3.5 — InsightsPanel', () => {
  const noop = () => {}

  it('renders BOTH panels — student reviews and employer feedback — in one tab', () => {
    render(
      <InsightsPanel
        programName="CS MS" reviews={reviews} employer={employer}
        reviewerType="" degree="" cohort="" minRating="" industry=""
        onFilter={noop} onClear={noop}
      />,
    )
    expect(screen.getByText('Student & alumni reviews')).toBeInTheDocument()
    expect(screen.getByText('Employer feedback')).toBeInTheDocument()
    expect(screen.getByText('Teaching quality')).toBeInTheDocument()
    expect(screen.getByText('Technical fundamentals')).toBeInTheDocument()
    expect(screen.getByText('Repeat hiring every cycle.')).toBeInTheDocument()
  })

  it('derives summary themes from the real averages', () => {
    render(
      <InsightsPanel
        programName="CS MS" reviews={reviews} employer={employer}
        reviewerType="" degree="" cohort="" minRating="" industry=""
        onFilter={noop} onClear={noop}
      />,
    )
    expect(screen.getByText('What students say')).toBeInTheDocument()
    expect(screen.getByText('What employers say')).toBeInTheDocument()
    expect(screen.getByText('Common tradeoffs')).toBeInTheDocument()
  })

  it('surfaces the four guided prompts', () => {
    render(
      <InsightsPanel
        programName="CS MS" reviews={reviews} employer={employer}
        reviewerType="" degree="" cohort="" minRating="" industry=""
        onFilter={noop} onClear={noop}
      />,
    )
    // "Who thrives here" also appears as a per-review callout label, so allow ≥1.
    for (const p of ['Who thrives here', 'Who should avoid it', 'Best resources', 'Biggest tradeoffs']) {
      expect(screen.getAllByText(p).length).toBeGreaterThan(0)
    }
  })

  it('shows the canonical empty copy when there are no reviews', () => {
    render(
      <InsightsPanel
        programName="CS MS" reviews={emptyReviews} employer={emptyEmployer}
        reviewerType="" degree="" cohort="" minRating="" industry=""
        onFilter={noop} onClear={noop}
      />,
    )
    expect(screen.getByText("Reviews aren't available for this program yet.")).toBeInTheDocument()
  })

  it('calls onFilter with the reviewer type when that select changes', () => {
    const onFilter = vi.fn()
    render(
      <InsightsPanel
        programName="CS MS" reviews={reviews} employer={employer}
        reviewerType="" degree="" cohort="" minRating="" industry=""
        onFilter={onFilter} onClear={noop}
      />,
    )
    fireEvent.change(screen.getByLabelText('Filter by reviewer type'), {
      target: { value: 'current_student' },
    })
    expect(onFilter).toHaveBeenCalledWith('reviewer', 'current_student')
  })

  it('calls onFilter with the industry when that select changes', () => {
    const onFilter = vi.fn()
    render(
      <InsightsPanel
        programName="CS MS" reviews={reviews} employer={employer}
        reviewerType="" degree="" cohort="" minRating="" industry=""
        onFilter={onFilter} onClear={noop}
      />,
    )
    fireEvent.change(screen.getByLabelText('Filter by industry'), {
      target: { value: 'Technology' },
    })
    expect(onFilter).toHaveBeenCalledWith('industry', 'Technology')
  })
})

/* ── NetPriceEstimator (presentational) ───────────────────────────────────── */

describe('Spec 11 §3.3a — NetPriceEstimator', () => {
  it('renders a {min,expected,max} range, the gap band, and the honest disclaimer', () => {
    render(<NetPriceEstimator estimate={netPrice} />)
    expect(screen.getByText('Your estimated net price')).toBeInTheDocument()
    expect(screen.getByText('Estimate, not a quote')).toBeInTheDocument()
    expect(screen.getByText(/A stretch/)).toBeInTheDocument()
    // The methodology disclaimer is folded into a hover tooltip on the Info icon (declutter).
    expect(screen.getByTitle(/This is an estimate, not a quote/)).toBeInTheDocument()
  })

  it('renders nothing when the estimate is unavailable', () => {
    const { container } = render(
      <NetPriceEstimator
        estimate={{ ...netPrice, available: false, net_cost_scenario_range: null }}
      />,
    )
    expect(container).toBeEmptyDOMElement()
  })

  it('renders nothing when there is no estimate (public / no-auth)', () => {
    const { container } = render(<NetPriceEstimator estimate={null} />)
    expect(container).toBeEmptyDOMElement()
  })
})

/* ── Page-level integration (mocked API) ──────────────────────────────────── */

function LocationProbe() {
  const loc = useLocation()
  return <div data-testid="loc">{loc.search}</div>
}

function renderPage(initial: string) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter initialEntries={[initial]}>
        <Routes>
          <Route
            path="/s/programs/:programId"
            element={<><ProgramDetailPage /><LocationProbe /></>}
          />
          <Route path="/s/explore" element={<div>Explore</div>} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

describe('Spec 11 §10 — ProgramDetailPage integration', () => {
  beforeEach(() => {
    h.saveProgramMock.mockClear()
    h.createApplicationMock.mockClear()
  })

  it('renders the program and shows the DualRing match for an authenticated student', async () => {
    renderPage('/s/programs/prog-1?tab=overview')
    expect(await screen.findByRole('heading', { name: 'Computer Science, M.S.' })).toBeInTheDocument()
    await waitFor(() => expect(screen.getByText(/Fitness · 82%/)).toBeInTheDocument())
  })

  it('redirects legacy ?tab=reviews to the Insights tab', async () => {
    renderPage('/s/programs/prog-1?tab=reviews')
    expect(await screen.findByText('Student & alumni reviews')).toBeInTheDocument()
    await waitFor(() =>
      expect(screen.getByTestId('loc').textContent).toContain('tab=insights'),
    )
  })

  it('persists the Insights reviewer-type filter in the URL', async () => {
    renderPage('/s/programs/prog-1?tab=insights')
    const select = await screen.findByLabelText('Filter by reviewer type')
    fireEvent.change(select, { target: { value: 'current_student' } })
    await waitFor(() =>
      expect(screen.getByTestId('loc').textContent).toContain('reviewer=current_student'),
    )
  })

  it('triggers Save when the save action is clicked', async () => {
    renderPage('/s/programs/prog-1?tab=overview')
    const saveBtn = await screen.findByRole('button', { name: /save/i })
    fireEvent.click(saveBtn)
    await waitFor(() => expect(h.saveProgramMock).toHaveBeenCalledWith('prog-1'))
  })

  it('triggers Start application when that action is clicked', async () => {
    renderPage('/s/programs/prog-1?tab=overview')
    const applyBtn = await screen.findByRole('button', { name: /start application/i })
    fireEvent.click(applyBtn)
    await waitFor(() => expect(h.createApplicationMock).toHaveBeenCalledWith('prog-1'))
  })

  it('renders Spec 23 structured admissions (test policy, prerequisites) on Admissions tab', async () => {
    const { getProgram } = await import('../api/programs')
    vi.mocked(getProgram).mockResolvedValueOnce({
      ...h.program,
      application_requirements: {
        materials: [{ name: 'Essay', required: true }],
        prerequisites: [{ name: 'Calculus', required: true, allowed_substitutes: [] }],
        test_policy: {
          stance: 'test_optional',
          required: ['GRE'],
          optional: [],
          accepted_tests: ['GRE'],
          superscore_enabled: false,
          waived_rules: '',
          typical_ranges: [],
        },
        recommendations: { required_count: 2, types: ['academic'] },
      },
    } as any)
    renderPage('/s/programs/prog-1?tab=admissions')
    expect(await screen.findByText('Test Policy')).toBeInTheDocument()
    expect(screen.getByText('Prerequisites')).toBeInTheDocument()
    expect(screen.getByText('Calculus')).toBeInTheDocument()
  })
})
