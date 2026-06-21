/**
 * Spec 09 §4A — "Your realistic shot" probability bands.
 *
 * Distinct from fitness + confidence: this answers *"what's my realistic
 * shot?"* with conservative ranges for admit / scholarship / waitlist plus
 * the top drivers. Honesty guardrail (§4A / Spec 46 §6):
 *   - Always a range — the bar's WIDTH encodes uncertainty, never a point.
 *   - When there isn't enough signal we show "Not enough data yet", never a
 *     misleading number.
 *   - Decision-support, not a promise — institutions decide, not the model.
 *
 * Reused on the Match card (expandable) and prominently on the program
 * detail page. No gold in the body (Spec 09 §10) — cobalt + neutral only.
 */
import { ArrowDownRight, ArrowUpRight, Info } from 'lucide-react'

import Skeleton from '../../../components/ui/Skeleton'
import type { ProbabilityBands as Bands } from '../../../types'

function pct(n: number): string {
  return `${Math.round(n * 100)}%`
}

const ADMIT_LABEL: Record<string, string> = {
  likely: 'Likely',
  target: 'Target',
  reach: 'Reach',
  unlikely: 'Unlikely',
}

/** A range bar: the filled segment spans [low, high]; its width = uncertainty. */
function RangeRow({
  label,
  low,
  high,
  approx,
  caption,
}: {
  label: string
  low?: number
  high?: number
  approx?: number
  caption?: string
}) {
  const lo = approx != null ? Math.max(0, approx - 0.03) : (low ?? 0)
  const hi = approx != null ? Math.min(1, approx + 0.03) : (high ?? 0)
  const leftPct = Math.max(0, Math.min(100, lo * 100))
  const widthPct = Math.max(2, Math.min(100 - leftPct, (hi - lo) * 100))
  const valueText =
    approx != null ? `~${pct(approx)}` : `${pct(low ?? 0)}–${pct(high ?? 0)}`
  return (
    <div className="grid grid-cols-[88px_1fr_88px] items-center gap-3">
      <span className="text-xs font-medium text-foreground">{label}</span>
      <div className="relative h-2 rounded-full bg-muted overflow-hidden" aria-hidden>
        <div
          className="absolute h-full rounded-full bg-secondary/70"
          style={{ left: `${leftPct}%`, width: `${widthPct}%` }}
        />
      </div>
      <span className="text-xs font-bold tabular-nums text-foreground text-right">
        {valueText}
        {caption && <span className="block text-[10px] font-normal text-foreground/70">{caption}</span>}
      </span>
    </div>
  )
}

export interface ProbabilityBandsProps {
  bands?: Bands | null
  reason?: string | null
  loading?: boolean
  /** Hide the "Your realistic shot" heading (e.g. inside a card that has its own). */
  hideHeading?: boolean
  className?: string
}

// The "not enough data yet" copy depends on WHOSE side the gap is on (Spec 09
// §4A honesty guardrail) — a program with no admit history reads differently
// from a student profile too sparse to estimate. Without this the two collapse
// into one misleading line.
const NO_DATA_COPY: Record<string, string> = {
  no_history: 'No admissions history yet for this program.',
  not_match_ready: 'Add more to your profile to estimate your realistic shot.',
}

export default function ProbabilityBands({
  bands,
  reason,
  loading,
  hideHeading,
  className,
}: ProbabilityBandsProps) {
  if (loading) {
    return (
      <div className={className}>
        {!hideHeading && <Heading />}
        <div className="space-y-2">
          {[0, 1, 2].map(i => (
            <Skeleton key={i} className="h-2 rounded-full" />
          ))}
        </div>
      </div>
    )
  }

  if (!bands) {
    return (
      <div className={className}>
        {!hideHeading && <Heading />}
        <div className="flex items-start gap-2 text-xs text-foreground">
          <Info size={13} className="mt-0.5 shrink-0 text-foreground/60" />
          <span className="font-medium text-foreground">
            {(reason && NO_DATA_COPY[reason]) || 'Not enough data yet.'}
          </span>
        </div>
      </div>
    )
  }

  return (
    <div className={className}>
      {!hideHeading && <Heading label={ADMIT_LABEL[bands.admit.label]} />}
      <div className="space-y-2">
        <RangeRow label="Admit" low={bands.admit.low} high={bands.admit.high} />
        {bands.scholarship && (
          <RangeRow label="Scholarship" low={bands.scholarship.low} high={bands.scholarship.high} />
        )}
        {bands.waitlist && <RangeRow label="Waitlist" approx={bands.waitlist.approx} />}
      </div>

      {bands.drivers.length > 0 && (
        <div className="mt-3 flex flex-wrap gap-1.5">
          {bands.drivers.map(d => (
            <span
              key={d.signal}
              aria-label={`${d.signal} — ${d.direction === 'up' ? 'raises your odds' : 'lowers your odds'}`}
              className="inline-flex items-center gap-1 rounded-pill border border-border bg-card px-2 py-0.5 text-[11px] text-foreground"
            >
              {d.direction === 'up' ? (
                <ArrowUpRight size={11} className="text-success" aria-hidden="true" />
              ) : (
                <ArrowDownRight size={11} className="text-foreground/60" aria-hidden="true" />
              )}
              {d.signal}
            </span>
          ))}
        </div>
      )}

      <p className="mt-2 text-[10px] text-foreground/60">
        Ranges, not promises — institutions decide.
      </p>
    </div>
  )
}

function Heading({ label }: { label?: string }) {
  return (
    <div className="flex items-center justify-between mb-2">
      <span className="text-eyebrow uppercase text-muted-foreground">Your realistic shot</span>
      {label && (
        <span className="text-[11px] font-semibold text-secondary uppercase tracking-wide">{label}</span>
      )}
    </div>
  )
}
