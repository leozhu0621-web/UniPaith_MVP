import apiClient from './client'
import type {
  DataGovernanceResponse,
  DataGovernanceSettings,
  FairnessOverride,
  FairnessSignal,
  FairnessStatusResponse,
} from '../types/fairness'

// Spec 46 · Data Rights & Fairness Governance — /institutions/me/{fairness,data}

const BASE = '/institutions/me'

// ── fairness (§6) ───────────────────────────────────────────────────────────

export const getFairnessStatus = () =>
  apiClient.get(`${BASE}/fairness/status`).then(r => r.data as FairnessStatusResponse)

export const listFairnessSignals = (programId?: string) =>
  apiClient
    .get(`${BASE}/fairness/signals`, { params: programId ? { program_id: programId } : {} })
    .then(r => r.data as FairnessSignal[])

export const listFairnessOverrides = (programId?: string) =>
  apiClient
    .get(`${BASE}/fairness/overrides`, { params: programId ? { program_id: programId } : {} })
    .then(r => r.data as FairnessOverride[])

export const createFairnessOverride = (body: {
  signal_id: string
  rationale: string
  expires_weeks?: number
}) => apiClient.post(`${BASE}/fairness/overrides`, body).then(r => r.data)

export const updateFairnessThreshold = (body: { program_id: string; threshold: number }) =>
  apiClient.patch(`${BASE}/fairness/threshold`, body).then(r => r.data)

export const computeFairness = (programId?: string) =>
  apiClient
    .post(`${BASE}/fairness/compute`, programId ? { program_id: programId } : {})
    .then(r => r.data as { computed: number })

// ── data governance (§9) + sub-processors (§10) ───────────────────────────────

export const getDataGovernance = () =>
  apiClient.get(`${BASE}/data/governance`).then(r => r.data as DataGovernanceResponse)

export const updateDataGovernance = (patch: Partial<DataGovernanceSettings>) =>
  apiClient
    .patch(`${BASE}/data/governance`, patch)
    .then(r => r.data as { settings: DataGovernanceSettings })
