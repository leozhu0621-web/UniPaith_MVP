// Spec 48/49/50/53 — types for the public build-transparency surface.
// Mirror unipaith-backend/src/unipaith/transparency/{roadmap,features,api_contract,ux_benchmark}.py
// and api/build.py field-for-field.

// ── Roadmap (spec 48) ───────────────────────────────────────────────────────
export type PhaseStatus = 'shipped' | 'deferred'

export interface RoadmapPhase {
  number: number
  title: string
  goal: string
  specs: string[]
  gap_items: string[]
  effort: string
  workstream: string
  status: PhaseStatus
  status_label: string
  evidence: string
  done_when: string
}

export interface RoadmapSummary {
  phase_count: number
  shipped: number
  deferred: number
  mvp_complete: boolean
}

export interface Roadmap {
  summary: RoadmapSummary
  phases: RoadmapPhase[]
  workstreams: string[]
}

// ── Features (spec 49) ──────────────────────────────────────────────────────
export type FeatureStatus = 'covered' | 'written' | 'net_new'
export type FeatureKlass = 'core' | 'extend' | 'defer'

export interface FeatureItem {
  name: string
  side: 'student' | 'institution'
  status: FeatureStatus
  status_label: string
  spec: string
  klass: FeatureKlass
  klass_label: string
  delivered: boolean
  note: string
}

export interface FeatureSummary {
  feature_count: number
  student_count: number
  institution_count: number
  delivered: number
  klass_counts: Record<string, number>
  mvp_scope_count: number
  mvp_delivered: number
  mvp_complete: boolean
  ahead_of_plan: number
}

export interface FeatureCatalog {
  summary: FeatureSummary
  features: FeatureItem[]
}

// ── API contract (spec 50) ──────────────────────────────────────────────────
export interface ContractConvention {
  title: string
  body: string
}

export interface StatusCode {
  code: string
  when: string
  frontend: string
}

export interface RouterGroup {
  tag: string
  route_count: number
  methods: Record<string, number>
  role: string
  access: string
  sample_paths: string[]
}

export interface ApiContractSummary {
  route_count: number
  router_count: number
  public_route_count: number
  authenticated_route_count: number
  ai_endpoint_count: number
  method_totals: Record<string, number>
  prefix: string
  doc_claimed_routers: number
  doc_claimed_routes: number
  live_is_source_of_truth: boolean
}

export interface ApiContract {
  summary: ApiContractSummary
  conventions: ContractConvention[]
  status_taxonomy: StatusCode[]
  groups: RouterGroup[]
  ai_endpoints: string[]
  access_note: string
}

// ── Overview / hub ──────────────────────────────────────────────────────────
export interface OverviewSurface {
  key: string
  title: string
  spec: string
  blurb: string
  path: string
  stat: string | number
  stat_label: string
}

export interface AgentsSummary {
  agent_count: number
  llm_agent_count: number
  fallback_coverage: string
  provider: string
  tier_counts: Record<string, number>
}

export interface BuildOverview {
  roadmap: RoadmapSummary
  features: FeatureSummary
  api: ApiContractSummary
  agents: AgentsSummary
  provider: string
  surfaces: OverviewSurface[]
}

// ── UX benchmark / interaction standards (spec 53) ──────────────────────────
export interface UxSurface {
  key: string
  name: string
  specs: string[]
  files: string[]
  benchmark: string
  benchmark_key: string // linkedin | handshake | chatgpt | ats
  build_contract: string[]
  backed_route_count: number // resolved live from the running route table
  sample_paths: string[]
}

export interface InteractionStandard {
  title: string
  body: string
  mechanism: string // the 54 / 56 / 57 mechanism it maps to
}

export interface EmptyStateFirstRun {
  side: string
  to: string
  file: string
}

export interface EmptyStatePolicy {
  rule: string
  first_run: EmptyStateFirstRun[]
}

export interface UxTheBar {
  statement: string
  benchmarks: string[]
}

export interface UxBenchmarkSummary {
  surface_count: number
  standard_count: number
  acceptance_count: number
  benchmarks: string[]
  benchmark_keys: string[]
  backed_route_total: number
  surfaces_backed: number
}

export interface UxBenchmark {
  the_bar: UxTheBar
  summary: UxBenchmarkSummary
  surfaces: UxSurface[]
  standards: InteractionStandard[]
  empty_state: EmptyStatePolicy
  acceptance: string[]
}
