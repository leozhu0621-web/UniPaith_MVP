import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Sparkles, X, Clock } from 'lucide-react'

import { useStudentBilling } from '../../hooks/useBilling'

/** Slim trial / plan banner under the top nav (Spec 05 §9, 07 §4.1).
 * Trialing → days-left + upgrade nudge; canceled → resume; expired → reactivate.
 * Paying (active) students see nothing. Dismissible for the session. */
export default function TrialBanner() {
  const { data: billing } = useStudentBilling()
  const navigate = useNavigate()
  const [dismissed, setDismissed] = useState(false)

  if (!billing || dismissed) return null
  if (billing.status === 'active') return null

  const goManage = () => navigate('/s/settings')

  let tone = 'bg-muted text-foreground border-border/60'
  let icon = <Sparkles size={15} className="text-secondary shrink-0" />
  let message: string
  let cta = 'Upgrade — $15/mo'

  if (billing.status === 'trialing') {
    const days = billing.trial_days_left ?? 0
    const urgent = days <= 2
    if (urgent) {
      tone = 'bg-warning-soft text-foreground border-warning/40'
      icon = <Clock size={15} className="text-warning shrink-0" />
    }
    message =
      days <= 0
        ? 'Your free trial ends today.'
        : `${days} day${days === 1 ? '' : 's'} left in your free trial.`
  } else if (billing.status === 'canceled') {
    tone = 'bg-warning-soft text-foreground border-warning/40'
    message = 'Your plan is set to cancel.'
    cta = 'Resume plan'
  } else {
    tone = 'bg-error-soft text-foreground border-error/40'
    message = 'Your free trial has ended. Reactivate to keep full access.'
    cta = 'Reactivate — $15/mo'
  }

  return (
    <div className={`flex items-center gap-2 px-4 sm:px-8 py-2 border-b text-sm ${tone}`}>
      {icon}
      <span className="flex-1 min-w-0 truncate">
        {message}{' '}
        <span className="hidden sm:inline text-muted-foreground">Everyone’s private college counselor — for $15/mo.</span>
      </span>
      <button
        onClick={goManage}
        className="ui-btn shrink-0 inline-flex items-center h-7 px-3 rounded-lg bg-primary text-on-primary text-xs font-semibold hover:brightness-95 transition"
      >
        {cta}
      </button>
      <button
        onClick={() => setDismissed(true)}
        aria-label="Dismiss"
        className="ui-btn shrink-0 p-1 rounded-md text-muted-foreground hover:bg-black/5 transition"
      >
        <X size={14} />
      </button>
    </div>
  )
}
