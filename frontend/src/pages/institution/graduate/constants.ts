// Spec 41 · Graduate & PhD Admissions — shared labels + helpers.

import type {
  FundingComponentKind,
  FundingPoolKind,
  RecommendedDecision,
} from '../../../api/graduate'

export const DECISION_LABELS: Record<RecommendedDecision, string> = {
  admitted: 'Admit',
  conditional_admission: 'Conditional admit',
  waitlisted: 'Waitlist',
  rejected: 'Reject',
  deferred: 'Defer',
}

export const DECISION_OPTIONS = (
  Object.keys(DECISION_LABELS) as RecommendedDecision[]
).map(d => ({ value: d, label: DECISION_LABELS[d] }))

export const COMPONENT_KIND_LABELS: Record<FundingComponentKind, string> = {
  TA: 'Teaching assistantship',
  RA: 'Research assistantship',
  fellowship: 'Fellowship',
  tuition_waiver: 'Tuition waiver',
  stipend: 'Stipend',
}

export const COMPONENT_KIND_OPTIONS = (
  Object.keys(COMPONENT_KIND_LABELS) as FundingComponentKind[]
).map(k => ({ value: k, label: COMPONENT_KIND_LABELS[k] }))

export const POOL_KIND_LABELS: Record<FundingPoolKind, string> = {
  department: 'Department',
  grant: 'Grant',
  fellowship: 'Fellowship',
  other: 'Other',
}

export const POOL_KIND_OPTIONS = (
  Object.keys(POOL_KIND_LABELS) as FundingPoolKind[]
).map(k => ({ value: k, label: POOL_KIND_LABELS[k] }))

export type AlignmentBand = 'strong' | 'moderate' | 'weak'

export function alignmentBand(score: number): AlignmentBand {
  if (score >= 60) return 'strong'
  if (score >= 30) return 'moderate'
  return 'weak'
}

const CURRENCY_SYMBOL: Record<string, string> = { USD: '$', GBP: '£', EUR: '€' }

export function fmtMoney(amount: number | null | undefined, currency = 'USD'): string {
  const sym = CURRENCY_SYMBOL[currency] ?? ''
  const n = Number(amount ?? 0)
  return `${sym}${n.toLocaleString(undefined, { maximumFractionDigits: 0 })}`
}

export function yearsLabel(years: number[] | null | undefined): string {
  const ys = (years ?? []).filter(Boolean)
  if (ys.length === 0) return 'Year 1'
  if (ys.length === 1) return `Year ${ys[0]}`
  const sorted = [...ys].sort((a, b) => a - b)
  return `Years ${sorted[0]}–${sorted[sorted.length - 1]}`
}

/** Status of a decision/central pair, for badges. */
export const CENTRAL_STATUS_LABEL: Record<string, string> = {
  pending: 'Awaiting central confirmation',
  confirmed: 'Confirmed by central',
  overridden: 'Overridden by central',
}
