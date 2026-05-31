import type { ReactNode } from 'react'
import { AlertTriangle, Info } from 'lucide-react'

import Button from '../../../components/ui/Button'
import Card from '../../../components/ui/Card'

/** First-run / no-result hint (Spec/14-workshops.md §8 empty state). */
export function EmptyHint({ children }: { children: ReactNode }) {
  return (
    <Card variant="card-flush" className="px-4 py-10 text-center text-sm text-student-text">
      {children}
    </Card>
  )
}

/**
 * Hard-failure note (Spec/14-workshops.md §8 error state). The backend falls
 * back to a rule-based result on agent failure (never 5xx), so this only
 * surfaces on real infra/network errors.
 */
export function ErrorNote({ onRetry }: { onRetry: () => void }) {
  return (
    <Card className="space-y-3">
      <div className="flex items-start gap-2 text-sm text-student-ink">
        <AlertTriangle size={16} className="mt-0.5 shrink-0 text-warning" />
        <span>We couldn't reach the workshop service just now. Please try again in a moment.</span>
      </div>
      <Button variant="tertiary" size="sm" onClick={onRetry}>
        Try again
      </Button>
    </Card>
  )
}

/** Surfaced when a run came back rule-based (Spec/14-workshops.md §8 "Showing rule-based result"). */
export function StubNote() {
  return (
    <span className="inline-flex items-center gap-1 text-xs text-student-text">
      <Info size={12} /> Showing rule-based feedback
    </span>
  )
}

/** Per-program readiness summary card (Spec/14-workshops.md §6). */
export function ReadinessCard({ programName, summary }: { programName: string; summary: string }) {
  return (
    <Card>
      <div className="mb-1 text-eyebrow uppercase text-cobalt">Readiness · {programName}</div>
      <p className="text-sm text-student-ink">{summary}</p>
    </Card>
  )
}
