import { useState } from 'react'
import { Check, CreditCard, Lock } from 'lucide-react'

import Badge from '../ui/Badge'
import Button from '../ui/Button'
import Card from '../ui/Card'
import {
  useCancelSubscription,
  useResumeSubscription,
  useSubscription,
  useToggleAdFree,
} from '../../hooks/useSubscription'
import { formatDate } from '../../utils/format'
import PaywallModal from './PaywallModal'

const PRO_FEATURES = [
  'Expanded matching with full reasoning',
  'Real-time deadline alerts',
  'Scholarship and affordability tools',
  'Structured writing workflows',
  'Priority support',
]

/** Spec 07 (§4/§11) — student plan & billing, embedded in Settings as a Card. */
export default function BillingSection() {
  const { data: sub, isLoading } = useSubscription()
  const cancel = useCancelSubscription()
  const resume = useResumeSubscription()
  const adFree = useToggleAdFree()
  const [payOpen, setPayOpen] = useState(false)

  const hasPro = sub?.has_pro_access ?? false

  return (
    <Card className="p-5" id="billing">
      <h2 className="flex items-center gap-2 font-semibold mb-3 text-charcoal">
        <CreditCard size={16} className="text-cobalt" />
        Plan &amp; billing
      </h2>

      {isLoading || !sub ? (
        <div className="h-20 animate-pulse rounded-md bg-muted" />
      ) : (
        <div className="space-y-4">
          {/* Status line */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              {sub.status === 'active' && <Badge variant="success">UniPaith Pro</Badge>}
              {sub.status === 'trialing' && (
                <Badge variant="info">
                  Free trial · {sub.days_left_in_trial ?? 0}{' '}
                  {sub.days_left_in_trial === 1 ? 'day' : 'days'} left
                </Badge>
              )}
              {sub.status === 'canceled' && <Badge variant="warning">Canceling</Badge>}
              {sub.status === 'expired' && <Badge variant="neutral">Free plan</Badge>}
            </div>
            <span className="text-sm text-slate">
              {sub.status === 'active' && sub.current_period_end && `Renews ${formatDate(sub.current_period_end)}`}
              {sub.status === 'trialing' && sub.trial_ends_at && `Trial ends ${formatDate(sub.trial_ends_at)}`}
              {sub.status === 'canceled' && sub.current_period_end && `Access until ${formatDate(sub.current_period_end)}`}
            </span>
          </div>

          {/* Pro features — unlocked vs locked by entitlement */}
          <ul className="space-y-1.5">
            {PRO_FEATURES.map(f => (
              <li key={f} className="flex items-center gap-2 text-sm text-charcoal">
                {hasPro ? (
                  <Check size={15} className="text-success shrink-0" />
                ) : (
                  <Lock size={14} className="text-muted-foreground shrink-0" />
                )}
                <span className={hasPro ? '' : 'text-muted-foreground'}>{f}</span>
              </li>
            ))}
          </ul>

          {sub.card_last4 && (
            <p className="text-xs text-muted-foreground capitalize">
              {sub.card_brand} ending {sub.card_last4}
            </p>
          )}

          {/* Ad-free add-on */}
          <label className="flex items-center gap-2 text-sm text-charcoal">
            <input
              type="checkbox"
              className="accent-cobalt"
              checked={sub.ad_free}
              disabled={adFree.isPending}
              onChange={e => adFree.mutate(e.target.checked)}
            />
            Ad-free browsing
            <span className="text-muted-foreground">($5/mo)</span>
          </label>

          {/* Actions */}
          <div className="flex flex-wrap items-center gap-2 pt-1">
            {(sub.status === 'trialing' || sub.status === 'expired') && (
              <Button size="sm" onClick={() => setPayOpen(true)}>
                Subscribe · $15/mo
              </Button>
            )}
            {sub.status === 'active' && (
              <Button size="sm" variant="ghost" loading={cancel.isPending} onClick={() => cancel.mutate()}>
                Cancel subscription
              </Button>
            )}
            {sub.status === 'canceled' && (
              <Button size="sm" loading={resume.isPending} onClick={() => resume.mutate()}>
                Resume subscription
              </Button>
            )}
          </div>
        </div>
      )}

      <PaywallModal isOpen={payOpen} onClose={() => setPayOpen(false)} />
    </Card>
  )
}
