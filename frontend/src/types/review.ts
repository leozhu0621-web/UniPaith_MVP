// AUTO-SPLIT from the former monolithic types/index.ts.
// Domain module — see CONTRIBUTING.md. Edit types here, not in a barrel.
import type { IntlFeasibilityBand } from './discovery';

// === REVIEW / SCORING ===
export interface Rubric {
  id: string
  institution_id: string
  program_id: string | null
  rubric_name: string
  criteria: RubricCriterion[] | null
  is_active: boolean
  created_at: string
}

export interface RubricCriterion {
  name: string
  weight: number
  description?: string
  scale_min?: number
  scale_max?: number
  max_score?: number
}

export interface ApplicationScore {
  id: string
  application_id: string
  reviewer_id: string
  rubric_id: string
  criterion_scores: Record<string, number> | null
  total_weighted_score: number | null
  reviewer_notes: string | null
  scored_by_type: 'human' | 'ai' | null
  scored_at: string
}

export interface ReviewAssignment {
  id: string
  application_id: string
  reviewer_id: string
  assigned_at: string
  due_date: string | null
  status: 'pending' | 'in_progress' | 'completed' | null
}

export interface AIReviewSummary {
  summary: string
  strengths: string[]
  concerns: string[]
  recommended_score_range: { min: number; max: number } | null
}

export interface IntegritySignal {
  id: string
  application_id: string
  signal_type: string
  severity: 'high' | 'medium' | 'low'
  title: string
  description: string
  evidence: Record<string, unknown> | null
  status: 'open' | 'resolved' | 'dismissed' | 'acknowledged' | 'clarifying' | 'rejected'
  resolution?: 'acceptable' | 'requires_clarification' | 'reject_application' | null
  resolved_by: string | null
  resolved_at: string | null
  resolution_notes: string | null
  created_at: string
}

export type IntegrityResolution = 'acceptable' | 'requires_clarification' | 'reject_application'
export type IntegrityAction = 'acknowledge' | 'clarify' | 'reject_application' | 'resolve'

export interface AIPacketSummary {
  id: string | null
  application_id: string
  rubric_id: string | null
  overall_summary: string
  strengths: { text: string; evidence: string; source_field: string }[] | null
  concerns: { text: string; evidence: string; source_field: string }[] | null
  criterion_assessments: {
    criterion_name: string
    score: number | null
    assessment: string
    evidence: { field: string; value: string; citation?: string }[]
  }[] | null
  recommended_score: number | null
  confidence_level: 'high' | 'medium' | 'low' | null
  model_used: string | null
  generated_at: string | null
}

export interface PipelineData {
  total: number
  program_id: string | null
  [column: string]: any
}

// --- Spec 32 · Review Workspace consolidated packet ---

export interface ReviewPacketStudent {
  student_id: string
  display_name: string
  first_name: string | null
  last_name: string | null
  preferred_name: string | null
  preferred_pronouns: string | null
  date_of_birth: string | null
  age: number | null
  gender_identity: string | null
  nationality: string | null
  country_of_residence: string | null
  bio: string | null
  goals: string | null
  academics: { institution: string | null; degree: string | null; field: string | null; gpa: string | null }[]
  test_scores: { type: string; total: string | null }[]
  activities: { type: string | null; title: string | null; organization: string | null }[]
}

export interface RubricScoreRow {
  criterion: string
  weight: number | null
  max_score: number
  per_reviewer: { reviewer_id: string; reviewer_name: string; score: number; note: string | null }[]
  variance: number
  divergent: boolean
  synthesized_recommendation: string | null
}

export interface ReviewerNoteRow {
  reviewer_id: string
  reviewer_name: string
  total_weighted_score: number | null
  note: string | null
  scored_at: string | null
}

export interface HolisticFlag {
  key: string
  label: string
  value: string
  sensitivity: 'standard' | 'high'
  source: string
}

