// AUTO-SPLIT from the former monolithic types/index.ts.
// Domain module — see CONTRIBUTING.md. Edit types here, not in a barrel.
import type { MatchBand } from './discovery';
import type { Program, ProgramSummary } from './program';

// === APPLICATIONS ===
// --- Spec 18 · Decisions & Offers ---
export interface OfferKeyTerm {
  label: string
  value: string
  explanation?: string
}
export interface OfferDeadline {
  label: string
  date: string
  days_remaining?: number
}
export interface OfferNextStep {
  action: string
  by_date?: string | null
}
export interface PlainLanguageBrief {
  key_terms: OfferKeyTerm[]
  deadlines: OfferDeadline[]
  next_steps: OfferNextStep[]
  summary: string
  source?: string
}

export type DecisionState =
  | 'pending'
  | 'accepted'
  | 'rejected'
  | 'waitlisted'
  | 'deferred'
  | 'accepted_by_student'
  | 'declined_by_student'
  | 'withdrawn'

export interface ApplicationOffer {
  id: string
  application_id: string
  offer_type: string | null
  tuition_amount: number | null
  scholarship_amount: number
  financial_package_total: number | null
  conditions: Record<string, unknown> | null
  response_deadline: string | null
  status: string | null
  student_response: string | null
  response_at: string | null
  brief: string | null
  // Spec 18
  received_externally?: boolean
  decision_date?: string | null
  scholarship_currency?: string | null
  tuition_estimate?: number | null
  total_cost_estimate?: number | null
  start_term_season?: string | null
  start_term_year?: number | null
  next_step_actions?: OfferNextStep[] | null
  plain_language_brief?: PlainLanguageBrief | null
  // Spec 41 §2.3 — graduate funding package mirrored onto the offer.
  assistantship_details?: GraduateFundingPackageSummary | Record<string, unknown> | null
  generated_letter_url?: string | null
}

export interface GraduateFundingPackageSummary {
  kind: 'graduate_funding_package'
  total_value: number
  currency: string
  multi_year: boolean
  components: Array<{
    kind: 'TA' | 'RA' | 'fellowship' | 'tuition_waiver' | 'stipend'
    amount: number
    years: number[]
    label: string | null
  }>
}

export interface OfferComparisonItem {
  application_id: string
  offer_id: string
  program_name: string | null
  institution_name: string | null
  degree_type: string | null
  decision_state: string | null
  cost: {
    tuition: number | null
    scholarship: number
    currency: string
    net_cost: number | null
  }
  fit: { fitness: number | null; confidence: number | null }
  outcomes: { median_salary: number | null; placement_rate: number | null }
  location: string | null
  response_deadline: string | null
  conditions: Record<string, unknown> | null
}

export interface OffersComparison {
  offers: OfferComparisonItem[]
  indicators: {
    best_value: string | null
    best_fit: string | null
    most_affordable: string | null
  }
  must_have_constraints: { need: string; signal: string }[]
  count: number
  advisor_summary?: string | null
}

export interface WithdrawableApp {
  id: string
  program_name: string | null
  institution_name: string | null
  decision_state: string | null
}

export interface OfferDecisionResult {
  offer: ApplicationOffer
  withdrawable_apps: WithdrawableApp[]
}

export interface Application {
  id: string
  student_id: string
  student_name?: string | null
  program_id: string
  status: 'draft' | 'submitted' | 'under_review' | 'interview' | 'decision_made'
  // Phase A dual-score split (see CLAUDE.md). `match_score` is legacy (Phase E
  // drop) — consumers read `fitness_score ?? match_score`. Typed here so the
  // dual-score reads in ApplicationsPage / ApplicationDetailPage are type-safe.
  match_score: number | null
  fitness_score?: number | null
  confidence_score?: number | null
  match_reasoning_text: string | null
  submitted_at: string | null
  decision: 'admitted' | 'accepted' | 'conditional_admission' | 'rejected' | 'waitlisted' | 'deferred' | null
  decision_at: string | null
  decision_notes: string | null
  // Spec 18 §2 — student-side action + unified derived state
  student_decision?: 'accepted_by_student' | 'declined_by_student' | 'withdrawn' | null
  decision_state?: DecisionState | null
  completeness_status: string | null
  missing_items: string[] | null
  // --- Spec 15 workspace ---
  submission_mode: 'internal' | 'external'
  readiness_pct: number | null
  intent_picker: string | null
  intent_rationale: string | null
  fit_band: 'low' | 'medium' | 'high' | null
  guardrail_blockers: string[] | null
  offer: ApplicationOffer | null
  created_at: string
  updated_at: string
  program?: Program & { institution_name?: string | null }
}

