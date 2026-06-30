// AUTO-SPLIT from the former monolithic types/index.ts.
// Domain module — see CONTRIBUTING.md. Edit types here, not in a barrel.
// === PHASE A — DISCOVERY ===

export type DiscoveryTrack = 'profile' | 'goals' | 'needs'
export type DiscoveryLayer = 'basic' | 'personality' | 'identity'
export type DiscoveryStatus = 'active' | 'completed' | 'abandoned'
export type DiscoveryRole = 'student' | 'assistant' | 'system'

export interface DiscoveryMessage {
  id: string
  session_id: string
  role: DiscoveryRole
  content: string
  extracted_signals: Record<string, unknown> | null
  created_at: string
}

export interface DiscoverySession {
  id: string
  student_id: string
  track: DiscoveryTrack
  layer: DiscoveryLayer | null
  status: DiscoveryStatus
  completion_pct: string  // numeric(4,3) → string from JSON
  exit_signal: Record<string, unknown> | null
  started_at: string
  completed_at: string | null
  created_at: string
  updated_at: string
}

export interface DiscoverySessionDetail extends DiscoverySession {
  messages: DiscoveryMessage[]
}

export interface AppendMessageResponse {
  student_message: DiscoveryMessage
  assistant_message: DiscoveryMessage | null
}

export interface CompletionMap {
  profile: string
  goals: string
  needs: string
  identity: string
}

// Signals the orchestrator may stamp onto an assistant message's
// `extracted_signals` (spec 19). All optional — the rule-based / stub paths
// omit most of them.
export interface AssistantTurnSignals {
  _phase?: string
  _mode?: 'rule_based' | string
  suggested_options?: string[]
  requested_layer_advance?: boolean
  advance_rationale?: string | null
  [key: string]: unknown
}

// Spec 19 §6 — personality-layer facet for the Discover artifact rail.
export interface PersonalitySignal {
  facet: string
  value: string
  evidence: string | null
  confidence: number | null
}

// Spec 19 §7/§10 — deterministic DiscoveryJudge verdict.
export interface HandoffVerdict {
  should_handoff: boolean
  handoff_target: 'recommendation' | null
  reason: string
  completion: Record<string, number>
}


// === PHASE A — DISCOVERY ARTIFACTS ===

export type GoalCategory = 'academic' | 'social' | 'personal'
export type GoalStatus = 'active' | 'met' | 'revised' | 'dropped'
export type GoalSource = 'discovery' | 'manual'

export interface StudentGoal {
  id: string
  student_id: string
  category: GoalCategory
  specific: string
  measurable: string | null
  achievable_notes: string | null
  relevant_notes: string | null
  time_bound: string | null
  status: GoalStatus
  source: GoalSource
  source_session_id: string | null
  confidence: string | null
  created_at: string
  updated_at: string
}

export type MaslowLevel =
  | 'physiological'
  | 'safety'
  | 'social'
  | 'self_esteem'
  | 'self_actualization'
export type NeedSeverity = 'must_have' | 'strong_preference' | 'nice_to_have'
export type NeedSource = 'discovery' | 'manual' | 'inferred'

export interface StudentNeed {
  id: string
  student_id: string
  maslow_level: MaslowLevel
  need_type: string
  signal: string
  severity: NeedSeverity
  source: NeedSource
  source_session_id: string | null
  source_quote: string | null
  confidence: string | null
  created_at: string
  updated_at: string
}

export interface CoreValue {
  value: string
  evidence: string
  confidence: string | null
  source_quote: string | null
}

export interface WorldviewItem {
  belief: string
  context: string
  confidence: string | null
  source_quote: string | null
}

export interface SelfAwarenessItem {
  insight: string
  trigger_event: string | null
  confidence: string | null
  source_quote: string | null
}

