// ============ AUTH ============
export interface User {
  id: string
  email: string
  role: 'student' | 'institution_admin'
  created_at: string
}

export interface TokenResponse {
  access_token: string
  refresh_token: string | null
  expires_in: number
  token_type: string
}

// ============ STUDENT PROFILE ============
export interface StudentProfile {
  id: string
  user_id: string
  first_name: string | null
  last_name: string | null
  date_of_birth: string | null
  nationality: string | null
  country_of_residence: string | null
  bio_text: string | null
  goals_text: string | null
  created_at: string
  updated_at: string
  academic_records: AcademicRecord[]
  test_scores: TestScore[]
  activities: Activity[]
  online_presence: OnlinePresence[]
  portfolio_items: PortfolioItem[]
  research_entries: ResearchEntry[]
  languages: StudentLanguage[]
  work_experiences: WorkExperience[]
  competitions: Competition[]
  accommodations: StudentAccommodation | null
  scheduling: StudentScheduling | null
  visa_info: StudentVisaInfo | null
  data_consent: StudentDataConsent | null
  preferences: StudentPreference | null
  onboarding: OnboardingStatus | null
}

export interface OnlinePresence {
  id: string
  student_id: string
  platform_type: string
  url: string
  display_name: string | null
  created_at: string
  updated_at: string
}

export interface PortfolioItem {
  id: string
  student_id: string
  title: string
  description: string | null
  item_type: string
  url: string | null
  document_id: string | null
  display_order: number
  created_at: string
  updated_at: string
}

export interface ResearchEntry {
  id: string
  student_id: string
  title: string
  institution_lab: string | null
  field_discipline: string | null
  role: string
  advisor_name: string | null
  methods_tools: string | null
  outcomes: string | null
  outputs: string | null
  publication_link: string | null
  start_date: string | null
  end_date: string | null
  is_current: boolean
  created_at: string
  updated_at: string
}

export interface StudentLanguage {
  id: string
  student_id: string
  language: string
  proficiency_level: string
  certification_type: string | null
  certification_score: string | null
  test_date: string | null
  created_at: string
  updated_at: string
}

export interface WorkExperience {
  id: string
  student_id: string
  experience_type: string
  organization: string
  role_title: string
  description: string | null
  start_date: string | null
  end_date: string | null
  is_current: boolean
  hours_per_week: number | null
  compensation_type: string | null
  key_achievements: string | null
  supervisor_name: string | null
  organization_country: string | null
  organization_city: string | null
  created_at: string
  updated_at: string
}

export interface StudentAccommodation {
  id: string
  student_id: string
  accommodations_needed: boolean
  category: string | null
  details_text: string | null
  documentation_status: string | null
  dyslexia_friendly_mode: boolean
  font_size_pref: string | null
  created_at: string
  updated_at: string
}

export interface StudentDataConsent {
  id: string
  student_id: string
  consent_matching: boolean
  consent_outreach: boolean
  consent_research: boolean
  data_retention_preference: string | null
  deletion_requested: boolean
  deletion_requested_at: string | null
  created_at: string
  updated_at: string
}

export interface StudentVisaInfo {
  id: string
  student_id: string
  current_immigration_status: string | null
  visa_required: boolean
  target_study_country: string | null
  passport_expiration_date: string | null
  sponsorship_source: string | null
  financial_proof_available: boolean
  financial_proof_amount_band: string | null
  post_study_work_interest: boolean
  prior_visa_refusals: boolean
  travel_constraints: string | null
  work_authorization_needed: boolean
  created_at: string
  updated_at: string
}

export interface StudentScheduling {
  id: string
  student_id: string
  timezone: string | null
  general_availability: Record<string, unknown> | null
  preferred_interview_format: string | null
  campus_visit_interest: boolean
  notes: string | null
  created_at: string
  updated_at: string
}

export interface Competition {
  id: string
  student_id: string
  competition_name: string
  domain: string | null
  level: string
  role: string | null
  result_placement: string | null
  year: number | null
  team_size: number | null
  description: string | null
  link_proof: string | null
  created_at: string
  updated_at: string
}

export interface Course {
  id: string
  academic_record_id: string
  course_name: string
  course_code: string | null
  subject_area: string | null
  course_level: string
  grade: string | null
  credits: number | null
  term: string | null
  created_at: string
  updated_at: string
}

export interface AcademicRecord {
  id: string
  student_id: string
  institution_name: string
  degree_type: 'high_school' | 'bachelors' | 'masters' | 'phd' | 'associate' | 'diploma'
  field_of_study: string | null
  gpa: number | null
  gpa_scale: string | null
  start_date: string
  end_date: string | null
  is_current: boolean
  honors: string | null
  thesis_title: string | null
  country: string | null
  transcript_language: string | null
  credential_evaluation_status: string | null
  credential_evaluation_report_url: string | null
  rigor_indicator_count: number | null
  courses: Course[]
  created_at: string
  updated_at: string
}