export interface HolisticContext {
  standard: HolisticFlag[]
  high_sensitivity: HolisticFlag[]
  note: string
}

export interface TestOptionalAnalysis {
  policy: 'test_optional' | 'required' | 'test_blind'
  submitted: boolean
  compatibility: string
  recommendation: string
  guardrail: string
}

export interface BlindReviewState {
  enabled: boolean
  revealed: boolean
  redacted_fields: string[]
}

export interface ReviewPacket {
  application_id: string
  student: ReviewPacketStudent
  program: { id: string; program_name: string; degree_type: string | null; department: string | null; label: string }
  ai_packet_summary: AIPacketSummary | null
  rubric_id: string | null
  rubric_scores: RubricScoreRow[]
  reviewer_notes: ReviewerNoteRow[]
  reviewer_count: number
  integrity_signals: IntegritySignal[]
  documents: { id: string; document_type: string; file_name: string; file_url: string | null; mime_type: string | null; uploaded_at: string | null }[]
  essays: { id: string; prompt_text: string | null; content: string | null; word_count: number | null; status: string | null; essay_version: number }[]
  decision: { decision: string | null; decision_notes: string | null; decision_at: string | null } | null
  offer: { id: string; offer_type: string | null; status: string | null; tuition_amount: number | null; scholarship_amount: number; response_deadline: string | null; student_response: string | null } | null
  status: string | null
  match_score: number | null
  completeness_status: string | null
  submitted_at: string | null
  locked: boolean
  blind_review: BlindReviewState
  holistic_context: HolisticContext
  test_optional: TestOptionalAnalysis
  // Spec 41 — graduate gate (shows the advisor-match tab for graduate programs).
  is_graduate?: boolean
  // Spec 38 — international signals (operational only; never a selection criterion).
  is_international: boolean
  international: {
    is_international: boolean
    credential_status: string | null
    normalized_gpa: string | null
    raw_gpa: string | null
    english: { test: string | null; score: string | null; meets_minimum: boolean | null; waiver_eligible: boolean } | null
    country_requirements: { complete: number; total: number }
    immigration_doc_status: string
    immigration_can_generate: boolean
    feasibility: { band: IntlFeasibilityBand; reasons: string[] }
    fairness_note: string
  }
}

export interface ReviewSynthesis {
  overall_recommendation: string
  agreement: 'high' | 'mixed' | 'divergent'
  per_criterion: { criterion_name: string; synthesis: string; divergent?: boolean }[]
  model_used: string
  reviewer_count: number
}

export interface ReviewAssistantAnswer {
  answer: string
  citations: string[]
  model_used: string
  grounded: boolean
}

export interface ReviewCalibration {
  panel_mean: number
  inter_rater: { criterion: string; mean_score: number; scored_pairs: number; mean_spread: number; needs_calibration: boolean }[]
  reviewer_drift: { reviewer_id: string; reviewer_name: string; n_scores: number; mean_total: number; delta_vs_panel: number; tendency: 'harsher' | 'lenient' | 'aligned' }[]
  test_optional_cohort: {
    submitters: { n: number; admitted: number; admit_rate: number | null }
    non_submitters: { n: number; admitted: number; admit_rate: number | null }
    guardrail: string
  }
  note: string
}


// === PRIORITY QUEUE ===
export interface PrioritizedApplication {
  application_id: string
  student_id: string
  student_name?: string | null
  program_id: string
  program_name: string
  status: string
  match_score: number | null
  completeness_status: string | null
  submitted_at: string | null
  priority_score: number
  priority_reasons: string[]
  deadline_days: number | null
  assigned_count: number
}


// === INTERVIEW SCORING ===
export interface InterviewScore {
  id: string
  interview_id: string
  interviewer_id: string
  criterion_scores: Record<string, number> | null
  total_weighted_score: number | null
  interviewer_notes: string | null
  recommendation: 'strong_admit' | 'admit' | 'borderline' | 'reject' | null
}
