// AUTO-SPLIT from the former monolithic types/index.ts.
// Domain module — see CONTRIBUTING.md. Edit types here, not in a barrel.
import type { OnboardingState } from './onboarding';

// === STUDENT PROFILE ===
export interface StudentProfile {
  id: string
  user_id: string
  first_name: string | null
  last_name: string | null
  preferred_pronouns: string | null
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
  // Nullable; missing entirely when the backend predates the column (treated
  // the same as null — needs onboarding). UX overhaul Ship C §3.
  onboarding_state?: OnboardingState | null
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
