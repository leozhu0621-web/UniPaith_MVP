/**
 * Spec 46 §9/§10/§1/§5 — institution Data & Privacy settings smoke test.
 * DataGovernanceCard renders the sub-processor list (§10), brand commitments
 * (§1), retention (§5), and the governance config (§9) without crashing.
 */
import { render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { describe, expect, it, vi } from 'vitest'

vi.mock('../api/dataGovernance', () => ({
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
    retention_policy: [
      { data_type: 'Account (auth)', retention: 'Indefinite while active.' },
      { data_type: 'AI audit ledger', retention: '7 years.' },
    ],
    no_data_sale: 'UniPaith never sells raw student data.',
  })),
  updateDataGovernance: vi.fn(async () => ({ settings: {} })),
}))

import DataGovernanceCard from '../pages/institution/settings/DataGovernanceCard'

function renderCard() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter initialEntries={['/i/settings?tab=data']}>
        <DataGovernanceCard />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

describe('Spec 46 · Data & Privacy governance', () => {
  it('renders sub-processors (§10), commitments (§1), and config (§9)', async () => {
    renderCard()
    await waitFor(() => expect(screen.getByText('Sub-processors')).toBeInTheDocument())
    expect(screen.getByText('AWS (ECS, RDS, S3, CloudFront)')).toBeInTheDocument()
    expect(screen.getByText('Fit, not fame.')).toBeInTheDocument()
    expect(screen.getByText('No-training tier')).toBeInTheDocument()
    expect(screen.getByText('Data retention')).toBeInTheDocument()
    expect(screen.getByText('UniPaith never sells raw student data.')).toBeInTheDocument()
  })
})