export interface StudentIdentity {
  student_id: string
  core_values: CoreValue[]
  worldview: WorldviewItem[]
  self_awareness: SelfAwarenessItem[]
  identity_summary: string | null
  last_session_id: string | null
  updated_at: string
}


// === PHASE A — STRATEGY ===

export type StrategyStatus = 'draft' | 'active' | 'archived'

export interface AcademicPathStep {
  step: string
  options: string[]
  rationale: string
}

export interface FinancialPathItem {
  aid_type: string
  eligibility: string
  estimated_value: string | null
}

export interface GeographicPathItem {
  region: string
  rationale: string
  constraints: string[]
}

export interface StudentStrategy {
  id: string
  student_id: string
  version: number
  status: StrategyStatus
  career_target: string | null
  target_degree: string | null
  academic_path: AcademicPathStep[]
  financial_path: FinancialPathItem[]
  geographic_path: GeographicPathItem[]
  narrative: string | null
  generated_at: string
  generated_from_session_ids: string[]
  is_stub: boolean
  created_at: string
  updated_at: string
}


// === PHASE A — MATCH DUAL SCORES ===

// Spec 09 §4A — probability bands (admit / scholarship / waitlist + drivers).
export type AdmitLabel = 'likely' | 'target' | 'reach' | 'unlikely'

export interface ProbabilityBands {
  admit: { low: number; high: number; label: AdmitLabel }
  scholarship: { low: number; high: number } | null
  waitlist: { approx: number } | null
  drivers: Array<{ signal: string; direction: 'up' | 'down' }>
}

export type MatchBand = 'reach' | 'target' | 'safer'

export interface MatchResultDual {
  id: string
  student_id: string
  program_id: string
  // AI-Structure-3 §14 — backend-only contract: the STUDENT match response no
  // longer carries the raw fitness/confidence numbers (only band + rationale +
  // probability bands). These stay typed-but-optional for institution/admin
  // payloads and any cached pre-cutover responses; student surfaces read the
  // band_label instead.
  fitness_score?: string | null
  confidence_score?: string | null
  fitness_breakdown: Record<string, unknown> | null
  confidence_breakdown: Record<string, unknown> | null
  rationale_text: string | null
  rationale_generated_at: string | null
  strategy_version_id: string | null
  // DEPRECATED — drop in Phase E. Kept for backcompat during transition.
  match_score?: string | null
  score_breakdown?: Record<string, unknown> | null
  match_tier: number | null
  reasoning_text: string | null
  model_version: string | null
  computed_at: string
  is_stale: boolean
  program_name?: string | null
  institution_id?: string | null
  institution_name?: string | null
  degree_type?: string | null
  tuition?: number | null
  acceptance_rate?: number | null
  // Spec 09 §6 / §4A — derived on the server and carried on every match.
  band_label?: MatchBand | null
  // Simple range-based "Fit" readout (server-computed; not the raw number).
  fit_label?: string | null
  // Affordability — estimated annual NET price (after expected aid) + a band vs
  // the student's budget ("affordable" | "stretch" | "out_of_reach" | "unknown").
  net_price_annual?: number | null
  affordability_band?: string | null
  probability_bands?: ProbabilityBands | null
}

// Spec 09 §4A — GET /me/matches/:id/probability response.
export interface ProbabilityBandsResponse {
  program_id: string
  probability_bands: ProbabilityBands | null
  match_ready: boolean
  reason: string | null // "no_history" | "not_match_ready" | "disabled" | null
}

export interface DecisionBriefEvidence {
  side: 'student' | 'program'
  path: string
  label: string
  url?: string | null
}

export interface DecisionBriefItem {
  statement: string
  confidence?: number
  uncertainty?: string | null
  evidence: DecisionBriefEvidence[]
}

export interface DecisionBrief {
  standard_version: number
  student_profile_version: number
  program_profile_version: number
  sections: Record<string, DecisionBriefItem[]>
  omissions?: Array<{ section: string; reason: string }>
}

