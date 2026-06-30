// AUTO-SPLIT from the former monolithic types/index.ts.
// Domain module — see CONTRIBUTING.md. Edit types here, not in a barrel.
// === KNOWLEDGE ENGINE ===

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
