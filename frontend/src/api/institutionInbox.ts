import apiClient from './client'
import type {
  InstInboxThread,
  InstInboxThreadSummary,
  InstSuggestedReply,
  InstBulkMessageResult,
  InstReasonCode,
  InboxMessage,
} from '../types'

export type InstInboxFilters = {
  filter?: 'mine' | 'unassigned' | 'all'
  reason?: InstReasonCode
  program_id?: string
}

export const getInstInboxThreads = (params?: InstInboxFilters) =>
  apiClient.get<InstInboxThreadSummary[]>('/institutions/me/inbox/threads', { params }).then(r => r.data)

export const getInstInboxThread = (id: string) =>
  apiClient.get<InstInboxThread>(`/institutions/me/inbox/threads/${id}`).then(r => r.data)

export const postInstInboxMessage = (
  id: string,
  payload: {
    body: string
    reason_code: InstReasonCode
    due_date?: string
    attachments?: { name: string; kind?: string; url?: string }[]
    checklist_category?: string
    ai_draft_used?: boolean
  },
) =>
  apiClient.post<InboxMessage>(`/institutions/me/inbox/threads/${id}/messages`, payload).then(r => r.data)

export const assignInstInboxThread = (id: string, staff_user_id?: string | null) =>
  apiClient
    .post<InstInboxThreadSummary>(`/institutions/me/inbox/threads/${id}/assign`, {
      staff_user_id: staff_user_id ?? null,
    })
    .then(r => r.data)

export const closeInstInboxThread = (id: string) =>
  apiClient.post<InstInboxThreadSummary>(`/institutions/me/inbox/threads/${id}/close`).then(r => r.data)

export const getInstInboxAiDraft = (id: string, reason_code?: InstReasonCode) =>
  apiClient
    .post<InstSuggestedReply | null>(`/institutions/me/inbox/threads/${id}/ai-draft`, null, {
      params: reason_code ? { reason_code } : {},
    })
    .then(r => r.data)

export const postInstBulkMessage = (payload: {
  segment_id?: string
  application_ids?: string[]
  template_id?: string
  body?: string
  variables?: Record<string, string>
  reason_code: InstReasonCode
  due_date?: string
}) =>
  apiClient.post<InstBulkMessageResult>('/institutions/me/inbox/bulk-message', payload).then(r => r.data)
