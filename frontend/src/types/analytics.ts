// AUTO-SPLIT from the former monolithic types/index.ts.
// Domain module — see CONTRIBUTING.md. Edit types here, not in a barrel.
// === DASHBOARD & ANALYTICS ===
export interface PriorityQueueItem {
  category: string
  count: number
  deep_link: string
}

export interface FairnessSignal {
  status: 'ok' | 'warning' | 'insufficient_data'
  message: string
  dimension?: string
  pool?: number
}

export interface DashboardSummary {
  program_count: number
  published_program_count: number
  total_applications: number
  pending_review_count: number
  active_events_count: number
  unread_messages_count: number
  acceptance_rate: number | null
  yield_rate: number | null
  // Spec 31 · Admissions Intake contract (§2 / §8)
  cycle?: string | null
  avg_match?: number | null
  conversion_pct?: number | null
  projected_yield_pct?: number | null
  new_inquiries_24h?: number
  unanswered_inquiries_4h?: number
  integrity_signals_count?: number
  priority_queue?: PriorityQueueItem[]
  fairness?: FairnessSignal | null
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


// === ATTRIBUTION & FUNNEL ANALYTICS (Spec 28) ===

export interface AnalyticsFilters {
  program_id?: string
  intake_id?: string
  segment_id?: string
  campaign_id?: string
  source_kind?: string
  source_id?: string
  time_window?: string
  from?: string
  to?: string
}

export interface KpiMetric {
  value: number | null
  prior: number | null
  delta_pct: number | null
  unit: 'count' | 'percent' | 'score'
}

export interface NamedCount {
  label: string
  count: number
}

export interface PeriodCount {
  period: string
  count: number
}

export interface OverviewReport {
  filter: AnalyticsFilters
  total_applications: KpiMetric
  acceptance_rate: KpiMetric
  avg_match_score: KpiMetric
  yield_rate: KpiMetric
  apps_by_status: Record<string, number>
  apps_by_program: NamedCount[]
  apps_over_time: PeriodCount[]
  decisions_breakdown: Record<string, number>
  has_data: boolean
  generated_at: string
}

export interface FunnelStageItem {
  stage: string
  label: string
  count: number
  conversion_from_prev: number | null
}

export interface SubFunnel {
  key: string
  label: string
  stages: FunnelStageItem[]
}

export interface TopSource {
  source_id: string | null
  source_kind: string
  label: string
  action_count: number
}

export interface DropOffAlert {
  from_stage: string
  to_stage: string
  drop_pct: number
  hint: string
}

export interface FunnelReport {
  filter: AnalyticsFilters
  stages: FunnelStageItem[]
  sub_funnels: SubFunnel[]
  top_sources_by_clicks: TopSource[]
  top_sources_by_apply_started: TopSource[]
  drop_off_alerts: DropOffAlert[]
  total_events: number
  has_data: boolean
  generated_at: string
}

export interface CampaignMetricRow {
  campaign_id: string
  campaign_name: string
  channels: string[]
  status: string | null
  send_volume: number
  delivered: number
  delivery_rate: number | null
  opened: number
  open_rate: number | null
  open_supported: boolean
  clicked: number
  click_rate: number | null
  applications_started: number
}

export interface EventMetricRow {
  event_id: string
  event_name: string
  rsvps: number
  attended: number
  attendance_rate: number | null
  applications_after: number
}

export interface TopContentRow {
  source_id: string | null
  source_kind: string
  title: string
  clicks: number
  apply_started: number
}

export interface AttributionReport {
  filter: AnalyticsFilters
  campaigns: CampaignMetricRow[]
  events: EventMetricRow[]
  top_content_by_clicks: TopContentRow[]
  top_content_by_apply_started: TopContentRow[]
  has_data: boolean
  generated_at: string
}


// === COHORT COMPARISON ===
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
