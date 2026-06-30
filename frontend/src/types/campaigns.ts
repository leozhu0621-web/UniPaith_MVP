// AUTO-SPLIT from the former monolithic types/index.ts.
// Domain module — see CONTRIBUTING.md. Edit types here, not in a barrel.
// === CAMPAIGNS ===

// === CAMPAIGNS (Spec 25) ===
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


// === CAMPAIGN LINKS & ATTRIBUTION ===
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


// === PROMOTIONS ===
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


// === SEGMENTS (Spec 26 · Audience Segmentation) ===

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
