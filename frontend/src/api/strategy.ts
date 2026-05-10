/**
 * Phase A — Student strategy API client.
 *
 * Strategy is the broad-strategy artifact bridging Discovery → Match. New
 * strategies land as `draft`; promote with activate(). Editing an active
 * strategy archives it and creates a NEW draft (not auto-activated) — the
 * caller must explicitly activate the new id if they want it live.
 */
import apiClient from './client'
import type {
  AcademicPathStep,
  FinancialPathItem,
  GeographicPathItem,
  StudentStrategy,
} from '../types'

const BASE = '/students/me/strategy'

export interface UpdateStrategyBody {
  career_target?: string | null
  target_degree?: string | null
  academic_path?: AcademicPathStep[]
  financial_path?: FinancialPathItem[]
  geographic_path?: GeographicPathItem[]
  narrative?: string | null
}

export const generateStrategy = (): Promise<StudentStrategy> =>
  apiClient.post(`${BASE}/generate`).then(r => r.data)

/**
 * Returns null if the student has no active strategy yet — surface a
 * "generate strategy" CTA in that case.
 */
export const getActiveStrategy = (): Promise<StudentStrategy | null> =>
  apiClient.get(`${BASE}/active`).then(r => r.data)

export const listStrategyVersions = (): Promise<StudentStrategy[]> =>
  apiClient.get(`${BASE}/versions`).then(r => r.data)

export const getStrategy = (id: string): Promise<StudentStrategy> =>
  apiClient.get(`${BASE}/${id}`).then(r => r.data)

export const activateStrategy = (id: string): Promise<StudentStrategy> =>
  apiClient.post(`${BASE}/${id}/activate`).then(r => r.data)

/**
 * Manual edit — archives the original (must be draft or active) and creates
 * a new draft with the patch applied. NOT auto-activated.
 */
export const updateStrategy = (
  id: string,
  body: UpdateStrategyBody,
): Promise<StudentStrategy> =>
  apiClient.patch(`${BASE}/${id}`, body).then(r => r.data)

export type {
  AcademicPathStep,
  FinancialPathItem,
  GeographicPathItem,
  StudentStrategy,
}
