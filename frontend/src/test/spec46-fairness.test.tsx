/**
 * Spec 46 — Data Rights & Fairness Governance frontend smoke tests.
 *   - FairnessPage renders the §6 commitment, the halted cohort, and override history.
 *   - DataGovernanceCard renders the sub-processor list (§10) + brand commitments (§1).
 */
import { render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { describe, expect, it, vi } from 'vitest'

vi.mock('../api/fairness', () => ({
  getFairnessStatus: vi.fn(async () => ({
    overall_status: 'halted',
    threshold_default: 0.2,
    min_sample: 50,
    weeks: ['2026-05-04', '2026-05-11', '2026-05-18', '2026-05-25'],
    programs: [
      {
        program_id: 'p1',
        program_name: 'MS Computer Science',
        matching_halted: true,
        fairness_override_active: false,
        override_expires_at: null,
        fairness_threshold: 0.2,
        status: 'halted',
        trend: [
          { week_start: '2026-05-04', delta: 0.1 },
          { week_start: '2026-05-11', delta: 0.3 },
          { week_start: '2026-05-18', delta: 0.6 },
          { week_start: '2026-05-25', delta: 0.8 },
        ],
        attributes: { gender: { '2026-05-18': 0.6, '2026-05-25': 0.8 } },
      },
    ],
  })),
  listFairnessSignals: vi.fn(async () => []),
  listFairnessOverrides: vi.fn(async () => []),
  createFairnessOverride: vi.fn(async () => ({})),
  updateFairnessThreshold: vi.fn(async () => ({})),
  computeFairness: vi.fn(async () => ({ computed: 0 })),
  getDataGovernance: vi.fn(async () => ({
    settings: {
      override_expiry_weeks_default: 1,
      protected_attributes_tracked: ['gender', 'first_gen', 'international', 'nationality_region'],
      no_training_tier: false,
      data_residency: 'us',
    },
    program_thresholds: [
      { program_id: 'p1', program_name: 'MS CS', fairness_threshold: 0.2, matching_halted: true },
    ],
    subprocessors: [
      {
        name: 'AWS (ECS, RDS, S3, CloudFront)',
        touches: 'All production data',
        classification: 'All classes including PII',
        region: 'us-east-1 (default)',
      },
      {
        name: 'Anthropic API',
        touches: 'Inference inputs at call time',
        classification: 'PII (not retained)',
        region: 'US',
      },
    ],
    subprocessor_note: 'Every sub-processor is bound by a DPA.',
    brand_commitments: [
      { title: 'Fit, not fame.', body: 'We match students where they thrive.' },
      { title: 'Partnership, not extraction.', body: "We exchange value for data — we don't sell it." },
    ],
    retention_policy: [{ data_type: 'Account (auth)', retention: 'Indefinite while active.' }],
    no_data_sale: 'UniPaith never sells raw student data.',
  })),
  updateDataGovernance: vi.fn(async () => ({ settings: {} })),
}))

import FairnessPage from '../pages/institution/fairness/FairnessPage'
import DataGovernanceCard from '../pages/institution/settings/DataGovernanceCard'

function renderWithProviders(ui: React.ReactNode, path = '/i/admissions?tab=fairness') {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter initialEntries={[path]}>{ui}</MemoryRouter>
    </QueryClientProvider>,
  )
}

describe('Spec 46 · Fairness governance', () => {
  it('FairnessPage shows the §6 commitment, the halted cohort, and override history', async () => {
    renderWithProviders(<FairnessPage />)
    // The page shows a loading skeleton first; wait for the resolved content.
    await waitFor(() => expect(screen.getByText('MS Computer Science')).toBeInTheDocument())
    // The verbatim §6 auto-halt commitment.
    expect(screen.getByText(/stops scoring new applicants for that cohort/i)).toBeInTheDocument()
    expect(screen.getAllByText('Halted').length).toBeGreaterThan(0)
    expect(screen.getByText('Override history')).toBeInTheDocument()
  })

  it('DataGovernanceCard shows sub-processors (§10) + brand commitments (§1)', async () => {
    renderWithProviders(<DataGovernanceCard />)
    await waitFor(() => expect(screen.getByText('Sub-processors')).toBeInTheDocument())
    expect(screen.getByText('AWS (ECS, RDS, S3, CloudFront)')).toBeInTheDocument()
    expect(screen.getByText('Fit, not fame.')).toBeInTheDocument()
    expect(screen.getByText('No-training tier')).toBeInTheDocument()
    expect(screen.getByText('Sub-processors')).toBeInTheDocument()
  })
})
