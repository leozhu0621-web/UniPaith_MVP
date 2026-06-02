// Spec 46 §6/§9/§10 — fairness auto-halt + data-governance types.

export type FairnessSeverity = 'info' | 'warning' | 'high' | 'auto_halt' | 'override_active'
export type FairnessStatus = 'ok' | 'warning' | 'halted'

export interface FairnessTrendPoint {
  week_start: string
  delta: number
}

export interface FairnessProgramStatus {
  program_id: string
  program_name: string
  matching_halted: boolean
  fairness_override_active: boolean
  override_expires_at: string | null
  fairness_threshold: number
  status: FairnessStatus
  trend: FairnessTrendPoint[]
  // attribute -> { week_start -> delta | null }
  attributes: Record<string, Record<string, number | null>>
}

export interface FairnessStatusResponse {
  overall_status: FairnessStatus
  threshold_default: number
  min_sample: number
  weeks: string[]
  programs: FairnessProgramStatus[]
}

export interface FairnessSignal {
  id: string
  program_id: string
  week_start: string
  protected_attribute: string
  cohort_size: number
  di_ratio: number | null
  delta: number | null
  severity: FairnessSeverity
  sample_sufficient: boolean
  notes: string | null
  created_at: string
}

export interface FairnessOverride {
  id: string
  program_id: string
  program_name: string
  protected_attribute: string
  rationale: string
  override_expires_at: string
  revoked_at: string | null
  active: boolean
  created_at: string
}

export interface DataGovernanceSettings {
  override_expiry_weeks_default: number
  protected_attributes_tracked: string[]
  no_training_tier: boolean
  data_residency: string
}

export interface ProgramThreshold {
  program_id: string
  program_name: string
  fairness_threshold: number
  matching_halted: boolean
}

export interface SubProcessor {
  name: string
  touches: string
  classification: string
  region: string
}

export interface BrandCommitment {
  title: string
  body: string
}

export interface RetentionRow {
  data_type: string
  retention: string
}

export interface DataGovernanceResponse {
  settings: DataGovernanceSettings
  program_thresholds: ProgramThreshold[]
  subprocessors: SubProcessor[]
  subprocessor_note: string
  brand_commitments: BrandCommitment[]
  retention_policy: RetentionRow[]
  no_data_sale: string
}
