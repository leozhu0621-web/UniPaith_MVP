/** Spec 25 — campaigns lifecycle, objectives, channels, brand copy. */

export const CAMPAIGN_OBJECTIVES = [
  { value: 'application_open', label: 'Application open' },
  { value: 'event_promotion', label: 'Event promotion' },
  { value: 'scholarship_announcement', label: 'Scholarship announcement' },
  { value: 'deadline_reminder', label: 'Deadline reminder' },
  { value: 'nurture', label: 'Nurture' },
  { value: 'general', label: 'General outreach' },
] as const

export const CAMPAIGN_CHANNELS = [
  { value: 'in_app', label: 'Internal messaging', hint: 'Delivered to student Inbox on UniPaith' },
  { value: 'email', label: 'External email', hint: 'Sent via email with unsubscribe link' },
  { value: 'both', label: 'Both channels', hint: 'Inbox notification plus external email' },
] as const

export const DESTINATION_TYPES = [
  { value: 'program', label: 'Program page' },
  { value: 'institution', label: 'Institution page' },
  { value: 'event', label: 'Event' },
  { value: 'custom', label: 'External URL' },
] as const

export const CTA_TYPES = [
  { value: 'learn_more', label: 'Learn more' },
  { value: 'rsvp_event', label: 'RSVP event' },
  { value: 'request_info', label: 'Request info' },
  { value: 'start_application', label: 'Start application' },
] as const

/** Backend status values; UI labels per Spec §2 / §11. */
export const STATUS_BADGE: Record<string, 'neutral' | 'info' | 'success' | 'warning' | 'danger'> = {
  draft: 'neutral',
  pending_approval: 'warning',
  scheduled: 'info',
  active: 'success',
  paused: 'warning',
  sent: 'success',
  completed: 'success',
}

export function statusLabel(status: string | null | undefined): string {
  const s = status ?? 'draft'
  if (s === 'sent') return 'Completed'
  if (s === 'active') return 'Active'
  return s.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())
}

export function channelLabel(type: string | null | undefined): string {
  if (type === 'in_app') return 'Internal'
  if (type === 'email') return 'External email'
  if (type === 'both') return 'Both'
  if (type === 'sms') return 'SMS'
  return type ?? 'Email'
}

export const LIST_TABS = [
  { id: 'all', label: 'All' },
  { id: 'draft', label: 'Drafts' },
  { id: 'scheduled', label: 'Scheduled' },
  { id: 'sent', label: 'Completed' },
] as const

export const PERSONALIZATION_VARS = [
  '{{first_name}}',
  '{{last_name}}',
  '{{institution_name}}',
  '{{program_name}}',
  '{{email}}',
  '{{event_link}}',
]
