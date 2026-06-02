import { useMemo, useState } from 'react'
import { loadStripe } from '@stripe/stripe-js'
import { CardElement, Elements, useElements, useStripe } from '@stripe/react-stripe-js'
import { ShieldCheck } from 'lucide-react'
import Button from '../ui/Button'

// PCI-safe card capture for the $15/mo subscription (Spec 07 §4.1 / 43 §10).
// The card lives only inside the Stripe-hosted iframe (CardElement); we receive
// an opaque PaymentMethod id (pm_...) and hand THAT to the backend — the raw PAN
// never touches our code. Rendered in place of the one-click upgrade whenever
// provider === "stripe".

const CARD_OPTIONS = {
  style: {
    base: {
      color: '#2A2724',
      fontFamily: 'europa, system-ui, sans-serif',
      fontSize: '15px',
      '::placeholder': { color: '#8A8580' },
    },
    invalid: { color: '#B5321F' },
  },
}

interface Props {
  publishableKey: string
  submitLabel: string
  loading?: boolean
  onToken: (paymentMethodId: string) => void
  onCancel: () => void
}

function Inner({ submitLabel, loading, onToken, onCancel }: Omit<Props, 'publishableKey'>) {
  const stripe = useStripe()
  const elements = useElements()
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)

  const submit = async () => {
    if (!stripe || !elements) return
    const card = elements.getElement(CardElement)
    if (!card) return
    setSubmitting(true)
    setError('')
    const { error: err, paymentMethod } = await stripe.createPaymentMethod({ type: 'card', card })
    setSubmitting(false)
    if (err || !paymentMethod) {
      setError(err?.message || 'Could not validate card')
      return
    }
    onToken(paymentMethod.id)
  }

  return (
    <div className="space-y-3 rounded-lg border border-border bg-muted/40 p-3">
      <div className="flex h-10 items-center rounded-lg border border-border bg-background px-3">
        <div className="w-full">
          <CardElement options={CARD_OPTIONS} />
        </div>
      </div>
      {error && <p className="text-xs text-error">{error}</p>}
      <div className="flex items-center gap-2">
        <Button variant="secondary" size="sm" onClick={submit} loading={loading || submitting} disabled={!stripe}>
          {submitLabel}
        </Button>
        <Button variant="ghost" size="sm" onClick={onCancel} disabled={submitting || loading}>
          Cancel
        </Button>
      </div>
      <p className="flex items-center gap-1.5 text-xs text-muted-foreground">
        <ShieldCheck size={13} /> Card details go straight to Stripe — they never touch our servers.
      </p>
    </div>
  )
}

export default function StripeSubscriptionForm({ publishableKey, ...rest }: Props) {
  const stripePromise = useMemo(() => loadStripe(publishableKey), [publishableKey])
  return (
    <Elements stripe={stripePromise}>
      <Inner {...rest} />
    </Elements>
  )
}
