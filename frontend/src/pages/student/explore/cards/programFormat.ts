import { daysUntil, deadlineTone } from '../../../../utils/deadline'
import { formatDateShort } from '../../../../utils/format'

// Shared program field formatters — used by ProgramCard and ProgramListRow so
// the card and the dense row never disagree on how a value reads.

// The degree monogram. `bachelors`/`masters` are coarse — they carry no BA vs BS
// distinction — so a bare map stamped "BS" on every bachelor's, including a
// "Bachelor of Arts". Inspect the program title for the real monogram; fall back
// to a neutral abbreviation rather than guessing the wrong one.
export function degreeAbbrev(degree: string, programName?: string): string {
  const n = (programName || '').toLowerCase()
  if (degree === 'bachelors') {
    if (/bachelor of arts|\bb\.?a\.?\b/.test(n)) return 'BA'
    if (/bachelor of fine arts|\bbfa\b/.test(n)) return 'BFA'
    if (/bachelor of science|\bb\.?s\.?\b/.test(n)) return 'BS'
    return 'BACH'
  }
  if (degree === 'masters') {
    if (/master of business|\bmba\b/.test(n)) return 'MBA'
    if (/master of fine arts|\bmfa\b/.test(n)) return 'MFA'
    if (/master of arts|\bm\.?a\.?\b/.test(n)) return 'MA'
    if (/master of science|\bm\.?s\.?\b/.test(n)) return 'MS'
    return 'MAST'
  }
  const map: Record<string, string> = {
    phd: 'PhD', certificate: 'CERT', doctorate: 'DOC', associate: 'AA',
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
  // Parse the date-only string the SAME way the detail page's formatDate does
  // (parseISO → local midnight), not `new Date()` (UTC midnight), which rolled a
  // "2027-01-03" deadline back to "Jan 2" for any viewer west of UTC while the
  // detail page showed "Jan 3" — the two screens disagreed by a day.
  const date = formatDateShort(deadline)
  if (days < 0) return { text: date, urgent: false, closed: true }
  // Show the "Xd left" countdown for up to a month, but drive `urgent` (the amber
  // tone) by the canonical 7/21 table so a 25-day deadline isn't amber here while
  // it's neutral on the calendar dot and every other surface.
  if (days <= 30) return { text: `${days}d left`, urgent: deadlineTone(days) !== 'normal', closed: false, date }
  return { text: date, urgent: false, closed: false }
}
