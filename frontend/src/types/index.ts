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
