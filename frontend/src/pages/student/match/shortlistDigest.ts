/**
 * A counselor's read of the WHOLE shortlist — the shape (how many reach/target/
 * safer), whether it's balanced, and the standout (best-fit) match. Complements
 * the per-card storyline with a synthesis of the list as a whole.
 *
 * Pure + isolated so it's unit-tested without rendering. Returns null for an
 * empty list (nothing to read).
 */
import type { MatchBand, MatchResultDual } from '../../../types'

export interface ShortlistDigest {
  total: number
  counts: Record<MatchBand, number>
  balance: 'balanced' | 'reach_heavy' | 'safe_heavy'
  standout: MatchResultDual | null
}

function num(s: string | null | undefined): number {
  const n = s ? parseFloat(s) : NaN
  return Number.isFinite(n) ? n : 0
}

export function shortlistDigest(matches: MatchResultDual[]): ShortlistDigest | null {
  if (matches.length === 0) return null

  const counts: Record<MatchBand, number> = { reach: 0, target: 0, safer: 0 }
  for (const mm of matches) {
    const band = (mm.band_label ?? 'target') as MatchBand
    counts[band in counts ? band : 'target']++
  }

  const { reach, target, safer } = counts
  let balance: ShortlistDigest['balance'] = 'balanced'
  if (reach >= 2 && reach > target + safer) balance = 'reach_heavy'
  else if (safer >= 2 && safer > reach + target) balance = 'safe_heavy'

  // Standout = the best-fit program (highest fitness; first when none are scored).
  const standout = [...matches].sort((a, b) => num(b.fitness_score) - num(a.fitness_score))[0] ?? null

  return { total: matches.length, counts, balance, standout }
}
