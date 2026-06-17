import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import Card from '../../../../components/ui/Card'
import Button from '../../../../components/ui/Button'
import Badge from '../../../../components/ui/Badge'
import Textarea from '../../../../components/ui/Textarea'
import Select from '../../../../components/ui/Select'
import Stepper from '../../../../components/ui/Stepper'
import Skeleton from '../../../../components/ui/Skeleton'
import QueryError from '../../../../components/ui/QueryError'
import { showToast } from '../../../../stores/toast-store'
import {
  getMyEnrollment,
  confirmEnrollment,
  declineEnrollment,
  requestDeferral,
  toggleEnrollmentChecklistItem,
} from '../../../../api/enrollment'
import {
  getCostTracker,
  payEnrollmentDeposit,
  formatMoney,
  downloadReceipt,
  type CheckoutSession,
} from '../../../../api/payments'
import PaymentCheckout from '../../../../components/student/PaymentCheckout'
import { formatTermDate, daysUntil } from '../offer/offerFormat'
import type {
  Application,
  Enrollment,
  EnrollmentChecklistItem,
  ChecklistItemStatus,
} from '../../../../types'
import {
  CheckCircle2,
  Check,
  Circle,
  Clock,
  AlertTriangle,
  GraduationCap,
  CalendarClock,
  Wallet,
  ArrowRight,
  Receipt,
  Download,
} from 'lucide-react'

const CONFIRMED_STATES = ['intent_confirmed', 'deposit_recorded', 'enrollment_confirmed', 'enrolled']

const STATE_LABEL: Record<string, string> = {
  accepted: 'Offer accepted',
  intent_confirmed: 'Enrollment confirmed',
  deposit_recorded: 'Deposit recorded',
  enrollment_confirmed: 'Confirmed by school',
  enrolled: 'Enrolled',
  withdrew: 'Withdrew',
  deferred: 'Deferred',
}

// §5 state machine (enrollment_service._STATE_ORDER) → a visual journey.
// Off-path branches (withdrew/deferred) aren't on the line; withdrew has its
// own terminal card, deferred maps onto the step it was confirmed at.
const ENROLLMENT_STEPS = [
  { key: 'accepted', label: 'Accepted' },
  { key: 'intent_confirmed', label: 'Confirmed' },
  { key: 'deposit_recorded', label: 'Deposit' },
  { key: 'enrollment_confirmed', label: 'Verified' },
  { key: 'enrolled', label: 'Enrolled' },
] as const

// Map the live state onto a step key the stepper understands.
function stepKeyForState(state: string): string {
  if (state === 'deferred') return 'intent_confirmed'
  return ENROLLMENT_STEPS.some(s => s.key === state) ? state : 'accepted'
}

const DEPOSIT_LABEL: Record<string, string> = {
  none: 'Not yet recorded',
  pending: 'Pending',
  paid: 'Recorded — paid',
  waived: 'Waived',
}

function ChecklistRow({ item, appId }: { item: EnrollmentChecklistItem; appId: string }) {
  const queryClient = useQueryClient()
  // confirm_intent + deposit are state-driven; the rest are self-serve toggles.
  const selfServe = !['confirm_intent', 'deposit'].includes(item.key)
  const toggleMut = useMutation({
    mutationFn: () =>
      toggleEnrollmentChecklistItem(appId, item.key, item.status !== 'complete'),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['enrollment', appId] }),
    onError: () => showToast('Could not update that step', 'error'),
  })

  const icon =
    item.status === 'complete' ? (
      <Check size={16} className="text-success shrink-0" />
    ) : item.status === 'waived' ? (
      <Check size={16} className="text-secondary shrink-0" />
    ) : item.status === 'overdue' ? (
      <AlertTriangle size={16} className="text-error shrink-0" />
    ) : (
      <Circle size={16} className="text-foreground/50 shrink-0" />
    )
  const done = item.status === 'complete' || item.status === 'waived'

  return (
    <div className="flex items-start gap-3 py-2.5">
      {selfServe ? (
        <button
          onClick={() => toggleMut.mutate()}
          disabled={toggleMut.isPending}
          className="mt-0.5"
          aria-label={done ? 'Mark incomplete' : 'Mark complete'}
        >
          {icon}
        </button>
      ) : (
        <span className="mt-0.5">{icon}</span>
      )}
      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-2 flex-wrap">
          <span
            className={`text-sm ${done ? 'text-foreground line-through' : 'text-foreground font-medium'}`}
          >
            {item.item}
          </span>
          {item.status === 'overdue' && <Badge variant="error">Overdue</Badge>}
          {item.status === 'waived' && <Badge variant="neutral">Waived</Badge>}
        </div>
        {item.consequence && !done && (
          <p className="text-xs text-foreground mt-0.5">{item.consequence}</p>
        )}
        {item.due && !done && (
          <p className="text-xs text-foreground/80 mt-0.5">Due {formatTermDate(item.due)}</p>
        )}
      </div>
    </div>
  )
}

