import clsx from 'clsx'

// Skeleton — Spec/02-design-system.md §13. 1.2s shimmer on muted base.
interface SkeletonProps {
  className?: string
}

export default function Skeleton({ className }: SkeletonProps) {
  return <div className={clsx('up-skeleton rounded-md', className || 'h-4 w-full')} />
}

export function SkeletonCard() {
  return (
    <div className="bg-card rounded-lg border border-border elev-subtle p-4 space-y-3">
      <Skeleton className="h-5 w-3/4" />
      <Skeleton className="h-4 w-1/2" />
      <Skeleton className="h-4 w-full" />
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
