/**
 * Spec 23 §1 — public program page at /program/:id must render the same
 * canonical editor output as the authenticated student page (via programNormalize).
 */
import { render, screen } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { describe, expect, it, vi } from 'vitest'

const h = vi.hoisted(() => ({
  canonicalProgram: {
    id: 'prog-1',
    institution_id: 'inst-1',
    program_name: 'Computer Science, M.S.',
    degree_type: 'masters',
    department: 'Engineering',
    duration_months: 24,
    tuition: 48000,
    acceptance_rate: 0.12,
    delivery_format: 'in_person',
    description_text: 'A rigorous program.',
    who_its_for: 'Builders who ship.',
    tracks: { concentrations: ['AI', 'Systems'], note: 'Pick one', learning_format: 'Cohort-based, 20 hrs/week' },
    highlights: ['STEM-designated'],
    faculty_contacts: [{ name: 'Dr. Lee', email: 'lee@uni.edu', role: 'Director' }],
    application_requirements: {
      materials: [{ name: 'Statement of purpose', required: true }],
      prerequisites: [{ name: 'Linear algebra', required: true, allowed_substitutes: ['Matrix theory'] }],
      test_policy: {
        stance: 'test_optional',
        required: ['GRE'],
        optional: ['GMAT'],
        accepted_tests: ['GRE', 'GMAT'],
        superscore_enabled: false,
        waived_rules: 'Waived with 5+ years experience',
        typical_ranges: [{ test: 'GRE', low: 310, high: 330 }],
      },
      recommendations: { required_count: 2, types: ['academic'] },
    },
    intake_rounds: [
      { id: 'r1', name: 'Round 1', term: { season: 'Fall', year: 2027 }, deadline: '2026-11-01', decision_date: '2027-01-15', open_date: null, start_date: null, capacity: 30 },
    ],
    cost_data: {
      tuition_amount: 48000,
      tuition_currency: 'USD',
      tuition_period: 'per_year',
      fees: [{ name: 'Lab fee', amount: 300, required: true }],
      estimated_total_cost_band: { min: 80000, max: 92000, currency: 'USD' },
      funding_signals: { ta_funded: true, ra_funded: false, merit_scholarship_available: true, need_based_available: false },
    },
    outcomes_data: {
      median_starting_salary: 95000,
      placement_rate_pct: 94,
      salary_distribution_bands: [{ band_label: '$80k–$100k', percent: 45 }],
      common_roles: ['Software Engineer'],
      top_employers: ['Google'],
    },
    is_published: true,
  },
}))

vi.mock('../api/programs', () => ({
  getProgram: vi.fn().mockResolvedValue(h.canonicalProgram),
}))
vi.mock('../api/institutions', () => ({
  getPublicInstitution: vi.fn().mockResolvedValue({ id: 'inst-1', name: 'Test University' }),
  submitInquiry: vi.fn(),
}))
vi.mock('../api/events', () => ({
  listEvents: vi.fn().mockResolvedValue([]),
}))
vi.mock('../stores/toast-store', () => ({ showToast: vi.fn() }))

import PublicProgramDetailPage from '../pages/public/ProgramDetailPage'

function renderPublic(path = '/program/prog-1') {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter initialEntries={[path]}>
        <Routes>
          <Route path="/program/:programId" element={<PublicProgramDetailPage />} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

describe('Spec 23 — public program detail (/program/:id)', () => {
  it('renders canonical editor output on Overview', async () => {
    renderPublic()
    expect(await screen.findByText('Computer Science, M.S.')).toBeInTheDocument()
    expect(screen.getByText('Tracks & Structure')).toBeInTheDocument()
    expect(screen.getByText('AI')).toBeInTheDocument()
    expect(screen.getByText(/Cohort-based/)).toBeInTheDocument()
  })

  it('renders structured admissions on Admissions tab', async () => {
    renderPublic()
    await screen.findByText('Computer Science, M.S.')
    screen.getByText('Admissions').click()
    expect(await screen.findByText('Test Policy')).toBeInTheDocument()
    expect(screen.getByText('Test-optional')).toBeInTheDocument()
    expect(screen.getByText('Prerequisites')).toBeInTheDocument()
    expect(screen.getByText('Linear algebra')).toBeInTheDocument()
    expect(screen.getByText('Round 1')).toBeInTheDocument()
  })

  it('renders cost band and funding on Costs & Aid tab', async () => {
    renderPublic()
    await screen.findByText('Computer Science, M.S.')
    screen.getByText('Costs & Aid').click()
    expect(await screen.findByText('Funding & Aid Signals')).toBeInTheDocument()
    expect(screen.getByText('TA funding available')).toBeInTheDocument()
    expect(screen.getByText(/80,000.*92,000/)).toBeInTheDocument()
  })

  it('renders salary bands on Outcomes tab', async () => {
    renderPublic()
    await screen.findByText('Computer Science, M.S.')
    screen.getByText('Outcomes').click()
    expect(await screen.findByText('$80k–$100k')).toBeInTheDocument()
    expect(screen.getByText('Google')).toBeInTheDocument()
  })
})
