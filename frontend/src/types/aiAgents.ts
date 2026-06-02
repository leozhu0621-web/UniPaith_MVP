// Spec 45 — types for the public AI agent catalog (GET /api/v1/ai/agents).
// Mirrors unipaith-backend/src/unipaith/ai/catalog.py::build_catalog().

export interface ModelPrice {
  input: number
  output: number
}

export interface AgentTier {
  tier: string
  label: string
  role: string
  model_id: string | null
  price: ModelPrice | null
  agent_count: number
}

export interface AgentCache {
  system: string | null
  persona: string | null
}

export interface AiAgent {
  name: string
  title: string
  spec_sections: string[]
  surface: 'student' | 'institution' | 'shared'
  group: string
  purpose: string
  tier: string
  tier_label: string | null
  model_id: string | null
  consent: string | null
  consent_label: string
  mode: 'tool_use' | 'json' | 'deterministic'
  streaming: boolean
  cache: AgentCache
  fallback: string
  flag: string | null
  enabled: boolean
  prompt_file: string | null
}

export interface AiPrinciple {
  title: string
  body: string
}

export interface FallbackStep {
  trigger: string
  action: string
}

export interface CacheLayer {
  layer: string
  ttl: string
  note: string
}

export interface AiValidation {
  summary: string
  steps: string[]
}

export interface AiAgentSummary {
  agent_count: number
  llm_agent_count: number
  tier_counts: Record<string, number>
  fallback_coverage: string
  provider: string
}

export interface AiAgentCatalog {
  summary: AiAgentSummary
  tiers: AgentTier[]
  agents: AiAgent[]
  principles: AiPrinciple[]
  fallback_flow: FallbackStep[]
  cache_strategy: CacheLayer[]
  validation: AiValidation
}
