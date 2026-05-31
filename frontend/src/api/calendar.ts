import apiClient from './client'
import { toArrayData } from './normalize'

// Spec 16 §6 — unified admissions-timeline item.
export type CalendarItemType =
  | 'interview_live'
  | 'interview_recorded_window'
  | 'campus_visit'
  | 'info_session'
  | 'portfolio_review'
  | 'audition'
  | 'submission_deadline'
  | 'document_deadline'
  | 'recommendation_deadline'
  | 'interview_submission_deadline'
  | 'deposit_deadline'
  | 'reminder'
  | 'work_block'

export type CalendarItemStatus = 'scheduled' | 'completed' | 'cancelled' | 'overdue'

export interface ReminderSettings {
  lead_time_minutes: number
  channels: ('email' | 'push' | 'in_app')[]
}

export interface CalendarItem {
  id: string
  type: CalendarItemType
  title: string
  start_at: string
  end_at: string | null
  location: string | null
  meeting_link: string | null
  application_id: string | null
  status: CalendarItemStatus
  notes: string | null
  reminder_settings: ReminderSettings | null
  // display helpers
  subtitle: string | null
  link: string | null
  institution_name: string | null
  recommender_name: string | null
  confirmation_url: string | null
  editable: boolean
}

export interface ReminderCreate {
  title: string
  start_at: string
  notes?: string | null
  application_id?: string | null
  reminder_settings?: ReminderSettings | null
}

export interface WorkBlockCreate {
  title: string
  start_at: string
  end_at?: string | null
  duration_minutes?: number | null
  category?: string | null
  application_id?: string | null
  notes?: string | null
}

export interface CalendarItemPatch {
  status?: CalendarItemStatus
  notes?: string | null
  title?: string | null
  start_at?: string | null
  end_at?: string | null
  confirmation_url?: string | null
}

export const getCalendar = (params?: { from?: string; to?: string }) =>
  apiClient.get('/me/calendar', { params }).then(r => toArrayData<CalendarItem>(r.data))

export const createReminder = (body: ReminderCreate) =>
  apiClient.post('/me/calendar/reminders', body).then(r => r.data as CalendarItem)

export const createWorkBlock = (body: WorkBlockCreate) =>
  apiClient.post('/me/calendar/work-blocks', body).then(r => r.data as CalendarItem)

export const patchCalendarItem = (id: string, body: CalendarItemPatch) =>
  apiClient.patch(`/me/calendar/${encodeURIComponent(id)}`, body).then(r => r.data as CalendarItem)
