// Spec 42 §3.19–§3.20 / §4.17 — Prompt Library + Story Bank wire types.
// Mirror of unipaith-backend/src/unipaith/schemas/prompt_library.py.

export type TargetChannel = 'interview' | 'essay' | 'short_answer' | 'video'
export type FormatRequired = 'STAR' | 'CAR' | 'freeform'
export type DraftStatus = 'none' | 'draft' | 'revised' | 'final'
export type ReadinessBand = 'low' | 'medium' | 'high'

export interface BehavioralPrompt {
  prompt_key: string
  title: string
  intent_tag: string
  target_channel: TargetChannel
  time_limit_seconds: number | null
  word_limit: number | null
  format_required: FormatRequired
  evidence_required_flag: boolean
  allowed_attachments_flag: boolean
  language_option: string
  confidentiality_scope: string
  reuse_allowed_flag: 'core' | 'school_specific'
  sort_order: number
}

export interface BehavioralResponse {
  prompt_key: string
  response_text: string | null
  draft_status: DraftStatus
  version_count: number
  last_edited: string | null
  confidence_self_rating: number | null
  authenticity_confidence_flag: boolean
  needs_feedback_flag: boolean
  reviewer_feedback_received_flag: boolean
  star_situation_present: boolean
  star_task_present: boolean
  star_action_present: boolean
  star_result_present: boolean
  star_reflection_present: boolean
  impact_metric_present: boolean
  impact_metric_type: string | null
  impact_metric_value_band: string | null
  linked_story_id: string | null
  source: string
  confidence: number
  record_version: number
  updated_at: string
}

export interface BehavioralResponseUpsert {
  response_text?: string | null
  draft_status?: DraftStatus
  confidence_self_rating?: number | null
  needs_feedback_flag?: boolean
  linked_story_id?: string | null
}

export interface Story {
  id: string
  title: string
  summary: string | null
  primary_competency: string | null
  secondary_competency: string | null
  competency_tags: string[]
  context_tags: string[]
  role_type: string | null
  stakeholder_type: string | null
  conflict_type: string | null
  difficulty_tier: number | null
  recency: string | null
  duration: string | null
  scale_tier: number | null
  evidence_link: string | null
  referenceable_contact_flag: boolean
  source: string
  confidence: number
  record_version: number
  created_at: string
  updated_at: string
}

export interface StoryInput {
  title: string
  summary?: string | null
  primary_competency?: string | null
  secondary_competency?: string | null
  competency_tags?: string[]
  context_tags?: string[]
  role_type?: string | null
  stakeholder_type?: string | null
  conflict_type?: string | null
  difficulty_tier?: number | null
  duration?: string | null
  scale_tier?: number | null
  evidence_link?: string | null
  referenceable_contact_flag?: boolean
}

export interface StoryMatch {
  prompt_key: string
  prompt_title: string
  best_story_id: string
  best_story_title: string
  score: number
}

export interface RevisionItem {
  prompt_key: string
  prompt_title: string
  strength: number
  reason: string
}

export interface PromptLibrarySummary {
  total_prompts: number
  answered_count: number
  final_count: number
  draft_count: number
  stories_count: number
  inference_enabled: boolean
  interview_readiness_band: ReadinessBand | null
  interview_readiness_score: number | null
  readiness_detail: {
    band: string
    score: number
    answered: number
    core_total: number
    star_avg: number
  } | null
  competency_coverage_map: Record<string, number> | null
  competency_coverage_gaps: string[] | null
  story_prompt_matching_table: StoryMatch[] | null
  revision_priority_list: RevisionItem[] | null
  suggested_practice_plan: string | null
}
