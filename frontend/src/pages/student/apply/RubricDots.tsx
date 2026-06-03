import clsx from 'clsx'

/**
 * Rubric dot meter — Spec/14-workshops.md §3.3 + §10.
 *
 *   "Rubric dot fills in --primary gold (this is the one accent moment)."
 *
 * Five (or `max`) dots; filled dots are gold (`--primary`), empty are a
 * muted hairline. The gold here is intentional and spec-sanctioned — it is
 * the single accent in the workshops UI; everything else stays cobalt /
 * neutral so the dots read as "earned" punctuation.
 */
export function RubricDots({ score, max = 5 }: { score: number; max?: number }) {
  const filled = Math.max(0, Math.min(max, Math.round(score)))
  return (
    <span
      className="inline-flex items-center gap-1"
      role="img"
      aria-label={`${score.toFixed(1)} out of ${max}`}
    >
      {Array.from({ length: max }).map((_, i) => (
        <span
          key={i}
          className={clsx(
            'h-2.5 w-2.5 rounded-full',
            i < filled ? 'bg-primary' : 'bg-muted ring-1 ring-inset ring-border',
          )}
        />
      ))}
    </span>
  )
}

/**
 * Full rubric block — one row per criterion (gold dots + numeric value).
 * `scores` is the backend `rubric_scores` map (criterion → 0..5). Helper
 * keys outside 0..5 (e.g. the test-prep current/target/gap numbers) are
 * filtered out — those render as stats, not dots.
 */
export function RubricScores({ scores }: { scores: Record<string, number> }) {
  const entries = Object.entries(scores).filter(
    ([, v]) => typeof v === 'number' && v >= 0 && v <= 5,
  )
  if (entries.length === 0) return null
  return (
    <div className="grid grid-cols-1 gap-x-8 gap-y-2.5 sm:grid-cols-2">
      {entries.map(([k, v]) => (
        <div key={k} className="flex items-center justify-between gap-3 text-sm">
          <span className="capitalize text-foreground">{k.replace(/_/g, ' ')}</span>
          <span className="flex items-center gap-2">
            <RubricDots score={Number(v)} />
            <span className="w-7 text-right text-xs tabular-nums text-foreground">
              {Number(v).toFixed(1)}
            </span>
          </span>
        </div>
      ))}
    </div>
  )
}

export default RubricDots
