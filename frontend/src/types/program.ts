// AUTO-SPLIT from the former monolithic types/index.ts.
// Domain module — see CONTRIBUTING.md. Edit types here, not in a barrel.
import type { IntlEnglishPolicy } from './discovery';

// === PROGRAMS ===
// --- Spec 23 §3 — typed structured blobs the program editor writes ---

export type TestStance = 'required' | 'recommended' | 'test_optional' | 'test_blind'

export interface ProgramRequirementItem {
  name: string
  required: boolean
  note?: string
}

export interface ProgramApplicationRequirements {
  materials: ProgramRequirementItem[]
  prerequisites: { name: string; required: boolean; allowed_substitutes: string[] }[]
  test_policy: {
    stance: TestStance
    required: string[]
    optional: string[]
    accepted_tests: string[]
    superscore_enabled: boolean
    waived_rules: string
    typical_ranges: { test: string; low: number; high: number }[]
  }
  recommendations: { required_count: number; types: ('academic' | 'professional' | 'other')[] }
}

// Spec 23 §3 — one intake round (camel of the IntakeRound shape used by the editor).
export interface IntakeRoundForm {
  id: string
  name: string
  term: { season: string; year: number }
  open_date: string | null
  deadline: string | null
  decision_date: string | null
  start_date: string | null
  capacity: number | null
}

export interface ProgramCostData {
  tuition_amount: number | null
  tuition_currency: string
  tuition_period: 'per_year' | 'per_credit' | 'total_program'
  fees: { name: string; amount: number; required: boolean }[]
  estimated_total_cost_band: { min: number | null; max: number | null; currency: string }
  funding_signals: {
    ta_funded: boolean
    ra_funded: boolean
    merit_scholarship_available: boolean
    need_based_available: boolean
  }
  [key: string]: any // back-compat: legacy seeds carry extra keys (tuition_annual, source, …)
}

export interface ProgramOutcomesData {
  placement_rate_pct: number | null
  median_starting_salary: number | null
  salary_distribution_bands: { band_label: string; percent: number }[]
  common_roles: string[]
  top_employers: string[]
  internship_to_offer_pct: number | null
  time_to_placement_months: number | null
  outcome_reporting_window: string
  [key: string]: any // back-compat: legacy seeds carry median_salary, employment_rate, …
}

export interface ProfileEvidenceReference {
  label: string
  url: string
  source_type?: 'official' | 'institution_report' | 'government' | 'verified_secondary' | 'student_employer' | 'unknown' | string
  field_path?: string | null
  freshness?: { status?: string; checked_at?: string; effective_date?: string | null } | null
}

export interface ProfileIntelligenceFinding {
  statement: string
  source_type?: 'fact' | 'inferred' | 'institution_confirmed' | string
  confidence?: number
  time_sensitive?: boolean
  freshness?: { status?: string; checked_at?: string; effective_date?: string | null } | null
  evidence: ProfileEvidenceReference[]
}

export interface ProfileIntelligenceSection {
  findings: ProfileIntelligenceFinding[]
}

export interface ProfileIntelligence {
  standard_version: number
  profile_version: number
  generated_at?: string
  sections: Record<string, ProfileIntelligenceSection>
  omissions?: Array<{ section: string; reason: string }>
}

export interface TargetProfileSignal {
  attribute: string
  preferred_values: string[]
  statement: string
  weight: number
  confidence: number
  evidence: ProfileEvidenceReference[]
}

export interface TargetProfile {
  standard_version: number
  derived_at: string
  layers: {
    background_academic: TargetProfileSignal[]
    goals_behaviors_learning_working_style: TargetProfileSignal[]
    values_motivations_community: TargetProfileSignal[]
  }
}

export interface Program {
  id: string
  institution_id: string
  school_id?: string | null
  program_name: string
  degree_type: 'bachelors' | 'masters' | 'phd' | 'certificate' | 'diploma'
  department: string | null
  duration_months: number | null
  tuition: number | null
  acceptance_rate: number | null
  delivery_format: 'in_person' | 'online' | 'hybrid' | null
  campus_setting: 'urban' | 'suburban' | 'rural' | null
  requirements: Record<string, any> | null
  application_requirements: ProgramApplicationRequirements | Record<string, any>[] | null
  description_text: string | null
  who_its_for: string | null
  is_published: boolean
  // Spec 23 §5 — derived status + optimistic-lock version, surfaced by the API.
  status?: 'draft' | 'published'
  version?: number
  feature_version?: number
  applications_count?: number
  application_deadline: string | null
  program_start_date: string | null
  tracks: string[] | Record<string, any> | null
  outcomes_data: ProgramOutcomesData | Record<string, any> | null
  intake_rounds: IntakeRoundForm[] | Record<string, any>[] | Record<string, any> | null
  media_urls: string[] | null
  highlights: string[] | null
  faculty_contacts: Record<string, any>[] | Record<string, any> | null
  external_reviews?: Record<string, any> | null
  cost_data: ProgramCostData | Record<string, any> | null
  promotion_categories?: string[] | null
  english_policy?: IntlEnglishPolicy | null
  website_url?: string | null
  source_url?: string | null
  cip_code?: string | null
  field_provenance?: Record<string, any> | null
  class_profile?: Record<string, any> | null
  institution_name?: string | null
  institution_website_url?: string | null
  content_sources?: ContentSources | null
  profile_intelligence?: ProfileIntelligence | null
  profile_intelligence_version?: number | null
  is_claimed?: boolean
  created_at: string
  updated_at: string
}

