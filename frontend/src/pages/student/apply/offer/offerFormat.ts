// Spec 18 · Decisions & Offers — shared formatting + state helpers.
import { formatDate } from '../../../../utils/format'

// Canonical deadline-tone helpers now live in utils/deadline. Re-exported here
// for back-compat so existing offer/applications imports keep working.
export { daysUntil, deadlineTone, DEADLINE_TONE_CLASS } from '../../../../utils/deadline'
export type { DeadlineTone } from '../../../../utils/deadline'

export function money(n?: number | null, currency = 'USD'): string | null {
  if (n == null) return null
  const prefix = currency === 'USD' || !currency ? '$' : `${currency} `
  return `${prefix}${n.toLocaleString()}`
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

/** Spec 18 §10 — bold amounts and ISO dates inside plain-language brief copy. */
export function briefSummaryParts(text: string): Array<{ text: string; bold: boolean }> {
  const re = /(\$[\d,]+(?:\.\d+)?|\b\d{4}-\d{2}-\d{2}\b|\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{1,2},? \d{4}\b)/gi
  const parts: Array<{ text: string; bold: boolean }> = []
  let last = 0
  for (const match of text.matchAll(re)) {
    const idx = match.index ?? 0
    if (idx > last) parts.push({ text: text.slice(last, idx), bold: false })
    parts.push({ text: match[0], bold: true })
    last = idx + match[0].length
  }
  if (last < text.length) parts.push({ text: text.slice(last), bold: false })
  return parts.length ? parts : [{ text, bold: false }]
}

export function hasPendingOfferResponse(app: {
  offer?: { student_response?: string | null } | null
  student_decision?: string | null
}): boolean {
  return Boolean(
    app.offer &&
      !app.offer.student_response &&
      app.student_decision !== 'accepted_by_student' &&
      app.student_decision !== 'declined_by_student',
  )
}
