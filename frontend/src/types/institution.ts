// AUTO-SPLIT from the former monolithic types/index.ts.
// Domain module — see CONTRIBUTING.md. Edit types here, not in a barrel.
import type { Application } from './application';
import type { ActionLabel, InboxAttachment } from './messaging';
import type { ProfileIntelligence } from './program';
import type { ApplicationScore } from './review';

// === INSTITUTION INBOX (Spec 29) ===
export type ReasonCode =
  | 'request_document'
  | 'request_clarification'
  | 'interview_invite'
  | 'status_update'
  | 'general_reply'
  | 'decision_notice'

export type InstThreadStatus = 'open' | 'awaiting_student' | 'awaiting_us' | 'closed'
export type InstThreadFilter = 'mine' | 'unassigned' | 'all'

export interface InstThreadContext {
  stage: string | null
  checklist_complete: number
  checklist_total: number
  missing_items: string[]
}

export interface InstThreadStudentRef {
  id: string
  name: string
}

export interface InstMessage {
  id: string
  thread_id: string
  sender: 'student' | 'institution' | 'admissions_officer' | 'system'
  body: string
  attachments: InboxAttachment[]
  sent_at: string
  read_at: string | null
  status: string
  ai_draft_used: boolean
}

export interface InstThreadSummary {
  id: string
  application_id: string | null
  student: InstThreadStudentRef
  program_name: string | null
  reason_label: ReasonCode | null
  action_label: ActionLabel | null
  status: InstThreadStatus
  assigned_to: string | null
  assigned_to_name: string | null
  due_date: string | null
  unread_count: number
  last_message_at: string | null
  context: InstThreadContext
}

export interface InstThread extends InstThreadSummary {
  messages: InstMessage[]
}

export interface InstSuggestedReply {
  draft: string
  tone: string
  length: string
  alternate_drafts: string[]
}

export interface IntentSuggestion {
  reason_code: ReasonCode
  confidence: number
  rationale: string
}

export interface StaffMember {
  id: string
  name: string
  email: string
  role: string
}

export interface BulkMessageResult {
  sent_count: number
  suppressed_count: number
  recipient_count: number
  thread_ids: string[]
}


// === INSTITUTION ===
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
  profile_intelligence?: ProfileIntelligence | null
  profile_intelligence_version?: number | null
  is_claimed?: boolean
  is_verified: boolean
  require_campaign_approval?: boolean
  setup_complete?: boolean
  setup_state?: InstitutionSetupState | null
  created_at: string
  updated_at: string
  program_count?: number
}


// === INSTITUTION SETUP (Spec 30) ===
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


// === INQUIRIES ===
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


// === INSTITUTION CLAIM ===
export interface UnclaimedInstitution {
  institution_name: string
  institution_country: string | null
  institution_city: string | null
  institution_type: string | null
  institution_website: string | null
  program_count: number
  extracted_ids: string[]
}


// === INSTITUTION DATASETS ===
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


// === PIPELINE KANBAN ===
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