// Spec 11 §3.5 — Insights: student/alumni reviews + employer feedback.
export interface ProgramReview {
  id: string
  program_id: string
  rating_teaching: number | null
  rating_workload: number | null
  rating_career_support: number | null
  rating_internship_access: number | null
  rating_community_culture: number | null
  rating_roi: number | null
  rating_overall: number | null
  review_text: string | null
  who_thrives_here: string | null
  reviewer_context: Record<string, unknown> | null
  external_source: Record<string, unknown> | null
  is_verified: boolean
  created_at: string
}

export interface ProgramReviewSummary {
  total_reviews: number
  avg_teaching: number | null
  avg_workload: number | null
  avg_career_support: number | null
  avg_internship_access: number | null
  avg_community_culture: number | null
  avg_roi: number | null
  avg_overall: number | null
  reviews: ProgramReview[]
}

export interface EmployerFeedback {
  id: string
  program_id: string
  employer_name: string
  industry: string | null
  rating_technical: number | null
  rating_practical: number | null
  rating_communication: number | null
  rating_teamwork: number | null
  rating_reliability: number | null
  rating_overall: number | null
  job_readiness_sentiment: string | null
  feedback_text: string | null
  hiring_pattern: string | null
  feedback_year: number | null
  created_at: string
}

export interface EmployerFeedbackSummary {
  total_feedback: number
  avg_technical: number | null
  avg_practical: number | null
  avg_communication: number | null
  avg_teamwork: number | null
  avg_reliability: number | null
  avg_overall: number | null
  sentiment_counts: Record<string, number>
  feedback: EmployerFeedback[]
}

// Spec 11 §3.3a — personalized Net Price Estimator (GET /me/programs/:id/net-price).
export type AffordabilityBand = 'affordable' | 'stretch' | 'out_of_reach' | 'unknown'
export type AidLikelihoodBand = 'low' | 'moderate' | 'high' | 'unknown'

export interface NetPriceRange {
  min: number
  expected: number
  max: number
}

export interface NetPriceEstimate {
  program_id: string
  available: boolean
  reason: string | null // "no_cost_data" | null
  currency: string
  cost_of_attendance_annual: number | null
  net_cost_scenario_range: NetPriceRange | null
  net_cost_scenario_range_total: NetPriceRange | null
  years: number | null
  affordability_band: AffordabilityBand
  aid_scholarship_likelihood_band: AidLikelihoodBand
  gap: {
    student_annual_budget: number | null
    shortfall_annual: number | null
    band: AffordabilityBand
  }
  drivers: string[]
  disclaimer: string
}

export interface ExplainMatchResponse {
  program_id: string
  rationale_text: string
  rationale_generated_at: string
  is_stub: boolean
  decision_brief?: DecisionBrief | null
  // Spec 06 §5.5 — student (redacted) projection. Institution-only
  // comparative signals are stripped server-side before reaching here.
  fitness_breakdown?: Record<string, unknown> | null
  confidence_breakdown?: Record<string, unknown> | null
  cited_student_fields?: string[]
  cited_program_fields?: string[]
  redacted?: boolean
}

// Spec 06 §3 / §5.5 — the FULL, evidence-linked rationale an institution
// reviewer sees (the asymmetric counterpart of ExplainMatchResponse).
export interface InstitutionMatchRationale {
  application_id: string
  student_id: string
  program_id: string
  available: boolean
  rationale_text: string
  cited_student_fields: string[]
  cited_program_fields: string[]
  fitness_breakdown: Record<string, unknown>
  confidence_breakdown: Record<string, unknown>
  fitness_score: number | null
  confidence_score: number | null
  grounded: boolean
  redacted: boolean
  is_stub: boolean
}


// === PHASE A — WORKSHOP FEEDBACK ===

export type WorkshopDomain = 'essay' | 'interview' | 'test'
export type IssueSeverity = 'minor' | 'moderate' | 'major'
export type ElementImportance = 'nice_to_have' | 'should_have' | 'required'

