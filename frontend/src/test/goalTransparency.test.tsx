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
import ProductionReadinessPage from '../pages/public/ProductionReadinessPage'
import SearchFeedRecsPage from '../pages/public/SearchFeedRecsPage'
import KnowledgeEnginePage from '../pages/public/KnowledgeEnginePage'
import SecurityTrustPage from '../pages/public/SecurityTrustPage'
import * as buildApi from '../api/build'
import type {
  Acceptance,
  ApiContract,
  BuildOverview,
  ChatbotEvalSummary,
  DataModel,
  FeatureCatalog,
  KnowledgeBuild,
  Production,
  ProductionSummary,
  Roadmap,
  SearchBuild,
  SearchBuildSummary,
  SecuritySummary,
  SecurityTrust,
  RealtimeBuildSummary,
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

const PRODUCTION_SUMMARY: ProductionSummary = {
  pillar_count: 7,
  pillars_live: 3,
  pillars_partial: 4,
  pillars_planned: 0,
  build_task_count: 9,
  tasks_live: 2,
  tasks_partial: 4,
  tasks_planned: 3,
  health_route_count: 2,
  middleware_count: 4,
  config_group_count: 6,
  config_knob_count: 18,
  scheduler_job_count: 4,
  scheduler_running: false,
  scheduler_live_jobs: 0,
  slo_count: 5,
  open_question_count: 3,
  cache_hit_rate: 0.5,
  cache_backend: 'memory',
  cache_entries: 1,
  cache_lookups: 2,
  live_is_source_of_truth: true,
}

const SEARCH_SUMMARY: SearchBuildSummary = {
  capability_count: 8,
  capabilities_live: 4,
  capabilities_partial: 2,
  capabilities_planned: 2,
  build_task_count: 7,
  tasks_live: 2,
  tasks_partial: 3,
  tasks_planned: 2,
  acceptance_count: 5,
  acceptance_live: 1,
  search_route_count: 8,
  feed_route_count: 12,
  saved_search_route_count: 3,
  backing_route_count: 33,
  saved_searches_table_present: true,
  config_knob_count: 6,
  open_question_count: 3,
  live_is_source_of_truth: true,
}

const KNOWLEDGE_SUMMARY = {
  capability_count: 11,
  capabilities_live: 9,
  capabilities_partial: 1,
  capabilities_planned: 1,
  acceptance_count: 9,
  acceptance_live: 9,
  acceptance_partial: 0,
  reference_domain_count: 8,
  registered_source_count: 16,
  reference_tables_present: 9,
  engine_tables_present: 4,
  pipeline_stage_count: 7,
  change_event_type_count: 8,
  reference_route_count: 9,
  ops_route_count: 7,
  backing_route_count: 19,
  config_knob_count: 8,
  open_question_count: 6,
  live_is_source_of_truth: true,
}

const SECURITY_SUMMARY: SecuritySummary = {
  control_count: 13,
  controls_live: 7,
  controls_partial: 4,
  controls_planned: 2,
  build_task_count: 10,
  tasks_live: 2,
  tasks_partial: 5,
  tasks_planned: 3,
  acceptance_count: 6,
  acceptance_live: 2,
  consent_agent_count: 36,
  consent_lever_count: 4,
  consent_default_permissive: true,
  redaction_map_size: 26,
  pii_field_count: 18,
  pii_class_count: 4,
  pii_encryption_target_count: 9,
  security_header_count: 5,
  cors_allowlist_size: 2,
  environment: 'development',
  cognito_bypass: true,
  auth_bypass_safe: true,
  prod_bypass_guarded: true,
  compliance_count: 8,
  open_question_count: 3,
  live_is_source_of_truth: true,
}

const REALTIME_SUMMARY: RealtimeBuildSummary = {
  capability_count: 9,
  capabilities_live: 6,
  capabilities_partial: 3,
  capabilities_planned: 0,
  build_task_count: 9,
  tasks_live: 6,
  tasks_partial: 3,
  tasks_planned: 0,
  acceptance_count: 6,
  acceptance_live: 6,
  sse_route_count: 1,
  ws_route_count: 1,
  notification_route_count: 6,
  backing_route_count: 8,
  event_type_count: 16,
  broker_backend: 'memory',
  distributed_ready: false,
  notifications_table_present: true,
  idempotency_wired: true,
  config_knob_count: 6,
  open_question_count: 3,
  live_is_source_of_truth: true,
}

const CHATBOT_EVAL_SUMMARY: ChatbotEvalSummary = {
  agent_count: 2,
  constitution_count: 2,
  constitutions_present: true,
  constitution_version: '1.0.0',
  dimension_count: 7,
  hard_floor_count: 1,
  suite_count: 4,
  suites_live: 4,
  hard_floor_suite_count: 2,
  golden_case_total: 44,
  deterministic_check_count: 5,
  loop_stage_count: 8,
  loop_stages_live: 3,
  build_task_count: 8,
  tasks_live: 5,
  tasks_partial: 3,
  tasks_planned: 0,
  acceptance_count: 6,
  acceptance_live: 4,
  safety_crisis_subtype_count: 3,
  safety_harmful_subtype_count: 4,
  backing_route_count: 19,
  config_knob_count: 4,
  open_question_count: 3,
  provider: 'anthropic',
  all_agents_claude: true,
  live_is_source_of_truth: true,
}

const EVAL_HARNESS_SUMMARY = {
  consumer_count: 3,
  consumers_live: 2,
  consumers_planned: 1,
  golden_case_total: 19,
  dimension_total: 11,
  hard_floor_dimension_count: 2,
  deterministic_check_total: 7,
  independent_judge_count: 1,
  judge_target_agreement: 0.85,
  suite_count: 2,
  suites_in_runner: 2,
  eval_mode_count: 4,
  modes_live: 1,
  new_table_count: 2,
  new_tables_present: 2,
  reused_table_count: 4,
  phase_count: 4,
  phases_live: 2,
  acceptance_count: 7,
  acceptance_live: 3,
  slo_count: 4,
  cost_control_count: 5,
  open_question_count: 4,
  backing_route_count: 26,
  config_knob_count: 3,
  provider: 'anthropic',
  live_is_source_of_truth: true,
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
  production: PRODUCTION_SUMMARY,
  search: SEARCH_SUMMARY,
  knowledge: KNOWLEDGE_SUMMARY,
  realtime: REALTIME_SUMMARY,
  chatbot_eval: CHATBOT_EVAL_SUMMARY,
  eval_harness: EVAL_HARNESS_SUMMARY,
  security: SECURITY_SUMMARY,
  provider: 'anthropic',
  surfaces: [
    { key: 'claude-api', title: 'AI agents', spec: '45', blurb: 'The live agent fleet.', path: '/goal/claude-api', stat: 40, stat_label: 'AI agents' },
    { key: 'roadmap', title: 'Build roadmap', spec: '48', blurb: 'Phased path to spec.', path: '/goal/roadmap', stat: '13/14', stat_label: 'phases shipped' },
    { key: 'features', title: 'Feature coverage', spec: '49', blurb: 'Every feature mapped.', path: '/goal/features', stat: 60, stat_label: 'features mapped' },
    { key: 'api', title: 'API contract', spec: '50', blurb: 'Read live from routes.', path: '/goal/api', stat: 553, stat_label: 'live routes' },
    { key: 'data-model', title: 'Data model', spec: '51', blurb: 'Introspected live.', path: '/goal/data-model', stat: 147, stat_label: 'live tables' },
    { key: 'acceptance', title: 'Acceptance & runbook', spec: '52', blurb: 'Definition of done.', path: '/goal/acceptance', stat: '10/10', stat_label: 'launch blockers cleared' },
    { key: 'experience', title: 'Experience standards', spec: '53', blurb: 'The interaction bar.', path: '/goal/experience', stat: 8, stat_label: 'benchmarked surfaces' },
    { key: 'frontend', title: 'Frontend engineering', spec: '54', blurb: 'The React build spec.', path: '/goal/frontend', stat: '6/10', stat_label: 'build tasks complete' },
    { key: 'backend', title: 'Production readiness', spec: '55', blurb: 'The backend hardening posture.', path: '/goal/backend', stat: 7, stat_label: 'readiness pillars' },
    { key: 'search', title: 'Search, feed & recs', spec: '56', blurb: 'The discovery substrate.', path: '/goal/search', stat: '4/8', stat_label: 'capabilities live' },
    { key: 'knowledge', title: 'Knowledge engine', spec: '60', blurb: 'The world-side knowledge graph.', path: '/goal/knowledge', stat: 16, stat_label: 'allowlisted sources' },
    { key: 'realtime', title: 'Realtime & notifications', spec: '57', blurb: 'Live SSE + WebSocket.', path: '/goal/realtime', stat: 16, stat_label: 'notification events' },
    { key: 'chatbot-eval', title: 'Chatbot training & eval', spec: '61', blurb: 'How the chatbot is measured.', path: '/goal/chatbot-eval', stat: 44, stat_label: 'graded eval cases' },
    { key: 'eval-harness', title: 'Evaluation harness', spec: '62', blurb: 'One shared eval harness.', path: '/goal/eval-harness', stat: 2, stat_label: 'consumers live' },
    { key: 'security', title: 'Security & trust', spec: '58', blurb: 'The security posture.', path: '/goal/security', stat: '7/13', stat_label: 'controls live' },
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

const PRODUCTION: Production = {
  the_bar: {
    statement: 'A backend is production-grade when it stays up, stays honest, and stays fast.',
    slo_headline: 'p95 < 400ms (non-AI) · < 2.5s (AI cached) · errors < 0.5% · uptime ≥ 99%',
  },
  summary: PRODUCTION_SUMMARY,
  pillars: [
    {
      key: 'observability',
      title: 'Observability',
      section: '§2',
      status: 'partial',
      blurb: 'The biggest real gap — now wired at the request layer.',
      built: ['Structured JSON logs', 'Request-id contextvar'],
      planned: ['/metrics via prometheus', 'OpenTelemetry tracing'],
    },
    {
      key: 'health',
      title: 'Health, deploy & SLOs',
      section: '§8',
      status: 'live',
      blurb: 'Liveness + readiness probes; migration-before-serve.',
      built: ['/health liveness', '/ready readiness'],
      planned: ['Graceful drain'],
    },
  ],
  config_groups: [
    {
      key: 'pool',
      title: 'Connection pool',
      section: '§7',
      knobs: [
        { name: 'db_pool_size', value: 30 },
        { name: 'rate_limit_enabled', value: true },
      ],
    },
  ],
  middleware: { count: 4, classes: ['observability_middleware', 'CORSMiddleware'] },
  scheduler: {
    running: false,
    jobs: [{ id: 'feature_refresh', name: 'Daily feature refresh', cadence: '24h' }],
  },
  health_probes: {
    paths: ['/api/v1/health', '/api/v1/ready'],
    count: 2,
    note: 'Liveness is DB-free; readiness checks the DB.',
  },
  cache: {
    backend: 'memory',
    enabled: true,
    entries: 1,
    hits: 1,
    misses: 1,
    evictions: 0,
    lookups: 2,
    hit_rate: 0.5,
    default_ttl_s: 60,
    distributed_ready: false,
    distributed_configured: false,
  },
  build_tasks: [
    {
      section: '§8',
      status: 'live',
      text: '/health + /ready; migration-before-serve entrypoint',
      evidence: 'Probes are live and route-backed.',
    },
    {
      section: '§7',
      status: 'planned',
      text: 'Index migration; PgBouncer; N+1 tests',
      evidence: 'Pool is live; the index audit is planned.',
    },
  ],
  slos: [{ metric: 'API latency p95 (non-AI)', target: '< 400 ms', note: 'Off the AI stack.' }],
  open_questions: [{ q: 'Queue engine', a: 'arq — async-native, Redis-backed.' }],
}

const SEARCH_BUILD: SearchBuild = {
  the_bar: {
    statement: 'Discovery is good when a student can describe what they want.',
    principle: 'Built on the real substrate that already exists.',
  },
  summary: SEARCH_SUMMARY,
  capabilities: [
    {
      key: 'fts',
      title: 'Full-text search',
      section: '§2',
      status: 'live',
      blurb: 'Postgres FTS over programs.',
      built: ['tsvector + plainto_tsquery', 'Constraint chips → filters'],
      planned: ['pg_trgm fuzzy ranking'],
    },
    {
      key: 'saved_search',
      title: 'Saved searches + alerts',
      section: '§6',
      status: 'live',
      blurb: 'The net-new build — save a search; it keeps watching.',
      built: ['saved_searches table + model', 'Scheduled alert loop'],
      planned: ['Scholarship / school entity search'],
    },
    {
      key: 'hybrid',
      title: 'Hybrid semantic fusion',
      section: '§2B',
      status: 'planned',
      blurb: 'Semantic recall fused with keyword precision.',
      built: ['Reranker scaffold'],
      planned: ['Qwen embeddings + pgvector ANN', 'Reciprocal-rank fusion'],
    },
  ],
  build_tasks: [
    {
      section: '§8',
      status: 'live',
      text: 'saved_searches table/model/service + alert job + endpoints + caps',
      evidence: 'Built here: model + migration + service + API + scheduler loop.',
    },
    {
      section: '§8',
      status: 'planned',
      text: 'Hybrid fusion (pgvector + keyword RRF) + reranker → Qwen3-Reranker',
      evidence: 'Reranker scaffold exists; embeddings depend on 63.',
    },
  ],
  acceptance: [
    { status: 'live', text: 'Saved searches fire alerts via 57, consent + cap respected.' },
    { status: 'planned', text: 'Ranking changes A/B-gated via 62.' },
  ],
  config_knobs: [
    { name: 'saved_search_alerts_enabled', value: true, section: '§6' },
    { name: 'saved_search_alert_cap_per_day', value: 5, section: '§6' },
  ],
  routes: {
    search: ['/api/v1/students/me/search/programs'],
    feed: ['/api/v1/connect/feed'],
    saved_search: ['/api/v1/students/me/saved-searches'],
    events: ['/api/v1/events'],
  },
  saved_searches_table_present: true,
  open_questions: [{ q: 'OpenSearch trigger threshold', a: 'Stay on Postgres FTS until measured.' }],
}

const KNOWLEDGE_BUILD: KnowledgeBuild = {
  the_bar: { statement: 'A source-cited picture of the world.', principle: 'Public, non-personal.' },
  summary: KNOWLEDGE_SUMMARY,
  benchmark: [
    {
      dimension: 'Provenance',
      kollegio: 'No published provenance',
      gap: 'opaque numbers',
      unipaith: 'Provenance on every fact',
    },
  ],
  reference_graph: [
    {
      key: 'occupations',
      title: 'Careers & occupations',
      section: '§3.1',
      table: 'ref_occupations',
      sources: 'BLS · O*NET',
      feeds: 'Career alignment',
      table_present: true,
    },
  ],
  pipeline: [{ n: 3, name: 'Extract', detail: 'Grounded, never invents.' }],
  change_event_types: [
    { type: 'deadline_moved', materiality: 'high', routes_to: 'notifications' },
  ],
  authority_ladder: [
    { rank: 1, source: 'institution_verified', note: 'The ceiling.' },
  ],
  capabilities: [
    {
      key: 'reference',
      title: 'Reference projection',
      section: '§3',
      status: 'live',
      blurb: 'Typed provenance tables.',
      built: ['8 reference tables'],
      planned: [],
    },
    {
      key: 'chatbot',
      title: 'RAG chatbot over the graph',
      section: '61',
      status: 'planned',
      blurb: 'Claude answers over the graph.',
      built: [],
      planned: ['Ships in 61'],
    },
  ],
  phases: [{ key: 'A', title: 'Institutional core', status: 'live', detail: 'Schools/programs.' }],
  acceptance: [{ status: 'live', text: 'No personal/individual data gathered.' }],
  config_knobs: [{ name: 'crawler_live_fetch_enabled', value: false, section: '§11' }],
  routes: {
    reference: ['/api/v1/reference/occupations'],
    crawler_ops: ['/api/v1/crawler/sources'],
    enrichment: ['/api/v1/institutions/me/enrichments'],
  },
  reference_domains: ['occupations', 'tests', 'visas'],
  open_questions: [{ q: 'Auto-apply threshold', a: 'Review-all for low-trust.' }],
}

const SECURITY: SecurityTrust = {
  the_bar: {
    statement: 'Security is a property of the running system, not a policy doc.',
    principle: 'Assistive, consent-gated, least-privilege — gaps surfaced, not hidden.',
  },
  summary: SECURITY_SUMMARY,
  controls: [
    {
      key: 'authn',
      title: 'Authentication',
      section: '§2',
      status: 'live',
      module: 'core/security.py',
      blurb: 'Cognito JWT verified against JWKS; the dev token only works under bypass.',
      built: ['Cognito JWT validated against JWKS', 'Boot guard refuses the prod bypass'],
      planned: ['MFA-state surfaced on sensitive actions'],
    },
    {
      key: 'pii',
      title: 'PII protection',
      section: '§3',
      status: 'partial',
      module: 'core/pii.py',
      blurb: 'Sensitive fields are classified and masked; column-encryption is next.',
      built: ['Classification registry', 'mask() redacts PII in logs + AI context'],
      planned: ['Column-level KMS-envelope encryption'],
    },
    {
      key: 'moderation',
      title: 'Trust & safety / moderation',
      section: '§6',
      status: 'planned',
      module: '—',
      blurb: 'Abuse rate-limits exist; the UGC moderation pass is the named gap.',
      built: ['Abuse rate-limits', 'Minors ↔ adults peer-matching block'],
      planned: ['UGC moderation pass', 'Crisis-signal escalation hard-floor'],
    },
  ],
  consent: {
    levers: ['matching', 'outreach', 'analytics', 'training'],
    lever_counts: [
      { lever: 'matching', agent_count: 8 },
      { lever: 'outreach', agent_count: 1 },
      { lever: 'analytics', agent_count: 2 },
      { lever: 'training', agent_count: 0 },
    ],
    agent_count: 36,
    default_permissive: true,
    redaction_map_size: 26,
    note: 'A denied lever short-circuits to the rule-based fallback, never a 5xx.',
  },
  pii: {
    field_count: 18,
    class_count: 4,
    encryption_target_count: 9,
    model_count: 6,
    classes: [
      { key: 'pii', label: 'Personal', description: 'Ordinary personal data.', count: 7, encryption_target: false },
      { key: 'pii_sensitive', label: 'FERPA education record', description: 'Education records.', count: 2, encryption_target: false },
      { key: 'policy_gated', label: 'Policy-gated identity', description: 'Gov-ID / eligibility.', count: 5, encryption_target: true },
      { key: 'health_pii', label: 'Health / disability', description: 'Health data.', count: 4, encryption_target: true },
    ],
  },
  headers: {
    count: 5,
    names: [
      'X-Content-Type-Options',
      'X-Frame-Options',
      'X-XSS-Protection',
      'Referrer-Policy',
      'Content-Security-Policy',
    ],
    hsts_in_production: true,
    note: 'Set on every response by core/middleware.py; HSTS is added in production.',
  },
  auth: {
    environment: 'development',
    cognito_bypass: true,
    bypass_safe: true,
    pool_configured: false,
    note: 'The boot guard refuses to start with the bypass on in production/staging.',
  },
  config_knobs: [
    { name: 'environment', value: 'development', section: '§2' },
    { name: 'cognito_bypass', value: true, section: '§2' },
    { name: 'rate_limit_enabled', value: true, section: '§5' },
  ],
  compliance: [
    { regime: 'FERPA', control: 'Education-record access is logged', status: 'live', module: 'services/audit_service.py' },
    { regime: 'GDPR/CCPA', control: 'Right to portability: data-export bundle', status: 'planned', module: 'services/data_export_service.py' },
  ],
  build_tasks: [
    {
      section: '§2',
      status: 'live',
      text: 'Startup assert: cognito_bypass=false in production (fail boot)',
      evidence: 'assert_secure_auth_config() runs at the top of the lifespan.',
    },
    {
      section: '§9',
      status: 'planned',
      text: 'infra/runbooks/incident.md',
      evidence: 'Deferred to the incident-response control.',
    },
  ],
  acceptance: [
    { status: 'live', text: 'Prod refuses to boot with auth bypass on; every me-route role+owner guarded.' },
    { status: 'partial', text: 'Uploads type/size-capped; AV scan + crawler SSRF guard are planned.' },
  ],
  open_questions: [
    { q: 'Column-encryption approach', a: 'A KMS envelope on the highest-sensitivity fields.' },
  ],
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

  it('hub renders the live stats and links to all thirteen surfaces', async () => {
    vi.spyOn(buildApi, 'getBuildOverview').mockResolvedValue(OVERVIEW)
    renderPage(<GoalHubPage />)

    expect(screen.getByText(/How UniPaith is built — in the open/i)).toBeInTheDocument()
    await waitFor(() => expect(screen.getByText('Build roadmap')).toBeInTheDocument())
    expect(screen.getByText('Feature coverage')).toBeInTheDocument()
    expect(screen.getByText('API contract')).toBeInTheDocument()
    // The new surfaces (specs 51–55) appear.
    expect(screen.getByText('Data model')).toBeInTheDocument()
    expect(screen.getByText('Acceptance & runbook')).toBeInTheDocument()
    expect(screen.getByText('Experience standards')).toBeInTheDocument()
    expect(screen.getByText('Frontend engineering')).toBeInTheDocument()
    expect(screen.getByText('Production readiness')).toBeInTheDocument()
    // Spec 56 — the search/feed/recs surface card appears.
    expect(screen.getByText('Search, feed & recs')).toBeInTheDocument()
    // Spec 60 — the knowledge engine surface card appears.
    expect(screen.getByText('Knowledge engine')).toBeInTheDocument()
    // Spec 57 — the realtime & notifications surface card appears.
    expect(screen.getByText('Realtime & notifications')).toBeInTheDocument()
    // Spec 61 — the chatbot training & eval surface card appears.
    expect(screen.getByText('Chatbot training & eval')).toBeInTheDocument()
    // Spec 58 — the security & trust surface card appears.
    expect(screen.getByText('Security & trust')).toBeInTheDocument()
    expect(screen.getByText(/Fifteen ways to read the build/i)).toBeInTheDocument()
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

  it('production page renders pillars, live config + ops and filters by status', async () => {
    vi.spyOn(buildApi, 'getProduction').mockResolvedValue(PRODUCTION)
    renderPage(<ProductionReadinessPage />, '/goal/backend')

    await waitFor(() => expect(screen.getByText('Observability')).toBeInTheDocument())
    expect(screen.getByText('Health, deploy & SLOs')).toBeInTheDocument()
    // The live, introspected signals show: health probe paths + middleware classes.
    expect(screen.getByText('/api/v1/ready')).toBeInTheDocument()
    expect(screen.getAllByText('observability_middleware').length).toBeGreaterThan(0)
    // Live config knob value + an SLO target render.
    expect(screen.getByText('db_pool_size')).toBeInTheDocument()
    expect(screen.getByText('< 400 ms')).toBeInTheDocument()
    // The live-backed hero beat (health probes + middleware count) shows.
    expect(screen.getByText(/2 health probes live/i)).toBeInTheDocument()

    // Filter to Live → the partial Observability pillar drops out.
    fireEvent.click(screen.getByRole('button', { name: 'Live' }))
    await waitFor(() => expect(screen.queryByText('Observability')).not.toBeInTheDocument())
    expect(screen.getByText('Health, deploy & SLOs')).toBeInTheDocument()
  })

  it('search page renders capabilities, live routes + config and filters by status', async () => {
    vi.spyOn(buildApi, 'getSearchBuild').mockResolvedValue(SEARCH_BUILD)
    renderPage(<SearchFeedRecsPage />, '/goal/search')

    await waitFor(() => expect(screen.getByText('Full-text search')).toBeInTheDocument())
    expect(screen.getByText('Saved searches + alerts')).toBeInTheDocument()
    expect(screen.getByText('Hybrid semantic fusion')).toBeInTheDocument()
    // The live, route-table-resolved backing paths show.
    expect(screen.getByText('/api/v1/students/me/saved-searches')).toBeInTheDocument()
    // A live config knob (read off settings) renders.
    expect(screen.getByText('saved_search_alerts_enabled')).toBeInTheDocument()
    // The saved-search hero beat (table wired + live endpoints) shows.
    expect(screen.getByText(/Saved-search alerts wired/i)).toBeInTheDocument()

    // Filter to Planned → the live Full-text-search capability drops out.
    fireEvent.click(screen.getByRole('button', { name: 'Planned' }))
    await waitFor(() => expect(screen.queryByText('Full-text search')).not.toBeInTheDocument())
    expect(screen.getByText('Hybrid semantic fusion')).toBeInTheDocument()
  })

  it('knowledge engine page renders the benchmark, reference graph, capabilities and routes', async () => {
    vi.spyOn(buildApi, 'getKnowledgeBuild').mockResolvedValue(KNOWLEDGE_BUILD)
    renderPage(<KnowledgeEnginePage />, '/goal/knowledge')

    // Wait for the data-dependent content (a reference-graph card) to resolve.
    await waitFor(() => expect(screen.getByText('Careers & occupations')).toBeInTheDocument())
    // The Kollegio benchmark asset (§1A) renders.
    expect(screen.getByText('Improving on Kollegio')).toBeInTheDocument()
    expect(screen.getByText('Provenance on every fact')).toBeInTheDocument()
    // The reference-graph card shows its live table name.
    expect(screen.getByText('ref_occupations')).toBeInTheDocument()
    // A live config knob (read off settings) + a backing route render.
    expect(screen.getByText('crawler_live_fetch_enabled')).toBeInTheDocument()
    expect(screen.getByText('/api/v1/reference/occupations')).toBeInTheDocument()
    // The hero beat shows the allowlisted-source count read live.
    expect(screen.getByText(/16 allowlisted sources/i)).toBeInTheDocument()

    // Filter to Planned → the live reference capability drops, the RAG chatbot stays.
    fireEvent.click(screen.getByRole('button', { name: 'Planned' }))
    await waitFor(() => expect(screen.queryByText('Reference projection')).not.toBeInTheDocument())
    expect(screen.getByText('RAG chatbot over the graph')).toBeInTheDocument()
  })

  it('security page renders controls, consent + PII and filters by status', async () => {
    vi.spyOn(buildApi, 'getSecurity').mockResolvedValue(SECURITY)
    renderPage(<SecurityTrustPage />, '/goal/security')

    // Wait on a data-dependent control card (unique title — the auth card header
    // 'Authentication' renders before data, so anchor on PII protection instead).
    await waitFor(() => expect(screen.getByText('PII protection')).toBeInTheDocument())
    expect(screen.getByText('Trust & safety / moderation')).toBeInTheDocument()
    // The live, introspected signals show: a consent lever + its gated-agent count,
    // and a PII class with its encryption-target badge.
    expect(screen.getByText('matching')).toBeInTheDocument()
    expect(screen.getByText('Policy-gated identity')).toBeInTheDocument()
    // A compliance row + a live config knob render.
    expect(screen.getByText(/Education-record access is logged/i)).toBeInTheDocument()
    expect(screen.getByText('cognito_bypass')).toBeInTheDocument()
    // The boot-guard hero beat (consent agents mapped) shows.
    expect(screen.getByText(/Boot-guarded against the prod auth bypass/i)).toBeInTheDocument()

    // Filter to Live → the partial PII + planned moderation controls drop out.
    fireEvent.click(screen.getByRole('button', { name: 'Live' }))
    await waitFor(() => expect(screen.queryByText('PII protection')).not.toBeInTheDocument())
    expect(screen.queryByText('Trust & safety / moderation')).not.toBeInTheDocument()
    // The live authn control remains (a built item unique to it).
    expect(screen.getByText('Boot guard refuses the prod bypass')).toBeInTheDocument()
  })
})
