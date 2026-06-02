import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { Check, Compass, MessageSquareText, ShieldCheck, Sparkles } from 'lucide-react'

import { upgradeStudentBilling, type StudentBilling } from '../../api/billing'
import { useStudentBilling } from '../../hooks/useBilling'
import { useAuthStore } from '../../stores/auth-store'
import { showToast } from '../../stores/toast-store'
import Button from '../ui/Button'
import Wordmark from '../ui/Wordmark'
import StripeSubscriptionForm from './StripeSubscriptionForm'

// The four brand values (Spec 07 §2 / §6) framed as what UniPaith Plus delivers.
const VALUES = [
  { icon: Compass, title: 'Fit, not fame', body: 'Matching optimizes where you’ll thrive — not where the brand ranks highest.' },
  { icon: MessageSquareText, title: 'Explain everything', body: 'Every score, rank, and recommendation ships with its reasoning.' },
  { icon: ShieldCheck, title: 'Partnership, not extraction', body: 'Your data works for you. Raw student data is never sold.' },
  { icon: Sparkles, title: 'Bias-avoidance is a practice', body: 'Cohorts are audited and decisions are never fully automated.' },
]

/** Hard trial→paywall gate (Spec 05 §9). Only blocks when the trial has lapsed
 * without a card AND the environment enforces the paywall (config flag, default
 * off). Otherwise the soft TrialBanner nudge carries the upsell. */
export default function Paywall() {
  const { data: billing } = useStudentBilling()
  const queryClient = useQueryClient()
  const logout = useAuthStore(s => s.logout)
  const [capturing, setCapturing] = useState(false)

  const upgradeMut = useMutation({
    mutationFn: (token?: string) => upgradeStudentBilling(token),
    onSuccess: (d: StudentBilling) => {
      queryClient.setQueryData(['student-billing'], d)
      setCapturing(false)
      showToast('Welcome to UniPaith Plus', 'success')
    },
    onError: (e: unknown) => {
      const msg =
        (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail ||
        'Could not start your plan'
      showToast(msg, 'error')
    },
  })

  if (!billing || !billing.paywall_enforced || billing.is_premium) return null

  const stripeMode = billing.provider === 'stripe' && !!billing.publishable_key

  return (
    <div className="fixed inset-0 z-[60] flex items-center justify-center p-4" style={{ background: 'rgba(10, 20, 40, 0.6)' }}>
      <div className="bg-card text-foreground w-full max-w-lg rounded-xl elev-raised max-h-[92vh] overflow-y-auto p-6 sm:p-8 animate-scale-in">
        <Wordmark className="h-7 w-auto" />
        <h2 className="text-h2 mt-5 text-charcoal">Your free trial has ended</h2>
        <p className="text-sm text-slate mt-1">
          Everyone’s private college counselor. Continue for{' '}
          <span className="font-semibold text-charcoal">${billing.plan_price_usd}/mo</span>.
        </p>

        <ul className="mt-5 space-y-3">
          {VALUES.map(v => (
            <li key={v.title} className="flex gap-3">
              <span className="mt-0.5 h-7 w-7 shrink-0 rounded-lg bg-cobalt/10 flex items-center justify-center">
                <v.icon size={15} className="text-cobalt" />
              </span>
              <div>
                <p className="text-sm font-semibold text-charcoal flex items-center gap-1.5">
                  <Check size={13} className="text-success" /> {v.title}
                </p>
                <p className="text-xs text-slate">{v.body}</p>
              </div>
            </li>
          ))}
        </ul>

        <div className="mt-6 space-y-2">
          {capturing && stripeMode ? (
            <StripeSubscriptionForm
              publishableKey={billing.publishable_key as string}
              submitLabel={`Continue with Plus — $${billing.plan_price_usd}/mo`}
              loading={upgradeMut.isPending}
              onToken={t => upgradeMut.mutate(t)}
              onCancel={() => setCapturing(false)}
            />
          ) : (
            <Button
              className="w-full"
              onClick={() => (stripeMode ? setCapturing(true) : upgradeMut.mutate(undefined))}
              loading={upgradeMut.isPending}
            >
              Continue with Plus — ${billing.plan_price_usd}/mo
            </Button>
          )}
          <button onClick={logout} className="ui-btn w-full text-center text-sm text-slate hover:text-charcoal py-1.5">
            Sign out
          </button>
        </div>
      </div>
    </div>
  )
}
