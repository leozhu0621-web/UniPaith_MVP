// Density layer — a compact stat (value + eyebrow label + optional sub), for the
// tight stat strips that replace large stat cards.
//
// Ship B motion: purely numeric values count up on mount (Imprint progress
// language, rAF ease-out, reduced-motion → instant). String/node values
// render static — never coerce formatted strings into the counter.

import { useCountUp } from '../../../hooks/useCountUp'

interface StatTileProps {
  label: string
  value: React.ReactNode
  sub?: string
}

export default function StatTile({ label, value, sub }: StatTileProps) {
  const numeric = typeof value === 'number' && Number.isFinite(value)
  const counted = useCountUp(numeric ? value : 0)
  return (
    <div className="min-w-0">
      <p className="text-lg font-semibold leading-none text-foreground">
        {numeric ? counted : value}
      </p>
      <p className="mt-1 truncate text-eyebrow uppercase text-muted-foreground">{label}</p>
      {sub && <p className="mt-0.5 truncate text-xs text-muted-foreground">{sub}</p>}
    </div>
  )
}
