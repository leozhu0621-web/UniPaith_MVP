import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { CreditCard, Check, Minus, Sparkles, ShieldCheck, Receipt } from 'lucide-react'
import {
  addPaymentMethod,
  cancelSubscription,
  getBillingHistory,
  setAdFree,
  subscribe,
} from '../../api/billing'
import { useBilling } from '../../hooks/useBilling'
import {
  EVENT_LABELS,
  FEATURE_LABELS,
  formatCents,
  type BillingEvent,
  type BillingStatus,
  type Feature,
} from '../../types/billing'
import Card from '../../components/ui/Card'
import Button from '../../components/ui/Button'
import Badge from '../../components/ui/Badge'
import { showToast } from '../../stores/toast-store'
import { formatDate } from '../../utils/format'

const ROW_ORDER: Feature[] = [
  'profile',
  'limited_match',
  'expanded_match',
  'deadline_alerts',
  'scholarship_tools',
  'workshops',
]

export default function BillingPage() {
  const qc = useQueryClient()
  const { data, isLoading } = useBilling()
  const { data: history } = useQuery({ queryKey: ['billing-history'], queryFn: getBillingHistory })

  const invalidate = () => {
    qc.invalidateQueries({ queryKey: ['billing'] })
    qc.invalidateQueries({ queryKey: ['billing-history'] })
  }

  if (isLoading) {
    return <div className="p-6 max-w-2xl mx-auto text-sm text-slate">Loading your plan…</div>
  }

  if (data && !data.enabled) {
    return (
      <div className="p-6 max-w-2xl mx-auto">
        <Header />
        <Card className="p-5 mt-6">
          <p className="text-sm text-slate">
            Billing is not enabled in this environment — you have full access to every feature.
          </p>
        </Card>
      </div>
    )
  }

  if (!data) return null

  return (
    <div className="p-6 max-w-2xl mx-auto space-y-6">
      <Header />
      {data.mock && (
        <p className="text-xs text-muted-foreground -mt-3">
          Demo billing — no card is charged. Use any card number (try 4242 4242 4242 4242).
        </p>
      )}

      <PlanCard data={data} onChange={invalidate} />
      <PaymentCard data={data} onChange={invalidate} />
      {data.plan === 'plus' && <PlusManagement data={data} onChange={invalidate} />}
      <IncludedCard data={data} />
      <HistoryCard history={history ?? []} />
    </div>
  )
}

function Header() {
  return (
    <div>
      <p className="text-eyebrow uppercase tracking-[0.22em] text-cobalt font-semibold">
        Plan &amp; billing
      </p>
      <h1 className="text-2xl font-bold text-charcoal mt-1">Your plan</h1>
    </div>
  )
}

function PlanBadge({ plan }: { plan: BillingStatus['plan'] }) {
  if (plan === 'plus') return <Badge variant="success">UniPaith Plus</Badge>
  if (plan === 'trial') return <Badge variant="info">Free trial</Badge>
  return <Badge variant="neutral">Free</Badge>
}

function PlanCard({ data, onChange }: { data: BillingStatus; onChange: () => void }) {
  const subscribeMut = useMutation({
    mutationFn: subscribe,
    onSuccess: () => {
      showToast('Welcome to UniPaith Plus', 'success')
      onChange()
    },
    onError: (e: Error) => showToast(e.message || 'Could not subscribe', 'error'),
  })

  const price = formatCents(data.prices.student_plan_cents)
  return (
    <Card className="p-5">
      <div className="flex items-start justify-between gap-3">
        <div>
          <div className="flex items-center gap-2">
            <PlanBadge plan={data.plan} />
            {data.cancel_at_period_end && <Badge variant="warning">Ends soon</Badge>}
          </div>
          <p className="text-sm text-slate mt-2">
            {data.plan === 'trial' && (
              <>
                {data.trial_days_left ?? 0} day{(data.trial_days_left ?? 0) === 1 ? '' : 's'} left.
                Add a card to keep full access when your trial ends.
              </>
            )}
            {data.plan === 'free' && <>Your trial has ended. Subscribe to unlock everything.</>}
            {data.plan === 'plus' && !data.cancel_at_period_end && (
              <>Renews {formatDate(data.current_period_end)} · {price}/month</>
            )}
            {data.plan === 'plus' && data.cancel_at_period_end && (
              <>Access continues until {formatDate(data.current_period_end)}.</>
            )}
          </p>
        </div>
        {data.plan !== 'plus' && (
          <div className="text-right flex-shrink-0">
            <div className="text-2xl font-bold text-charcoal leading-none">{price}</div>
            <div className="text-xs text-muted-foreground">per month</div>
          </div>
        )}
      </div>

      {data.plan !== 'plus' && (
        <div className="mt-4">
          <Button
            variant="primary"
            onClick={() => subscribeMut.mutate()}
            loading={subscribeMut.isPending}
            disabled={!data.has_payment_method}
          >
            <Sparkles size={15} className="mr-1.5" /> Subscribe to Plus
          </Button>
          {!data.has_payment_method && (
            <p className="text-xs text-muted-foreground mt-2">Add a payment method below first.</p>
          )}
        </div>
      )}
    </Card>
  )
}

