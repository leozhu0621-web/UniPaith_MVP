import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { CreditCard, Sparkles } from 'lucide-react'
import Button from '../../../components/ui/Button'
import Badge from '../../../components/ui/Badge'
import Toggle from '../../../components/ui/Toggle'
import StripeSubscriptionForm from '../../../components/student/StripeSubscriptionForm'
import SettingsSection from './SettingsSection'
import {
  cancelStudentBilling,
  resumeStudentBilling,
  setAdFree,
  upgradeStudentBilling,
  type StudentBilling,
} from '../../../api/billing'
import { useStudentBilling } from '../../../hooks/useBilling'
import { showToast } from '../../../stores/toast-store'
import { formatDate } from '../../../utils/format'

// Spec 21 §2.7 / 07 §4.1 — student plan state + manage. No gold (utility surface).

export default function BillingCard() {
  const queryClient = useQueryClient()
  const { data: billing, isLoading } = useStudentBilling()
  const [capturing, setCapturing] = useState(false)

  const refresh = (next: StudentBilling) => {
    queryClient.setQueryData(['student-billing'], next)
    queryClient.invalidateQueries({ queryKey: ['student-billing'] })
  }

  const upgradeMut = useMutation({
    mutationFn: (token?: string) => upgradeStudentBilling(token),
    onSuccess: d => {
      refresh(d)
      setCapturing(false)
      showToast('You’re on UniPaith Plus', 'success')
    },
    onError: (e: unknown) => {
      const msg =
        (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail ||
        'Could not update your plan'
      showToast(msg, 'error')
    },
  })
  const adFreeMut = useMutation({
    mutationFn: (enabled: boolean) => setAdFree(enabled),
    onSuccess: refresh,
    onError: () => showToast('Could not update ad-free', 'error'),
  })
  const cancelMut = useMutation({
    mutationFn: cancelStudentBilling,
    onSuccess: d => {
      refresh(d)
      showToast('Plan will cancel at period end', 'success')
    },
    onError: () => showToast('Could not cancel', 'error'),
  })
  const resumeMut = useMutation({
    mutationFn: resumeStudentBilling,
    onSuccess: d => {
      refresh(d)
      showToast('Plan resumed', 'success')
    },
    onError: () => showToast('Could not resume', 'error'),
  })

  const busy = upgradeMut.isPending || cancelMut.isPending || resumeMut.isPending

  return (
    <SettingsSection icon={CreditCard} title="Billing & plan" description="Your UniPaith subscription.">
      {isLoading || !billing ? (
        <div className="h-16 animate-pulse rounded-lg bg-muted" />
      ) : (
        <div className="space-y-4">
          <div className="flex items-start justify-between gap-3">
            <div>
              <div className="flex items-center gap-2">
                <span className="font-semibold text-foreground">UniPaith Plus</span>
                <PlanBadge billing={billing} />
              </div>
              <p className="text-sm text-muted-foreground mt-0.5">{planDescription(billing)}</p>
            </div>
            <div className="text-right shrink-0">
              <div className="text-lg font-bold text-foreground">
                ${billing.monthly_total_usd}
                <span className="text-xs font-normal text-muted-foreground">/mo</span>
              </div>
              {billing.ad_free && <div className="text-xs text-muted-foreground">incl. ad-free</div>}
            </div>
          </div>

          {billing.has_payment_method && (
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <CreditCard size={14} className="text-secondary" />
              {billing.payment_method_brand} •••• {billing.payment_method_last4}
            </div>
          )}

          <div className="flex items-center justify-between rounded-lg border border-border bg-muted/40 px-3 py-2.5">
            <div>
              <p className="text-sm font-medium text-foreground flex items-center gap-1.5">
                <Sparkles size={14} className="text-secondary" /> Ad-free experience
              </p>
              <p className="text-xs text-muted-foreground">
                Remove ads across UniPaith · +${billing.ad_free_addon_usd}/mo
              </p>
            </div>
            <Toggle
              checked={billing.ad_free}
              disabled={adFreeMut.isPending}
              onChange={v => adFreeMut.mutate(v)}
              label="Ad-free"
            />
          </div>

          {billing.invoices.length > 0 && (
            <div className="text-sm text-muted-foreground">
              Next charge:{' '}
              <span className="text-foreground font-medium">${billing.invoices[0].amount_usd}</span> on{' '}
              {formatDate(billing.invoices[0].date)}
            </div>
          )}

          {capturing && isStripe(billing) ? (
            <StripeSubscriptionForm
              publishableKey={billing.publishable_key as string}
              submitLabel={`Subscribe — $${billing.plan_price_usd}/mo`}
              loading={upgradeMut.isPending}
              onToken={token => upgradeMut.mutate(token)}
              onCancel={() => setCapturing(false)}
            />
          ) : (
            <div className="flex flex-wrap items-center gap-2 pt-1">
              {(billing.status === 'trialing' || billing.status === 'expired') && (
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={() => (isStripe(billing) ? setCapturing(true) : upgradeMut.mutate(undefined))}
                  loading={upgradeMut.isPending}
                >
                  {billing.status === 'expired' ? 'Reactivate — $15/mo' : 'Upgrade to Plus — $15/mo'}
                </Button>
              )}
              {billing.status === 'active' && (
                <Button variant="ghost" size="sm" onClick={() => cancelMut.mutate()} loading={cancelMut.isPending} disabled={busy}>
                  Cancel plan
                </Button>
              )}
              {billing.status === 'canceled' && (
                <Button variant="secondary" size="sm" onClick={() => resumeMut.mutate()} loading={resumeMut.isPending} disabled={busy}>
                  Resume plan
                </Button>
              )}
            </div>
          )}
        </div>
      )}
    </SettingsSection>
  )
}

function isStripe(b: StudentBilling): boolean {
  return b.provider === 'stripe' && !!b.publishable_key
}

function PlanBadge({ billing }: { billing: StudentBilling }) {
  if (billing.status === 'trialing') return <Badge variant="info">Free trial · {billing.trial_days_left}d left</Badge>
  if (billing.status === 'active') return <Badge variant="success">Active</Badge>
  if (billing.status === 'canceled') return <Badge variant="warning">Ends soon</Badge>
  return <Badge variant="neutral">Trial ended</Badge>
}

function planDescription(billing: StudentBilling): string {
  switch (billing.status) {
    case 'trialing':
      return `Your free trial ends ${formatDate(billing.trial_ends_at)}. Add a card to keep full access.`
    case 'active':
      return `Renews ${formatDate(billing.current_period_end)}.`
    case 'canceled':
      return `Access continues until ${formatDate(billing.current_period_end)}, then your plan ends.`
    default:
      return 'Your trial has ended. Reactivate to regain full access.'
  }
}
