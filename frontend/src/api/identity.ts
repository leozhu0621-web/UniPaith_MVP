/**
 * Phase A — Student identity (deepest profile layer) API client.
 *
 * Single row per student. The backend's PUT is partial-merge — fields not
 * sent are PRESERVED; passing `[]` explicitly is the intentional way to
 * clear a list. The frontend should NEVER read-then-write the whole object;
 * instead, send only the keys you intend to mutate.
 */
import apiClient from './client'
import type {
  CoreValue,
  SelfAwarenessItem,
  StudentIdentity,
  WorldviewItem,
} from '../types'

const BASE = '/students/me/identity'

export interface UpsertIdentityBody {
  core_values?: CoreValue[]
  worldview?: WorldviewItem[]
  self_awareness?: SelfAwarenessItem[]
  identity_summary?: string | null
  last_session_id?: string | null
}

export const getIdentity = (): Promise<StudentIdentity> =>
  apiClient.get(BASE).then(r => r.data)

export const upsertIdentity = (body: UpsertIdentityBody): Promise<StudentIdentity> =>
  apiClient.put(BASE, body).then(r => r.data)

export const regenerateIdentitySummary = (): Promise<StudentIdentity> =>
  apiClient.post(`${BASE}/regenerate-summary`).then(r => r.data)

export type { CoreValue, SelfAwarenessItem, StudentIdentity, WorldviewItem }
