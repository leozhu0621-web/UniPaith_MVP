import { useNavigate } from 'react-router-dom'
import { Check, Minus } from 'lucide-react'
import Modal from '../ui/Modal'
import Button from '../ui/Button'
import { useBilling } from '../../hooks/useBilling'
import { FEATURE_LABELS, formatCents, type Feature } from '../../types/billing'

interface PaywallModalProps {
  isOpen: boolean
  onClose: () => void
  /** The feature the student tried to use — highlighted in the comparison. */
  feature?: Feature
}

// The order the comparison rows appear in. Free-tier features first.
const ROW_ORDER: Feature[] = [
  'profile',
  'limited_match',
  'expanded_match',
  'deadline_alerts',
  'scholarship_tools',
  'workshops',
]

// "Explain everything" (Spec 06 §2): the paywall states exactly what Plus adds,
// row by row — no dark-pattern vagueness.
export default function PaywallModal({ isOpen, onClose, feature }: PaywallModalProps) {
  const navigate = useNavigate()
  const { data } = useBilling()
  const matrix = data?.feature_matrix
  const planPrice = data?.prices?.student_plan_cents ?? 1500

  const goToBilling = () => {
    onClose()
    navigate('/s/billing')
  }

  const lapsed = data?.plan === 'free'

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      size="sm"
      title={lapsed ? 'Your trial has ended' : 'Unlock UniPaith Plus'}
      footer={
        <div className="flex items-center justify-end gap-2">
          <Button variant="ghost" onClick={onClose}>
            Not now
          </Button>
          <Button variant="primary" onClick={goToBilling}>
            Continue · {formatCents(planPrice)}/mo
          </Button>
        </div>
      }
    >
      <p className="text-sm text-slate mb-4">
        {lapsed
          ? 'Keep full access to matching, workshops, and deadline tools.'
          : 'Your free plan covers the essentials. Plus adds the tools that move an application forward.'}
      </p>

      <div className="rounded-lg border border-border overflow-hidden">
        <div className="grid grid-cols-[1fr_auto_auto] text-xs font-semibold text-muted-foreground bg-muted/50 px-4 py-2">
          <span>Included</span>
          <span className="w-14 text-center">Free</span>
          <span className="w-14 text-center text-cobalt">Plus</span>
        </div>
        {ROW_ORDER.map(f => {
          const inFree = matrix?.free?.[f] ?? false
          const inPlus = matrix?.plus?.[f] ?? true
          const highlight = f === feature
          return (
            <div
              key={f}
              className={`grid grid-cols-[1fr_auto_auto] items-center px-4 py-2.5 text-sm border-t border-border ${
                highlight ? 'bg-primary/10' : ''
              }`}
            >
              <span className="text-charcoal">{FEATURE_LABELS[f]}</span>
              <span className="w-14 flex justify-center">
                {inFree ? (
                  <Check size={16} className="text-success" />
                ) : (
                  <Minus size={16} className="text-muted-foreground/50" />
                )}
              </span>
              <span className="w-14 flex justify-center">
                {inPlus ? (
                  <Check size={16} className="text-cobalt" />
                ) : (
                  <Minus size={16} className="text-muted-foreground/50" />
                )}
              </span>
            </div>
          )
        })}
      </div>

      <p className="text-xs text-muted-foreground mt-3">
        Cancel anytime. We exchange value for data — we never sell it.
      </p>
    </Modal>
  )
}
