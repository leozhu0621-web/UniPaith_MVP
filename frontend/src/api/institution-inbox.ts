import apiClient from './client'
import type {
  BulkMessageResult,
  InboxAttachment,
  InstSuggestedReply,
  InstThread,
  InstThreadFilter,
  InstThreadSummary,
  IntentSuggestion,
  ReasonCode,
  StaffMember,
} from '../types'

// Spec 29 — institution inbox. baseURL already includes /api/v1, so paths are
// /institutions/me/inbox/... (mirrors api/inbox.ts → /students/me/inbox/...).

export interface InstThreadFilters {
  filter?: InstThreadFilter
  reason?: ReasonCode
  program_id?: string
  state?: 'open' | 'awaiting_student' | 'awaiting_us' | 'closed'
}

export const getInstThreads = (filters?: InstThreadFilters): Promise<InstThreadSummary[]> =>
  apiClient.get('/institutions/me/inbox/threads', { params: filters }).then(r => r.data)

export const getInstThread = (id: string): Promise<InstThread> =>
  apiClient.get(`/institutions/me/inbox/threads/${id}`).then(r => r.data)

export interface PostInstMessagePayload {
  body: string
  reason_code: ReasonCode
  attachments?: InboxAttachment[]
  due_date?: string | null
  request_document?: boolean
  requested_item?: string | null
  ai_draft_used?: boolean
}

export const postInstMessage = (id: string, payload: PostInstMessagePayload): Promise<unknown> =>
  apiClient.post(`/institutions/me/inbox/threads/${id}/messages`, payload).then(r => r.data)

export const assignThread = (id: string, staffUserId: string | null): Promise<InstThread> =>
  apiClient
    .post(`/institutions/me/inbox/threads/${id}/assign`, { staff_user_id: staffUserId })
    .then(r => r.data)

export const closeThread = (id: string): Promise<InstThread> =>
  apiClient.post(`/institutions/me/inbox/threads/${id}/close`).then(r => r.data)

// Returns null when the AI assist is unavailable (flag off / agent failure).
export const getInstAiDraft = (id: string): Promise<InstSuggestedReply | null> =>
  apiClient.post(`/institutions/me/inbox/threads/${id}/ai-draft`).then(r => r.data)

// Returns null when the flag is off or there's no inbound message to classify.
export const getIntentSuggestion = (id: string): Promise<IntentSuggestion | null> =>
  apiClient.post(`/institutions/me/inbox/threads/${id}/intent-suggestion`).then(r => r.data)

export const getStaffRoster = (): Promise<StaffMember[]> =>
  apiClient.get('/institutions/me/inbox/staff').then(r => r.data)

export interface BulkMessagePayload {
  segment_id?: string | null
  application_ids?: string[]
  template_id?: string | null
  body?: string | null
  variables?: Record<string, string>
  reason_code: ReasonCode
  due_date?: string | null
}

export const bulkMessage = (payload: BulkMessagePayload): Promise<BulkMessageResult> =>
  apiClient.post('/institutions/me/inbox/bulk-message', payload).then(r => r.data)
