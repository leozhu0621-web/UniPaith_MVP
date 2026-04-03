// ============ AUTH ============
export interface User {
  id: string
  email: string
  role: 'student' | 'institution_admin' | 'admin'
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
  preferences: StudentPreference | null
  onboarding: OnboardingStatus | null
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
  created_at: string
  updated_at: string
}

export interface OnboardingStatus {
  completion_percentage: number
  steps_completed: string[]
  next_step: { section: string; fields: string[]; guidance_text: string } | null
}

// ============ PROGRAMS ============
export interface Program {
  id: string
  institution_id: string
  program_name: string
  degree_type: 'bachelors' | 'masters' | 'phd' | 'certificate' | 'diploma'
  department: string | null
  duration_months: number | null
  tuition: number | null
  acceptance_rate: number | null
  requirements: Record<string, any> | null
  description_text: string | null
  current_preferences_text: string | null
  is_published: boolean
  application_deadline: string | null
  program_start_date: string | null
  highlights: string[] | null
  page_header_image_url: string | null
  faculty_contacts: Record<string, any>[] | null
  created_at: string
  updated_at: string
}

export interface ProgramSummary {
  id: string
  program_name: string
  degree_type: string
  department: string | null
  tuition: number | null
  application_deadline: string | null
  institution_name: string
  institution_country: string
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

// ============ APPLICATIONS ============
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
  completeness_status: string | null
  missing_items: string[] | null
  created_at: string
  updated_at: string
  program?: Program
}

export interface ApplicationChecklist {
  id: string
  student_id: string
  program_id: string
  items: { name: string; status: string; required: boolean }[]
  completion_percentage: number
  auto_generated_at: string | null
}

export interface ReadinessCheck {
  ready: boolean
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
export interface SavedProgram {
  id: string
  student_id: string
  program_id: string
  notes: string | null
  added_at: string
  program?: ProgramSummary
}

export interface ComparisonResponse {
  programs: ProgramSummary[]
  comparison: Record<string, any>
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
  capacity: number | null
  rsvp_count: number
  status: string
}

export interface RSVP {
  id: string
  event_id: string
  student_id: string
  rsvp_status: string
  registered_at: string
  attended_at: string | null
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

export interface NotificationPreference {
  email_enabled: boolean
  preferences: Record<string, boolean>
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
  logo_url: string | null
  website_url: string | null
  is_verified: boolean
  created_at: string
  updated_at: string
  program_count?: number
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

export interface PipelineData {
  total: number
  program_id: string | null
  [column: string]: any
}

// ============ DASHBOARD & ANALYTICS ============
export interface DashboardSummary {
  program_count: number
  published_program_count: number
  total_applications: number
  pending_review_count: number
  active_events_count: number
  unread_messages_count: number
}

export interface ProgramApplicationCount {
  program_name: string
  count: number
}

export interface MonthlyApplicationCount {
  month: string
  count: number
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
}

// ============ CAMPAIGNS ============
export interface Campaign {
  id: string
  institution_id: string
  program_id: string | null
  segment_id: string | null
  campaign_name: string
  campaign_type: string | null
  message_subject: string | null
  message_body: string | null
  status: string | null
  scheduled_send_at: string | null
  sent_at: string | null
  created_at: string
  updated_at: string
}

export interface CampaignMetrics {
  campaign_id: string
  total_recipients: number
  delivered: number
  opened: number
  clicked: number
  responded: number
}

// ============ SEGMENTS ============
export interface Segment {
  id: string
  institution_id: string
  program_id: string | null
  segment_name: string
  criteria: Record<string, any> | null
  is_active: boolean
  created_at: string
  updated_at: string
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

// ============ CONVERSATION ENGINE ============
export type ConversationStage =
  | 'understand_context'
  | 'identify_issues'
  | 'define_demand'
  | 'translate_requirements'
  | 'ready_for_shortlist'

export type ConversationDomain =
  | 'academic_readiness'
  | 'budget_finance'
  | 'country_location'
  | 'timeline_intake'
  | 'career_outcome'
  | 'eligibility_compliance'
  | 'learning_preferences'

export type RequirementPriority = 'must_have' | 'should_have' | 'optional'
export type RequirementSource = 'student_explicit' | 'inferred' | 'imported'
export type RequirementStatus = 'draft' | 'confirmed' | 'rejected'
export type ConfidenceLevel =
  | 'insufficient'
  | 'provisional'
  | 'recommendation_ready'
  | 'high_confidence'

export interface ConversationSession {
  session_id: string
  student_id: string
  current_stage: ConversationStage
  active_domain: ConversationDomain
  turn_count: number
  last_updated_at: string
}

export interface ConversationTurnRequest {
  session_id?: string | null
  message: string
  entrypoint?: 'chat' | 'discover_shortcut' | 'resume'
  context_program_id?: string | null
  client_event_id?: string | null
}

export interface AssistantConversationMessage {
  message_id: string
  reply_text: string
  why_asked: string | null
  suggested_next_actions: string[]
}

export interface ConversationStateDelta {
  updated_domains: ConversationDomain[]
  new_requirements_count: number
  new_conflicts_count: number
}

export interface ConfidenceSummary {
  global_confidence: number
  global_level: ConfidenceLevel
}

export interface ConversationTurnResponse {
  session: ConversationSession
  assistant_message: AssistantConversationMessage
  state_delta: ConversationStateDelta
  confidence_summary: ConfidenceSummary
}

export interface ConversationRequirement {
  requirement_id: string
  domain: ConversationDomain
  field: string
  value: unknown
  priority: RequirementPriority
  source: RequirementSource
  confidence: number
  status: RequirementStatus
  evidence_turn_ids: string[]
  updated_at: string
}

export interface UpdateConversationRequirementRequest {
  status?: RequirementStatus
  value?: unknown
  priority?: RequirementPriority
}

export interface DomainConfidence {
  domain: ConversationDomain
  status: 'unknown' | 'partial' | 'sufficient' | 'conflicting'
  confidence: number
  missing_fields: string[]
  conflicts: string[]
}

export interface ConfidenceReport {
  global_confidence: number
  global_level: ConfidenceLevel
  domain_scores: DomainConfidence[]
  blocking_issues: string[]
  computed_at: string
}

export interface ShortlistUnlockThresholds {
  global_min: number
  domain_min: number
}

export interface ShortlistUnlockReport {
  eligible: boolean
  reasons: string[]
  thresholds: ShortlistUnlockThresholds
  blocking_conflicts: string[]
  missing_required_fields: string[]
  recommended_next_actions: string[]
}

export interface ConversationConflict {
  conflict_id: string
  fields_in_conflict: string[]
  reason: string
  resolution_options: string[]
  selected_resolution: string | null
}

export interface ResumeCheckpoint {
  session: ConversationSession
  checkpoint_summary: string
  open_tasks: string[]
  last_assistant_prompt: string | null
}

export interface ResolveConversationConflictRequest {
  selected_resolution: string
}

export interface ResolveConversationConflictResponse {
  conflict_id: string
  resolved: boolean
  selected_resolution: string
  updated_confidence: ConfidenceSummary
}

export interface ConversationApiError {
  error: {
    code:
      | 'validation_error'
      | 'not_found'
      | 'forbidden'
      | 'conflict_unresolved'
      | 'insufficient_confidence'
      | 'rate_limited'
    message: string
    details?: Record<string, unknown>
  }
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
