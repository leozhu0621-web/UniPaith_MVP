/**
 * Spec 28 — Attribution & Funnel Analytics frontend tests.
 *
 *   - KPI / delta formatters behave by unit and sign (§11).
 *   - The page renders the header, three tabs, filter bar, and KPI row.
 *   - The funnel tab surfaces the insufficient-data state (§9/§14).
 */
import { render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { describe, expect, it, vi } from 'vitest'

import { formatDelta, formatKpi, priorLabel } from '../pages/institution/analytics/constants'

vi.mock('../api/institutions', () => ({
  getAnalyticsOverview: vi.fn(async () => ({
    filter: {},
    total_applications: { value: 120, prior: 100, delta_pct: 0.2, unit: 'count' },
    acceptance_rate: { value: 0.25, prior: 0.2, delta_pct: 0.25, unit: 'percent' },
    avg_match_score: { value: 0.8, prior: null, delta_pct: null, unit: 'score' },
    yield_rate: { value: 0.4, prior: 0.5, delta_pct: -0.2, unit: 'percent' },
    apps_by_status: {},
    apps_by_program: [],
    apps_over_time: [],
    decisions_breakdown: {},
    has_data: true,
    generated_at: '2026-06-01T00:00:00Z',
  })),
  getAnalyticsFunnel: vi.fn(async () => ({
    filter: {},
    stages: [],
    sub_funnels: [],
    top_sources_by_clicks: [],
    top_sources_by_apply_started: [],
    drop_off_alerts: [],
    total_events: 0,
    has_data: false,
    generated_at: '2026-06-01T00:00:00Z',
  })),
  getAnalyticsAttribution: vi.fn(async () => ({
    filter: {},
    campaigns: [],
    events: [],
    top_content_by_clicks: [],
    top_content_by_apply_started: [],
    has_data: false,
    generated_at: '2026-06-01T00:00:00Z',
  })),
  getInstitutionPrograms: vi.fn(async () => []),
  getSegments: vi.fn(async () => []),
  getCampaigns: vi.fn(async () => []),
  getIntakeRounds: vi.fn(async () => []),
  exportAnalyticsCsv: vi.fn(async () => undefined),
}))

import AnalyticsPage from '../pages/institution/AnalyticsPage'

function renderPage(initial = '/i/analytics?tab=overview') {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter initialEntries={[initial]}>
        <AnalyticsPage />
      </MemoryRouter>
    </QueryClientProvider>
  )
}

describe('Spec 28 — analytics formatters', () => {
  it('formats KPI values by unit', () => {
    expect(formatKpi(1234, 'count')).toBe('1,234')
    expect(formatKpi(0.25, 'percent')).toBe('25%')
    expect(formatKpi(0.8, 'score')).toBe('80')
    expect(formatKpi(null, 'count')).toBe('—')
  })

  it('formats deltas with sign, tone, and prior-period label', () => {
    expect(formatDelta(0.12, '30d')).toEqual({ text: '+12% vs prior 30 days', tone: 'text-success' })
    expect(formatDelta(-0.1, '7d')?.tone).toBe('text-error')
    expect(formatDelta(null, '30d')).toBeNull()
    expect(priorLabel('yoy')).toBe('vs last year')
  })
})

describe('Spec 28 — AnalyticsPage', () => {
  it('renders header, tabs, and the KPI row with comparison', async () => {
    renderPage()
    expect(screen.getByText('Analytics')).toBeInTheDocument()
    expect(screen.getByText('Export CSV')).toBeInTheDocument()
    expect(screen.getByText('Funnel')).toBeInTheDocument()
    expect(screen.getByText('Attribution')).toBeInTheDocument()
    await waitFor(() => expect(screen.getByText('Total applications')).toBeInTheDocument())
    expect(screen.getByText('+20% vs prior 30 days')).toBeInTheDocument()
  })

  it('shows the insufficient-data state on the funnel tab', async () => {
    renderPage('/i/analytics?tab=funnel')
    await waitFor(() =>
      expect(screen.getByText('Not enough events in this window to plot.')).toBeInTheDocument()
    )
  })
})
