import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { MemoryRouter } from 'react-router-dom'

import GoalHubPage from '../pages/public/GoalHubPage'
import BuildRoadmapPage from '../pages/public/BuildRoadmapPage'
import FeatureBacklogPage from '../pages/public/FeatureBacklogPage'
import ApiContractPage from '../pages/public/ApiContractPage'
import * as buildApi from '../api/build'
import type { ApiContract, BuildOverview, FeatureCatalog, Roadmap } from '../types/build'

// Specs 48/49/50 — the public /goal transparency surfaces. Each renders live
// build data from the /build/* endpoints and lets the visitor filter it.

const OVERVIEW: BuildOverview = {
  roadmap: { phase_count: 14, shipped: 13, deferred: 1, mvp_complete: true },
  features: {
    feature_count: 60,
    student_count: 28,
    institution_count: 32,
    delivered: 45,
    klass_counts: { core: 28, extend: 12, defer: 20 },
    mvp_scope_count: 40,
    mvp_delivered: 40,
    mvp_complete: true,
    ahead_of_plan: 5,
  },
  api: {
    route_count: 553,
    router_count: 42,
    public_route_count: 22,
    authenticated_route_count: 531,
    ai_endpoint_count: 10,
    method_totals: { GET: 300, POST: 200 },
    prefix: '/api/v1',
    doc_claimed_routers: 22,
    doc_claimed_routes: 285,
    live_is_source_of_truth: true,
  },
  agents: {
    agent_count: 40,
    llm_agent_count: 34,
    fallback_coverage: '100%',
    provider: 'anthropic',
    tier_counts: { flagship: 2, workhorse: 20, batch: 6, rule_based: 12 },
  },
  provider: 'anthropic',
  surfaces: [
    { key: 'claude-api', title: 'AI agents', spec: '45', blurb: 'The live agent fleet.', path: '/goal/claude-api', stat: 40, stat_label: 'AI agents' },
    { key: 'roadmap', title: 'Build roadmap', spec: '48', blurb: 'Phased path to spec.', path: '/goal/roadmap', stat: '13/14', stat_label: 'phases shipped' },
    { key: 'features', title: 'Feature coverage', spec: '49', blurb: 'Every feature mapped.', path: '/goal/features', stat: 60, stat_label: 'features mapped' },
    { key: 'api', title: 'API contract', spec: '50', blurb: 'Read live from routes.', path: '/goal/api', stat: 553, stat_label: 'live routes' },
  ],
}

const ROADMAP: Roadmap = {
  summary: { phase_count: 14, shipped: 13, deferred: 1, mvp_complete: true },
  phases: [
    {
      number: 2,
      title: 'Claude LLM migration',
      goal: 'Every LLM call routes through Claude.',
      specs: ['04', '45'],
      gap_items: ['G-AI1'],
      effort: '8 days',
      workstream: 'Backend',
      status: 'shipped',
      status_label: 'Shipped',
      evidence: 'Provider registry live; default is Anthropic.',
      done_when: 'All agents on Claude.',
    },
    {
      number: 14,
      title: 'Deferred items',
      goal: 'Bedrock, data residency, multi-tenant.',
      specs: [],
      gap_items: ['G-C2'],
      effort: 'Reassess Q3 2026',
      workstream: 'Cross-cutting',
      status: 'deferred',
      status_label: 'Deferred',
      evidence: 'Out of MVP scope per spec 48 §17.',
      done_when: 'Reassessed Q3 2026.',
    },
  ],
  workstreams: ['Frontend', 'Backend', 'Data', 'Cross-cutting'],
}

const FEATURES: FeatureCatalog = {
  summary: {
    feature_count: 3,
    student_count: 1,
    institution_count: 2,
    delivered: 2,
    klass_counts: { core: 1, extend: 1, defer: 1 },
    mvp_scope_count: 2,
    mvp_delivered: 2,
    mvp_complete: true,
    ahead_of_plan: 1,
  },
  features: [
    { name: 'Universal Profile', side: 'student', status: 'covered', status_label: 'Covered', spec: '08', klass: 'core', klass_label: 'Core', delivered: true, note: '' },
    { name: 'Blind review mode', side: 'institution', status: 'written', status_label: 'Written', spec: '32', klass: 'extend', klass_label: 'Extend', delivered: true, note: '' },
    { name: 'International tooling', side: 'institution', status: 'net_new', status_label: 'Net-new', spec: '38', klass: 'defer', klass_label: 'Defer', delivered: true, note: 'Shipped ahead of plan.' },
  ],
}

