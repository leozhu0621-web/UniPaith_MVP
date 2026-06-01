import type { ReactNode } from 'react'
import Button from '../../../components/ui/Button'

// Spec 30 §8 / Spec 03 §7 — pinned-bottom action bar; Back (left) + actions (right).
// Sticky so it stays reachable on long mobile forms.
export default function WizardFooter({
  onBack,
  children,
}: {
  onBack?: () => void
  children: ReactNode
}) {
  return (
    <div className="sticky bottom-0 z-10 -mx-5 mt-8 flex items-center justify-between gap-3 border-t border-border bg-background/95 px-5 py-4 backdrop-blur sm:-mx-6 sm:px-6">
      {onBack ? (
        <Button variant="tertiary" onClick={onBack} type="button">
          Back
        </Button>
      ) : (
        <span />
      )}
      <div className="flex items-center gap-2">{children}</div>
    </div>
  )
}
