import clsx from 'clsx'

// Reach / Target / Safer band badge — Spec/02-design-system.md §9.
// Distinct treatment so students recognize bands instantly across surfaces.
export type Band = 'reach' | 'target' | 'safer'

const BAND_CLASSES: Record<Band, string> = {
  reach: 'border border-secondary bg-card text-secondary',
  target: 'bg-success-soft text-success',
  safer: 'bg-muted text-muted-foreground',
}

const BAND_LABEL: Record<Band, string> = {
  reach: 'Reach',
  target: 'Target',
  safer: 'Safer',
}

export default function BandBadge({
  band,
  size = 'sm',
  className,
  label,
}: {
  band: Band
  size?: 'sm' | 'md'
  className?: string
  label?: string
}) {
  return (
    <span
      className={clsx(
        'inline-flex items-center rounded-pill font-semibold uppercase tracking-wide',
        BAND_CLASSES[band],
        size === 'sm' ? 'px-2 py-0.5 text-[11px]' : 'px-2.5 py-1 text-xs',
        className
      )}
    >
      {label ?? BAND_LABEL[band]}
    </span>
  )
}