function PaymentCard({ data, onChange }: { data: BillingStatus; onChange: () => void }) {
  const [editing, setEditing] = useState(!data.has_payment_method)
  const [number, setNumber] = useState('')
  const [exp, setExp] = useState('')
  const [cvc, setCvc] = useState('')

  const addMut = useMutation({
    mutationFn: addPaymentMethod,
    onSuccess: () => {
      showToast('Card saved', 'success')
      setEditing(false)
      setNumber('')
      setExp('')
      setCvc('')
      onChange()
    },
    onError: (e: Error) => showToast(e.message || 'Could not save card', 'error'),
  })

  const save = () => {
    const [mm, yy] = exp.split('/').map(s => s.trim())
    const month = Number(mm)
    let year = Number(yy)
    if (year > 0 && year < 100) year += 2000
    addMut.mutate({
      number: number.replace(/\s/g, ''),
      exp_month: month || undefined,
      exp_year: year || undefined,
      cvc: cvc || undefined,
    })
  }

  const pm = data.payment_method
  return (
    <Card className="p-5">
      <h2 className="flex items-center gap-2 font-semibold mb-3 text-charcoal">
        <CreditCard size={16} className="text-cobalt" /> Payment method
      </h2>

      {!editing && pm ? (
        <div className="flex items-center justify-between">
          <span className="text-sm text-charcoal capitalize">
            {pm.brand} ···· {pm.last4}
            {pm.exp_month && (
              <span className="text-muted-foreground ml-2">
                exp {String(pm.exp_month).padStart(2, '0')}/{String(pm.exp_year).slice(-2)}
              </span>
            )}
          </span>
          <Button variant="ghost" size="sm" onClick={() => setEditing(true)}>
            Replace
          </Button>
        </div>
      ) : (
        <div className="space-y-3">
          <input
            inputMode="numeric"
            placeholder="Card number"
            value={number}
            onChange={e => setNumber(e.target.value)}
            className="w-full h-10 px-3 rounded-lg border border-border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring/40"
          />
          <div className="flex gap-3">
            <input
              placeholder="MM / YY"
              value={exp}
              onChange={e => setExp(e.target.value)}
              className="flex-1 h-10 px-3 rounded-lg border border-border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring/40"
            />
            <input
              inputMode="numeric"
              placeholder="CVC"
              value={cvc}
              onChange={e => setCvc(e.target.value)}
              className="w-24 h-10 px-3 rounded-lg border border-border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring/40"
            />
          </div>
          <div className="flex items-center gap-2">
            <Button
              variant="secondary"
              size="sm"
              onClick={save}
              loading={addMut.isPending}
              disabled={number.replace(/\s/g, '').length < 12}
            >
              Save card
            </Button>
            {data.has_payment_method && (
              <Button variant="ghost" size="sm" onClick={() => setEditing(false)}>
                Cancel
              </Button>
            )}
          </div>
          <p className="text-xs text-muted-foreground flex items-center gap-1.5">
            <ShieldCheck size={13} /> Card details are tokenized — we never store the full number.
          </p>
        </div>
      )}
    </Card>
  )
}

