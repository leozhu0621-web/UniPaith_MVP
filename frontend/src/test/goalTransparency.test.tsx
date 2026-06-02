import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { MemoryRouter } from 'react-router-dom'

import GoalHubPage from '../pages/public/GoalHubPage'
import BuildRoadmapPage from '../pages/public/BuildRoadmapPage'
import FeatureBacklogPage from '../pages/public/FeatureBacklogPage'
import ApiContractPage from '../pages/public/ApiContractPage'
import DataModelPage from '../pages/public/DataModelPage'
import AcceptancePage from '../pages/public/AcceptancePage'
import ExperienceStandardsPage from '../pages/public/ExperienceStandardsPage'
import * as buildApi from '../api/build'
import type {
  Acceptance,
  ApiContract,
  BuildOverview,
  DataModel,
  FeatureCatalog,
  Roadmap,
  UxBenchmark,
} from '../types/build'

const DATA_MODEL_SUMMARY = {
  table_count: 147,
  column_count: 1921,
  jsonb_column_count: 183,
  fk_count: 253,
  vector_table_count: 2,
  module_count: 34,
  uuid_pk_table_count: 144,
  timestamp_table_count: 86,
  domain_count: 5,
  doc_claimed_tables: 107,
  doc_claimed_model_files: 23,
  planned_total: 8,
  planned_now_live: 3,
  live_is_source_of_truth: true,
}