function statusOrder(s: ChecklistItemStatus): number {
  return { overdue: 0, pending: 1, complete: 2, waived: 3 }[s] ?? 1
}

export default function EnrollmentPanel({ application }: { application: Application }) {
  const appId = application.id
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [showDecline, setShowDecline] = useState(false)
  const [declineReason, setDeclineReason] = useState('')
  const [showDefer, setShowDefer] = useState(false)
  const [deferSeason, setDeferSeason] = useState('Fall')
  const [deferYear, setDeferYear] = useState(new Date().getFullYear() + 1)

  const [depositCheckout, setDepositCheckout] = useState<CheckoutSession | null>(null)

  const { data: enr, isLoading, isError, refetch } = useQuery({
    queryKey: ['enrollment', appId],
    queryFn: () => getMyEnrollment(appId),
  })
  // Spec 39 §3 — deposit config (amount/currency/payable) lives on the cost tracker.
  const {
    data: cost,
    isError: costIsError,
    refetch: refetchCost,
  } = useQuery({
    queryKey: ['payment', appId],
    queryFn: () => getCostTracker(appId),
    enabled: !!appId,
  })

  const invalidate = () => {
    queryClient.invalidateQueries({ queryKey: ['enrollment', appId] })
    queryClient.invalidateQueries({ queryKey: ['application', appId] })
    queryClient.invalidateQueries({ queryKey: ['payment', appId] })
    queryClient.invalidateQueries({ queryKey: ['my-applications'] })
  }

  const payDepositMut = useMutation({
    mutationFn: () => payEnrollmentDeposit(appId),
    onSuccess: session => setDepositCheckout(session),
    onError: (err: { response?: { data?: { detail?: string } } }) =>
      showToast(err.response?.data?.detail || 'Could not start deposit checkout', 'error'),
  })

  const confirmMut = useMutation({
    mutationFn: () => confirmEnrollment(appId),
    onSuccess: () => {
      invalidate()
      showToast("You're in!", 'success')
    },
    onError: (err: { response?: { data?: { detail?: string } } }) =>
      showToast(err.response?.data?.detail || 'Could not confirm enrollment', 'error'),
  })
  const declineMut = useMutation({
    mutationFn: () => declineEnrollment(appId, declineReason || undefined),
    onSuccess: () => {
      invalidate()
      setShowDecline(false)
      showToast('Your place has been released', 'success')
    },
    onError: () => showToast('Could not decline', 'error'),
  })
  const deferMut = useMutation({
    mutationFn: () => requestDeferral(appId, { season: deferSeason, year: Number(deferYear) }),
    onSuccess: () => {
      invalidate()
      setShowDefer(false)
      showToast('Deferral requested — pending the school’s approval', 'success')
    },
    onError: () => showToast('Could not request a deferral', 'error'),
  })

  if (isLoading) return <Skeleton className="h-64 w-full rounded-xl" />
  // Never blank on error — this panel carries enrollment + deposit (money-adjacent).
  if (isError || !enr) {
    return (
      <Card pad={false} className="p-6">
        <QueryError
          title="We couldn't load your enrollment."
          detail="Your enrollment status didn't load just now."
          onRetry={() => refetch()}
        />
      </Card>
    )
  }

  const e = enr as Enrollment
  if (!e.available) {
    return (
      <Card pad={false} className="p-6 text-center">
        <p className="text-sm text-foreground font-medium mb-1">Accept your offer first</p>
        <p className="text-sm text-foreground max-w-sm mx-auto">
          Your enrollment window opens once you accept an offer. Head to the Offer tab to respond.
        </p>
      </Card>
    )
  }

  const state = e.state || 'accepted'
  const confirmed = CONFIRMED_STATES.includes(state)
  const withdrew = state === 'withdrew'
  const enrolled = state === 'enrolled'
  const deferralPending = !!e.deferral?.requested && !e.deferral?.approved
  const deferralApproved = !!e.deferral?.approved
  const institutionName = e.institution_name || application.program?.institution_name || 'your school'
  const checklist = [...(e.checklist || [])].sort(
    (a, b) => statusOrder(a.status) - statusOrder(b.status),
  )
  const completeCount = checklist.filter(
    c => c.status === 'complete' || c.status === 'waived',
  ).length
  const respDays = daysUntil(e.response_deadline)

  // ── Withdrew terminal state ──
  if (withdrew) {
    return (
      <Card pad={false} className="p-6">
        <Badge variant="neutral">Place released</Badge>
        <h2 className="text-h3 font-bold text-foreground mt-3 mb-1">You declined this place</h2>
        <p className="text-sm text-foreground">
          You let {institutionName} know you won't be enrolling. Your seat has been released.
          {e.decline_reason ? ` Reason: “${e.decline_reason}.”` : ''}
        </p>
      </Card>
    )
  }

  return (
    <div className="space-y-4">
      {/* ── The journey, as a line you can follow (§5 state machine). ── */}
      <Card pad={false} className="p-4 sm:p-5">
        <Stepper steps={ENROLLMENT_STEPS as unknown as { key: string; label: string }[]} currentKey={stepKeyForState(state)} />
      </Card>

      {/* ── The celebratory beat (§2.2 / brand §15): gold glow, earned. ── */}
      {confirmed ? (
        <Card pad={false} variant="card-accent" className="p-6 text-center animate-beat">
          <div className="mx-auto mb-3 w-14 h-14 rounded-full bg-primary/10 flex items-center justify-center">
            {enrolled ? (
              <GraduationCap size={28} className="text-foreground" />
            ) : (
              <CheckCircle2 size={28} className="text-foreground" />
            )}
          </div>
          <h2 className="text-lg font-bold text-foreground mb-1">
            {enrolled ? "You're enrolled!" : "You're in!"}
          </h2>
          <p className="text-sm text-foreground max-w-md mx-auto">
            {enrolled
              ? `${institutionName} has finalized your enrollment.`
              : `You've confirmed your intent to enroll at ${institutionName}. Work through your pre-arrival checklist below.`}
          </p>
          <div className="flex items-center justify-center gap-2 mt-3 flex-wrap">
            <Badge variant="success">{STATE_LABEL[state]}</Badge>
            {deferralApproved && <Badge variant="neutral">Deferred to a later term</Badge>}
          </div>
        </Card>
      ) : (
        // ── Pre-confirm: the confirm CTA (gold, the rare earned accent). ──
        <Card pad={false} className="p-6">
          <p className="text-eyebrow font-semibold uppercase tracking-[0.22em] text-secondary mb-1">
            Enrollment · {institutionName}
          </p>
          <h2 className="text-h3 font-bold text-foreground mb-1">Confirm your enrollment</h2>
          <p className="text-sm text-foreground mb-2">
            You've accepted your offer. Confirm your intent to enroll to lock in your place
            {e.start_term ? ` for ${e.start_term}` : ''}.
          </p>
          {e.response_deadline && (
            <p className="text-sm text-foreground mb-4">
              <CalendarClock size={13} className="inline -mt-0.5 mr-1 text-foreground" />
              Confirm by {formatTermDate(e.response_deadline)}
              {respDays != null && respDays >= 0 && ` · ${respDays} day${respDays !== 1 ? 's' : ''} left`}
            </p>
          )}
          {deferralPending ? (
            <Badge variant="warning">Deferral requested — pending the school’s approval</Badge>
          ) : (
            <div className="flex flex-wrap items-center gap-3">
              {/* Gold — the single biggest celebratory beat is earned here. */}
              <Button variant="primary" loading={confirmMut.isPending} onClick={() => confirmMut.mutate()}>
                Confirm enrollment
              </Button>
              <Button variant="tertiary" onClick={() => setShowDefer(s => !s)}>
                Request a deferral
              </Button>
              <button
                onClick={() => setShowDecline(s => !s)}
                className="text-sm text-foreground hover:text-error ml-auto"
              >
                Decline after accepting
              </button>
            </div>
          )}
        </Card>
      )}

      {/* ── Multi-offer prompt (§2.3) — never auto-declines. ── */}
      {!confirmed && (e.other_active_offers?.length ?? 0) > 0 && (
        <Card pad={false} className="p-4 border-l-4 border-l-secondary">
          <p className="text-sm text-foreground font-medium mb-1">
            You have {e.other_active_offers!.length} other active offer
            {e.other_active_offers!.length !== 1 ? 's' : ''}. Decline them?
          </p>
          <p className="text-xs text-foreground mb-2">
            Confirming here doesn't decline anywhere else — the choice is yours.
          </p>
          <div className="space-y-1.5">
            {e.other_active_offers!.map(o => (
              <button
                key={o.application_id}
                onClick={() => navigate(`/s/applications/${o.application_id}?tab=offer`)}
                className="flex items-center gap-1.5 text-sm text-secondary hover:underline"
              >
                {o.program_name || 'Offer'}
                {o.institution_name ? ` · ${o.institution_name}` : ''}
                <ArrowRight size={13} />
              </button>
            ))}
          </div>
        </Card>
      )}

      {/* ── Decline-after-accept (inline confirm) ── */}
      {showDecline && !confirmed && (
        <Card pad={false} className="p-4">
          <p className="text-sm text-foreground font-medium mb-2">Decline after accepting</p>
          <p className="text-xs text-foreground mb-2">
            This releases your seat at {institutionName}. This can't be undone here.
          </p>
          <Textarea
            label="Reason (optional)"
            value={declineReason}
            onChange={e => setDeclineReason(e.target.value)}
            placeholder="Help the school learn — why are you declining?"
          />
          <div className="flex justify-end gap-2 mt-2">
            <Button variant="ghost" size="sm" onClick={() => setShowDecline(false)}>
              Cancel
            </Button>
            <Button variant="danger" size="sm" loading={declineMut.isPending} onClick={() => declineMut.mutate()}>
              Confirm decline
            </Button>
          </div>
        </Card>
      )}

      {/* ── Deferral request form ── */}
      {showDefer && !confirmed && !deferralPending && (
        <Card pad={false} className="p-4">
          <p className="text-sm text-foreground font-medium mb-2">Request a deferral</p>
          <p className="text-xs text-foreground mb-3">
            Ask {institutionName} to move your start to a later term. Subject to their approval.
          </p>
          <div className="flex gap-2 items-end">
            <Select
              label="Term"
              value={deferSeason}
              onChange={e => setDeferSeason(e.target.value)}
              options={['Fall', 'Spring', 'Summer', 'Winter'].map(s => ({ value: s, label: s }))}
            />
            <Select
              label="Year"
              value={String(deferYear)}
              onChange={e => setDeferYear(Number(e.target.value))}
              options={[0, 1, 2].map(d => {
                const y = new Date().getFullYear() + d
                return { value: String(y), label: String(y) }
              })}
            />
            <Button variant="secondary" size="sm" loading={deferMut.isPending} onClick={() => deferMut.mutate()}>
              Request deferral
            </Button>
          </div>
        </Card>
      )}

      {/* ── Pre-arrival checklist (§2.1) ── */}
      <Card pad={false} className="p-5">
        <div className="flex items-center justify-between mb-1">
          <p className="text-eyebrow font-semibold uppercase tracking-[0.22em] text-foreground">
            Pre-arrival checklist
          </p>
          <span className="text-xs text-foreground">
            {completeCount}/{checklist.length} done
          </span>
        </div>
        <p className="text-xs text-foreground mb-2">
          What's next to get you ready for {e.start_term || 'your start'}.
        </p>
        <div className="divide-y divide-border">
          {checklist.map(item => (
            <ChecklistRow key={item.key} item={item} appId={appId} />
          ))}
        </div>
      </Card>

      {/* ── Enrollment deposit (Spec 39 §3 — real collection; cobalt, never gold) ── */}
      {(() => {
        const deposit = cost?.deposit
        const settled = e.deposit_status === 'paid' || e.deposit_status === 'waived'
        return (
          <Card pad={false} className="p-5">
            <div className="flex items-center gap-2 mb-2">
              <Wallet size={16} className="text-foreground" />
              <p className="text-sm font-medium text-foreground">Enrollment deposit</p>
            </div>
            {settled ? (
              <div className="space-y-2">
                <div className="rounded-lg bg-success-soft px-3 py-2 text-xs text-success flex items-start gap-1.5">
                  <Receipt size={14} className="mt-0.5 shrink-0" />
                  <span>
                    Deposit {e.deposit_status === 'waived' ? 'waived' : 'paid'}
                    {deposit?.paid_at ? ` on ${new Date(deposit.paid_at).toLocaleDateString()}` : ''}. Your spot is confirmed.
                    {deposit?.refunded_amount
                      ? ` Refunded ${formatMoney(deposit.refunded_amount, deposit.currency)}.`
                      : ''}
                  </span>
                </div>
                {deposit?.paid_at && (
                  <button
                    onClick={() =>
                      downloadReceipt({
                        kind: 'enrollment_deposit',
                        amount: deposit.amount,
                        currency: deposit.currency,
                        status: deposit.status,
                        paidAt: deposit.paid_at,
                        refundedAmount: deposit.refunded_amount,
                        programName: e.program_name || application.program?.program_name,
                        institutionName: institutionName,
                        reference: deposit.payment_id,
                      })
                    }
                    className="text-xs text-secondary hover:underline inline-flex items-center gap-1"
                  >
                    <Download size={12} /> Download receipt
                  </button>
                )}
              </div>
            ) : deposit?.required ? (
              <>
                <p className="text-2xl font-bold text-foreground tabular-nums mb-1">
                  {formatMoney(deposit.amount, deposit.currency)}
                </p>
                <p className="text-xs text-foreground mb-3">
                  Pay your enrollment deposit to confirm your spot
                  {deposit.refundable ? '' : ' (non-refundable)'}.
                </p>
                <Button
                  variant="secondary"
                  loading={payDepositMut.isPending}
                  onClick={() => payDepositMut.mutate()}
                >
                  Pay enrollment deposit
                </Button>
              </>
            ) : costIsError ? (
              // The cost tracker carries the payable amount — don't silently hide the deposit.
              <QueryError
                variant="inline"
                detail="Your deposit details didn't load just now."
                onRetry={() => refetchCost()}
              />
            ) : (
              <p className="text-sm text-foreground">
                Status:{' '}
                <span className="font-semibold text-foreground">
                  {DEPOSIT_LABEL[e.deposit_status || 'none']}
                </span>
                {e.deposit_amount ? ` · ${e.deposit_amount.toLocaleString()}` : ''}
              </p>
            )}
          </Card>
        )
      })()}

      {/* ── Still-decidable actions while confirmed (until enrolled) ── */}
      {confirmed && !enrolled && (
        <div className="flex items-center gap-3">
          {deferralPending ? (
            <Badge variant="warning">Deferral requested — pending approval</Badge>
          ) : (
            <button
              onClick={() => setShowDecline(s => !s)}
              className="text-sm text-foreground hover:text-error inline-flex items-center gap-1"
            >
              <Clock size={13} /> Changed your mind? Decline your place
            </button>
          )}
        </div>
      )}
      {confirmed && !enrolled && showDecline && (
        <Card pad={false} className="p-4">
          <p className="text-sm text-foreground font-medium mb-2">Decline after confirming</p>
          <Textarea
            label="Reason (optional)"
            value={declineReason}
            onChange={e => setDeclineReason(e.target.value)}
          />
          <div className="flex justify-end gap-2 mt-2">
            <Button variant="ghost" size="sm" onClick={() => setShowDecline(false)}>
              Cancel
            </Button>
            <Button variant="danger" size="sm" loading={declineMut.isPending} onClick={() => declineMut.mutate()}>
              Confirm decline
            </Button>
          </div>
        </Card>
      )}

      {/* Spec 39 §3 — deposit checkout (calm, cobalt) */}
      <PaymentCheckout
        session={depositCheckout}
        label="Pay enrollment deposit"
        onClose={() => setDepositCheckout(null)}
        onPaid={() => {
          setDepositCheckout(null)
          invalidate()
          showToast('Deposit received — your spot is confirmed.', 'success')
        }}
      />
    </div>
  )
}
