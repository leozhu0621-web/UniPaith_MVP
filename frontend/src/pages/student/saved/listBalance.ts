// Application-list balance (Discover review 2026-06-14, idea #1). Counselors
// coach a balanced reach/target/safer list; this turns the saved programs'
// match bands into a deterministic balance read + a neutral nudge. Pure — no
// fabrication: a program with no band is "unscored", never assumed.
import type { MatchBand, SavedProgram } from '../../../types'

export interface ListBalance {
  reach: number
  target: number
  safer: number
  unscored: number
  /** scored total (reach + target + safer) — the denominator for balance. */
  scored: number
  /** neutral one-line guidance, or null when there's nothing useful to say. */
  nudge: string | null
}

export function computeBalance(programs: Pick<SavedProgram, 'band_label'>[]): ListBalance {
  let reach = 0
  let target = 0
  let safer = 0
  let unscored = 0
  for (const p of programs) {
    const band = p.band_label as MatchBand | null | undefined
    if (band === 'reach') reach++
    else if (band === 'target') target++
    else if (band === 'safer') safer++
    else unscored++
  }
  const scored = reach + target + safer

  // Neutral nudges only — never alarmist, never gold. Surface guidance once the
  // list is big enough that balance matters (>= 3 scored programs).
  let nudge: string | null = null
  if (scored >= 3) {
    if (safer === 0) nudge = 'No safer schools yet — consider adding one to balance your list.'
    else if (reach === 0) nudge = 'All within reach — room for an ambitious reach school.'
    else if (reach > scored / 2) nudge = 'Reach-heavy — a few more targets or safer schools would balance it.'
    else nudge = 'A balanced spread across reach, target, and safer.'
  }

  return { reach, target, safer, unscored, scored, nudge }
}
