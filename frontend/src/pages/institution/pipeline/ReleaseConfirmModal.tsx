import Modal from '../../../components/ui/Modal'
import Button from '../../../components/ui/Button'
import Badge from '../../../components/ui/Badge'
import type { InstitutionDecision, ReleaseOfferTerms } from '../../../types'
import { decisionLabel, formatOfferTermsSummary, INSTITUTION_DECISIONS } from './decisionUtils'

/** Spec 34 §8 — single decision release confirmation with offer terms summary. */
export default function ReleaseConfirmModal({
  isOpen,
  onClose,
  decision,
  offer,
  message,
  releasing,
  onConfirm,
}: {
  isOpen: boolean
  onClose: () => void
  decision: InstitutionDecision
  offer: ReleaseOfferTerms | null
  message: string
  releasing: boolean
  onConfirm: () => void
}) {
  const tone = INSTITUTION_DECISIONS.find(d => d.value === decision)?.tone ?? 'neutral'
  const offerLines = formatOfferTermsSummary(offer)

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Confirm release" size="md">
      <div className="space-y-4">
        <p className="text-sm text-muted-foreground">
          This will notify the applicant by Inbox and email. Calendar reminders are added for offer deadlines.
        </p>
        <div className="rounded-lg border border-border p-3 space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium text-foreground">Decision</span>
            <Badge variant={tone as 'success'}>{decisionLabel(decision)}</Badge>
          </div>
          {offerLines.length > 0 && (
            <div>
              <p className="text-xs font-medium text-muted-foreground mb-1">Offer terms</p>
              <ul className="text-sm text-foreground space-y-0.5 list-disc list-inside">
                {offerLines.map(line => (
                  <li key={line}>{line}</li>
                ))}
              </ul>
            </div>
          )}
          {message.trim() && (
            <div>
              <p className="text-xs font-medium text-muted-foreground mb-1">Notice to applicant</p>
              <p className="text-sm text-foreground whitespace-pre-wrap">{message.trim()}</p>
            </div>
          )}
        </div>
        <div className="flex justify-end gap-2">
          <Button variant="tertiary" onClick={onClose} disabled={releasing}>
            Cancel
          </Button>
          <Button variant="secondary" onClick={onConfirm} disabled={releasing}>
            {releasing ? 'Releasing…' : 'Confirm release'}
          </Button>
        </div>
      </div>
    </Modal>
  )
}