function PlusManagement({ data, onChange }: { data: BillingStatus; onChange: () => void }) {
  const adFreeMut = useMutation({
    mutationFn: (enabled: boolean) => setAdFree(enabled),
    onSuccess: () => onChange(),
    onError: (e: Error) => showToast(e.message || 'Could not update', 'error'),
  })
  const cancelMut = useMutation({
    mutationFn: cancelSubscription,
    onSuccess: () => {
      showToast('Subscription will end at the period close', 'success')
      onChange()
    },
    onError: (e: Error) => showToast(e.message || 'Could not cancel', 'error'),
  })

  const adfreePrice = formatCents(data.prices.student_adfree_cents)
  return (
    <Card className="p-5 space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-charcoal">Ad-free upgrade</p>
          <p className="text-xs text-muted-foreground">
            Remove ads across the app · {adfreePrice}/month
          </p>
        </div>
        <button
          role="switch"
          aria-checked={data.ad_free}
          aria-label="Toggle ad-free upgrade"
          onClick={() => adFreeMut.mutate(!data.ad_free)}
          disabled={adFreeMut.isPending}
          className={`relative w-11 h-6 rounded-full transition-colors flex-shrink-0 ${
            data.ad_free ? 'bg-cobalt' : 'bg-muted'
          }`}
        >
          <span
            className={`absolute top-0.5 left-0.5 w-5 h-5 rounded-full bg-card shadow transition-transform ${
              data.ad_free ? 'translate-x-5' : ''
            }`}
          />
        </button>
      </div>

      {!data.cancel_at_period_end && (
        <div className="pt-2 border-t border-border">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => {
              if (confirm('Cancel your subscription at the end of the current period?')) {
                cancelMut.mutate()
              }
            }}
            loading={cancelMut.isPending}
            className="text-error hover:bg-error-soft"
          >
            Cancel subscription
          </Button>
        </div>
      )}
    </Card>
  )
}

function IncludedCard({ data }: { data: BillingStatus }) {
  const matrix = data.feature_matrix
  return (
    <Card className="p-5">
      <h2 className="font-semibold mb-1 text-charcoal">What's included</h2>
      <p className="text-xs text-muted-foreground mb-3">
        Every plan keeps your portable profile. Plus unlocks the rest.
      </p>
      <div className="rounded-lg border border-border overflow-hidden">
        <div className="grid grid-cols-[1fr_auto_auto] text-xs font-semibold text-muted-foreground bg-muted/50 px-4 py-2">
          <span>Feature</span>
          <span className="w-12 text-center">Free</span>
          <span className="w-12 text-center text-cobalt">Plus</span>
        </div>
        {ROW_ORDER.map(f => (
          <div
            key={f}
            className="grid grid-cols-[1fr_auto_auto] items-center px-4 py-2.5 text-sm border-t border-border"
          >
            <span className="text-charcoal">{FEATURE_LABELS[f]}</span>
            <span className="w-12 flex justify-center">
              {matrix?.free?.[f] ? (
                <Check size={16} className="text-success" />
              ) : (
                <Minus size={16} className="text-muted-foreground/50" />
              )}
            </span>
            <span className="w-12 flex justify-center">
              {matrix?.plus?.[f] ? (
                <Check size={16} className="text-cobalt" />
              ) : (
                <Minus size={16} className="text-muted-foreground/50" />
              )}
            </span>
          </div>
        ))}
      </div>
    </Card>
  )
}

function HistoryCard({ history }: { history: BillingEvent[] }) {
  if (!history.length) return null
  return (
    <Card className="p-5">
      <h2 className="flex items-center gap-2 font-semibold mb-3 text-charcoal">
        <Receipt size={16} className="text-cobalt" /> Billing history
      </h2>
      <ul className="divide-y divide-border">
        {history.map(e => (
          <li key={e.id} className="flex items-center justify-between py-2.5 text-sm">
            <div>
              <p className="text-charcoal">{EVENT_LABELS[e.event_type] ?? e.event_type}</p>
              <p className="text-xs text-muted-foreground">{formatDate(e.occurred_at)}</p>
            </div>
            {e.amount_cents > 0 && (
              <span className="text-charcoal font-medium">{formatCents(e.amount_cents, e.currency)}</span>
            )}
          </li>
        ))}
      </ul>
    </Card>
  )
}
