import type { InstitutionDecision, OfferType, ReleaseOfferTerms } from '../../../types'

export const INSTITUTION_DECISIONS: {
  value: InstitutionDecision
  label: string
  tone: 'success' | 'info' | 'danger' | 'warning' | 'neutral'
}[] = [
  { value: 'admitted', label: 'Admit', tone: 'success' },
  { value: 'conditional_admission', label: 'Conditional admit', tone: 'info' },
  { value: 'waitlisted', label: 'Waitlist', tone: 'warning' },
  { value: 'deferred', label: 'Defer', tone: 'neutral' },
  { value: 'rejected', label: 'Reject', tone: 'danger' },
]

export const OFFER_TYPE_LABELS: Record<OfferType, string> = {
  full_admission: 'Full admission',
  conditional: 'Conditional',
  partial: 'Partial',
  transfer_credit_offer: 'Transfer credit',
  waitlist_to_admit: 'Waitlist → admit',
}

export function decisionLabel(decision: InstitutionDecision | string | null | undefined): string {
  return INSTITUTION_DECISIONS.find(d => d.value === decision)?.label ?? String(decision ?? '—')
}

export function formatOfferTermsSummary(offer: ReleaseOfferTerms | null | undefined): string[] {
  if (!offer) return []
  const lines: string[] = []
  if (offer.offer_type) lines.push(`Offer type: ${OFFER_TYPE_LABELS[offer.offer_type] ?? offer.offer_type}`)
  if (offer.scholarship_amount != null) lines.push(`Scholarship: $${offer.scholarship_amount.toLocaleString()}`)
  if (offer.tuition_estimate != null) lines.push(`Tuition estimate: $${offer.tuition_estimate.toLocaleString()}`)
  if (offer.total_cost_estimate != null) lines.push(`Total cost estimate: $${offer.total_cost_estimate.toLocaleString()}`)
  if (offer.response_deadline) lines.push(`Respond by: ${offer.response_deadline}`)
  if (offer.start_term?.season || offer.start_term?.year) {
    lines.push(`Start term: ${[offer.start_term.season, offer.start_term.year].filter(Boolean).join(' ')}`)
  }
  const cond = offer.conditions as { summary?: string } | null | undefined
  if (cond?.summary) lines.push(`Conditions: ${cond.summary}`)
  return lines
}

export function isOfferDecision(decision: InstitutionDecision): boolean {
  return decision === 'admitted' || decision === 'conditional_admission'
}
