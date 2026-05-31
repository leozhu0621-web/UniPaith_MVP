import { useState } from 'react'
import { Link } from 'react-router-dom'
import { Sparkles, X } from 'lucide-react'

import { useSubscription } from '../../hooks/useSubscription'

const DISMISS_KEY = 'unipaith_trial_banner_dismissed'

/**
 * Spec 07 (§4/§11) — the always-on trial / paywall touchpoint in the student
 * shell. Trialing → days-left countdown (dismissible per session). Expired →
 * a soft "subscribe to unlock Pro" nudge. Hidden for active subscribers.
 */
export default function TrialBanner() {
  const { data } = useSubscription()
  const [dismissed, setDismissed] = useState(() => sessionStorage.getItem(DISMISS_KEY) === '1')

  if (!data) return null
  if (data.status === 'active') return null
  if (data.status === 'canceled' && data.has_pro_access) return null

  if (data.status === 'trialing') {
    if (dismissed) return null
    const n = data.days_left_in_trial ?? 0
    const dismiss = () => {
      sessionStorage.setItem(DISMISS_KEY, '1')
      setDismissed(true)
    }
    return (
      <div className="flex items-center justify-center gap-3 px-4 py-2 text-sm bg-gold-soft/60 border-b border-gold/40 text-charcoal flex-shrink-0">
        <Sparkles size={15} className="text-gold shrink-0" />
        <span className="text-center">
          <span className="font-semibold">
            {n} {n === 1 ? 'day' : 'days'} left
          </span>{' '}
          in your free trial — keep Pro features after it ends.
        </span>
        <Link to="/s/settings" className="font-semibold text-cobalt hover:underline shrink-0">
          Subscribe
        </Link>
        <button
          onClick={dismiss}
          aria-label="Dismiss trial reminder"
          className="ml-1 text-muted-foreground hover:text-foreground shrink-0"
        >
          <X size={14} />
        </button>
      </div>
    )
  }

  // expired (or canceled with access lapsed) → soft paywall nudge
  return (
    <div className="flex items-center justify-center gap-3 px-4 py-2 text-sm bg-warning-soft border-b border-warning/30 text-warning flex-shrink-0">
      <span className="text-center">Your free trial has ended — you&apos;re on the free plan.</span>
      <Link to="/s/settings" className="font-semibold underline shrink-0">
        Subscribe to unlock Pro
      </Link>
    </div>
  )
}
