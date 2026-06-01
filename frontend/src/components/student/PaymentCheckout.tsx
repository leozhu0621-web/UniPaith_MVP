import { useState } from 'react'
import { Lock, ShieldCheck } from 'lucide-react'
import Modal from '../ui/Modal'
import Button from '../ui/Button'
import { showToast } from '../../stores/toast-store'
import { confirmMockPayment, formatMoney, type CheckoutSession, type CostTracker } from '../../api/payments'

// Spec 39 §8 — checkout is calm + trustworthy: clear amount, explicit currency,
// no gold pressure (cobalt CTA), never a dark pattern. Mock provider completes
// in-app; Stripe redirects to hosted checkout.

interface PaymentCheckoutProps {
  session: CheckoutSession | null
  label?: string
  onClose: () => void
  onPaid: (tracker: CostTracker) => void
}

export default function PaymentCheckout({ session, label, onClose, onPaid }: PaymentCheckoutProps) {
  const [paying, setPaying] = useState(false)
  if (!session) return null

  const isFee = session.kind === 'application_fee'
  const heading = label || (isFee ? 'Pay application fee' : 'Pay enrollment deposit')
  const money = formatMoney(session.amount, session.currency)

  const completeMock = async () => {
    setPaying(true)
    try {
      const tracker = await confirmMockPayment(session.payment_id)
      showToast('Payment received', 'success')
      onPaid(tracker)
    } catch (e) {
      showToast(e instanceof Error ? e.message : 'Payment could not be completed', 'error')
    } finally {
      setPaying(false)
    }
  }

  const goToStripe = () => {
    if (session.checkout_url) window.location.href = session.checkout_url
  }

  return (
    <Modal isOpen={!!session} onClose={onClose} title={heading} size="sm">
      <div className="space-y-4">
        <div className="rounded-lg border border-border bg-muted/40 px-4 py-3 flex items-center justify-between">
          <span className="text-sm text-muted-foreground">Amount due</span>
          <span className="text-2xl font-bold text-foreground tabular-nums">{money}</span>
        </div>

        <p className="flex items-center gap-1.5 text-xs text-muted-foreground">
          <Lock size={13} className="shrink-0" />
          Secure checkout in {session.currency}. We never store your card details.
        </p>

        {session.inline ? (
          <>
            <div className="rounded-lg bg-warning-soft px-3 py-2 text-xs text-warning flex items-start gap-1.5">
              <ShieldCheck size={14} className="mt-0.5 shrink-0" />
              <span>
                Test mode — no real charge is made. This records your{' '}
                {isFee ? 'application fee' : 'enrollment deposit'} for the demo.
              </span>
            </div>
            <Button variant="secondary" className="w-full" loading={paying} onClick={completeMock}>
              Pay {money}
            </Button>
          </>
        ) : (
          <Button variant="secondary" className="w-full" onClick={goToStripe}>
            Continue to secure checkout
          </Button>
        )}

        <button
          type="button"
          onClick={onClose}
          className="w-full text-sm text-muted-foreground hover:text-foreground"
        >
          Cancel
        </button>
      </div>
    </Modal>
  )
}
