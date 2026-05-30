// Skeleton — Spec/02-design-system.md §13.
// Light bars on --muted; 1.2s shimmer. Skeletons for content blocks
// ≥200px tall. Never block the UI with a centered spinner.

import clsx from 'clsx'

interface SkeletonProps {
  className?: string
  /** Optional accessible label for screen readers (defaults to "Loading"). */
  label?: string
}

export default function Skeleton({ className, label = 'Loading' }: SkeletonProps) {
  return (
    <div
      role="status"
      aria-label={label}
      className={clsx(
        'relative overflow-hidden rounded-md bg-muted',
        'before:absolute before:inset-0 before:-translate-x-full before:animate-shimmer',
        "before:bg-gradient-to-r before:from-transparent before:via-white/40 before:to-transparent",
        'dark:before:via-white/10',
        className || 'h-4 w-full',
      )}
    />
  )
}

export function SkeletonCard() {
  return (
    <div className="rounded-[14px] border border-border bg-card elev-subtle p-6 space-y-3">
      <Skeleton className="h-5 w-3/4" />
      <Skeleton className="h-4 w-1/2" />
      <Skeleton className="h-4 w-full" />
      <Skeleton className="h-4 w-5/6" />
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

export function SkeletonText({ lines = 3 }: { lines?: number }) {
  return (
    <div className="space-y-2">
      {Array.from({ length: lines }).map((_, i) => (
        <Skeleton
          key={i}
          className={clsx('h-4', i === lines - 1 ? 'w-3/4' : 'w-full')}
        />
      ))}
    </div>
  )
}
