// Density layer — a compact stat (value + eyebrow label + optional sub), for the
// tight stat strips that replace large stat cards.

interface StatTileProps {
  label: string
  value: React.ReactNode
  sub?: string
}

export default function StatTile({ label, value, sub }: StatTileProps) {
  return (
    <div className="min-w-0">
      <p className="text-lg font-semibold leading-none text-foreground">{value}</p>
      <p className="mt-1 truncate text-eyebrow uppercase text-muted-foreground">{label}</p>
      {sub && <p className="mt-0.5 truncate text-xs text-muted-foreground">{sub}</p>}
    </div>
  )
}
