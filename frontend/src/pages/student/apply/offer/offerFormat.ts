// Spec 18 · Decisions & Offers — shared formatting + state helpers.
import { formatDate } from '../../../../utils/format'

export function money(n?: number | null, currency = 'USD'): string | null {
  if (n == null) return null
  const prefix = currency === 'USD' || !currency ? '$' : `${currency} `
  return `${prefix}${n.toLocaleString()}`
}

/** Days from today to an ISO date (UTC-safe enough for deadline display). */
export function daysUntil(iso?: string | null): number | null {
  if (!iso) return null
  return Math.ceil((new Date(iso).getTime() - Date.now()) / 86400000)
}

/** Deadline color escalation, spec 18 §8: normal → warning → error. */
export type DeadlineTone = 'normal' | 'warning' | 'error'
export function deadlineTone(days?: number | null): DeadlineTone {
  if (days == null) return 'normal'
  if (days <= 7) return 'error'
  if (days <= 21) return 'warning'
  return 'normal'
}

export const DEADLINE_TONE_CLASS: Record<DeadlineTone, string> = {
  normal: 'text-student-text',
  warning: 'text-warning',
  error: 'text-destructive',
}

/** §2 decision-state → human label. */
export const DECISION_STATE_LABEL: Record<string, string> = {
  pending: 'Awaiting decision',
  accepted: 'Admitted',
  rejected: 'Not admitted',
  waitlisted: 'Waitlisted',
  deferred: 'Deferred',
  accepted_by_student: 'You accepted',
  declined_by_student: 'You declined',
  withdrawn: 'Withdrawn',
}

export const DECISION_STATE_BADGE: Record<
  string,
  'success' | 'warning' | 'danger' | 'info' | 'neutral'
> = {
  pending: 'info',
  accepted: 'success',
  rejected: 'danger',
  waitlisted: 'warning',
  deferred: 'warning',
  accepted_by_student: 'success',
  declined_by_student: 'neutral',
  withdrawn: 'neutral',
}

export function formatTermDate(iso?: string | null): string | null {
  if (!iso) return null
  // Reuse the app-wide date-fns formatter: locale-agnostic English
  // ("MMM d, yyyy") + parseISO avoids the UTC-midnight off-by-one.
  try {
    return formatDate(iso)
  } catch {
    return iso
  }
}

export const OFFER_TYPE_LABEL: Record<string, string> = {
  full_admission: 'Full admission',
  conditional: 'Conditional offer',
  waitlist_to_admit: 'Waitlist-to-admit',
  partial: 'Partial offer',
  transfer_credit_offer: 'Transfer credit offer',
}
