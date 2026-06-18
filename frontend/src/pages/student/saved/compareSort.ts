// Saved Compare board (Discover review 2026-06-14 #3) — a persistent, sortable
// side-by-side matrix of ALL saved programs (distinct from the transient 4-item
// CompareTray). Pure sort logic, tested. No fabrication: only fields present on
// the saved row become columns (salary/employment aren't on it, so they're out).
import type { MatchBand, SavedProgram } from '../../../types'

export type CompareColumn =
  | 'program'
  | 'school'
  | 'band'
  | 'acceptance'
  | 'tuition'
  | 'duration'
  | 'deadline'

export type SortDir = 'asc' | 'desc'

export const COMPARE_COLUMNS: { key: CompareColumn; label: string; numeric: boolean }[] = [
  { key: 'program', label: 'Program', numeric: false },
  { key: 'school', label: 'School', numeric: false },
  { key: 'band', label: 'Band', numeric: true },
  { key: 'acceptance', label: 'Acceptance', numeric: true },
  { key: 'tuition', label: 'Tuition / yr', numeric: true },
  { key: 'duration', label: 'Duration', numeric: true },
  { key: 'deadline', label: 'Deadline', numeric: true },
]

// reach is the "hardest" → rank so ascending = reach-first (the cautionary end).
const BAND_RANK: Record<MatchBand, number> = { reach: 0, target: 1, safer: 2 }

/** Comparable scalar for a column. Returns null for missing → always sorted last. */
function cellValue(sp: SavedProgram, key: CompareColumn): string | number | null {
  switch (key) {
    case 'program':
      return (sp.program_name ?? sp.program?.program_name ?? '').toLowerCase() || null
    case 'school':
      return (sp.institution_name ?? '').toLowerCase() || null
    case 'band':
      return sp.band_label ? BAND_RANK[sp.band_label as MatchBand] : null
    case 'acceptance':
      return sp.acceptance_rate ?? null
    case 'tuition':
      return sp.tuition ?? null
    case 'duration':
      return sp.duration_months ?? null
    case 'deadline':
      return sp.application_deadline ? new Date(sp.application_deadline).getTime() : null
  }
}

/** Sort saved programs by a column, nulls always last regardless of direction. */
export function sortRows(programs: SavedProgram[], key: CompareColumn, dir: SortDir): SavedProgram[] {
  const sign = dir === 'asc' ? 1 : -1
  return [...programs].sort((a, b) => {
    const av = cellValue(a, key)
    const bv = cellValue(b, key)
    if (av === null && bv === null) return 0
    if (av === null) return 1 // a missing → after b
    if (bv === null) return -1 // b missing → after a
    if (av < bv) return -1 * sign
    if (av > bv) return 1 * sign
    return 0
  })
}
