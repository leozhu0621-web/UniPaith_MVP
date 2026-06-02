import apiClient from './client'
import type { DataGovernanceResponse, DataGovernanceSettings } from '../types/dataGovernance'

// Spec 46 §9/§10 · Institution data-governance — /institutions/me/data

const BASE = '/institutions/me/data'

export const getDataGovernance = () =>
  apiClient.get(`${BASE}/governance`).then(r => r.data as DataGovernanceResponse)

export const updateDataGovernance = (patch: Partial<DataGovernanceSettings>) =>
  apiClient
    .patch(`${BASE}/governance`, patch)
    .then(r => r.data as { settings: DataGovernanceSettings })
