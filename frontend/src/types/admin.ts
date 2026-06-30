// AUTO-SPLIT from the former monolithic types/index.ts.
// Domain module — see CONTRIBUTING.md. Edit types here, not in a barrel.
// === AUDIT LOG ===
// Spec 36 — list-row shape (lightweight; full diff lives on AuditEventDetail).
export interface AuditLogEntry {
  id: string
  institution_id: string | null
  application_id: string | null
  actor_user_id: string | null
  actor_role: string | null
  category: string | null
  action: string
  entity_type: string
  entity_id: string
  description: string | null
  reason: string | null
  created_at: string
  occurred_at: string | null
  actor_email: string | null
}

// Spec 36 §5 — single-event detail with full before/after diff + provenance.
export interface AuditEventDetail extends AuditLogEntry {
  old_value: Record<string, unknown> | null
  new_value: Record<string, unknown> | null
  metadata_json: Record<string, unknown> | null
  ip_address: string | null
  user_agent: string | null
}

export interface AuditLogList {
  items: AuditLogEntry[]
  total: number
}


// === BATCH OPERATIONS ===
export interface BatchOperationResult {
  success_count: number
  failed_ids: string[]
  errors: string[]
}


// === ADMIN DATABASE CONTROL ===
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


// === ADMIN ARCHITECTURE TRACE ===
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
