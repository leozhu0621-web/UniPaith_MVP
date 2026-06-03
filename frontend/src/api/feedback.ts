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
