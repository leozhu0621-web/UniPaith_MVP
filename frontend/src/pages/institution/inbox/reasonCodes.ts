import {
  AlertCircle,
  CalendarClock,
  FileText,
  HelpCircle,
  Info,
  Scale,
} from 'lucide-react'
import type { ActionLabel, InstInboxThreadSummary, InstReasonCode } from '../../../types'

type BadgeVariant = 'success' | 'warning' | 'danger' | 'info' | 'neutral'

/** Institution reason codes → student action labels (Spec 29 §4). */
export const REASON_TO_ACTION: Record<InstReasonCode, ActionLabel> = {
  request_document: 'document_requested',
  request_clarification: 'clarification_required',
  interview_invite: 'interview_invite',
  status_update: 'status_update_only',
  general_reply: 'needs_reply',
  decision_notice: 'status_update_only',
}

export const REASON_CONFIG: Record<
  InstReasonCode,
  { label: string; variant: BadgeVariant; icon: typeof AlertCircle; requiresDue?: boolean }
> = {
  request_document: { label: 'Document requested', variant: 'warning', icon: FileText, requiresDue: true },
  request_clarification: { label: 'Clarification required', variant: 'info', icon: HelpCircle, requiresDue: true },
  interview_invite: { label: 'Interview invite', variant: 'info', icon: CalendarClock, requiresDue: true },
  status_update: { label: 'Status update', variant: 'neutral', icon: Info },
  general_reply: { label: 'General reply', variant: 'warning', icon: AlertCircle },
  decision_notice: { label: 'Decision notice', variant: 'neutral', icon: Scale },
}

export const REASON_OPTIONS: { value: InstReasonCode; label: string }[] = (
  Object.entries(REASON_CONFIG) as [InstReasonCode, (typeof REASON_CONFIG)[InstReasonCode]][]
).map(([value, cfg]) => ({ value, label: cfg.label }))

export function statusLabel(status: InstInboxThreadSummary['status']): string {
  switch (status) {
    case 'awaiting_student':
      return 'Awaiting student'
    case 'awaiting_us':
      return 'We owe a reply'
    case 'closed':
      return 'Closed'
    default:
      return 'Open'
  }
}