export interface TestScore {
  id: string
  student_id: string
  test_type: 'SAT' | 'GRE' | 'GMAT' | 'TOEFL' | 'IELTS' | 'AP' | 'IB' | 'ACT' | 'LSAT' | 'MCAT' | 'DUOLINGO'
  total_score: number | null
  section_scores: Record<string, number> | null
  test_date: string | null
  is_official: boolean
  created_at: string
  updated_at: string
}

export interface Activity {
  id: string
  student_id: string
  activity_type: 'work_experience' | 'research' | 'volunteering' | 'extracurricular' | 'leadership' | 'awards' | 'publications'
  title: string
  organization: string | null
  description: string | null
  start_date: string | null
  end_date: string | null
  is_current: boolean
  hours_per_week: number | null
  impact_description: string | null
  created_at: string
  updated_at: string
}

export interface StudentPreference {
  id: string
  student_id: string
  preferred_countries: string[]
  preferred_regions: string[]
  preferred_city_size: string | null
  preferred_climate: string | null
  budget_min: number | null
  budget_max: number | null
  funding_requirement: string | null
  program_size_preference: string | null
  career_goals: string[] | null
  values_priorities: Record<string, number> | null
  dealbreakers: string[] | null
  goals_text: string | null
  // Spec 09 §5.2 — priority weights (0–10). Drive the matcher re-rank.
  weight_cost: number | null
  weight_location: number | null
  weight_outcomes: number | null
  weight_ranking: number | null
  weight_flexibility: number | null
  weight_support: number | null
  weight_time_to_degree: number | null
  stretch_target_safety_mix: string | null
  created_at: string
  updated_at: string
}

export interface OnboardingStatus {
  completion_percentage: number
  steps_completed: string[]
  next_step: { section: string; fields: string[]; guidance_text: string } | null
}

// ============ PROGRAMS ============
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
  faculty_contacts: Record<string, any>[] | null
  cost_data: ProgramCostData | Record<string, any> | null
  promotion_categories?: string[] | null
  institution_name?: string | null
  created_at: string
  updated_at: string
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

