import { CheckCircle2, Send } from 'lucide-react'
import { formatDateTime } from '../../../utils/format'
import type { OfferStatus } from '../../../types'
import { decisionLabel } from './decisionUtils'

/** Spec 34 §8 — timeline when decision was released and student responded. */
export default function OfferResponseTimeline({ status }: { status: OfferStatus }) {
  const events: { at: string; label: string; detail?: string; icon: 'release' | 'response' }[] = []

  if (status.decision_at) {
    events.push({
      at: status.decision_at,
      label: 'Decision released',
      detail: status.decision ? decisionLabel(status.decision) : undefined,
      icon: 'release',
    })
  }
  if (status.response_at && status.student_response) {
    const responseLabel =
      status.student_response === 'accepted'
        ? 'Accepted'
        : status.student_response === 'declined'
          ? 'Declined'
          : status.student_response
    events.push({
      at: status.response_at,
      label: 'Applicant responded',
      detail: responseLabel,
      icon: 'response',
    })
  }

  if (events.length === 0) return null

  return (
    <div className="pt-2 border-t border-border">
      <p className="text-xs font-medium text-muted-foreground mb-2">Timeline</p>
      <ol className="space-y-2">
        {events.map(ev => (
          <li key={`${ev.icon}-${ev.at}`} className="flex gap-2 text-sm">
            <span className="mt-0.5 text-secondary shrink-0">
              {ev.icon === 'response' ? <CheckCircle2 size={14} /> : <Send size={14} />}
            </span>
            <div className="min-w-0">
              <span className="font-medium text-foreground">{ev.label}</span>
              {ev.detail && <span className="text-muted-foreground"> · {ev.detail}</span>}
              <p className="text-xs text-muted-foreground/70">{formatDateTime(ev.at)}</p>
            </div>
          </li>
        ))}
      </ol>
    </div>
  )
}
