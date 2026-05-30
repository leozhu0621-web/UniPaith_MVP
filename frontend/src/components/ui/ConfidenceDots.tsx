import clsx from 'clsx'

// Confidence dots — Spec/02-design-system.md §9.
// Five dots; filled = gold (--primary), empty = --border.
// Label: Low (1–2) / Medium (3) / High (4–5).

interface ConfidenceDotsProps {
  /** 0–100 confidence score; mapped to 0–5 filled dots. */
  value?: number
  /** Explicit filled count 0–5 (overrides value). */
  filled?: number
  showLabel?: boolean
  size?: 'sm' | 'md'
  className?: string
}

function levelLabel(n: number): string {
  if (n <= 0) return 'None'
  if (n <= 2) return 'Low'
  if (n === 3) return 'Medium'
  return 'High'
}

export default function ConfidenceDots({
  value,
  filled,
  showLabel = true,
  size = 'sm',
  className,
}: ConfidenceDotsProps) {
  const count = Math.max(0, Math.min(5, filled ?? Math.round((value ?? 0) / 20)))
  const dot = size === 'sm' ? 'h-1.5 w-1.5' : 'h-2 w-2'
  return (
    <span className={clsx('inline-flex items-center gap-2', className)}>
      <span className="inline-flex items-center gap-1" role="img" aria-label={`${levelLabel(count)} confidence`}>
        {Array.from({ length: 5 }).map((_, i) => (
          <span
            key={i}
            className={clsx('rounded-full', dot, i < count ? 'bg-primary' : 'bg-border')}
          />
        ))}
      </span>
      {showLabel && <span className="text-xs font-semibold text-muted-foreground">{levelLabel(count)}</span>}
    </span>
  )
}
