import {
  AlertCircle,
  CalendarClock,
  CheckCircle2,
  FileText,
  HelpCircle,
  Info,
} from 'lucide-react'
import type { ActionLabel, InboxThreadSummary, WaitingOn } from '../../../types'

type BadgeVariant = 'success' | 'warning' | 'danger' | 'info' | 'neutral'

// Spec 17 §5 / §10 — action labels render as chips. needs_reply →
// warning-soft/warning; completed → success-soft/success (per Badge variants).
export const ACTION_CONFIG: Record<
  ActionLabel,
  { label: string; variant: BadgeVariant; icon: typeof AlertCircle }
> = {
  needs_reply: { label: 'Needs reply', variant: 'warning', icon: AlertCircle },
  document_requested: { label: 'Document requested', variant: 'warning', icon: FileText },
  clarification_required: { label: 'Clarification required', variant: 'info', icon: HelpCircle },
  interview_invite: { label: 'Interview invite', variant: 'info', icon: CalendarClock },
  status_update_only: { label: 'Status update only', variant: 'neutral', icon: Info },
  completed: { label: 'Completed', variant: 'success', icon: CheckCircle2 },
}

// The two states that get an AI-assist suggested reply (spec 17 §7).
export const AI_REPLY_LABELS: ActionLabel[] = ['needs_reply', 'clarification_required']

export function waitingCopy(thread: Pick<InboxThreadSummary, 'waiting_on' | 'application'>): string | null {
  const w: WaitingOn = thread.waiting_on
  if (w === 'student') return 'Waiting on you'
  if (w === 'school') {
    const inst = thread.application?.institution_name
    return inst ? `Waiting on ${inst}` : 'Waiting on the school'
  }
  return null
}

export function formatDue(iso: string | null): string | null {
  if (!iso) return null
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return null
  // Force en-US so the due date matches the English UI (e.g. "Wed, Jun 3")
  // rather than the viewer's system locale.
  return d.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' })
}

// Eyebrow for a thread: "Application · U of Foo CS MS" or "University of Foo".
export function threadEyebrow(thread: Pick<InboxThreadSummary, 'application' | 'type'>): string {
  const { program_name, institution_name } = thread.application
  if (program_name && institution_name) return `${institution_name} · ${program_name}`
  if (institution_name) return institution_name
  if (program_name) return program_name
  return thread.type === 'system' ? 'UniPaith' : 'Admissions'
}