export interface ChecklistItem {
  key?: string
  name: string
  item_name?: string
  category?: string
  item_type?: string
  owner?: 'student' | 'recommender' | 'institution' | 'system'
  required?: boolean
  requirement_level?: string
  expected_format?: string | null
  status?: 'completed' | 'not_started' | 'in_progress' | 'blocked'
  completed?: boolean
  manual_complete?: boolean
  mismatch?: boolean
  description?: string | null
}

export interface ApplicationChecklist {
  id: string
  student_id: string
  program_id: string
  items: ChecklistItem[]
  completion_percentage: number
  auto_generated_at: string | null
}

export interface ReadinessCheck {
  is_ready: boolean
  completion_percentage: number
  missing_items: string[]
  warnings: string[]
}

export interface OfferLetter {
  id: string
  application_id: string
  offer_type: string
  tuition_amount: number | null
  scholarship_amount: number
  financial_package_total: number | null
  conditions: Record<string, any> | null
  response_deadline: string | null
  status: string
  student_response: string | null
  response_at: string | null
}

// --- Spec 34 · Decisions & Offers (institution-side) ---

export type InstitutionDecision =
  | 'admitted'
  | 'conditional_admission'
  | 'rejected'
  | 'waitlisted'
  | 'deferred'

export type OfferType =
  | 'full_admission'
  | 'conditional'
  | 'partial'
  | 'transfer_credit_offer'
  | 'waitlist_to_admit'

export interface ReleaseOfferTerms {
  offer_type?: OfferType
  scholarship_amount?: number | null
  scholarship_currency?: string
  tuition_amount?: number | null
  tuition_estimate?: number | null
  total_cost_estimate?: number | null
  conditions?: Record<string, any> | null
  response_deadline?: string | null
  start_term?: { season?: string | null; year?: number | null }
  next_step_actions?: { action: string; by_date?: string | null }[] | null
}

export interface OfferStatus {
  application_id: string
  student_id: string
  decision: string | null
  decision_at: string | null
  has_offer: boolean
  offer_id: string | null
  offer_type: string | null
  offer_status: string | null
  student_response: string | null
  response_at: string | null
  response_deadline: string | null
  days_remaining: number | null
  deadline_passed: boolean
  response_state:
    | 'accepted'
    | 'declined'
    | 'awaiting_response'
    | 'deadline_passed'
    | 'rescinded'
    | 'no_offer'
}

export interface ReleaseDecisionResult {
  application: Application
  offer: OfferLetter | null
}

export interface BatchReleaseItem {
  application_id: string
  decision: InstitutionDecision
  decision_notes?: string | null
  offer?: ReleaseOfferTerms | null
  message?: string | null
}

export interface BatchReleaseResult {
  results: { application_id: string; ok: boolean; decision?: string; offer_id?: string | null; error?: string }[]
  success_count: number
  failed_count: number
}


// === DOCUMENTS ===
export interface StudentDocument {
  id: string
  student_id: string
  document_type: 'transcript' | 'essay' | 'resume' | 'recommendation' | 'portfolio' | 'certificate'
  file_name: string
  file_size_bytes: number | null
  mime_type: string | null
  uploaded_at: string
  download_url?: string | null
}

export interface UploadResponse {
  upload_url: string
  document_id: string
  expires_in: number
}


// === ESSAYS & RESUMES ===
export interface Essay {
  id: string
  student_id: string
  program_id: string
  prompt_text: string | null
  essay_version: number
  content: string
  word_count: number | null
  ai_feedback: Record<string, any> | null
  status: 'draft' | 'reviewed' | 'revised' | 'finalized'
  created_at: string
  updated_at: string
}

export interface Resume {
  id: string
  student_id: string
  resume_version: number
  content: Record<string, any> | null
  rendered_pdf_url: string | null
  ai_suggestions: Record<string, any> | null
  target_program_id: string | null
  status: 'draft' | 'reviewed' | 'finalized'
  created_at: string
  updated_at: string
}


