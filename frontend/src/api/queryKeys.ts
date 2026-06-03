// Spec 54 §3 — the single query-key factory.
//
// Query keys were inline string-arrays per page, which drifts: two screens key
// the same resource differently and their caches never reconcile. This module
// is the one place keys are minted. The rule:
//
//   key = [resource, paramsObject]  — and paramsObject carries the FULL filter
//   set, so two different filter combinations never collide in the cache.
//
// Roots match the literals already used across the app, so adopting `qk` on a
// surface is drop-in — a cache entry written via `qk.profile()` is the same
// entry as the legacy `['profile']`. Migrate inline keys to these incrementally.
//
// `as const` keeps every key a readonly tuple, so `qc.getQueryData(qk.x())` is
// typed against the exact key shape.

// Param bags — each carries the complete filter set for cache correctness (§3).
export interface FeedParams {
  scope?: string
  cursor?: string | null
}
export interface PipelineParams {
  programId?: string
  stage?: string
  search?: string
  view?: string
}
export interface SearchParams {
  q?: string
  filters?: Record<string, unknown>
}

export const qk = {
  // ── Build-transparency (/goal hub — specs 45 / 48–54) ─────────────────────
  buildOverview: () => ['build-overview'] as const,
  buildRoadmap: () => ['build-roadmap'] as const,
  buildFeatures: () => ['build-features'] as const,
  buildApiContract: () => ['build-api-contract'] as const,
  buildDataModel: () => ['build-data-model'] as const,
  buildAcceptance: () => ['build-acceptance'] as const,
  buildUxBenchmark: () => ['build-ux-benchmark'] as const,
  buildFrontendStandards: () => ['build-frontend-standards'] as const,
  buildRealtime: () => ['build-realtime'] as const,
  buildEvalHarness: () => ['build-eval-harness'] as const,
  aiAgents: () => ['ai-agents'] as const,

  // ── Student · profile + discovery ─────────────────────────────────────────
  profile: () => ['profile'] as const,
  goals: () => ['goals'] as const,
  needs: () => ['needs'] as const,
  identity: () => ['identity'] as const,
  strategy: () => ['strategy'] as const,
  preferences: () => ['preferences'] as const,
  workExperiences: () => ['work-experiences'] as const,
  discovery: (track?: string) =>
    (track ? (['discovery', track] as const) : (['discovery'] as const)),

  // ── Student · match / explore ─────────────────────────────────────────────
  recommendations: (refresh = false) => ['recommendations', { refresh }] as const,
  matchProbability: (programId: string) => ['matchProbability', programId] as const,
  program: (id: string) => ['program', id] as const,
  institution: (id: string) => ['institution', id] as const,
  search: (params: SearchParams) => ['search', params] as const,
  majorSpecific: () => ['major-specific'] as const,

  // ── Student · saved + compare ─────────────────────────────────────────────
  saved: () => ['saved'] as const,
  savedPrograms: () => ['saved-programs'] as const,
  savedTags: () => ['saved-tags'] as const,

  // ── Student · apply ───────────────────────────────────────────────────────
  myApplications: () => ['my-applications'] as const,
  application: (id: string) => ['application', id] as const,
  checklist: (applicationId: string) => ['checklist', applicationId] as const,
  programChecklist: (programId: string) => ['program-checklist', programId] as const,
  documents: (scope?: string) =>
    (scope ? (['documents', scope] as const) : (['documents'] as const)),
  offersComparison: () => ['offers-comparison'] as const,

  // ── Student · connect + calendar + inbox ──────────────────────────────────
  connectFeed: (params: FeedParams = {}) => ['connect-feed', params] as const,
  connectFollows: () => ['connect-follows'] as const,
  myFollows: () => ['my-follows'] as const,
  myRsvps: () => ['my-rsvps'] as const,
  calendar: () => ['calendar'] as const,
  peersDiscover: () => ['peers-discover'] as const,
  notifications: () => ['notifications'] as const,
  notificationsUnread: () => ['notifications', 'unread-count'] as const,

  // ── Institution ───────────────────────────────────────────────────────────
  institutionPrograms: () => ['institution-programs'] as const,
  institutionTeam: () => ['institution-team'] as const,
  institutionEvents: () => ['institution-events'] as const,
  institutionSetup: () => ['institution-setup'] as const,
  institutionSettings: () => ['institution-settings'] as const,
  pipelineApplications: (params: PipelineParams = {}) =>
    ['pipeline-applications', params] as const,
  reviewPacket: (applicationId: string) => ['review-packet', applicationId] as const,
  rubrics: () => ['rubrics'] as const,
  interviews: () => ['interviews'] as const,
  inquiries: () => ['inquiries'] as const,
  segments: () => ['segments'] as const,
  campaigns: () => ['campaigns'] as const,
  templates: () => ['templates'] as const,
  datasets: () => ['datasets'] as const,
  posts: () => ['posts'] as const,
  promotions: () => ['promotions'] as const,
  intakeRounds: () => ['intake-rounds'] as const,
  recruitmentProspects: () => ['recruitment-prospects'] as const,
  recruitmentSummary: () => ['recruitment-summary'] as const,
  enrollment: () => ['enrollment'] as const,
  instInboxThreads: () => ['inst-inbox-threads'] as const,
  instInboxThread: (id: string) => ['inst-inbox-thread', id] as const,
  dataRights: () => ['data-rights'] as const,

  // ── Cross-role ────────────────────────────────────────────────────────────
  payment: (applicationId: string) => ['payment', applicationId] as const,
  billing: () => ['billing'] as const,
} as const

export type QueryKeyFactory = typeof qk
