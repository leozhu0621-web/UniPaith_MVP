// Spec 46 §9/§10/§1/§5 — institution data-governance config + disclosure surfaces.
// (Spec 46 §6 fairness DTOs live in api/fairness.ts, owned by the §6 build.)

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
