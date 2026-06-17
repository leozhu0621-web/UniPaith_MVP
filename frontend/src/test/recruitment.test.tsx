/**
 * Spec 40 — Recruitment CRM (Pre-Applicant) frontend tests.
 *
 *   - The page renders the header + the four tabs (Prospects / Travel / Fairs / Territories).
 *   - The empty Prospects state shows the spec §6/§10 copy.
 *   - Consent + AI-priority display metadata are correct (§7 / §5).
 */
import { render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { describe, expect, it, vi } from 'vitest'

import { STAGE_META, SOURCE_META, BAND_META, RECRUIT_SERIES } from '../pages/institution/recruitment/constants'

vi.mock('../api/recruitment', () => ({
  getRecruitmentSummary: vi.fn(async () => ({
    prospect_count: 0,
    applicant_count: 0,
    trip_count: 0,
    fair_count: 0,
    territory_count: 0,
    unassigned_territory_count: 0,
    over_budget_trip_count: 0,
    stage_counts: {},
    source_counts: {},
    is_empty: true,
  })),
  listProspects: vi.fn(async () => ({
    items: [],
    total: 0,
    prioritized: false,
    stage_counts: {},
  })),
}))

import RecruitmentPage from '../pages/institution/RecruitmentPage'

function renderPage() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter initialEntries={['/i/recruitment']}>
        <RecruitmentPage />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

describe('Spec 40 · Recruitment CRM', () => {
  it('renders the header and all four tabs', async () => {
    renderPage()
    expect(screen.getByRole('heading', { name: 'Recruitment', level: 1 })).toBeInTheDocument()
    expect(screen.getByRole('tab', { name: 'Prospects' })).toBeInTheDocument()
    expect(screen.getByRole('tab', { name: 'Travel' })).toBeInTheDocument()
    expect(screen.getByRole('tab', { name: 'Fairs & Schools' })).toBeInTheDocument()
    expect(screen.getByRole('tab', { name: 'Territories' })).toBeInTheDocument()
  })

  it('shows the empty-state copy from §6/§10', async () => {
    renderPage()
    await waitFor(() =>
      expect(
        screen.getByText('Import a prospect list or capture leads at a fair.'),
      ).toBeInTheDocument(),
    )
  })

  it('defines the no-gold chart palette (§7) and stage/source/band metadata', () => {
    // §7 — no gold (#FFD60A) in the recruitment palette.
    expect(RECRUIT_SERIES).not.toContain('#FFD60A')
    expect(RECRUIT_SERIES[0]).toBe('#2A6BD4') // cobalt lead
    expect(STAGE_META.applicant.tone).toBe('success')
    expect(STAGE_META.suspect.label).toBe('Suspect')
    expect(SOURCE_META.fair).toBe('Fair')
    expect(BAND_META.hot.label).toBe('Hot')
  })
})
