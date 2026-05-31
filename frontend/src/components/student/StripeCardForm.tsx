import { useMemo, useState } from 'react'
import { loadStripe } from '@stripe/stripe-js'
import { CardElement, Elements, useElements, useStripe } from '@stripe/react-stripe-js'
import { ShieldCheck } from 'lucide-react'
import Button from '../ui/Button'

// PCI-safe card capture (Spec 43 §10). The card details live only inside the
// Stripe-hosted iframe (CardElement); we receive an opaque PaymentMethod id
// (pm_...) and send THAT to the backend — the raw PAN never touches our code.
// Used in place of the dev/mock raw inputs whenever provider === "stripe".

const CARD_OPTIONS = {
  style: {
    base: {
      color: '#2A2724', // --ink
      fontFamily: 'europa, system-ui, sans-serif',
      fontSize: '15px',
      '::placeholder': { color: '#8A8580' },
    },
    invalid: { color: '#B5321F' }, // --error
  },
}

interface StripeCardFormProps {
  publishableKey: string
  onToken: (paymentMethodId: string) => void
  loading?: boolean
}

function InnerForm({ onToken, loading }: { onToken: (id: string) => void; loading?: boolean }) {
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
    <div className="space-y-3">
      <div className="h-10 px-3 flex items-center rounded-lg border border-border bg-background">
        <div className="w-full">
          <CardElement options={CARD_OPTIONS} />
        </div>
      </div>
      {error && <p className="text-xs text-error">{error}</p>}
      <Button
        variant="secondary"
        size="sm"
        onClick={submit}
        loading={loading || submitting}
        disabled={!stripe}
      >
        Save card
      </Button>
      <p className="text-xs text-muted-foreground flex items-center gap-1.5">
        <ShieldCheck size={13} /> Card details go straight to Stripe — they never touch our servers.
      </p>
    </div>
  )
}

export default function StripeCardForm({ publishableKey, onToken, loading }: StripeCardFormProps) {
  const stripePromise = useMemo(() => loadStripe(publishableKey), [publishableKey])
  return (
    <Elements stripe={stripePromise}>
      <InnerForm onToken={onToken} loading={loading} />
    </Elements>
  )
}
