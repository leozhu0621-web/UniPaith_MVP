// Specs 48–53 — types for the public build-transparency surface.
// Mirror unipaith-backend/src/unipaith/transparency/*.py and api/build.py
// field-for-field.

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
  data_model: DataModelSummary
  acceptance: AcceptanceSummary
  production: ProductionSummary
  search: SearchBuildSummary
  knowledge: KnowledgeBuildSummary
  chatbot_eval: ChatbotEvalSummary
  provider: string
  surfaces: OverviewSurface[]
}

// ── Data model (spec 51) ────────────────────────────────────────────────────
export interface DataModelSummary {
  table_count: number
  column_count: number
  jsonb_column_count: number
  fk_count: number
  vector_table_count: number
  module_count: number
  uuid_pk_table_count: number
  timestamp_table_count: number
  domain_count: number
  doc_claimed_tables: number
  doc_claimed_model_files: number
  planned_total: number
  planned_now_live: number
  live_is_source_of_truth: boolean
}

export interface DataModelTable {
  table: string
  module: string
  spec: string
  note: string
  column_count: number
  jsonb_count: number
  fk_count: number
  fk_targets: string[]
  is_vector: boolean
  has_uuid_pk: boolean
  has_timestamps: boolean
}

export interface DataModelDomain {
  key: string
  title: string
  section: string
  spec: string
  blurb: string
  table_count: number
  modules: string[]
  tables: DataModelTable[]
}

export interface DataModelModule {
  module: string
  table_count: number
  domain: string
}

export interface AlreadyBuiltItem {
  capability: string
  table: string
  spec: string
  note: string
  live: boolean
}

export interface PlannedTableItem {
  table: string
  spec: string
  note: string
  covered_by: string
  live: boolean
  covered_by_live: boolean
}

export interface DataModel {
  summary: DataModelSummary
  conventions: ContractConvention[]
  domains: DataModelDomain[]
  modules: DataModelModule[]
  already_built: AlreadyBuiltItem[]
  planned: PlannedTableItem[]
  note: string
}

// ── Acceptance & runbook (spec 52) ──────────────────────────────────────────
export interface AcceptanceSummary {
  boots: boolean
  critical_paths_total: number
  launch_blockers_total: number
  launch_blockers_cleared: number
  launch_ready: boolean
  core_areas_total: number
  core_areas_green: number
  mvp_features_complete: boolean
  route_count: number
  ai_endpoint_count: number
  agent_count: number
  table_count: number
  mvp_delivered: number
  mvp_scope_count: number
  phases_shipped: number
  phase_count: number
}

export interface AcceptanceLevel {
  order: number
  key: string
  title: string
  status: 'green' | 'amber' | 'red'
  body: string
  evidence: string
}

export interface JourneyStep {
  n: number
  title: string
  spec: string
  detail: string
}

export interface AcceptanceJourney {
  key: string
  title: string
  actor: string
  spec: string
  blurb: string
  steps: JourneyStep[]
}

export interface DodItem {
  text: string
  spec: string
}

export interface IntegrationGate {
  title: string
  body: string
  spec: string
}

export interface LaunchBlocker {
  title: string
  spec: string
  status: 'cleared' | 'deferred'
  evidence: string
}

export interface SeedItem {
  label: string
  detail: string
}

export interface AcceptanceSeed {
  intro: string
  items: SeedItem[]
}

export interface SignoffArea {
  area: string
  klass: 'core' | 'extend' | 'excluded'
  path_ref: string
  boots: boolean
  critical_path: boolean
  dod: boolean
}

