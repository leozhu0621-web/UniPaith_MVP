import { useState } from 'react'
import { Link } from 'react-router-dom'
import { Clock, Sparkles, X } from 'lucide-react'
import { useBilling } from '../../hooks/useBilling'

// Slim status bar under the top nav (Spec 06 §4.1 trial → paywall). Cobalt-tinted
// during the trial (informational, dismissible per session); warning-tinted once
// the trial lapses (persistent — it's the paywall nudge). Hidden for paying
// subscribers and whenever billing is disabled. Gold stays "earned" — it appears
// only on the CTA button, never as a fill.
export default function TrialBanner() {
  const { data } = useBilling()
  const [dismissed, setDismissed] = useState(
    () => sessionStorage.getItem('trial-banner-dismissed') === '1',
  )

  if (!data || !data.enabled || data.plan === 'plus') return null

  const dismiss = () => {
    sessionStorage.setItem('trial-banner-dismissed', '1')
    setDismissed(true)
  }

  if (data.plan === 'trial') {
    if (dismissed) return null
    const days = data.trial_days_left ?? 0
    const dayLabel = days === 1 ? '1 day' : `${days} days`
    return (
      <div className="flex items-center gap-2 px-4 lg:px-8 h-9 bg-secondary/8 border-b border-border text-xs">
        <Clock size={14} className="text-cobalt flex-shrink-0" />
        <span className="text-charcoal truncate">
          {days > 0 ? `${dayLabel} left in your free trial.` : 'Your free trial ends today.'}
        </span>
        <Link
          to="/s/billing"
          className="text-cobalt font-semibold hover:underline whitespace-nowrap ml-auto"
        >
          Manage plan
        </Link>
        <button
          onClick={dismiss}
          aria-label="Dismiss"
          className="ui-btn p-1 rounded hover:bg-muted text-muted-foreground flex-shrink-0"
        >
          <X size={13} />
        </button>
      </div>
    )
  }

  // plan === 'free' — trial lapsed. Persistent paywall nudge.
  return (
    <div className="flex items-center gap-2 px-4 lg:px-8 h-9 bg-warning-soft border-b border-warning/30 text-xs">
      <Sparkles size={14} className="text-warning flex-shrink-0" />
      <span className="text-charcoal truncate">
        Your free trial has ended. Subscribe to keep full access.
      </span>
      <Link
        to="/s/billing"
        className="ml-auto inline-flex items-center px-2.5 h-6 rounded-md bg-primary text-on-primary font-semibold whitespace-nowrap hover:brightness-95 transition"
      >
        Subscribe
      </Link>
    </div>
  )
}
