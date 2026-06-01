import {
  AlertCircle,
  CalendarClock,
  CheckCircle2,
  FileText,
  Gavel,
  HelpCircle,
  Info,
  MessageSquare,
} from 'lucide-react'
import type { InstThreadStatus, ReasonCode } from '../../../types'

type BadgeVariant = 'success' | 'warning' | 'danger' | 'info' | 'neutral'

// Spec 29 §4/§10 — reason-code chips. Colors mirror the student-side
// action-label palette (spec 17 §10 / actionLabels.ts) so both ends of the
// conversation speak the same visual language.
export const REASON_CONFIG: Record<
  ReasonCode,
  { label: string; variant: BadgeVariant; icon: typeof AlertCircle }
> = {
  request_document: { label: 'Document requested', variant: 'warning', icon: FileText },
  request_clarification: { label: 'Clarification', variant: 'info', icon: HelpCircle },
  interview_invite: { label: 'Interview invite', variant: 'info', icon: CalendarClock },
  status_update: { label: 'Status update', variant: 'neutral', icon: Info },
  general_reply: { label: 'Reply', variant: 'neutral', icon: MessageSquare },
  decision_notice: { label: 'Decision', variant: 'info', icon: Gavel },
}

// Reasons that REQUIRE a due date on send (spec 29 §5).
export const REASON_REQUIRES_DUE: ReasonCode[] = [
  'request_document',
  'request_clarification',
  'interview_invite',
]

// Reason that links/creates a student checklist item when attached (spec 29 §5).
export const DOCUMENT_REASON: ReasonCode = 'request_document'

export const REASON_OPTIONS: { value: ReasonCode; label: string }[] = (
  Object.keys(REASON_CONFIG) as ReasonCode[]
).map(value => ({ value, label: REASON_CONFIG[value].label }))

// Spec 29 §9 — thread lifecycle states.
export const STATUS_CONFIG: Record<
  InstThreadStatus,
  { label: string; variant: BadgeVariant; icon: typeof AlertCircle }
> = {
  open: { label: 'Open', variant: 'info', icon: MessageSquare },
  awaiting_student: { label: 'Awaiting student', variant: 'neutral', icon: CalendarClock },
  awaiting_us: { label: 'We owe a reply', variant: 'warning', icon: AlertCircle },
  closed: { label: 'Closed', variant: 'success', icon: CheckCircle2 },
}

export function formatDue(iso: string | null): string | null {
  if (!iso) return null
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return null
  return d.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' })
}

// Overdue = we owe a reply AND the due date is in the past (spec 29 §9).
export function isOverdue(thread: { status: InstThreadStatus; due_date: string | null }): boolean {
  if (thread.status !== 'awaiting_us' || !thread.due_date) return false
  const d = new Date(thread.due_date)
  return !Number.isNaN(d.getTime()) && d.getTime() < Date.now()
}
