/**
 * A one-line counselor read of a match's band — the "strategy → matches"
 * storytelling. Turns the two ring numbers (fitness + the reach/target/safer
 * band, which encodes admission odds) into plain language framed as fit-for-you
 * + odds, so a student sees WHY a program sits where it does, not just a score.
 *
 * Pure + isolated so it's unit-tested without rendering.
 */
import type { MatchBand } from '../../../types'

const FIT = { high: 'Strong fit for you', mid: 'A solid fit', low: 'A fair fit' } as const
const ODDS = {
  reach: 'admission here is competitive',
  target: 'your odds look realistic',
  safer: "you're very likely to get in",
} as const
const LEAD = { reach: 'A reach', target: 'A target', safer: 'A safer choice' } as const

function tier(fitness: number): 'high' | 'mid' | 'low' {
  return fitness >= 0.7 ? 'high' : fitness >= 0.45 ? 'mid' : 'low'
}

export function matchStoryline(
  band: MatchBand | null | undefined,
  fitness: number,
  hasFitness: boolean,
): string {
  if (band !== 'reach' && band !== 'target' && band !== 'safer') return ''
  const odds = ODDS[band]
  // No raw fitness served (ring is band-derived) — frame the band alone by odds.
  if (!hasFitness) return `${LEAD[band]} — ${odds}.`
  // A reach contrasts fit against odds ("— but"); target/safer are additive.
  const fit = FIT[tier(fitness)]
  const connector = band === 'reach' ? ' — but ' : ', and '
  return `${fit}${connector}${odds}.`
}
