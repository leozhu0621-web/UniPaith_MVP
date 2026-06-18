// "Your list balance" strip (Discover review 2026-06-14, idea #1) — a compact,
// deterministic read of the saved list's reach/target/safer mix + a neutral
// nudge. Cobalt/neutral only (no gold — this is guidance, not an earned beat).
import { Scale } from 'lucide-react'
import type { SavedProgram } from '../../../types'
import { computeBalance } from './listBalance'

const SEGMENTS: { key: 'reach' | 'target' | 'safer'; label: string; bar: string; dot: string }[] = [
  { key: 'reach', label: 'reach', bar: 'bg-secondary/30', dot: 'bg-secondary/40' },
  { key: 'target', label: 'target', bar: 'bg-secondary/60', dot: 'bg-secondary/70' },
  { key: 'safer', label: 'safer', bar: 'bg-secondary', dot: 'bg-secondary' },
]

export default function ListBalanceMeter({ programs }: { programs: SavedProgram[] }) {
  const b = computeBalance(programs)
  if (b.scored === 0) return null // nothing scored yet — the page's own guidance covers it

  return (
    <section className="mb-5 rounded-xl border border-border bg-card p-4" aria-label="Your list balance">
      <div className="flex items-center gap-2 mb-2">
        <Scale size={14} className="text-secondary" aria-hidden />
        <h2 className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground flex-1">Your list balance</h2>
        <span className="text-xs text-muted-foreground tabular-nums">
          {b.reach} reach · {b.target} target · {b.safer} safer
          {b.unscored > 0 && <span className="text-muted-foreground/70"> · {b.unscored} unscored</span>}
        </span>
      </div>

      {/* Proportional bar — reach (lightest) → safer (cobalt). Pure display. */}
      <div className="flex h-2 w-full overflow-hidden rounded-full bg-muted" aria-hidden>
        {SEGMENTS.map(s => {
          const n = b[s.key]
          if (n === 0) return null
          return <div key={s.key} className={s.bar} style={{ width: `${(n / b.scored) * 100}%` }} />
        })}
      </div>

      {b.nudge && <p className="mt-2 text-xs text-foreground">{b.nudge}</p>}
    </section>
  )
}