const ACCEPTANCE_SUMMARY = {
  boots: true,
  critical_paths_total: 2,
  launch_blockers_total: 10,
  launch_blockers_cleared: 10,
  launch_ready: true,
  core_areas_total: 6,
  core_areas_green: 6,
  mvp_features_complete: true,
  route_count: 555,
  ai_endpoint_count: 10,
  agent_count: 40,
  table_count: 147,
  mvp_delivered: 40,
  mvp_scope_count: 40,
  phases_shipped: 13,
  phase_count: 14,
}

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
  data_model: DATA_MODEL_SUMMARY,
  acceptance: ACCEPTANCE_SUMMARY,
  provider: 'anthropic',
  surfaces: [
    { key: 'claude-api', title: 'AI agents', spec: '45', blurb: 'The live agent fleet.', path: '/goal/claude-api', stat: 40, stat_label: 'AI agents' },
    { key: 'roadmap', title: 'Build roadmap', spec: '48', blurb: 'Phased path to spec.', path: '/goal/roadmap', stat: '13/14', stat_label: 'phases shipped' },
    { key: 'features', title: 'Feature coverage', spec: '49', blurb: 'Every feature mapped.', path: '/goal/features', stat: 60, stat_label: 'features mapped' },
    { key: 'api', title: 'API contract', spec: '50', blurb: 'Read live from routes.', path: '/goal/api', stat: 553, stat_label: 'live routes' },
    { key: 'data-model', title: 'Data model', spec: '51', blurb: 'Introspected live.', path: '/goal/data-model', stat: 147, stat_label: 'live tables' },
    { key: 'acceptance', title: 'Acceptance & runbook', spec: '52', blurb: 'Definition of done.', path: '/goal/acceptance', stat: '10/10', stat_label: 'launch blockers cleared' },
    { key: 'experience', title: 'Experience standards', spec: '53', blurb: 'The interaction bar.', path: '/goal/experience', stat: 8, stat_label: 'benchmarked surfaces' },
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

const DATA_MODEL: DataModel = {
  summary: DATA_MODEL_SUMMARY,
  conventions: [{ title: 'UUID keys + timestamps', body: 'Almost every table carries a UUID PK.' }],
  domains: [
    {
      key: 'profile',
      title: 'Student identity & profile',
      section: '§2',
      spec: '08',
      blurb: 'The profile is fully relational.',
      table_count: 1,
      modules: ['student'],
      tables: [
        { table: 'student_profiles', module: 'student', spec: '08', note: 'The hub.', column_count: 20, jsonb_count: 2, fk_count: 1, fk_targets: ['users'], is_vector: false, has_uuid_pk: true, has_timestamps: true },
      ],
    },
    {
      key: 'institution',
      title: 'Institution & engagement',
      section: '§5',
      spec: '22',
      blurb: 'The institution stack.',
      table_count: 1,
      modules: ['institution'],
      tables: [
        { table: 'programs', module: 'institution', spec: '23', note: 'JSONB read by exact key.', column_count: 30, jsonb_count: 5, fk_count: 1, fk_targets: ['institutions'], is_vector: false, has_uuid_pk: true, has_timestamps: true },
      ],
    },
  ],
  modules: [{ module: 'institution', table_count: 25, domain: 'institution' }],
  already_built: [{ capability: 'Consent', table: 'student_data_consent', spec: '46 §2', note: 'The 4-lever record.', live: true }],
  planned: [
    { table: 'payments', spec: '39', note: 'Shipped since the doc.', covered_by: '', live: true, covered_by_live: false },
    { table: 'student_follows', spec: '20', note: 'Absent as named.', covered_by: 'institution_follows', live: false, covered_by_live: true },
  ],
  note: 'Introspected live — the source of truth.',
}

const ACCEPTANCE: Acceptance = {
  summary: ACCEPTANCE_SUMMARY,
  levels: [
    { order: 1, key: 'boots', title: 'Boots', status: 'green', body: 'Backend serves; the DB migrates.', evidence: 'Live route table.' },
    { order: 2, key: 'critical_paths', title: 'Critical paths pass', status: 'green', body: 'Two journeys complete.', evidence: 'Every surface is live.' },
    { order: 3, key: 'quality_gates', title: 'Quality gates pass', status: 'green', body: 'No blocker open.', evidence: 'All clear.' },
  ],
  journeys: [
    { key: 'student', title: 'Student journey — Discover → Apply → Decide', actor: 'student', spec: '08–21', blurb: 'Sign-up to decision.', steps: [{ n: 1, title: 'Sign up & land on Discover', spec: '19', detail: 'First-run Discover.' }] },
    { key: 'institution', title: 'Institution journey — Setup → Review → Decide', actor: 'institution_admin', spec: '22–37', blurb: 'Setup to decision.', steps: [{ n: 1, title: 'Sign in', spec: '05', detail: 'To the dashboard.' }] },
  ],
  acceptance_bar: 'Both journeys complete with zero 5xx.',
  dod: [{ text: 'Renders with the correct role guard.', spec: '05' }],
  integration_gates: [{ title: 'api-module parity', body: 'Maps to a real router.', spec: '50 §4' }],
  launch_blockers: [
    { title: 'Europa Typekit loads', spec: '47 G-B1', status: 'cleared', evidence: 'Phase 1 shipped.' },
    { title: 'AI never 5xx', spec: '50 §6', status: 'cleared', evidence: 'Fallback path.' },
  ],
  seed: { intro: 'A clicker needs populated accounts.', items: [{ label: '2 students', detail: 'Mid + fresh.' }] },
  signoff: [
    { area: 'Student: Discover / Match', klass: 'core', path_ref: '2.1', boots: true, critical_path: true, dod: true },
    { area: 'Phase-2 (38–41)', klass: 'excluded', path_ref: '—', boots: false, critical_path: false, dod: false },
  ],
  note: 'Readiness read from the running system.',
}

const UX: UxBenchmark = {
  the_bar: { statement: 'Built to the LinkedIn / Handshake bar.', benchmarks: ['LinkedIn', 'Handshake'] },
  summary: {
    surface_count: 2,
    standard_count: 1,
    acceptance_count: 1,
    benchmarks: ['LinkedIn', 'Handshake'],
    benchmark_keys: ['handshake', 'linkedin'],
    backed_route_total: 12,
    surfaces_backed: 2,
  },
  surfaces: [
    { key: 'profile', name: 'Profile', specs: ['08'], files: ['student/ProfilePage.tsx'], benchmark: 'LinkedIn profile', benchmark_key: 'linkedin', build_contract: ['Inline-edit per section'], backed_route_count: 7, sample_paths: ['/api/v1/students/me/profile'] },
    { key: 'match', name: 'Match / Explore', specs: ['09', '10'], files: ['student/ExplorePage.tsx'], benchmark: 'Handshake search', benchmark_key: 'handshake', build_contract: ['Typeahead'], backed_route_count: 5, sample_paths: ['/api/v1/students/me/matches'] },
  ],
  standards: [{ title: 'Optimistic UI', body: 'Apply instantly.', mechanism: '54 §4' }],
  empty_state: {
    rule: 'Instructional empty states, never a generic no-data.',
    first_run: [
      { side: 'student', to: 'Discover chat', file: 'student/DiscoverHomePage.tsx' },
      { side: 'institution', to: 'Setup wizard', file: 'institution/SetupPage.tsx' },
    ],
  },
  acceptance: ['Every mutation optimistic or ≤1 skeleton.'],
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

  it('hub renders the live stats and links to all seven surfaces', async () => {
    vi.spyOn(buildApi, 'getBuildOverview').mockResolvedValue(OVERVIEW)
    renderPage(<GoalHubPage />)

    expect(screen.getByText(/How UniPaith is built — in the open/i)).toBeInTheDocument()
    await waitFor(() => expect(screen.getByText('Build roadmap')).toBeInTheDocument())
    expect(screen.getByText('Feature coverage')).toBeInTheDocument()
    expect(screen.getByText('API contract')).toBeInTheDocument()
    // The new surfaces (specs 51 + 52 + 53) appear.
    expect(screen.getByText('Data model')).toBeInTheDocument()
    expect(screen.getByText('Acceptance & runbook')).toBeInTheDocument()
    expect(screen.getByText('Experience standards')).toBeInTheDocument()
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

  it('data model renders the live table map, the doc drift and filters by domain', async () => {
    vi.spyOn(buildApi, 'getDataModel').mockResolvedValue(DATA_MODEL)
    renderPage(<DataModelPage />, '/goal/data-model')

    await waitFor(() => expect(screen.getByText('student_profiles')).toBeInTheDocument())
    expect(screen.getByText('programs')).toBeInTheDocument()
    // The "can't drift" gold beat + the 107→live correction.
    expect(screen.getByText(/Introspected live — can't drift/i)).toBeInTheDocument()
    expect(screen.getAllByText(/107 tables/i).length).toBeGreaterThan(0)
    // §8 'payments' shipped since the doc → "Now live".
    expect(screen.getByText('payments')).toBeInTheDocument()
    expect(screen.getAllByText(/Now live/i).length).toBeGreaterThan(0)

    // Filter to the institution domain → student_profiles drops out.
    fireEvent.click(screen.getByRole('button', { name: 'Institution & engagement' }))
    await waitFor(() => expect(screen.queryByText('student_profiles')).not.toBeInTheDocument())
    expect(screen.getByText('programs')).toBeInTheDocument()
  })

  it('acceptance renders the readiness levels, journeys and launch blockers', async () => {
    vi.spyOn(buildApi, 'getAcceptance').mockResolvedValue(ACCEPTANCE)
    renderPage(<AcceptancePage />, '/goal/acceptance')

    await waitFor(() =>
      expect(screen.getByText(/Student journey — Discover/i)).toBeInTheDocument(),
    )
    expect(screen.getByText(/Institution journey — Setup/i)).toBeInTheDocument()
    // 'Boots' renders as a level title and as a sign-off matrix column header.
    expect(screen.getAllByText('Boots').length).toBeGreaterThan(0)
    // A launch blocker + its cleared chip.
    expect(screen.getByText('AI never 5xx')).toBeInTheDocument()
    expect(screen.getAllByText('Cleared').length).toBeGreaterThan(0)
    // The MVP-ready gold beat shows when launch_ready is true.
    expect(screen.getByText(/MVP-ready — all gates clear/i)).toBeInTheDocument()
    // The sign-off matrix row.
    expect(screen.getByText('Student: Discover / Match')).toBeInTheDocument()
  })

  it('experience page renders surfaces + standards and filters by benchmark', async () => {
    vi.spyOn(buildApi, 'getUxBenchmark').mockResolvedValue(UX)
    renderPage(<ExperienceStandardsPage />, '/goal/experience')

    await waitFor(() => expect(screen.getByText('Profile')).toBeInTheDocument())
    expect(screen.getByText('Match / Explore')).toBeInTheDocument()
    // §3 standard + §5 acceptance render.
    expect(screen.getByText('Optimistic UI')).toBeInTheDocument()
    expect(screen.getByText(/Every mutation optimistic/i)).toBeInTheDocument()
    // The live-route backing beat (read from the running system) shows.
    expect(screen.getByText(/12 live routes back these surfaces/i)).toBeInTheDocument()

    // Filter to Handshake → the LinkedIn-benchmarked Profile drops out.
    fireEvent.click(screen.getByRole('button', { name: 'Handshake' }))
    await waitFor(() => expect(screen.queryByText('Profile')).not.toBeInTheDocument())
    expect(screen.getByText('Match / Explore')).toBeInTheDocument()
  })
})
