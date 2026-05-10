/**
 * Phase A — Student needs (Maslow-keyed map) API client.
 */
import apiClient from './client'
import type {
  MaslowLevel,
  NeedSeverity,
  NeedSource,
  StudentNeed,
} from '../types'

const BASE = '/students/me/needs'

export interface CreateNeedBody {
  maslow_level: MaslowLevel
  need_type: string
  signal: string
  severity: NeedSeverity
  source?: NeedSource
  source_session_id?: string | null
  source_quote?: string | null
  confidence?: string | number | null
}

export interface UpdateNeedBody {
  maslow_level?: MaslowLevel
  need_type?: string
  signal?: string
  severity?: NeedSeverity
  source_quote?: string | null
  confidence?: string | number | null
}

export const listNeeds = (maslow_level?: MaslowLevel): Promise<StudentNeed[]> =>
  apiClient
    .get(BASE, { params: maslow_level ? { maslow_level } : undefined })
    .then(r => r.data)

export const createNeed = (body: CreateNeedBody): Promise<StudentNeed> =>
  apiClient.post(BASE, body).then(r => r.data)

export const updateNeed = (id: string, body: UpdateNeedBody): Promise<StudentNeed> =>
  apiClient.put(`${BASE}/${id}`, body).then(r => r.data)

export const deleteNeed = (id: string): Promise<void> =>
  apiClient.delete(`${BASE}/${id}`).then(() => undefined)

export type { MaslowLevel, NeedSeverity, NeedSource, StudentNeed }
