// Spec 25 — campaign editor option lists, labels, and brand badge mapping.
import type {
  CampaignChannel,
  CampaignCtaType,
  CampaignDestinationType,
  CampaignObjective,
  CampaignStatus,
} from '../../../types'

export const OBJECTIVE_OPTIONS: { value: CampaignObjective; label: string }[] = [
  { value: 'application_open', label: 'Application open' },
  { value: 'event_promotion', label: 'Event promotion' },
  { value: 'scholarship_announcement', label: 'Scholarship announcement' },
  { value: 'deadline_reminder', label: 'Deadline reminder' },
  { value: 'nurture', label: 'Nurture' },
  { value: 'general', label: 'General' },
]

export const CTA_OPTIONS: { value: CampaignCtaType; label: string }[] = [
  { value: 'learn_more', label: 'Learn more' },
  { value: 'rsvp_event', label: 'RSVP to event' },
  { value: 'request_info', label: 'Request info' },
  { value: 'start_application', label: 'Start application' },
]

export const DESTINATION_OPTIONS: { value: CampaignDestinationType; label: string }[] = [
  { value: 'institution_page', label: 'Institution page' },
  { value: 'program_page', label: 'Program page' },
  { value: 'campaign_landing_page', label: 'Campaign landing page' },
  { value: 'external_url', label: 'External URL' },
]

export const CHANNEL_OPTIONS: { value: CampaignChannel; label: string; hint: string }[] = [
  {
    value: 'internal_messaging',
    label: 'Internal messaging',
    hint: 'Delivered to the student’s UniPaith Inbox (consent-gated).',
  },
  {
    value: 'external_email',
    label: 'External email',
    hint: 'Sent via email to platform + uploaded recipients (opt-out honored).',
  },
]

export const OBJECTIVE_LABELS: Record<string, string> = Object.fromEntries(
  OBJECTIVE_OPTIONS.map((o) => [o.value, o.label]),
)
export const CTA_LABELS: Record<string, string> = Object.fromEntries(
  CTA_OPTIONS.map((o) => [o.value, o.label]),
)

export const STATUS_LABELS: Record<CampaignStatus, string> = {
  draft: 'Draft',
  pending_approval: 'Pending approval',
  scheduled: 'Scheduled',
  active: 'Active',
  paused: 'Paused',
  completed: 'Completed',
}

// Brand badge variant per lifecycle state (Spec 25 §11). 'active' uses success;
// scheduled uses cobalt/info; pending_approval + paused use warning.
export const STATUS_BADGE: Record<CampaignStatus, 'neutral' | 'info' | 'success' | 'warning'> = {
  draft: 'neutral',
  pending_approval: 'warning',
  scheduled: 'info',
  active: 'success',
  paused: 'warning',
  completed: 'neutral',
}

export const ATTRIBUTION_LABELS: Record<string, string> = {
  view: 'Views',
  save: 'Saves',
  rsvp: 'RSVPs',
  request_info: 'Info requests',
  apply_started: 'Apps started',
  apply_submitted: 'Apps submitted',
  decision: 'Decisions',
}

export const PERSONALIZATION_TOKENS = ['{{first_name}}', '{{program_name}}', '{{event_link}}']

// Parse a pasted CSV/TSV (or newline list) into contact rows {email, first_name?, last_name?}.
export function parseContactsText(text: string): Record<string, string>[] {
  const lines = text
    .split(/\r?\n/)
    .map((l) => l.trim())
    .filter(Boolean)
  if (lines.length === 0) return []
  const delim = lines[0].includes('\t') ? '\t' : ','
  // Detect a header row.
  const header = lines[0].toLowerCase()
  const hasHeader = header.includes('email')
  let cols = ['email', 'first_name', 'last_name']
  let start = 0
  if (hasHeader) {
    cols = lines[0].split(delim).map((c) => c.trim().toLowerCase().replace(/\s+/g, '_'))
    start = 1
  }
  const emailIdx = cols.indexOf('email') === -1 ? 0 : cols.indexOf('email')
  const out: Record<string, string>[] = []
  for (let i = start; i < lines.length; i++) {
    const parts = lines[i].split(delim).map((p) => p.trim())
    const email = parts[emailIdx]
    if (!email || !email.includes('@')) continue
    const row: Record<string, string> = { email }
    cols.forEach((c, idx) => {
      if (c !== 'email' && parts[idx]) row[c] = parts[idx]
    })
    out.push(row)
  }
  return out
}