export interface SchoolSummary {
  id: string
  institution_id: string
  name: string
  description_text?: string | null
  media_urls?: string[] | null
  logo_url?: string | null
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

// ============ MATCHING ============
export interface MatchResult {
  id: string
  student_id: string
  program_id: string
  match_score: number
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

// ============ CONVERSATION / PROGRAM MATCH ============
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

// ============ APPLICATIONS ============
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
  generated_letter_url?: string | null
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
  program_id: string
  status: 'draft' | 'submitted' | 'under_review' | 'interview' | 'decision_made'
  match_score: number | null
  match_reasoning_text: string | null
  submitted_at: string | null
  decision: 'admitted' | 'rejected' | 'waitlisted' | 'deferred' | null
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

// ============ DOCUMENTS ============
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

// ============ ESSAYS & RESUMES ============
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

// ============ SAVED LISTS ============
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

// ============ MESSAGING ============
export interface Conversation {
  id: string
  student_id: string
  institution_id: string
  program_id: string | null
  subject: string | null
  status: 'open' | 'awaiting_response' | 'resolved' | 'closed'
  started_at: string
  last_message_at: string | null
  unread_count?: number
}

export interface Message {
  id: string
  conversation_id: string
  sender_type: 'student' | 'institution'
  sender_id: string
  message_body: string
  sent_at: string
  read_at: string | null
}

// ============ INBOX (Spec 17) ============
export type ActionLabel =
  | 'needs_reply'
  | 'document_requested'
  | 'clarification_required'
  | 'interview_invite'
  | 'status_update_only'
  | 'completed'

export type WaitingOn = 'student' | 'school' | 'none'

export interface InboxAttachment {
  id?: string
  name: string
  kind?: 'document' | 'link'
  url?: string | null
}

export interface InboxThreadApplication {
  program_name: string | null
  institution_name: string | null
}

export interface InboxParticipant {
  id: string
  role: 'student' | 'admissions_officer' | 'system'
  name: string
}

export interface InboxMessage {
  id: string
  thread_id: string
  sender: 'student' | 'admissions_officer' | 'system'
  body: string
  attachments: InboxAttachment[]
  sent_at: string
  read_at: string | null
  status: 'sent' | 'delivered' | 'read'
}

export interface InboxThreadSummary {
  id: string
  application_id: string | null
  application: InboxThreadApplication
  type: 'human' | 'system'
  subject: string | null
  action_label: ActionLabel | null
  due_date: string | null
  waiting_on: WaitingOn
  unread: boolean
  last_message_at: string | null
  linked_checklist_item_category: string | null
  linked_calendar_item_id: string | null
}

export interface InboxThread extends InboxThreadSummary {
  participants: InboxParticipant[]
  messages: InboxMessage[]
}

export interface SuggestedReply {
  draft: string
  tone: string
  length: string
  alternate_drafts: string[]
}

// ============ EVENTS ============
export interface EventItem {
  id: string
  institution_id: string
  program_id: string | null
  event_name: string
  event_type: 'webinar' | 'campus_visit' | 'info_session' | 'workshop'
  description: string | null
  location: string | null
  start_time: string
  end_time: string
  meeting_link?: string | null
  capacity: number | null
  rsvp_count: number
  // Spec 27 §3.1 — confirmed vs waitlisted split + impressions.
  confirmed_count?: number
  waitlist_count?: number
  view_count?: number
  status: string
}

export interface RSVP {
  id: string
  event_id: string
  student_id: string
  rsvp_status: string
  registered_at: string
  attended_at: string | null
  // Spec 27 §3.1 — attendance capture + roster identity.
  attendance_status?: string | null
  student_name?: string | null
  student_email?: string | null
}

// ============ INTERVIEWS ============
export interface Interview {
  id: string
  application_id: string
  interviewer_id: string
  interview_type: 'video' | 'in_person' | 'phone' | 'group'
  proposed_times: string[]
  confirmed_time: string | null
  location_or_link: string | null
  status: 'invited' | 'scheduling' | 'confirmed' | 'completed' | 'cancelled' | 'no_show'
  duration_minutes: number
  created_at: string
  updated_at: string
}

// ============ NOTIFICATIONS ============
export interface Notification {
  id: string
  title: string
  body: string
  notification_type: string
  is_read: boolean
  reference_type: string | null
  reference_id: string | null
  created_at: string
}

export type NotificationChannelKey = 'email' | 'sms' | 'in_app' | 'push'
export type NotificationChannels = Record<NotificationChannelKey, boolean>
export type EmailFrequency = 'all' | 'weekly' | 'important' | 'none'

export interface NotificationTypePref {
  type: string
  label: string
  essential: boolean
  channels: NotificationChannels
}

export interface NotificationPreference {
  email_enabled: boolean
  email_frequency: EmailFrequency
  preferences: Record<string, NotificationChannels> | null
  matrix: NotificationTypePref[]
}

// ============ SETTINGS (Spec 21) ============
export type ThemePref = 'light' | 'dark' | 'system'
export type FontSizePref = 'sm' | 'md' | 'lg' | 'xl'

export interface AccessibilityPrefs {
  dyslexia_mode: boolean
  font_size: FontSizePref
  reduced_motion: boolean
}

export interface SettingsPreferences {
  locale: string | null
  timezone: string | null
  theme: ThemePref
  accessibility: AccessibilityPrefs
}

export interface DeletionInfo {
  scheduled_at: string
  purge_at: string
}

export interface UserSettings {
  account: {
    email: string
    role: string
    member_since: string | null
    display_name: string | null
    photo_url: string | null
    pending_email: string | null
  }
  security: { mfa_enabled: boolean; mfa_method: string | null }
  preferences: SettingsPreferences
  notifications: NotificationTypePref[]
  email_enabled: boolean
  email_frequency: EmailFrequency
  deletion: DeletionInfo | null
}

export interface MfaEnrollResponse {
  secret: string
  otpauth_uri: string
  recovery_codes: string[]
}

export interface SessionInfo {
  id: string
  device: string
  current: boolean
  last_active: string | null
  location: string | null
}

export interface LoginEvent {
  at: string
  device: string | null
  location: string | null
  risk: string | null
}

export interface TeamMember {
  id: string
  email: string
  role: string
  status: string
  invited_at: string | null
}

export interface ReviewConfig {
  blind_review_default: boolean
  calibration_enabled: boolean
  reviewer_assignment_mode: 'round_robin' | 'load_balanced' | 'manual'
}

export interface InstitutionSettings {
  account: {
    institution_id: string | null
    name: string | null
    contact_email: string | null
    website_url: string | null
    primary_domain: string | null
    member_since: string | null
  }
  security: { mfa_enabled: boolean; mfa_method: string | null }
  preferences: SettingsPreferences
  notifications: NotificationTypePref[]
  email_enabled: boolean
  email_frequency: EmailFrequency
  team: TeamMember[]
  deletion: DeletionInfo | null
  review_config: ReviewConfig
}

// ============ RECOMMENDATIONS ============
export interface RecommendationRequest {
  id: string
  student_id: string
  recommender_name: string
  recommender_email: string | null
  recommender_title: string | null
  recommender_institution: string | null
  relationship: string | null
  status: 'draft' | 'requested' | 'submitted' | 'received'
  requested_at: string | null
  due_date: string | null
  notes: string | null
  target_program_id: string | null
  created_at: string
  updated_at: string
}

// ============ INSTITUTION ============
export interface Institution {
  id: string
  admin_user_id: string
  name: string
  type: string
  country: string
  region: string | null
  city: string | null
  ranking_data: Record<string, number> | null
  description_text: string | null
  campus_description: string | null
  campus_setting: 'urban' | 'suburban' | 'rural' | null
  student_body_size: number | null
  founded_year: number | null
  contact_email: string | null
  contact_phone: string | null
  logo_url: string | null
  website_url: string | null
  media_gallery: string[] | null
  social_links: Record<string, string> | null
  inquiry_routing: Record<string, any> | null
  support_services: Record<string, any> | null
  policies: Record<string, any> | null
  international_info: Record<string, any> | null
  school_outcomes: Record<string, any> | null
  is_verified: boolean
  require_campaign_approval?: boolean
  setup_complete?: boolean
  setup_state?: InstitutionSetupState | null
  created_at: string
  updated_at: string
  program_count?: number
}

// ============ INSTITUTION SETUP (Spec 30) ============
export interface SetupStepsComplete {
  profile: boolean
  program: boolean
  data: boolean
  team: boolean
}

export interface InstitutionSetupState {
  institution_id: string | null
  step: 1 | 2 | 3 | 4 | 'done'
  steps_complete: SetupStepsComplete
  skipped: { data: boolean; team: boolean }
  first_program_id: string | null
  setup_complete: boolean
  published_program_count: number
}

export interface SetupStepPatch {
  step?: 1 | 2 | 3 | 4
  skip_data?: boolean
  skip_team?: boolean
  mark_complete?: Partial<SetupStepsComplete>
}

// ============ REVIEW / SCORING ============
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
  status: 'open' | 'resolved' | 'dismissed'
  resolved_by: string | null
  resolved_at: string | null
  resolution_notes: string | null
  created_at: string
}

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

// ============ PRIORITY QUEUE ============
export interface PrioritizedApplication {
  application_id: string
  student_id: string
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

// ============ DASHBOARD & ANALYTICS ============
export interface DashboardSummary {
  program_count: number
  published_program_count: number
  total_applications: number
  pending_review_count: number
  active_events_count: number
  unread_messages_count: number
  acceptance_rate: number | null
  yield_rate: number | null
}

export interface ProgramApplicationCount {
  program_name: string
  count: number
}

export interface MonthlyApplicationCount {
  month: string
  count: number
}

export interface FunnelStage {
  stage: string
  count: number
  conversion_rate: number | null
}

export interface CampaignAttributionData {
  campaign_id: string
  campaign_name: string
  recipients: number
  delivered: number
  opened: number
  clicked: number
  applications_started: number
}

export interface EventAttributionData {
  event_id: string
  event_name: string
  rsvps: number
  attended: number
  applications_after: number
}

export interface AnalyticsData {
  total_applications: number
  acceptance_rate: number | null
  avg_match_score: number | null
  yield_rate: number | null
  apps_by_status: Record<string, number>
  apps_by_program: ProgramApplicationCount[]
  apps_by_month: MonthlyApplicationCount[]
  decisions_breakdown: Record<string, number>
  funnel_stages: FunnelStage[] | null
  campaign_attribution: CampaignAttributionData[] | null
  event_attribution: EventAttributionData[] | null
}

// ============ CAMPAIGNS ============
// ============ CAMPAIGNS (Spec 25) ============
export type CampaignObjective =
  | 'application_open'
  | 'event_promotion'
  | 'scholarship_announcement'
  | 'deadline_reminder'
  | 'nurture'
  | 'general'
export type CampaignDestinationType =
  | 'institution_page'
  | 'program_page'
  | 'campaign_landing_page'
  | 'external_url'
export type CampaignCtaType = 'learn_more' | 'rsvp_event' | 'request_info' | 'start_application'
export type CampaignChannel = 'internal_messaging' | 'external_email'
export type CampaignStatus =
  | 'draft'
  | 'pending_approval'
  | 'scheduled'
  | 'active'
  | 'paused'
  | 'completed'
export type AttributionAction =
  | 'view'
  | 'save'
  | 'rsvp'
  | 'request_info'
  | 'apply_started'
  | 'apply_submitted'
  | 'decision'

export interface CampaignAudience {
  segment_ids: string[]
  uploaded_list_ids: string[]
  deduped_count: number | null
}

export interface CampaignMetrics {
  campaign_id?: string
  sent: number
  delivered: number
  opens: number
  clicks: number
  conversions: Record<string, number>
  unsubscribes: number
  bounces: number
}

export interface Campaign {
  id: string
  institution_id: string
  name: string
  objective: CampaignObjective | null
  owner_id: string | null
  status: CampaignStatus
  associate_program_ids: string[]
  associate_intake_round_id: string | null
  destination_type: CampaignDestinationType | null
  destination_id: string | null
  destination_url: string | null
  cta_type: CampaignCtaType | null
  channels: CampaignChannel[]
  audience: CampaignAudience
  subject: string | null
  body: string | null
  scheduled_at: string | null
  sent_at: string | null
  sent_count: number | null
  metrics: CampaignMetrics | null
  submitted_for_approval_at: string | null
  approved_by: string | null
  approved_at: string | null
  rejection_comment: string | null
  requires_approval: boolean
  created_at: string
  updated_at: string
}

export interface AudienceSamplePerson {
  student_id: string | null
  name: string | null
  email: string | null
  source: string
  channel: string
}

export interface AudiencePreview {
  campaign_id?: string | null
  deduped_count: number
  platform_count: number
  uploaded_count: number
  suppressed_count: number
  consent_excluded_count: number
  sample: AudienceSamplePerson[]
}

export interface UploadedList {
  id: string
  institution_id: string
  name: string
  description: string | null
  source: string
  source_consent_confirmed: boolean
  contact_count: number
  created_at: string
  updated_at: string
}

export interface CampaignSuppression {
  id: string
  institution_id: string
  email: string
  reason: string | null
  created_at: string
}

export interface DraftCampaignCopy {
  subject: string
  body: string
  alternate_subjects: string[]
  preview_text: string
  source: string
}

// ============ CAMPAIGN LINKS & ATTRIBUTION ============
export interface CampaignLink {
  id: string
  campaign_id: string
  institution_id: string
  destination_type: 'program' | 'institution' | 'event' | 'post' | 'custom'
  destination_id: string | null
  custom_url: string | null
  short_code: string
  label: string | null
  click_count: number
  trackable_url: string | null
  destination_name: string | null
  created_at: string
}

export interface LinkPerformance {
  link_id: string
  label: string | null
  destination_name: string | null
  clicks: number
  views: number
  saves: number
  applications: number
}

export interface CampaignAttributionDetail {
  campaign_id: string
  campaign_name: string
  recipients: number
  delivered: number
  opened: number
  clicked: number
  views: number
  saves: number
  rsvps: number
  request_infos: number
  applications: number
  links: LinkPerformance[]
}

// ============ INQUIRIES ============
export interface Inquiry {
  id: string
  institution_id: string
  program_id: string | null
  student_id: string | null
  student_name: string
  student_email: string
  subject: string
  message: string
  inquiry_type: string
  status: 'new' | 'in_progress' | 'responded' | 'closed'
  assigned_to: string | null
  response_text: string | null
  responded_at: string | null
  campaign_id: string | null
  created_at: string
  updated_at: string
  program_name: string | null
}

// ============ INSTITUTION CLAIM ============
export interface UnclaimedInstitution {
  institution_name: string
  institution_country: string | null
  institution_city: string | null
  institution_type: string | null
  institution_website: string | null
  program_count: number
  extracted_ids: string[]
}

// ============ PROGRAM CHECKLIST ============
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

// ============ INTAKE ROUNDS ============
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

// ============ COHORT COMPARISON ============
export interface CohortApplicant {
  application_id: string
  student_id: string
  student_name: string
  status: string | null
  match_score: number | null
  decision: string | null
  completeness_status: string | null
  submitted_at: string | null
  scores: {
    id: string
    reviewer_id: string
    rubric_id: string
    criterion_scores: Record<string, number> | null
    total_weighted_score: number | null
    reviewer_notes: string | null
    scored_by_type: string | null
    scored_at: string | null
  }[]
  avg_score: number | null
  gpa: number | null
  nationality: string | null
}

export interface CohortComparisonData {
  applicants: CohortApplicant[]
  count: number
}

// ============ COMMUNICATION TEMPLATES ============
export interface CommunicationTemplate {
  id: string
  institution_id: string
  program_id: string | null
  template_type: string
  name: string
  subject: string
  body: string
  variables: string[] | null
  is_default: boolean
  is_active: boolean
  created_at: string
  updated_at: string
  program_name: string | null
}

export interface TemplatePreview {
  rendered_subject: string
  rendered_body: string
  variables_used: string[]
}

// ============ AUDIT LOG ============
export interface AuditLogEntry {
  id: string
  institution_id: string
  application_id: string | null
  actor_user_id: string | null
  action: string
  entity_type: string
  entity_id: string
  description: string | null
  old_value: Record<string, unknown> | null
  new_value: Record<string, unknown> | null
  metadata_json: Record<string, unknown> | null
  created_at: string
  actor_email: string | null
}

export interface AuditLogList {
  items: AuditLogEntry[]
  total: number
}

// ============ BATCH OPERATIONS ============
export interface BatchOperationResult {
  success_count: number
  failed_ids: string[]
  errors: string[]
}

// ============ PROMOTIONS ============
export interface Promotion {
  id: string
  institution_id: string
  program_id: string | null
  promotion_type: 'spotlight' | 'featured' | 'banner'
  title: string
  description: string | null
  targeting: {
    regions?: string[]
    countries?: string[]
    degree_types?: string[]
    interests?: string[]
  } | null
  status: 'draft' | 'scheduled' | 'active' | 'paused' | 'expired'
  starts_at: string | null
  ends_at: string | null
  impression_count: number
  click_count: number
  // Spec 27 §4.1 — promotion target: program | institution | landing.
  target_kind?: 'program' | 'institution' | 'landing'
  target_url?: string | null
  created_at: string
  updated_at: string
  program_name: string | null
  institution_name: string | null
  is_eligible: boolean
}

// ============ SEGMENTS (Spec 26 · Audience Segmentation) ============

/** One leaf rule: a signal field + operator + value. */
export interface SegmentRule {
  field: string
  operator: string
  value?: any
  branch?: 'include' | 'exclude'
  ambiguous?: boolean
}

/** A nested AND/OR/NOT group of rules or sub-groups. */
export interface SegmentRuleGroup {
  op: 'AND' | 'OR' | 'NOT'
  rules: Array<SegmentRule | SegmentRuleGroup>
}

/** The stored rule tree: separate include / exclude branches. */
export interface SegmentRuleTree {
  include: SegmentRuleGroup
  exclude: SegmentRuleGroup
}

export interface Segment {
  id: string
  institution_id: string
  program_id: string | null
  segment_name: string
  description?: string | null
  rules?: SegmentRuleTree | null
  criteria: Record<string, any> | null
  uploaded_list_ids?: string[] | null
  frequency_cap_per_week?: number | null
  created_by_user_id?: string | null
  preview_audience_count?: number | null
  preview_generated_at?: string | null
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface SignalDef {
  key: string
  label: string
  category: string
  category_label: string
  operators: string[]
  value_type: 'enum_multi' | 'enum_single' | 'number' | 'band' | 'boolean' | 'days'
  options: Array<{ value: string; label: string }> | null
  plain_language: string
  protected: boolean
  derived: boolean
  help_text: string
}

export interface SignalDictionary {
  categories: Array<{ key: string; label: string }>
  signals: SignalDef[]
}

export interface StudentSummary {
  student_id: string
  name: string
  email: string | null
  nationality: string | null
  country_of_residence: string | null
  fit_band: string | null
}

export interface SegmentPreview {
  audience_count: number
  platform_count: number
  uploaded_external_count: number
  sample: StudentSummary[]
  composition: Record<string, Record<string, number>>
  fairness_warning: string | null
}

export interface NLBridgeResult {
  rules: SegmentRule[]
  confidence_overall: number
  ambiguity_notes: string[]
}

// ============ INTERVIEW SCORING ============
export interface InterviewScore {
  id: string
  interview_id: string
  interviewer_id: string
  criterion_scores: Record<string, number> | null
  total_weighted_score: number | null
  interviewer_notes: string | null
  recommendation: 'strong_admit' | 'admit' | 'borderline' | 'reject' | null
}

// ============ INSTITUTION DATASETS ============
export type DatasetType = 'admissions_history' | 'prospect_list' | 'outcomes_summary'
export type DatasetStatus = 'uploaded' | 'validated' | 'processed' | 'failed' | 'pending' | 'active' | 'archived'

export interface DatasetHistogramColumn {
  top: { value: string; count: number }[]
  null_count: number
  distinct: number
}
export type DatasetHistogram = Record<string, DatasetHistogramColumn>

export interface InstitutionDataset {
  id: string
  institution_id: string
  dataset_name: string
  dataset_type: 'admissions_history' | 'prospect_list' | 'outcomes_summary'
  description: string | null
  file_name: string
  file_size_bytes: number | null
  row_count: number | null
  column_mapping: Record<string, string> | null
  validation_errors: ValidationReport | null
  status: DatasetStatus
  usage_scope: string | null
  coverage_start: string | null
  coverage_end: string | null
  version: number
  created_at: string
  updated_at: string
  download_url?: string
  used_by?: string[]
}

export interface ValidationReport {
  missing_required?: { row: number; field: string }[]
  duplicates?: { row: number; duplicate_of_row?: number }[]
  invalid_dates?: { row: number; field: string; value: string }[]
  unmappable_programs?: { row: number; value: string; suggestions?: string[] }[]
  error_count?: number
  total_rows?: number
  valid_rows?: number
  summary?: string
}

/** Legacy alias for Spec 24 data-upload modules. */
export type DatasetValidationReport = ValidationReport

export interface DatasetInspect {
  columns: string[]
  rows: Record<string, string>[]
  total_rows: number
  histogram: DatasetHistogram
}

export interface DatasetPreview {
  columns: string[]
  rows: Record<string, string>[]
  total_rows: number
  column_histogram?: Record<string, Record<string, number>>
}

export interface DatasetVersion {
  id: string
  dataset_id: string
  version_number: number
  row_count: number | null
  changes_summary: { added?: number; modified?: number; invalidated?: number } | null
  validation_report: ValidationReport | null
  uploaded_at: string
}

export interface DatasetMappingTemplate {
  id: string
  institution_id: string
  name: string
  dataset_type: string
  column_mapping: Record<string, string>
  created_at: string
  updated_at: string
}

// ============ POSTS ============
// Spec 27 §2.4 — a call-to-action attached to a post.
export type PostCTAType =
  | 'view_program'
  | 'rsvp'
  | 'request_info'
  | 'start_application'
  | 'add_to_calendar'

export interface PostCTA {
  type: PostCTAType
  label: string
  target?: string | null
}

// Spec 27 §2.3 — visibility scope for a post.
export interface PostVisibility {
  public: boolean
  segment_ids: string[]
  region_scopes: string[]
}

export interface InstitutionPost {
  id: string
  institution_id: string
  author_id: string | null
  title: string
  body: string
  media_urls: { url: string; type: string; caption?: string }[] | null
  pinned: boolean
  tagged_program_ids: string[] | null
  tagged_intake: string | null
  status: 'draft' | 'published' | 'scheduled' | 'archived'
  scheduled_for: string | null
  published_at: string | null
  is_template: boolean
  template_name: string | null
  view_count: number
  // Spec 27 §5 — per-object engagement counters.
  click_count?: number
  save_count?: number
  request_info_count?: number
  apply_started_count?: number
  // Spec 27 §2.4 / §2.3 — authored CTAs + visibility scope.
  ctas?: PostCTA[] | null
  visibility?: PostVisibility | null
  created_at: string
  updated_at: string
  author_email?: string
  program_names?: string[]
}

// ============ PIPELINE KANBAN ============
export type PipelineColumn =
  | 'discovered'
  | 'applied'
  | 'under_review'
  | 'interview'
  | 'decision_made'
  | 'enrolled'

export interface PipelineCard {
  application: Application
  student_name: string
  match_score: number | null
  last_activity: string | null
  scores: ApplicationScore[]
}

// ============ ADMIN DATABASE CONTROL ============
export interface DatabaseHealthSnapshot {
  api_reachable: boolean
  database: { status: 'healthy' | 'degraded'; latency_ms: number }
  jobs: { recent_failed_24h: number; last_job_at: string | null }
  footprint: {
    tracked_entities: number
    users: number
    institutions: number
    programs: number
    applications: number
    matches: number
    embeddings: number
  }
  last_admin_action_at: string | null
  generated_at: string
}

export interface DatabaseQualityItem {
  entity: string
  missing_count: number
  duplicate_count: number
  invalid_count: number
  risk_score: number
  severity: 'low' | 'medium' | 'high'
  recommended_action: 'monitor' | 'run_dedupe' | 'run_repair'
}

export interface DatabaseQualitySnapshot {
  items: DatabaseQualityItem[]
  generated_at: string
}

export interface DatabaseRecommendation {
  entity: string
  action: 'run_dedupe' | 'run_repair'
  priority_score: number
  reason: string
  auto_generated: boolean
}

export interface DatabaseRecommendationsSnapshot {
  items: DatabaseRecommendation[]
  generated_at: string
}

export interface DatabaseJobItem {
  id: string
  status: string
  pages_crawled: number
  items_extracted: number
  items_ingested: number
  error_log: Record<string, any> | null
  created_at: string | null
  completed_at: string | null
}

export interface DatabaseActionAuditItem {
  id: string
  action: string
  entity_type: string
  entity_id: string
  payload_json: Record<string, any> | null
  created_at: string | null
}

/** Latest row from `crawl_jobs` (university data crawler), not the knowledge frontier. */
export interface LatestCrawlRun {
  id?: string
  status?: string
  items_extracted?: number
  created_at?: string | null
  started_at?: string | null
  completed_at?: string | null
}

export interface AdminCrawlerSnapshot {
  active_sources: number
  active_jobs: number
  pending_review_items: number
  latest_crawl?: LatestCrawlRun | null
}

// ============ ADMIN ARCHITECTURE TRACE ============
export type ArchitectureStageStatus = 'ok' | 'warning' | 'error' | 'idle'

export interface ArchitectureStageTrace {
  stage_id: string
  label: string
  status: ArchitectureStageStatus
  last_run_at: string | null
  duration_ms: number | null
  counts: Record<string, string | number | null>
  error: string | null
  source: string
}

export interface ArchitectureRunTrace {
  run_id: string
  run_type: 'engine' | 'training' | 'evaluation' | 'crawler' | 'promotion' | 'outcome'
  status: 'ok' | 'warning' | 'error' | 'idle' | 'degraded'
  started_at: string | null
  completed_at: string | null
  duration_ms: number | null
  stage_id: string
  mode: string | null
  trigger_reason: string | null
  metrics: Record<string, unknown>
  links: Record<string, string>
}

export interface ArchitectureTraceResponse {
  generated_at: string
  stages: ArchitectureStageTrace[]
  runs: ArchitectureRunTrace[]
}

export interface MLLearningKPIResponse {
  generated_at: string
  latest_outcome_at: string | null
  latest_evaluation_at: string | null
  latest_training_at: string | null
  hours_outcome_to_eval_latest: number | null
  hours_eval_to_training_latest: number | null
  retrain_runs_24h: number
  retrain_runs_7d: number
  promotions_7d: number
  rollbacks_7d: number
  promotion_hit_rate_7d: number | null
  training_failure_rate_7d: number | null
  net_accuracy_uplift_vs_active: number | null
  avg_evaluation_duration_ms_7d: number | null
  avg_training_duration_ms_7d: number | null
  runtime_provider: string | null
  runtime_mode: string | null
}

// ============ KNOWLEDGE ENGINE ============

export interface KnowledgeEngineState {
  status: string
  rpm: number
  requests_this_minute: number
  total_processed: number
  total_errors: number
  total_discovered: number
  last_tick_at: string | null
  last_error: string | null
  paused: boolean
  current_url: string | null
  session_started_at: string | null
}

export interface KnowledgeStats {
  total_documents: number
  active_documents: number
  by_format: Record<string, number>
  by_type: Record<string, number>
}

export interface FrontierStats {
  pending: number
  failed: number
}

/** Single-row snapshot from Postgres after each scheduler/API tick (cross-request truth). */
export interface KnowledgeEnginePersisted {
  last_tick_at: string | null
  last_processed: number
  last_errors: number
  last_discovered: number
  last_skipped: number
  last_bootstrap_added: number
  frontier_pending_before: number
  frontier_pending_after: number
  batch_was_empty: boolean
  tick_status: string
  last_error_message: string | null
  cumulative_processed: number
  cumulative_errors: number
  ai_mock_mode: boolean
  gpu_mode: string
}

export interface KnowledgeEngineRuntimeFlags {
  openai_key_configured: boolean
  ai_mock_mode: boolean
  gpu_mode: string
  engine_bootstrap_enabled: boolean
}

export interface KnowledgeStatusResponse {
  engine: KnowledgeEngineState
  knowledge: KnowledgeStats
  frontier: FrontierStats
  engine_persisted?: KnowledgeEnginePersisted | null
  engine_runtime_flags?: KnowledgeEngineRuntimeFlags | null
}

export interface KnowledgeDirective {
  id: string
  directive_type: string
  directive_key: string
  directive_value: Record<string, unknown>
  description: string | null
  priority: number
  is_active: boolean
  expires_at: string | null
  created_at: string | null
}

export interface KnowledgeDocument {
  id: string
  title: string | null
  source_url: string | null
  source_domain: string | null
  content_format: string
  content_type: string | null
  quality_score: number | null
  processing_status: string
  word_count: number | null
  created_at: string | null
}

export interface FrontierItem {
  id: string
  url: string
  domain: string
  priority: number
  status: string
  crawl_count: number
  discovery_method: string | null
  last_crawled_at: string | null
  consecutive_failures: number
}

export interface PipelineStageStatus {
  status: string
  last_activity_at: string | null
  items_processed_total: number
  items_processed_hour: number
  queue_depth: number
  last_error: string | null
  extra: Record<string, unknown> | null
  worker_heartbeat_at: string | null
  worker_hostname: string | null
  budget_spent_this_hour: number
  budget_per_hour: number
}

export interface PipelineStatus {
  enabled: boolean
  stages: Record<string, PipelineStageStatus>
  totals: {
    raw_docs_queued: number
    docs_completed: number
    frontier_pending: number
    outcome_count: number
  }
  budget: {
    per_hour: number
    spent_this_hour: number
  }
}

// ============ PHASE A — DISCOVERY ============

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

// ============ PHASE A — DISCOVERY ARTIFACTS ============

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

// ============ PHASE A — STRATEGY ============

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

// ============ PHASE A — MATCH DUAL SCORES ============

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
  fitness_score: string
  confidence_score: string
  fitness_breakdown: Record<string, unknown> | null
  confidence_breakdown: Record<string, unknown> | null
  rationale_text: string | null
  rationale_generated_at: string | null
  strategy_version_id: string | null
  // DEPRECATED — drop in Phase E. Kept for backcompat during transition.
  match_score: string | null
  score_breakdown: Record<string, unknown> | null
  match_tier: number | null
  reasoning_text: string | null
  model_version: string | null
  computed_at: string
  is_stale: boolean
  program_name?: string | null
  institution_name?: string | null
  degree_type?: string | null
  tuition?: number | null
  acceptance_rate?: number | null
  // Spec 09 §6 / §4A — derived on the server and carried on every match.
  band_label?: MatchBand | null
  probability_bands?: ProbabilityBands | null
}

// Spec 09 §4A — GET /me/matches/:id/probability response.
export interface ProbabilityBandsResponse {
  program_id: string
  probability_bands: ProbabilityBands | null
  match_ready: boolean
  reason: string | null // "no_history" | "not_match_ready" | "disabled" | null
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

// ============ PHASE A — WORKSHOP FEEDBACK ============

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
  input_artifact_id: string | null
  prompt_text: string | null
  rubric_scores: Record<string, number>
  structural_issues: StructuralIssue[]
  missing_elements: MissingElement[]
  suggested_questions: SuggestedQuestion[]
  is_stub: boolean
  created_at: string
}
