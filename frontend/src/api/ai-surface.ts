import apiClient from './client'

// Spec 37 §3 — human<->AI edit-diff capture. Surface endpoints return a
// `draft_token` when they generate an AI draft; the frontend threads it back
// here when the human saves/sends so the edit diff is audit-logged.

export interface AISurfaceCommitPayload {
  surface: string
  final_content: Record<string, unknown> | string
  action?: string
  draft_token?: string | null
  application_id?: string | null
}

export interface AISurfaceCommitResult {
  captured: boolean
  was_edited: boolean
  similarity: number
}

export interface AISurfaceEvent {
  id: string
  action: string
  surface: string | null
  application_id: string | null
  actor_user_id: string | null
  was_edited: boolean | null
  similarity: number | null
  training_eligible: boolean | null
  description: string | null
  created_at: string
}

export const commitAISurfaceEvent = (
  payload: AISurfaceCommitPayload
): Promise<AISurfaceCommitResult> =>
  apiClient.post('/institutions/me/ai-surface/commit', payload).then(r => r.data)

export const getAISurfaceEvents = (params?: {
  surface?: string
  application_id?: string
  limit?: number
}): Promise<AISurfaceEvent[]> =>
  apiClient.get('/institutions/me/ai-surface/events', { params }).then(r => r.data)
