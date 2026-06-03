// PageLoader — Spec/02-design-system.md §13.
// Thin 2px progress bar at the top of the viewport, --primary color.
// Use when the entire route is loading. Indeterminate by default;
// `progress` (0–100) drives a determinate fill if known.

import clsx from 'clsx'

interface PageLoaderProps {
  /** When provided (0-100), shows a determinate fill instead of an indeterminate sweep. */
  progress?: number
  className?: string
}

export default function PageLoader({ progress, className }: PageLoaderProps) {
  const determinate = typeof progress === 'number'
  const clamped = determinate ? Math.max(0, Math.min(100, progress!)) : 0
  return (
    <div
      role="progressbar"
      aria-valuemin={0}
      aria-valuemax={100}
      aria-valuenow={determinate ? clamped : undefined}
      aria-label="Loading page"
      className={clsx(
        'fixed top-0 inset-x-0 z-[60] h-0.5 overflow-hidden bg-transparent pointer-events-none',
        className,
      )}
    >
      {determinate ? (
        <div
          className="h-full bg-primary transition-[width] duration-200 ease-out"
          style={{ width: `${clamped}%` }}
        />
      ) : (
        <div className="h-full w-1/3 bg-primary animate-page-loader-sweep" />
      )}
    </div>
  )
}
