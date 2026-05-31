import { Check } from 'lucide-react'

import Modal from '../ui/Modal'
import SubscribeForm from './SubscribeForm'

const PRO_POINTS = [
  'Expanded matching with full reasoning',
  'Real-time deadline alerts',
  'Scholarship and affordability tools',
  'Structured writing workflows',
]

/** Soft paywall (Spec 07 §4/§11). Opened from the trial banner + entitlement gates. */
export default function PaywallModal({
  isOpen,
  onClose,
}: {
  isOpen: boolean
  onClose: () => void
}) {
  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Upgrade to UniPaith Pro" size="sm">
      <div className="space-y-5">
        <p className="text-sm text-slate">$15/month after your free trial. Cancel anytime.</p>
        <ul className="space-y-1.5">
          {PRO_POINTS.map(p => (
            <li key={p} className="flex items-start gap-2 text-sm text-charcoal">
              <Check size={16} className="text-success mt-0.5 shrink-0" />
              {p}
            </li>
          ))}
        </ul>
        <SubscribeForm onDone={onClose} />
      </div>
    </Modal>
  )
}
