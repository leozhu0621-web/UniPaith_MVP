// AUTO-SPLIT from the former monolithic types/index.ts.
// Domain module — see CONTRIBUTING.md. Edit types here, not in a barrel.
// === MESSAGING ===
export interface Conversation {
  id: string
  student_id: string
  institution_id: string
  program_id: string | null
  subject: string | null
  status: 'open' | 'awaiting_response' | 'resolved' | 'closed'
  started_at: string
  last_message_at: string | null
  unread_count?: number
}

export interface Message {
  id: string
  conversation_id: string
  sender_type: 'student' | 'institution'
  sender_id: string
  message_body: string
  sent_at: string
  read_at: string | null
}


// === INBOX (Spec 17) ===
export type ActionLabel =
  | 'needs_reply'
  | 'document_requested'
  | 'clarification_required'
  | 'interview_invite'
  | 'status_update_only'
  | 'completed'

export type WaitingOn = 'student' | 'school' | 'none'

export interface InboxAttachment {
  id?: string
  name: string
  kind?: 'document' | 'link'
  url?: string | null
}

export interface InboxThreadApplication {
  program_name: string | null
  institution_name: string | null
}

export interface InboxParticipant {
  id: string
  role: 'student' | 'admissions_officer' | 'system'
  name: string
}

export interface InboxMessage {
  id: string
  thread_id: string
  sender: 'student' | 'admissions_officer' | 'system'
  body: string
  attachments: InboxAttachment[]
  sent_at: string
  read_at: string | null
  status: 'sent' | 'delivered' | 'read'
}

export interface InboxThreadSummary {
  id: string
  application_id: string | null
  application: InboxThreadApplication
  type: 'human' | 'system'
  subject: string | null
  action_label: ActionLabel | null
  due_date: string | null
  waiting_on: WaitingOn
  unread: boolean
  last_message_at: string | null
  linked_checklist_item_category: string | null
  linked_calendar_item_id: string | null
}

export interface InboxThread extends InboxThreadSummary {
  participants: InboxParticipant[]
  messages: InboxMessage[]
}

export interface SuggestedReply {
  draft: string
  tone: string
  length: string
  alternate_drafts: string[]
}


// === NOTIFICATIONS ===
export interface Notification {
  id: string
  title: string
  body: string
  notification_type: string
  is_read: boolean
  // Deep-link into the app (e.g. /applications/123) — the real API field.
  action_url?: string | null
  // Spec 57 — urgent | digest classification.
  urgency?: string
  reference_type?: string | null
  reference_id?: string | null
  created_at: string
}

export type NotificationChannelKey = 'email' | 'sms' | 'in_app' | 'push'
export type NotificationChannels = Record<NotificationChannelKey, boolean>
export type EmailFrequency = 'all' | 'weekly' | 'important' | 'none'

export interface NotificationTypePref {
  type: string
  label: string
  essential: boolean
  channels: NotificationChannels
}

export interface NotificationPreference {
  email_enabled: boolean
  email_frequency: EmailFrequency
  preferences: Record<string, NotificationChannels> | null
  matrix: NotificationTypePref[]
}


// === COMMUNICATION TEMPLATES ===
export interface CommunicationTemplate {
  id: string
  institution_id: string
  program_id: string | null
  template_type: string
  name: string
  subject: string
  body: string
  variables: string[] | null
  is_default: boolean
  is_active: boolean
  created_at: string
  updated_at: string
  program_name: string | null
}

export interface TemplatePreview {
  rendered_subject: string
  rendered_body: string
  variables_used: string[]
}
