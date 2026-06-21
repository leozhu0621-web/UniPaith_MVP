/**
 * Strategy school-list word scales — turn the dual match scores into plain words.
 *
 * The white-paper model keeps two things separate: how well a program FITS you
 * (`fitness_score`) and how likely you are to GET IN (`confidence_score`, used
 * here as the admission-likelihood proxy). A reach can still be an excellent fit,
 * so we never collapse the two into one number.
 *
 * Scores arrive on `MatchResultDual` as 0..1 — and sometimes as strings (the
 * student match payload types them `string | null`), so we coerce with Number()
 * and guard NaN. A null / undefined / 0 score yields `null` (no tag at all).
 */

/** Coerce a possibly-string, possibly-null score into a finite number, or null. */
function toScore(score: number | string | null | undefined): number | null {
  if (score === null || score === undefined) return null
  const n = Number(score)
  if (!Number.isFinite(n) || n <= 0) return null
  return n
}

/** Fit word from `fitness_score` (0..1). Null when the score is absent / zero. */
export function fitWord(score: number | string | null | undefined): string | null {
  const n = toScore(score)
  if (n === null) return null
  if (n >= 0.85) return 'Excellent fit'
  if (n >= 0.7) return 'Strong fit'
  if (n >= 0.55) return 'Good fit'
  if (n >= 0.4) return 'Moderate fit'
  return 'Low fit'
}

/** Odds word from `confidence_score` (admission-likelihood proxy, 0..1). Null when absent / zero. */
export function oddsWord(score: number | string | null | undefined): string | null {
  const n = toScore(score)
  if (n === null) return null
  if (n >= 0.8) return 'Safe'
  if (n >= 0.6) return 'Likely'
  if (n >= 0.4) return 'Toss-up'
  if (n >= 0.2) return 'Reach'
  return 'Long shot'
}
