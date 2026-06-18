// AI-Structure-3 §14 — the student match payload is band-only (no raw
// fitness/confidence number). When no raw score is served, the DualRing reads
// from the reach/target/safer band: a representative fill so the visual still
// communicates at a glance WITHOUT surfacing a precise number the backend
// deliberately withholds. Shared by MatchCard and ProgramCard so the two cards
// for the same program never disagree on what's knowable.

export const BAND_FILL: Record<string, number> = { safer: 0.82, target: 0.62, reach: 0.4 }

function toUnit(v: string | number | null | undefined): number {
  const n = typeof v === 'string' ? parseFloat(v) : (v ?? 0)
  if (!Number.isFinite(n)) return 0
  const u = n > 1 ? n / 100 : n
  return Math.max(0, Math.min(1, u))
}

/** Resolve a ring fill from a raw score if present, else from the band.
 *  `fromBand` is true when the value is band-derived → the caller hides the
 *  precise numeral (DualRing shows the band glyph instead). */
export function ringFromMatch(
  raw: string | number | null | undefined,
  band: string | null | undefined,
): { value: number; fromBand: boolean } {
  if (raw != null && raw !== '') return { value: toUnit(raw), fromBand: false }
  if (band && band in BAND_FILL) return { value: BAND_FILL[band], fromBand: true }
  return { value: 0, fromBand: true }
}