export interface StructuralIssue {
  issue: string
  severity: IssueSeverity
  location_ref: string | null
}

export interface MissingElement {
  element: string
  importance: ElementImportance
}

export interface SuggestedQuestion {
  question: string
  why: string
}

export interface WorkshopFeedbackRun {
  id: string
  student_id: string
  domain: WorkshopDomain
  // Backend WorkshopFeedbackResponse also carries the run's targeting; used
  // to surface program-relevant runs on the application detail page.
  mode?: 'general' | 'program_specific'
  target_program_id?: string | null
  input_artifact_id: string | null
  prompt_text: string | null
  rubric_scores: Record<string, number>
  structural_issues: StructuralIssue[]
  missing_elements: MissingElement[]
  suggested_questions: SuggestedQuestion[]
  is_stub: boolean
  created_at: string
}

// ── Spec 35 · Enrollment Confirmation & Yield ──────────────────────────────

export type EnrollmentState =
  | 'accepted'
  | 'intent_confirmed'
  | 'deposit_recorded'
  | 'enrollment_confirmed'
  | 'enrolled'
  | 'withdrew'
  | 'deferred'

export type DepositStatus = 'none' | 'pending' | 'paid' | 'waived'
export type ChecklistItemStatus = 'pending' | 'complete' | 'overdue' | 'waived'

export interface EnrollmentChecklistItem {
  key: string
  item: string
  status: ChecklistItemStatus
  due: string | null
  consequence?: string
}

export interface EnrollmentDeferral {
  requested: boolean
  to_term: { season?: string | null; year?: number | null } | null
  approved: boolean
}

export interface EnrollmentOtherOffer {
  application_id: string
  program_name: string | null
  institution_name: string | null
}

export interface EnrollmentTimelineEvent {
  label: string
  at: string | null
}

export interface Enrollment {
  available: boolean
  application_id: string
  offer_id?: string | null
  state?: EnrollmentState
  deposit_status?: DepositStatus
  deposit_amount?: number | null
  intent_confirmed_at?: string | null
  enrollment_confirmed_at?: string | null
  decline_reason?: string | null
  deferral?: EnrollmentDeferral | null
  checklist?: EnrollmentChecklistItem[]
  program_name?: string | null
  institution_name?: string | null
  start_term?: string | null
  response_deadline?: string | null
  student_name?: string | null
  decision?: string | null
  other_active_offers?: EnrollmentOtherOffer[]
  timeline?: EnrollmentTimelineEvent[]
}

export interface WaitlistEntry {
  application_id: string
  student_id: string
  student_name: string | null
  program_id: string
  program_name: string
  waitlist_rank: number | null
  waitlisted_at: string | null
}

export interface WaitlistView {
  waitlist: WaitlistEntry[]
  waitlist_count: number
  seats_open: number | null
  program_id: string | null
}

export interface YieldFunnelStep {
  step: string
  count: number
  pct_of_admitted: number
  drop_off: number | null
}

export interface YieldCohortGroup {
  group: string
  admitted: number
  enrolled: number
  yield_rate: number
}

export interface YieldCohort {
  dimension: string
  label: string
  groups: YieldCohortGroup[]
  disparity: number | null
  fairness_concern: boolean
}

export interface YieldNextBestAction {
  kind: string
  label: string
  rationale: string
  count?: number | null
}

export interface YieldAtRiskAdmit {
  application_id: string
  student_id: string
  student_name: string | null
  confirm_probability: number
  risk_level: 'high' | 'medium' | 'low'
  state: string
  days_remaining: number | null
}

export interface YieldTimeToConfirm {
  count: number
  avg_days: number | null
  median_days: number | null
  buckets: { label: string; count: number }[]
}