export interface Acceptance {
  summary: AcceptanceSummary
  levels: AcceptanceLevel[]
  journeys: AcceptanceJourney[]
  acceptance_bar: string
  dod: DodItem[]
  integration_gates: IntegrationGate[]
  launch_blockers: LaunchBlocker[]
  seed: AcceptanceSeed
  signoff: SignoffArea[]
  note: string
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

// ── Frontend engineering standards (spec 54) ─────────────────────────────────
export type BuildTaskStatus = 'done' | 'partial' | 'planned'

export interface FrontendStandardsSummary {
  live_router_count: number // resolved live from the running route table
  live_route_count: number
  doc_claimed_api_modules: number
  doc_claimed_routers: number
  doc_claimed_stores: number
  doc_claimed_hooks: number
  state_rule_count: number
  build_task_count: number
  build_tasks_done: number
  build_tasks_partial: number
  build_tasks_planned: number
  perf_budget_count: number
  acceptance_count: number
  live_is_source_of_truth: boolean
}

export interface StateRule {
  kind: string
  tool: string
  where: string
  rule: string
}

export interface QueryKeyConvention {
  rule: string
  example: string
  stale_time: string
}

export interface MutationConvention {
  shape: string
  rule: string
  surfaces: string[]
}

export interface ApiRouterParity {
  statement: string
  live_router_count: number
  live_route_count: number
  doc_claimed_api_modules: number
  doc_claimed_routers: number
}

export interface ErrorHandling {
  interceptor: string
  ai_fallback: string
}

export interface PerfBudget {
  metric: string
  target: string
  note: string
}

export interface RealtimeContract {
  summary: string
  transports: string[]
  status: string
}

export interface AnalyticsContract {
  summary: string
  rules: string[]
}

export interface FrontendBuildTask {
  key: string
  title: string
  status: BuildTaskStatus
  evidence: string
  artifact: string | null // a src/ path the page confirms live via import.meta.glob
  fe_verifiable: boolean
}

export interface FrontendOpenQuestion {
  question: string
  recommendation: string
}

export interface FrontendStandards {
  summary: FrontendStandardsSummary
  the_standard: string
  state_rules: StateRule[]
  state_build_rule: string
  query_key: QueryKeyConvention
  mutation: MutationConvention
  parity: ApiRouterParity
  routing: string[]
  error_handling: ErrorHandling
  perf_budgets: PerfBudget[]
  perf_tactics: string[]
  realtime: RealtimeContract
  analytics: AnalyticsContract
  testing: string[]
  build_tasks: FrontendBuildTask[]
  acceptance: string[]
  open_questions: FrontendOpenQuestion[]
}

// ── Production readiness (spec 55) ──────────────────────────────────────────
export type ReadinessStatus = 'live' | 'partial' | 'planned'

export interface ProductionPillar {
  key: string
  title: string
  section: string // spec 55 section, e.g. "§2"
  status: ReadinessStatus
  blurb: string
  built: string[]
  planned: string[]
}

export interface ConfigKnob {
  name: string
  value: string | number | boolean
}

export interface ConfigGroup {
  key: string
  title: string
  section: string
  knobs: ConfigKnob[]
}

export interface SchedulerJob {
  id: string
  name: string
  cadence: string
}

export interface ProductionBuildTask {
  section: string
  status: ReadinessStatus
  text: string
  evidence: string
}

export interface Slo {
  metric: string
  target: string
  note: string
}

export interface OpenQuestion {
  q: string
  a: string
}

export interface ProductionTheBar {
  statement: string
  slo_headline: string
}

export interface CacheStats {
  backend: string
  enabled: boolean
  entries: number
  hits: number
  misses: number
  evictions: number
  lookups: number
  hit_rate: number
  default_ttl_s: number
  distributed_ready: boolean
  distributed_configured: boolean
}

export interface ProductionSummary {
  pillar_count: number
  pillars_live: number
  pillars_partial: number
  pillars_planned: number
  build_task_count: number
  tasks_live: number
  tasks_partial: number
  tasks_planned: number
  health_route_count: number
  middleware_count: number
  config_group_count: number
  config_knob_count: number
  scheduler_job_count: number
  scheduler_running: boolean
  scheduler_live_jobs: number
  slo_count: number
  open_question_count: number
  cache_hit_rate: number
  cache_backend: string
  cache_entries: number
  cache_lookups: number
  live_is_source_of_truth: boolean
}

export interface Production {
  the_bar: ProductionTheBar
  summary: ProductionSummary
  pillars: ProductionPillar[]
  config_groups: ConfigGroup[]
  middleware: { count: number; classes: string[] }
  scheduler: { running: boolean; jobs: SchedulerJob[] }
  health_probes: { paths: string[]; count: number; note: string }
  cache: CacheStats
  build_tasks: ProductionBuildTask[]
  slos: Slo[]
  open_questions: OpenQuestion[]
}

// ── Search, feed & recommendations (spec 56) ────────────────────────────────
export interface SearchCapability {
  key: string
  title: string
  section: string // spec 56 section, e.g. "§2"
  status: ReadinessStatus
  blurb: string
  built: string[]
  planned: string[]
}

export interface SearchConfigKnob {
  name: string
  value: string | number | boolean
  section: string
}

export interface SearchBuildTask {
  section: string
  status: ReadinessStatus
  text: string
  evidence: string
}

export interface SearchAcceptanceItem {
  status: ReadinessStatus
  text: string
}

export interface SearchTheBar {
  statement: string
  principle: string
}

export interface SearchRoutes {
  search: string[]
  feed: string[]
  saved_search: string[]
  events: string[]
}

export interface SearchBuildSummary {
  capability_count: number
  capabilities_live: number
  capabilities_partial: number
  capabilities_planned: number
  build_task_count: number
  tasks_live: number
  tasks_partial: number
  tasks_planned: number
  acceptance_count: number
  acceptance_live: number
  search_route_count: number
  feed_route_count: number
  saved_search_route_count: number
  backing_route_count: number
  saved_searches_table_present: boolean
  config_knob_count: number
  open_question_count: number
  live_is_source_of_truth: boolean
}

export interface SearchBuild {
  the_bar: SearchTheBar
  summary: SearchBuildSummary
  capabilities: SearchCapability[]
  build_tasks: SearchBuildTask[]
  acceptance: SearchAcceptanceItem[]
  config_knobs: SearchConfigKnob[]
  routes: SearchRoutes
  saved_searches_table_present: boolean
  open_questions: OpenQuestion[]
}

// ── Knowledge engine / data crawler (spec 60) ───────────────────────────────
export interface KnowledgeBenchmark {
  dimension: string
  kollegio: string
  gap: string
  unipaith: string
}

export interface KnowledgeRefDomain {
  key: string
  title: string
  section: string
  table: string
  sources: string
  feeds: string
  table_present: boolean
}

export interface KnowledgeStage {
  n: number
  name: string
  detail: string
}

export interface KnowledgeChangeType {
  type: string
  materiality: string
  routes_to: string
}

export interface KnowledgeAuthorityRung {
  rank: number
  source: string
  note: string
}

export interface KnowledgeCapability {
  key: string
  title: string
  section: string
  status: ReadinessStatus
  blurb: string
  built: string[]
  planned: string[]
}

export interface KnowledgePhase {
  key: string
  title: string
  status: ReadinessStatus
  detail: string
}

export interface KnowledgeAcceptanceItem {
  status: ReadinessStatus
  text: string
}

export interface KnowledgeConfigKnob {
  name: string
  value: string | number | boolean
  section: string
}

export interface KnowledgeRoutes {
  reference: string[]
  crawler_ops: string[]
  enrichment: string[]
}

export interface KnowledgeBuildSummary {
  capability_count: number
  capabilities_live: number
  capabilities_partial: number
  capabilities_planned: number
  acceptance_count: number
  acceptance_live: number
  acceptance_partial: number
  reference_domain_count: number
  registered_source_count: number
  reference_tables_present: number
  engine_tables_present: number
  pipeline_stage_count: number
  change_event_type_count: number
  reference_route_count: number
  ops_route_count: number
  backing_route_count: number
  config_knob_count: number
  open_question_count: number
  live_is_source_of_truth: boolean
}

export interface KnowledgeBuild {
  the_bar: SearchTheBar
  summary: KnowledgeBuildSummary
  benchmark: KnowledgeBenchmark[]
  reference_graph: KnowledgeRefDomain[]
  pipeline: KnowledgeStage[]
  change_event_types: KnowledgeChangeType[]
  authority_ladder: KnowledgeAuthorityRung[]
  capabilities: KnowledgeCapability[]
  phases: KnowledgePhase[]
  acceptance: KnowledgeAcceptanceItem[]
  config_knobs: KnowledgeConfigKnob[]
  routes: KnowledgeRoutes
  reference_domains: string[]
  open_questions: OpenQuestion[]
}

// ── Chatbot training & evaluation (spec 61) ─────────────────────────────────
export interface ChatbotEvalSummary {
  agent_count: number
  constitution_count: number
  constitutions_present: boolean
  constitution_version: string | null
  dimension_count: number
  hard_floor_count: number
  suite_count: number
  suites_live: number
  hard_floor_suite_count: number
  golden_case_total: number
  deterministic_check_count: number
  loop_stage_count: number
  loop_stages_live: number
  build_task_count: number
  tasks_live: number
  tasks_partial: number
  tasks_planned: number
  acceptance_count: number
  acceptance_live: number
  safety_crisis_subtype_count: number
  safety_harmful_subtype_count: number
  backing_route_count: number
  config_knob_count: number
  open_question_count: number
  provider: string
  all_agents_claude: boolean
  live_is_source_of_truth: boolean
}

export interface ChatbotConstitutionDimension {
  key: string
  label: string
  hard_floor: boolean
  summary: string
}

export interface ChatbotConstitution {
  agent: string
  present: boolean
  version?: string
  dimension_count?: number
  hard_floor_keys?: string[]
  dimensions?: ChatbotConstitutionDimension[]
}

export interface ChatbotAgent {
  key: string
  title: string
  spec: string
  file: string
  surface: string
  agent_name: string
  tier: string
  provider: string
  role: string
  blurb: string
}

export interface ChatbotLoopStage {
  n: number
  key: string
  title: string
  blurb: string
  status: ReadinessStatus
}

export interface ChatbotEvalSuite {
  key: string
  title: string
  section: string
  status: ReadinessStatus
  hard_floor: boolean
  blurb: string
  case_count: number
  in_runner: boolean
}

export interface ChatbotSafety {
  always_on: boolean
  status: ReadinessStatus
  crisis_subtypes: string[]
  harmful_subtypes: string[]
  crisis_pattern_count: number
  harmful_pattern_count: number
  note: string
}

export interface ChatbotDeterministicCheck {
  name: string
  blurb: string
}

export interface ChatbotBuildTask {
  section: string
  status: ReadinessStatus
  text: string
  evidence: string
}

export interface ChatbotAcceptanceItem {
  status: ReadinessStatus
  text: string
}

export interface ChatbotConfigKnob {
  name: string
  value: string | number | boolean
  section: string
}

export interface ChatbotEvalRoutes {
  discovery: string[]
  institution_reply: string[]
}

export interface ChatbotTheBar {
  statement: string
  principle: string
}

export interface ChatbotEval {
  the_bar: ChatbotTheBar
  summary: ChatbotEvalSummary
  constitutions: ChatbotConstitution[]
  agents: ChatbotAgent[]
  loop_stages: ChatbotLoopStage[]
  eval_suites: ChatbotEvalSuite[]
  safety: ChatbotSafety
  deterministic_checks: ChatbotDeterministicCheck[]
  build_tasks: ChatbotBuildTask[]
  acceptance: ChatbotAcceptanceItem[]
  config_knobs: ChatbotConfigKnob[]
  routes: ChatbotEvalRoutes
  open_questions: OpenQuestion[]
}
