import apiClient from './client'

// Demo feedback survey (title + message). Submissions are collected server-side
// and read by the team via the system-guarded /feedback/admin endpoint.
export interface FeedbackPayload {
  title?: string
  message: string
  context?: Record<string, unknown>
}

export async function submitFeedback(payload: FeedbackPayload): Promise<void> {
  await apiClient.post('/feedback', payload)
}

// One collected feedback submission, as returned by the owner inbox.
export interface FeedbackItem {
  id: string
  user_id: string | null
  role: string | null
  title: string | null
  message: string
  context: { path?: string } | Record<string, unknown> | null
  created_at: string
}

// Owner-only feedback inbox (newest first). 403s for non-owner accounts —
// access is the server-side email allowlist (settings.owner_emails).
export async function getFeedbackInbox(): Promise<FeedbackItem[]> {
  const { data } = await apiClient.get<FeedbackItem[]>('/feedback/inbox')
  return data
}
