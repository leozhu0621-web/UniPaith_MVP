import { useState, type ReactNode } from 'react'
import { Lock } from 'lucide-react'

import Button from '../ui/Button'
import { useEntitlement } from '../../hooks/useSubscription'
import PaywallModal from './PaywallModal'

/**
 * Soft feature gate (Spec 07 §4.1). Renders children when the student is
 * entitled to `feature` (free tier, active trial, or Pro); otherwise shows a
 * non-blocking upgrade nudge. Never hard-blocks the core journey — while the
 * subscription is loading, `useEntitlement` reports entitled so nothing flashes.
 */
export default function EntitlementGate({
  feature,
  children,
  label = 'This is a Pro feature',
}: {
  feature: string
  children: ReactNode
  label?: string
}) {
  const { entitled } = useEntitlement(feature)
  const [open, setOpen] = useState(false)

  if (entitled) return <>{children}</>

  return (
    <div className="rounded-lg border border-dashed border-border bg-muted/40 p-4 text-center">
      <p className="inline-flex items-center gap-1.5 text-sm font-semibold text-muted-foreground">
        <Lock size={14} /> {label}
      </p>
      <div className="mt-2">
        <Button size="sm" onClick={() => setOpen(true)}>
          Upgrade to Pro
        </Button>
      </div>
      <PaywallModal isOpen={open} onClose={() => setOpen(false)} />
    </div>
  )
}
