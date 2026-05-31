import { useState } from 'react'
import { Lock } from 'lucide-react'
import Card from '../ui/Card'
import Button from '../ui/Button'
import PaywallModal from './PaywallModal'
import { useEntitlement } from '../../hooks/useBilling'
import type { Feature } from '../../types/billing'

interface LockedFeatureProps {
  feature: Feature
  title: string
  description: string
  /** The real feature UI. Rendered as-is when the plan is entitled (or while
   * loading / when billing is off). */
  children: React.ReactNode
}

// Non-destructive gate (Spec 06 §4.1). Entitled plans see the real content;
// free users see a quiet lock card with a single upgrade affordance. The
// backend enforces the same entitlement, so this is UX, not the security
// boundary.
export default function LockedFeature({
  feature,
  title,
  description,
  children,
}: LockedFeatureProps) {
  const { entitled, loading } = useEntitlement(feature)
  const [open, setOpen] = useState(false)

  if (loading || entitled) return <>{children}</>

  return (
    <>
      <Card className="p-8 flex flex-col items-center text-center">
        <div className="w-11 h-11 rounded-full bg-secondary/10 flex items-center justify-center mb-3">
          <Lock size={18} className="text-cobalt" />
        </div>
        <h3 className="font-semibold text-charcoal">{title}</h3>
        <p className="text-sm text-slate mt-1 max-w-sm">{description}</p>
        <Button variant="primary" size="sm" className="mt-4" onClick={() => setOpen(true)}>
          See plans
        </Button>
      </Card>
      <PaywallModal isOpen={open} onClose={() => setOpen(false)} feature={feature} />
    </>
  )
}
