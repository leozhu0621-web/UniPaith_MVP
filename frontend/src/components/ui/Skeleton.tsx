import clsx from 'clsx'

// Skeleton — Spec/02-design-system.md §13. 1.2s shimmer on muted base.
interface SkeletonProps {
  className?: string
}

export default function Skeleton({ className }: SkeletonProps) {
  return <div className={clsx('up-skeleton rounded-md', className || 'h-4 w-full')} />
}

// SkeletonRing — placeholder for the DualRing score (Spec 77 §4: skeletons
// mirror the final layout to avoid CLS when content arrives).
export function SkeletonRing({ size = 72 }: { size?: number }) {
  return <div className="up-skeleton rounded-full shrink-0" style={{ height: size, width: size }} />
}

// SkeletonCard — mirrors the real match/program card (ring + title + meta +
// badge row + footer bar) so the grid does not reflow when matches load.
export function SkeletonCard() {
  return (
    <div className="bg-card rounded-xl border border-border elev-subtle overflow-hidden">
      <div className="p-4 flex items-start gap-3">
        <SkeletonRing />
        <div className="flex-1 space-y-2 pt-1">
          <Skeleton className="h-4 w-3/4" />
          <Skeleton className="h-3 w-1/2" />
          <div className="flex gap-1.5 pt-1">
            <Skeleton className="h-4 w-12" />
            <Skeleton className="h-4 w-16" />
          </div>
        </div>
      </div>
      <div className="border-t border-border h-10" />
    </div>
  )
}

export function SkeletonTable({ rows = 5 }: { rows?: number }) {
  return (
    <div className="space-y-2">
      <Skeleton className="h-10 w-full" />
      {Array.from({ length: rows }).map((_, i) => (
        <Skeleton key={i} className="h-12 w-full" />
      ))}
    </div>
  )
}