// === SAVED LISTS ===
// Spec 13 §4.2 — persisted priority. Spec 13 §4.4 — derived status.
export type SavedPriority = 'considering' | 'planning_to_apply' | 'applied' | 'dropped'
export type SavedStatus =
  | 'considering'
  | 'application_started'
  | 'submitted'
  | 'accepted'
  | 'rejected'
  | 'waitlisted'
  | 'dropped'

export interface SavedProgram {
  id: string
  list_id?: string
  program_id: string
  notes: string | null
  added_at: string
  // Spec 13 §4.2 / §4.3 — persisted curation.
  priority: SavedPriority
  tags: string[]
  // Spec 13 §4.4 — derived from application existence.
  status: SavedStatus
  // Spec 13 §7 — reach/target/safer + dual scores (from the match row).
  band_label?: MatchBand | null
  fitness_score?: number | null
  confidence_score?: number | null
  // Program / institution detail (flattened) + nested for back-compat.
  program_name?: string | null
  institution_id?: string | null
  institution_name?: string | null
  institution_country?: string | null
  institution_city?: string | null
  degree_type?: string | null
  tuition?: number | null
  application_deadline?: string | null
  acceptance_rate?: number | null
  duration_months?: number | null
  program?: ProgramSummary
}

// Spec 13 §5 — compare row carries dual fitness/confidence scores + band.
export interface ComparisonProgram {
  id: string
  institution_id: string
  program_name: string
  institution_name?: string | null
  institution_country?: string | null
  institution_city?: string | null
  degree_type?: string | null
  department?: string | null
  duration_months?: number | null
  tuition?: number | null
  delivery_format?: string | null
  acceptance_rate?: number | null
  application_deadline?: string | null
  requirements?: unknown
  fitness_score?: number | null
  confidence_score?: number | null
  band_label?: MatchBand | null
  // Legacy — drop in Phase E.
  match_score?: number | null
  match_tier?: number | null
}

export interface ComparisonResponse {
  programs: ComparisonProgram[]
  ai_analysis: string | null
}

export interface StartApplicationResponse {
  app_id: string
  program_id: string
  status: SavedStatus
  created: boolean
}


// === INTERVIEWS ===
// Spec 33 §2 interview types + §7 statuses.
export type InterviewType =
  | 'live'
  | 'recorded_async'
  | 'portfolio_review'
  | 'technical_assessment'
  | 'third_party_platform'

export type InterviewStatus =
  | 'proposed'
  | 'confirmed'
  | 'completed'
  | 'cancelled'
  | 'no_show'

export interface InterviewScoreView {
  interviewer_id: string
  criterion_scores: Record<string, number> | null
  total_weighted_score: number | null
  notes: string | null
  recommendation: string | null
  created_at: string | null
}

// Spec 33 §7 — the institution-facing rich interview shape returned by the API.
export interface Interview {
  id: string
  application_id: string
  applicant: { student_id: string | null; name: string }
  program: { id: string | null; name: string }
  interviewer_id: string | null
  interview_type: InterviewType | string
  status: InterviewStatus | string
  async_expired: boolean
  proposed_times: string[]
  proposed_slots: string[] | null
  confirmed_time: string | null
  scheduled_at: string | null
  duration_minutes: number
  location: string | null
  meeting_link: string | null
  location_or_link: string | null
  async_window_end: string | null
  recording_url: string | null
  notes_to_student: string | null
  recommendation: string | null
  scores: InterviewScoreView[]
  created_at: string | null
}

// Spec 33 §6 — interviewing rubric (with a built-in default).
export interface InterviewRubric {
  id: string | null
  rubric_name: string
  program_id: string | null
  rubric_kind: string
  criteria: Array<{ key: string; label: string; description: string; max: number }>
}


// === PROGRAM CHECKLIST ===
export interface ProgramChecklistItem {
  id: string
  program_id: string
  item_name: string
  category: 'essay' | 'test_score' | 'recommendation' | 'interview' | 'portfolio' | 'document' | 'financial' | 'other'
  requirement_level: 'required' | 'optional' | 'conditional' | 'not_applicable'
  description: string | null
  instructions: string | null
  sort_order: number
  is_active: boolean
  created_at: string
  updated_at: string
}
