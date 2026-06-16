// Material ingest — "upload any file, Uni reads it, turns it into My Space."
// Multipart upload → AI-proposed profile → student confirms → written to profile.
import apiClient from './client'

export interface ProposedProfile {
  summary?: string
  profile?: Record<string, unknown>
  online_presence?: Record<string, unknown>[]
  languages?: Record<string, unknown>[]
  academic_records?: Record<string, unknown>[]
  test_scores?: Record<string, unknown>[]
  activities?: Record<string, unknown>[]
  work_experiences?: Record<string, unknown>[]
  goals?: Record<string, unknown>[]
  needs?: Record<string, unknown>[]
  identity?: {
    core_values?: Record<string, unknown>[]
    worldview?: Record<string, unknown>[]
    self_awareness?: Record<string, unknown>[]
  }
}

export interface MaterialIngest {
  id: string
  filename: string | null
  mime_type: string | null
  status: 'parsed' | 'applied' | 'failed'
  proposed: ProposedProfile | null
  applied_summary: { counts?: Record<string, number>; skipped?: Record<string, number> } | null
  error: string | null
}

export interface ApplyResult {
  counts: Record<string, number>
  skipped: Record<string, number>
}

export const uploadMaterial = (file: File): Promise<MaterialIngest> => {
  const form = new FormData()
  form.append('file', file)
  return apiClient
    .post('/students/me/materials', form, { headers: { 'Content-Type': 'multipart/form-data' } })
    .then(r => r.data)
}

export const applyMaterial = (id: string, selection: Partial<ProposedProfile>): Promise<ApplyResult> =>
  apiClient.post(`/students/me/materials/${id}/apply`, selection).then(r => r.data)

export const listMaterials = (): Promise<MaterialIngest[]> =>
  apiClient.get('/students/me/materials').then(r => r.data)

export interface FollowupQuestion {
  id: string
  category: string
  target_field: string
  kind: 'text' | 'choice'
  prompt: string
  options?: string[]
  ref?: Record<string, unknown>
}

export const getFollowups = (ingestId: string): Promise<FollowupQuestion[]> =>
  apiClient.get(`/students/me/materials/${ingestId}/followups`).then(r => r.data.questions ?? [])

export const answerFollowup = (
  gap: FollowupQuestion,
  answer: string,
): Promise<{ applied: boolean; target_field: string }> =>
  apiClient.post('/students/me/materials/followups/answer', { gap, answer }).then(r => r.data)
