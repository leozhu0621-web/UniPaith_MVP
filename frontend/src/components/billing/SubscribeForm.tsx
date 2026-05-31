import { useState } from 'react'
import { Lock } from 'lucide-react'

import Button from '../ui/Button'
import Input from '../ui/Input'
import { useSubscribe } from '../../hooks/useSubscription'

const BRANDS = ['visa', 'mastercard', 'amex', 'discover']

/**
 * Mock card-on-file checkout (Spec 07 §4 — no real PSP). Collects only a brand +
 * last 4, never a PAN. Shared by the paywall modal and the settings billing card.
 */
export default function SubscribeForm({
  defaultAdFree = false,
  onDone,
}: {
  defaultAdFree?: boolean
  onDone?: () => void
}) {
  const [brand, setBrand] = useState('visa')
  const [last4, setLast4] = useState('')
  const [error, setError] = useState('')
  const [adFree, setAdFree] = useState(defaultAdFree)
  const sub = useSubscribe()

  const submit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!/^\d{4}$/.test(last4)) {
      setError('Enter the last 4 digits')
      return
    }
    setError('')
    sub.mutate(
      { card_brand: brand, card_last4: last4, ad_free: adFree },
      { onSuccess: () => onDone?.() }
    )
  }

  return (
    <form onSubmit={submit} className="space-y-4">
      <p className="flex items-center gap-1.5 text-xs text-muted-foreground">
        <Lock size={13} /> Demo checkout — no real card is charged.
      </p>

      <div>
        <label htmlFor="card-brand" className="block text-[13px] font-semibold text-muted-foreground mb-1.5">
          Card type
        </label>
        <select
          id="card-brand"
          value={brand}
          onChange={e => setBrand(e.target.value)}
          className="h-10 w-full rounded-md border border-border bg-card px-3 text-sm capitalize focus:outline-none focus:ring-2 focus:ring-ring focus:border-secondary"
        >
          {BRANDS.map(b => (
            <option key={b} value={b}>
              {b}
            </option>
          ))}
        </select>
      </div>

      <Input
        label="Card number (last 4)"
        inputMode="numeric"
        maxLength={4}
        placeholder="4242"
        value={last4}
        onChange={e => setLast4(e.target.value.replace(/\D/g, '').slice(0, 4))}
        error={error}
      />

      <label className="flex items-center gap-2 text-sm text-charcoal">
        <input
          type="checkbox"
          className="accent-cobalt"
          checked={adFree}
          onChange={e => setAdFree(e.target.checked)}
        />
        Add ad-free browsing for $5/mo
      </label>

      <Button type="submit" loading={sub.isPending} className="w-full">
        Start UniPaith Pro · $15/mo
      </Button>
    </form>
  )
}
