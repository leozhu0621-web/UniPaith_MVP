import apiClient from './client'

// Spec 46 §6 · Fairness governance — /institutions/me/fairness
const BASE = '/institutions/me/fairness'

export type FairnessStatus = 'green' | 'yellow' | 'red'
export type FairnessSeverity = 'info' | 'warning' | 'high' | 'auto_halt' | 'override_active'

export interface FairnessSignalDTO {
  id: string
  program_id: string
  program_name: string | null
  week_start: string
  attribute: string
  cohort_size: number
  di_ratio: number | null
  delta: number | null
  severity: FairnessSeverity
  sample_sufficient: boolean
  notes: string | null
  detail: Record<string, unknown>
}

export interface FairnessProgramBrief {
  program_id: string
  program_name: string
  matching_halted: boolean
  fairness_override_active: boolean
}

export interface FairnessOverview {
  status: FairnessStatus
  halted_count: number
  halted_programs: FairnessProgramBrief[]
  program_count: number
  latest_signals: FairnessSignalDTO[]
}

export interface FairnessAttributeBlock {
  attribute: string
  series: FairnessSignalDTO[]
  latest: FairnessSignalDTO | null
}

export interface FairnessProgramBlock extends FairnessProgramBrief {
  fairness_threshold: number
  override_expires_at: string | null
  attributes: FairnessAttributeBlock[]
}

export interface FairnessOverrideDTO {
  id: string
  program_id: string
  program_name: string | null
  rationale: string
  created_at: string | null
  override_expires_at: string | null
  revoked_at: string | null
  active: boolean
}

export interface FairnessCohorts {
  programs: FairnessProgramBlock[]
  overrides: FairnessOverrideDTO[]
}

export interface FairnessOverrideResult {
  program_id: string
  matching_halted: boolean
  fairness_override_active: boolean
  override_expires_at: string
}

export const getFairnessOverview = (): Promise<FairnessOverview> =>
  apiClient.get(`${BASE}/overview`).then(r => r.data)

export const getFairnessCohorts = (): Promise<FairnessCohorts> =>
  apiClient.get(`${BASE}/cohorts`).then(r => r.data)

export const applyFairnessOverride = (body: {
  program_id: string
  rationale: string
  weeks?: number
  signal_id?: string | null
}): Promise<FairnessOverrideResult> =>
  apiClient.post(`${BASE}/override`, body).then(r => r.data)

export const revokeFairnessOverride = (
  programId: string
): Promise<{ program_id: string; matching_halted: boolean }> =>
  apiClient.post(`${BASE}/revoke`, { program_id: programId }).then(r => r.data)

export const setFairnessThreshold = (
  programId: string,
  threshold: number
): Promise<{ program_id: string; fairness_threshold: number }> =>
  apiClient.patch(`${BASE}/threshold`, { program_id: programId, threshold }).then(r => r.data)

export const recomputeFairness = (
  weeksBack = 4
): Promise<{ computations: number }> =>
  apiClient.post(`${BASE}/recompute`, { weeks_back: weeksBack }).then(r => r.data)
