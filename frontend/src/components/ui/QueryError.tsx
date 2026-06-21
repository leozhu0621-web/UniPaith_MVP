import { AlertTriangle } from 'lucide-react'
import { COPY } from '../../lib/copy'
import Button from './Button'

// QueryError — the canonical error state for a failed data fetch (Spec 78 §3).
// Icon + plain-language cause + retry. No illustration (brand). Use everywhere a
// useQuery/useMutation can fail so a surface never renders blank on error.
// Voice (Spec 78 §8): plain, honest, no blame, always a next step.
interface QueryErrorProps {
  /** Short heading. Defaults to the generic, never-blame copy. */
  title?: string
  /** Optional plain-language cause (e.g. the mapped client.ts message). */
  detail?: string
  /** Wire to `query.refetch()` / `mutation.mutate()`. Renders a Try-again control. */
  onRetry?: () => void
  retryLabel?: string
  /** block = full-region (default) · inline = in-panel note · row = table cell. */
  variant?: 'block' | 'inline' | 'row'
}

export default function QueryError({
  title = COPY.errLoad,
  detail = COPY.errRetry,
  onRetry,
  retryLabel = COPY.errRetryAction,
  variant = 'block',
}: QueryErrorProps) {
  if (variant === 'inline' || variant === 'row') {
    return (
      <div
        className={
          variant === 'row'
            ? 'flex items-center justify-center gap-2 py-6 text-sm'
            : 'flex items-center gap-2 py-3 text-sm'
        }
        role="alert"
      >
        <AlertTriangle size={15} className="text-warning shrink-0" />
        <span className="text-muted-foreground">
          <span className="font-semibold text-foreground">{title}</span>
          {detail && <span> {detail}</span>}
        </span>
        {onRetry && (
          <button onClick={onRetry} className="text-secondary font-medium hover:underline">
            {retryLabel}
          </button>
        )}
      </div>
    )
  }

  return (
    <div className="flex flex-col items-center justify-center py-16 text-center" role="alert">
      <div className="mb-4 text-warning">
        <AlertTriangle size={28} />
      </div>
      <h3 className="text-h3 text-foreground">{title}</h3>
      {detail && <p className="mt-1.5 text-sm text-muted-foreground max-w-[56ch]">{detail}</p>}
      {onRetry && (
        <Button onClick={onRetry} variant="secondary" className="mt-5" aria-label={retryLabel}>
          {retryLabel}
        </Button>
      )}
    </div>
  )
}
