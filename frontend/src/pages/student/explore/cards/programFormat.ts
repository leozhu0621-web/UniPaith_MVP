import { daysUntil } from '../../../../utils/deadline'

// Shared program field formatters — used by ProgramCard and ProgramListRow so
// the card and the dense row never disagree on how a value reads.

export function degreeAbbrev(degree: string): string {
  const map: Record<string, string> = {
    bachelors: 'BS', masters: 'MS', phd: 'PhD',
    certificate: 'CERT', doctorate: 'DOC', associate: 'AA',
  }
  return map[degree] || degree.slice(0, 3).toUpperCase()
}

export function formatDuration(months?: number | null): string | null {
  if (!months) return null
  if (months < 12) return `${months} mo`
  const years = months / 12
  return Number.isInteger(years) ? `${years} yr${years > 1 ? 's' : ''}` : `${years.toFixed(1)} yrs`
}

export function formatFormat(f?: string | null): string | null {
  if (!f) return null
  const map: Record<string, string> = {
    on_campus: 'On campus', online: 'Online',
    hybrid: 'Hybrid', in_person: 'In-person',
  }
  return map[f] || f.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())
}

export interface DeadlineInfo {
  text: string
  urgent: boolean
  closed: boolean
  date?: string
}

export function deadlineInfo(deadline?: string | null): DeadlineInfo | null {
  if (!deadline) return null
  const days = daysUntil(deadline) ?? 0
  const date = new Date(deadline).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
  if (days < 0) return { text: date, urgent: false, closed: true }
  if (days <= 30) return { text: `${days}d left`, urgent: true, closed: false, date }
  return { text: date, urgent: false, closed: false }
}
