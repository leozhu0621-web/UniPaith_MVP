import clsx from 'clsx'
import type { Band } from '../ui/BandBadge'
import { prefersReducedMotion } from '../../hooks/useCountUp'

// Portfolio balance meter — a stacked reach/target/safer bar a counselor can read
// at a glance, shared by Saved and Applications. Segment fills reuse the same
// color family as BandBadge so a band looks identical everywhere: reach = cobalt
// (secondary), target = green (success), safer = neutral (muted-foreground).
// Guidance, not an earned beat — never gold.
const BAND_ORDER: Band[] = ['reach', 'target', 'safer']

const BAND_LABEL: Record<Band, string> = {
  reach: 'reach',
  target: 'target',
  safer: 'safer',
}

const BAND_FILL: Record<Band, string> = {
  reach: 'bg-secondary',
  target: 'bg-success',
  safer: 'bg-muted-foreground',
}

/**
 * Gentle, inform-only nudge — shown only when the mix is genuinely lopsided.
 * Returns null when the spread is reasonable. Pure, so it's unit-testable.
 */
export function balanceNudge(counts: Record<Band, number>): string | null {
  const total = counts.reach + counts.target + counts.safer
  if (total === 0) return null
  if (counts.reach > 0 && counts.safer === 0) return 'Add a safer option to balance your list.'
  const present = BAND_ORDER.filter(b => counts[b] > 0)
  if (present.length === 1) return `Your list is all ${present[0]} — consider a wider range.`
  return null
}

export default function BandBalanceBar({
  reach,
  target,
  safer,
  className,
}: {
  reach: number
  target: number
  safer: number
  className?: string
}) {
  const counts: Record<Band, number> = { reach, target, safer }
  const total = reach + target + safer
  if (total === 0) return null

  const summary = BAND_ORDER.map(b => `${counts[b]} ${BAND_LABEL[b]}`).join(', ')
  const nudge = balanceNudge(counts)
  const animate = !prefersReducedMotion()

  return (
    <section className={clsx('rounded-xl border border-border bg-card p-4', className)}>
      <div className="mb-2 flex items-center gap-2">
        <h2 className="flex-1 text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">
          Portfolio balance
        </h2>
        <span className="text-xs text-muted-foreground tabular-nums">{summary}</span>
      </div>

      <div
        role="img"
        aria-label={summary}
        className="flex h-2 w-full overflow-hidden rounded-full bg-muted"
      >
        {BAND_ORDER.map(b => {
          const n = counts[b]
          if (n === 0) return null
          return (
            <div
              key={b}
              className={clsx(BAND_FILL[b], animate && 'motion-safe:transition-[width]')}
              style={{ width: `${(n / total) * 100}%` }}
            />
          )
        })}
      </div>

      <div className="mt-2 flex flex-wrap gap-x-4 gap-y-1">
        {BAND_ORDER.map(b => (
          <span key={b} className="inline-flex items-center gap-1.5 text-[11px] text-muted-foreground">
            <span className={clsx('h-2 w-2 rounded-full', BAND_FILL[b])} aria-hidden />
            {counts[b]} {BAND_LABEL[b]}
          </span>
        ))}
      </div>

      {nudge && <p className="mt-2 text-xs text-foreground">{nudge}</p>}
    </section>
  )
}