const CONTRACT: ApiContract = {
  summary: {
    route_count: 553,
    router_count: 2,
    public_route_count: 22,
    authenticated_route_count: 531,
    ai_endpoint_count: 2,
    method_totals: { GET: 1, POST: 1 },
    prefix: '/api/v1',
    doc_claimed_routers: 22,
    doc_claimed_routes: 285,
    live_is_source_of_truth: true,
  },
  conventions: [{ title: 'One prefix, one client', body: 'Everything under /api/v1.' }],
  status_taxonomy: [{ code: '401', when: 'No token', frontend: 'Redirect to login.' }],
  groups: [
    { tag: 'institutions', route_count: 129, methods: { GET: 80, POST: 49 }, role: 'mixed', access: 'mixed', sample_paths: ['/api/v1/institutions/me'] },
    { tag: 'build-transparency', route_count: 4, methods: { GET: 4 }, role: 'public', access: 'public', sample_paths: ['/api/v1/build/roadmap'] },
  ],
  ai_endpoints: ['/api/v1/students/me/strategy/generate'],
  access_note: 'Conservative read; live source of truth.',
}

function renderPage(ui: React.ReactElement, route = '/goal') {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter initialEntries={[route]}>{ui}</MemoryRouter>
    </QueryClientProvider>,
  )
}

describe('Spec 48/49/50 — build-transparency /goal surfaces', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
  })

  it('hub renders the live stats and links to all four surfaces', async () => {
    vi.spyOn(buildApi, 'getBuildOverview').mockResolvedValue(OVERVIEW)
    renderPage(<GoalHubPage />)

    expect(screen.getByText(/How UniPaith is built — in the open/i)).toBeInTheDocument()
    await waitFor(() => expect(screen.getByText('Build roadmap')).toBeInTheDocument())
    expect(screen.getByText('Feature coverage')).toBeInTheDocument()
    expect(screen.getByText('API contract')).toBeInTheDocument()
    // Live route count from the overview appears (stat band + surface card).
    expect(screen.getAllByText('553').length).toBeGreaterThan(0)
    // The MVP-complete gold beat shows.
    expect(screen.getByText(/MVP scope complete/i)).toBeInTheDocument()
  })

  it('roadmap renders phases and filters by status', async () => {
    vi.spyOn(buildApi, 'getRoadmap').mockResolvedValue(ROADMAP)
    renderPage(<BuildRoadmapPage />, '/goal/roadmap')

    await waitFor(() => expect(screen.getByText('Claude LLM migration')).toBeInTheDocument())
    expect(screen.getByText('Deferred items')).toBeInTheDocument()

    // Filter to shipped → the deferred phase drops out.
    fireEvent.click(screen.getByRole('button', { name: 'Shipped' }))
    await waitFor(() => expect(screen.queryByText('Deferred items')).not.toBeInTheDocument())
    expect(screen.getByText('Claude LLM migration')).toBeInTheDocument()
  })

  it('features renders the map and filters by side', async () => {
    vi.spyOn(buildApi, 'getFeatureCatalog').mockResolvedValue(FEATURES)
    renderPage(<FeatureBacklogPage />, '/goal/features')

    await waitFor(() => expect(screen.getByText('Universal Profile')).toBeInTheDocument())
    expect(screen.getByText('International tooling')).toBeInTheDocument()
    // The ahead-of-plan beat is surfaced (hero pill + the feature note).
    expect(screen.getAllByText(/shipped ahead of plan/i).length).toBeGreaterThan(0)

    fireEvent.click(screen.getByRole('button', { name: 'Institution' }))
    await waitFor(() => expect(screen.queryByText('Universal Profile')).not.toBeInTheDocument())
    expect(screen.getByText('Blind review mode')).toBeInTheDocument()
  })

  it('api contract renders the live router map and the doc-vs-live correction', async () => {
    vi.spyOn(buildApi, 'getApiContract').mockResolvedValue(CONTRACT)
    renderPage(<ApiContractPage />, '/goal/api')

    await waitFor(() => expect(screen.getByText('institutions')).toBeInTheDocument())
    expect(screen.getByText('build-transparency')).toBeInTheDocument()
    // The drift correction (22/285 → live) is shown.
    expect(screen.getByText(/the running code wins/i)).toBeInTheDocument()
    // The "can't drift" gold beat.
    expect(screen.getByText(/Generated live — can't drift/i)).toBeInTheDocument()

    // Filter to public → only the build-transparency group remains.
    fireEvent.click(screen.getByRole('button', { name: 'Public' }))
    await waitFor(() => expect(screen.queryByText('institutions')).not.toBeInTheDocument())
    expect(screen.getByText('build-transparency')).toBeInTheDocument()
  })
})