export interface YieldSnapshot {
  scope: { institution_id: string; program_id: string | null; intake_id: string | null }
  admitted: number
  intent_confirmed: number
  deposited: number
  enrolled: number
  yield_rate: number
  melt: number
  melt_rate: number
  waitlist_conversion: number | null
  predicted_final_class_size: number
  target_class_size: number | null
  funnel: YieldFunnelStep[]
  time_to_confirm: YieldTimeToConfirm
  waitlist_count: number
  seats_open: number | null
  at_risk: YieldAtRiskAdmit[]
  at_risk_count: number
  cohorts: YieldCohort[]
  next_best_actions: YieldNextBestAction[]
  empty?: boolean
}

// ── Spec 38 · International Admissions (institution processing) ───────────────
export interface IntlCountryRequirement {
  item: string
  status: 'pending' | 'received' | 'verified' | 'waived'
}

export interface IntlProcessingRecord {
  id: string
  credential_eval: {
    provider: 'WES' | 'ECE' | 'SpanTran' | 'other' | null
    status: 'none' | 'requested' | 'in_progress' | 'received' | 'verified'
    report_ref: string | null
    normalized_gpa: string | null
    source_scale: string | null
    notes: string | null
  }
  english_proficiency: {
    test: 'TOEFL' | 'IELTS' | 'DET' | 'PTE' | null
    score: string | null
    meets_minimum: boolean | null
    waiver: { eligible: boolean; basis: string | null }
  }
  country_requirements: IntlCountryRequirement[]
  immigration_doc: {
    type: 'I-20' | 'DS-2019' | null
    status: 'not_started' | 'drafted' | 'issued' | 'sent' | 'received'
    sevis_id: string | null
    issued_at: string | null
    sevis_export: Record<string, unknown> | null
  }
  visa: {
    appointment_at: string | null
    consulate: string | null
    outcome: 'pending' | 'approved' | 'denied' | null
  }
}

export interface IntlStudentInputs {
  nationality: string | null
  country_of_birth: string | null
  country_of_residence: string | null
  passport_issuing_country: string | null
  raw_gpa: string | null
  gpa_scale: string | null
  grading_scale_type: string | null
  academic_country: string | null
  degree_type: string | null
  self_reported_normalized_gpa: string | null
  student_credential_eval_status: string | null
  credential_report_url: string | null
  english_test_scores: { test: string; score: string | null }[]
  financial_proof_available: boolean
  financial_proof_amount_band: string | null
  sponsorship_source: string | null
}

export type IntlFeasibilityBand = 'blocked' | 'at_risk' | 'moderate' | 'strong'

export interface IntlFeasibility {
  band: IntlFeasibilityBand
  reasons: string[]
}

export interface IntlImmigrationGate {
  can_generate: boolean
  blockers: { field: string; message: string }[]
}

export interface IntlProcessingView {
  application_id: string
  institution_id: string | null
  is_international: boolean
  student: { display_name: string; name_in_native_script: string | null; date_of_birth: string | null }
  program: { id: string; program_name: string; degree_type: string; english_policy: IntlEnglishPolicy | null }
  decision: string | null
  student_inputs: IntlStudentInputs
  processing: IntlProcessingRecord | null
  immigration_gate: IntlImmigrationGate
  feasibility: IntlFeasibility
  english_waiver_suggestion: { eligible: boolean; basis: string | null }
}

export interface IntlApplicantRow {
  application_id: string
  student_name: string
  program_name: string | null
  nationality: string | null
  status: string | null
  decision: string | null
  credential_status: string
  normalized_gpa: string | null
  english_meets_minimum: boolean | null
  country_requirements: { complete: number; total: number }
  immigration_doc_status: string
  feasibility: IntlFeasibilityBand
}

export interface IntlEnglishPolicyTest {
  test: 'TOEFL' | 'IELTS' | 'DET' | 'PTE'
  min_score: number
}

export interface IntlEnglishPolicy {
  accepted_tests?: IntlEnglishPolicyTest[]
  waiver_native_english_countries?: string[]
  waiver_prior_degree_in_english?: boolean
}

