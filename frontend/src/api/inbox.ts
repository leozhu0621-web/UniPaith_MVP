import apiClient from './client'
import type {
  InboxAttachment,
  InboxMessage,
  InboxThread,
  InboxThreadSummary,
  SuggestedReply,
} from '../types'

// Spec 17 — student Inbox. baseURL already includes /api/v1, so paths are
// /students/me/inbox/... (mirrors api/messaging.ts → /messages/...).

export interface ThreadFilters {
  application_id?: string
  type?: 'human' | 'system'
  state?: 'needs_reply' | 'requested' | 'completed' | 'status_update_only'
  sort?: 'urgent' | 'recent' | 'action_required'
}

export const getThreads = (filters?: ThreadFilters): Promise<InboxThreadSummary[]> =>
  apiClient.get('/students/me/inbox/threads', { params: filters }).then(r => r.data)

export const getThread = (id: string): Promise<InboxThread> =>
  apiClient.get(`/students/me/inbox/threads/${id}`).then(r => r.data)

export const postInboxMessage = (
  id: string,
  payload: { body: string; attachments?: InboxAttachment[]; ai_draft_used?: boolean },
): Promise<InboxMessage> =>
  apiClient.post(`/students/me/inbox/threads/${id}/messages`, payload).then(r => r.data)

export const markThreadComplete = (id: string): Promise<InboxThread> =>
  apiClient.post(`/students/me/inbox/threads/${id}/mark-complete`).then(r => r.data)

// Returns null when the AI assist is unavailable (flag off / consent / failure).
export const getSuggestedReply = (id: string): Promise<SuggestedReply | null> =>
  apiClient.post(`/students/me/inbox/threads/${id}/suggested-reply`).then(r => r.data)