/** Channel feeds + official social links for keyword-relevant Events/Updates
 *  (carried on institutions, schools, and programs). */
export interface ContentSources {
  news_rss?: string
  news_curated?: boolean
  events_feed?: { url: string; type: string } | null
  keywords?: string[]
  social?: {
    instagram?: string | null
    linkedin?: string | null
    x?: string | null
    youtube?: string | null
    facebook?: string | null
  } | null
}

export interface ProgramSummary {
  id: string
  institution_id: string
  program_name: string
  degree_type: string
  department: string | null
  tuition: number | null
  duration_months: number | null
  delivery_format: string | null
  acceptance_rate: number | null
  application_deadline: string | null
  institution_name: string
  institution_country: string
  institution_city: string | null
  median_salary: number | null
  employment_rate: number | null
  payback_months: number | null
  description_text?: string | null
  media_urls?: string[] | null
  highlights?: string[] | Record<string, unknown> | null
  institution_logo_url?: string | null
  institution_image_url?: string | null
  school_id?: string | null
}

/** Rich, sourced About-tab content for a school (e.g. MIT Sloan). */
export interface SchoolAboutDetail {
  founded?: number
  named_for?: string
  leadership?: string
  scale?: { faculty?: number; students?: number }
  faculty?: { name: string; title: string; focus?: string }[]
  research_centers?: string[]
  source?: { label: string; url: string }
}

export interface SchoolSummary {
  id: string
  institution_id: string
  name: string
  description_text?: string | null
  media_urls?: string[] | null
  logo_url?: string | null
  website_url?: string | null
  content_sources?: ContentSources | null
  about_detail?: SchoolAboutDetail | null
  field_provenance?: Record<string, any> | null
  profile_intelligence?: ProfileIntelligence | null
  profile_intelligence_version?: number | null
  is_claimed?: boolean
  program_count: number
  program_names: string[]
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  page_size: number
  total_pages: number
}


// === MATCHING ===
export interface MatchResult {
  id: string
  student_id: string
  program_id: string
  // Phase A dual-score split (see CLAUDE.md). `match_score` is legacy (Phase E
  // drop); consumers read `fitness_score ?? match_score`. Typed so card widgets
  // (ProgramCard / MatchCard) read the dual score without casts.
  match_score: number
  fitness_score?: number | null
  confidence_score?: number | null
  match_tier: number
  score_breakdown: Record<string, number> | null
  reasoning_text: string | null
  model_version: string | null
  computed_at: string
  is_stale: boolean
  program?: Program
}

export interface EngagementSignal {
  id: string
  student_id: string
  program_id: string
  signal_type: string
  signal_value: number
  created_at: string
}


// === CONVERSATION / PROGRAM MATCH ===
export type ConversationStage = 'understand_context' | 'identify_issues' | 'define_demand' | 'translate_requirements' | 'ready_for_shortlist'
export type ConversationDomain = 'academic_readiness' | 'budget_finance' | 'country_location' | 'timeline_intake' | 'career_outcome' | 'eligibility_compliance' | 'learning_preferences'

export interface ConversationSession {
  session_id: string
  student_id: string
  current_stage: ConversationStage
  active_domain: ConversationDomain
  turn_count: number
  last_updated_at: string
}

export interface ConversationTurnResponse {
  session: ConversationSession
  assistant_message: {
    message_id: string
    reply_text: string
    why_asked: string | null
    suggested_next_actions: string[]
  }
  state_delta: {
    updated_domains: ConversationDomain[]
    new_requirements_count: number
    new_conflicts_count: number
  }
  confidence_summary: {
    global_confidence: number
    global_level: string
  }
}

export interface ConversationRequirement {
  requirement_id: string
  domain: ConversationDomain
  field: string
  value: unknown
  priority: 'must_have' | 'should_have' | 'optional'
  source: string
  confidence: number
  status: 'draft' | 'confirmed' | 'rejected'
  updated_at: string
}

export interface ShortlistUnlock {
  eligible: boolean
  reasons: string[]
  blocking_conflicts: string[]
  missing_required_fields: string[]
  recommended_next_actions: string[]
}


// === INTAKE ROUNDS ===
export interface IntakeRound {
  id: string
  program_id: string
  round_name: string
  intake_term: string | null
  application_open: string | null
  application_deadline: string | null
  decision_date: string | null
  program_start: string | null
  capacity: number | null
  enrolled_count: number
  requirements: Record<string, unknown> | null
  status: 'upcoming' | 'open' | 'closed' | 'completed'
  is_active: boolean
  sort_order: number
  created_at: string
  updated_at: string
  spots_remaining: number | null
}
