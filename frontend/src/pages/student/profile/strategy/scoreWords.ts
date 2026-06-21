/**
 * Strategy school-list word tags — the SAME fit/odds language Discover uses
 * (`pages/student/match/matchStoryline.ts`, #969), so a program reads the same
 * on both surfaces. Two separate scales by design — a reach can still be a
 * strong fit, so we never collapse them into one number.
 *
 * - Fit comes from `fitness_score` (how well a program suits you), tiered at the
 *   same 0.7 / 0.45 boundaries Discover uses.
 * - Odds come from the `band_label` (reach / target / safer) — the reliable
 *   admission-odds signal present on every match row — NOT `confidence_score`,
 *   which the student match payload usually omits.
 */
import type { MatchBand } from '../../../../types'

/** Coerce a possibly-string, possibly-null score into a finite number, or null. */
function toScore(score: number | string | null | undefined): number | null {
  if (score === null || score === undefined) return null
  const n = Number(score)
  if (!Number.isFinite(n) || n <= 0) return null
  return n
}

/** Fit word from `fitness_score` (0..1) — mirrors Discover's tiers. Null when absent. */
export function fitWord(score: number | string | null | undefined): string | null {
  const n = toScore(score)
  if (n === null) return null
  if (n >= 0.7) return 'Strong fit'
  if (n >= 0.45) return 'Solid fit'
  return 'Fair fit'
}

/** Odds word from the admission band (Discover's reliable signal). Null when absent. */
export function oddsWord(band: MatchBand | null | undefined): string | null {
  if (band === 'reach') return 'Reach'
  if (band === 'target') return 'Target'
  if (band === 'safer') return 'Safer'
  return null
}
