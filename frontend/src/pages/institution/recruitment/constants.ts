// Spec 40 · Recruitment CRM — shared display metadata.
// Brand (§7): operational CRM density, charts per Spec 28 palette, NO GOLD.
import type { ProspectSource, ProspectStage } from '../../../types'

// No-gold chart palette (cobalt → green → amber → muted), Spec 40 §7 / 28.
export const RECRUIT_SERIES = ['#2A6BD4', '#1F6B2E', '#B8741D', '#4A4640'] as const

export const STAGE_META: Record<
  ProspectStage,
  { label: string; tone: 'neutral' | 'info' | 'success' }
> = {
  suspect: { label: 'Suspect', tone: 'neutral' },
  prospect: { label: 'Prospect', tone: 'neutral' },
  engaged: { label: 'Engaged', tone: 'info' },
  inquiry: { label: 'Inquiry', tone: 'info' },
  applicant: { label: 'Applicant', tone: 'success' },
}

export const STAGE_ORDER: ProspectStage[] = [
  'suspect',
  'prospect',
  'engaged',
  'inquiry',
  'applicant',
]

export const SOURCE_META: Record<ProspectSource, string> = {
  fair: 'Fair',
  list: 'List',
  inquiry: 'Inquiry',
  referral: 'Referral',
  web: 'Web',
  visit: 'Visit',
}

export const SOURCE_OPTIONS = Object.entries(SOURCE_META).map(([value, label]) => ({
  value,
  label,
}))

export const STAGE_OPTIONS = STAGE_ORDER.map(s => ({ value: s, label: STAGE_META[s].label }))

export const BAND_META: Record<'hot' | 'warm' | 'cold', { label: string; dot: string }> = {
  hot: { label: 'Hot', dot: 'bg-success' },
  warm: { label: 'Warm', dot: 'bg-warning' },
  cold: { label: 'Cold', dot: 'bg-border' },
}