export interface IntlCountryPack {
  country_code: string
  country_name: string
  requirements: { item: string; description?: string }[]
  source: 'platform_default' | 'institution'
}

export interface IntlNormalizeResult {
  normalized_gpa: string | null
  source_scale: string
  raw_gpa: string
  course_map_note: string | null
  ai_used: boolean
}

// ── Spec 40 · Recruitment CRM (Pre-Applicant) ────────────────────────────────

export type ProspectSource = 'fair' | 'list' | 'inquiry' | 'referral' | 'web' | 'visit'
export type ProspectStage = 'suspect' | 'prospect' | 'engaged' | 'inquiry' | 'applicant'

export interface Prospect {
  id: string
  name: string
  email: string | null
  phone: string | null
  city: string | null
  region: string | null
  country: string | null
  interests: string[] | null
  source: ProspectSource
  source_detail: string | null
  stage: ProspectStage
  territory_id: string | null
  owner_user_id: string | null
  owner_name: string | null
  converted_application_id: string | null
  consent_outreach: boolean
  apply_likelihood: number | null
  priority_reason: string | null
  priority_band: 'hot' | 'warm' | 'cold' | null
  notes: string | null
  created_at: string
  updated_at: string
}

export interface ProspectList {
  items: Prospect[]
  total: number
  prioritized: boolean
  stage_counts: Record<string, number>
}

export interface ProspectImportResult {
  imported: number
  deduped: number
  suppressed: number
  total_rows: number
}

export interface ProspectToSegmentResult {
  list_id: string
  list_name: string
  added: number
  skipped_no_consent: number
  skipped_no_email: number
}

export interface TripVisit {
  id: string
  trip_id: string
  kind: 'school' | 'fair'
  name: string
  fair_id: string | null
  visit_date: string | null
  prospects_met: number
  status: 'planned' | 'confirmed' | 'done'
  notes: string | null
}

export interface RecruitmentTrip {
  id: string
  name: string
  region: string | null
  start_date: string
  end_date: string
  recruiter_user_id: string | null
  recruiter_name: string | null
  budget: number | null
  spend: number
  status: 'planned' | 'active' | 'done' | 'cancelled'
  notes: string | null
  visits: TripVisit[]
  over_budget: boolean
  conflict: boolean
  created_at: string
  updated_at: string
}

export interface RecruitmentFair {
  id: string
  name: string
  kind: 'fair' | 'high_school'
  city: string | null
  region: string | null
  country: string | null
  contact_name: string | null
  contact_email: string | null
  prior_year_yield: number | null
  event_date: string | null
  status: 'prospective' | 'registered' | 'confirmed' | 'attended' | 'skipped'
  notes: string | null
  created_at: string
  updated_at: string
}

export interface Territory {
  id: string
  name: string
  geo: { regions?: string[]; countries?: string[]; cities?: string[] } | null
  owner_user_id: string | null
  owner_name: string | null
  notes: string | null
  prospect_count: number
  applicant_count: number
  conversion_rate: number
  unassigned: boolean
  created_at: string
  updated_at: string
}

export interface TerritoryDashboard {
  territories: Territory[]
  total_prospects: number
  total_applicants: number
  overall_conversion_rate: number
  unassigned_count: number
}

export interface TerritorySuggestion {
  kind: string
  label: string
  rationale: string
  candidate_name: string | null
}

export interface TerritoryOptimize {
  territory_id: string
  suggestions: TerritorySuggestion[]
  ai_generated: boolean
}

export interface RecruitmentSummary {
  prospect_count: number
  applicant_count: number
  trip_count: number
  fair_count: number
  territory_count: number
  unassigned_territory_count: number
  over_budget_trip_count: number
  stage_counts: Record<string, number>
  source_counts: Record<string, number>
  is_empty: boolean
}
