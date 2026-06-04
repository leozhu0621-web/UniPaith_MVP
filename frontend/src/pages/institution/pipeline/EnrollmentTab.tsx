import { useState } from 'react'
import QueryError from '../../../components/ui/QueryError'
import { useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  CheckCircle2,
  Circle,
  AlertTriangle,
  Wallet,
  GraduationCap,
  CalendarClock,
  Clock,
  Send,
} from 'lucide-react'
import {
  getApplicantEnrollment,
  recordDeposit,
  markEnrollmentConfirmed,
  approveDeferral,
} from '../../../api/enrollment'
import Card from '../../../components/ui/Card'
import Badge from '../../../components/ui/Badge'
import Button from '../../../components/ui/Button'
import Input from '../../../components/ui/Input'
import Select from '../../../components/ui/Select'
import Skeleton from '../../../components/ui/Skeleton'
import { showToast } from '../../../stores/toast-store'
import { formatDate } from '../../../utils/format'
import type { DepositStatus, Enrollment } from '../../../types'

const STATE_META: Record<string, { label: string; tone: 'success' | 'info' | 'warning' | 'neutral' | 'danger' }> = {
  accepted: { label: 'Offer accepted', tone: 'info' },
  intent_confirmed: { label: 'Intent confirmed', tone: 'success' },
  deposit_recorded: { label: 'Deposit recorded', tone: 'success' },
  enrollment_confirmed: { label: 'Enrollment confirmed', tone: 'success' },
  enrolled: { label: 'Enrolled', tone: 'success' },
  withdrew: { label: 'Withdrew after accepting', tone: 'danger' },
  deferred: { label: 'Deferred', tone: 'neutral' },
}

const DEPOSIT_OPTIONS: { value: DepositStatus; label: string }[] = [
  { value: 'none', label: 'Not recorded' },
  { value: 'pending', label: 'Pending' },
  { value: 'paid', label: 'Paid' },
  { value: 'waived', label: 'Waived' },
]

export default function EnrollmentTab({ applicationId }: { applicationId: string }) {
  const queryClient = useQueryClient()
  const navigate = useNavigate()
  const { data: enr, isLoading, isError, refetch } = useQuery({
    queryKey: ['applicant-enrollment', applicationId],
    queryFn: () => getApplicantEnrollment(applicationId),
  })
  const [depositStatus, setDepositStatus] = useState<DepositStatus>('paid')
  const [depositAmount, setDepositAmount] = useState('')

  const invalidate = () =>
    queryClient.invalidateQueries({ queryKey: ['applicant-enrollment', applicationId] })

  const depositMut = useMutation({
    mutationFn: () =>
      recordDeposit(applicationId, depositStatus, depositAmount ? Number(depositAmount) : null),
    onSuccess: () => {
      invalidate()
      showToast('Deposit status recorded', 'success')
    },
    onError: () => showToast('Could not record deposit', 'error'),
  })
  const confirmMut = useMutation({
    mutationFn: (final: boolean) => markEnrollmentConfirmed(applicationId, final),
    onSuccess: (_d, final) => {
      invalidate()
      showToast(final ? 'Marked as enrolled' : 'Enrollment confirmed', 'success')
    },
    onError: () => showToast('Could not update enrollment', 'error'),
  })
  const deferralMut = useMutation({
    mutationFn: (approved: boolean) => approveDeferral(applicationId, approved),
    onSuccess: (_d, approved) => {
      invalidate()
      showToast(approved ? 'Deferral approved' : 'Deferral declined', 'success')
    },
    onError: () => showToast('Could not update the deferral', 'error'),
  })

  if (isLoading) return <Skeleton className="h-64" />
  if (isError)
    return (
      <QueryError detail="Couldn’t load enrollment." onRetry={() => refetch()} />
    )
  if (!enr) return null
  const e = enr as Enrollment

  if (!e.available) {
    return (
      <Card className="p-6">
        <p className="text-sm font-medium text-foreground mb-1">Enrollment hasn't started</p>
        <p className="text-sm text-muted-foreground">
          The enrollment window opens once {e.student_name || 'the applicant'} accepts their offer.
          {e.decision ? ` Current decision: ${e.decision}.` : ''}
        </p>
      </Card>
    )
  }

  const state = e.state || 'accepted'
  const meta = STATE_META[state] || STATE_META.accepted
  const deferralPending = !!e.deferral?.requested && !e.deferral?.approved
  const checklist = e.checklist || []
  const done = checklist.filter(c => c.status === 'complete' || c.status === 'waived').length
  const enrolled = state === 'enrolled'
  const withdrew = state === 'withdrew'

  return (
    <div className="space-y-4">
      {/* State + deposit summary */}
      <Card className="p-5">
        <div className="flex items-center justify-between flex-wrap gap-2">
          <div className="flex items-center gap-2">
            <GraduationCap size={18} className="text-secondary" />
            <span className="font-semibold text-foreground">{e.student_name || 'Applicant'}</span>
            <Badge variant={meta.tone}>{meta.label}</Badge>
            {deferralPending && <Badge variant="warning">Deferral pending</Badge>}
            {e.deferral?.approved && <Badge variant="neutral">Deferred</Badge>}
          </div>
          <span className="text-xs text-muted-foreground">
            Checklist {done}/{checklist.length}
          </span>
        </div>
        {e.start_term && (
          <p className="text-xs text-muted-foreground mt-2">
            <CalendarClock size={12} className="inline -mt-0.5 mr-1" />
            Start term: {e.start_term}
          </p>
        )}
      </Card>

      {/* Deposit (status-only — no money moves, §3.1) */}
      <Card className="p-5">
        <div className="flex items-center gap-2 mb-2">
          <Wallet size={16} className="text-muted-foreground" />
          <p className="text-sm font-medium text-foreground">Enrollment deposit</p>
          <Badge variant={e.deposit_status === 'paid' || e.deposit_status === 'waived' ? 'success' : 'neutral'}>
            {e.deposit_status}
          </Badge>
        </div>
        <p className="text-xs text-muted-foreground mb-3">
          Status only — no payment is processed here (Spec 39 owns collection).
        </p>
        {!withdrew && (
          <div className="flex items-end gap-2 flex-wrap">
            <Select
              label="Deposit status"
              value={depositStatus}
              onChange={ev => setDepositStatus(ev.target.value as DepositStatus)}
              options={DEPOSIT_OPTIONS}
            />
            <Input
              label="Amount (optional)"
              type="number"
              min={0}
              value={depositAmount}
              onChange={ev => setDepositAmount(ev.target.value)}
              placeholder="e.g. 500"
            />
            <Button variant="secondary" size="sm" loading={depositMut.isPending} onClick={() => depositMut.mutate()}>
              Record deposit
            </Button>
          </div>
        )}
      </Card>

      {/* Checklist completion (read-only mirror of the student's) */}
      <Card className="p-5">
        <p className="text-eyebrow font-semibold uppercase tracking-[0.22em] text-muted-foreground mb-2">
          Pre-arrival checklist
        </p>
        <div className="divide-y divide-border">
          {checklist.map(item => (
            <div key={item.key} className="flex items-center gap-2 py-2 text-sm">
              {item.status === 'complete' || item.status === 'waived' ? (
                <CheckCircle2 size={15} className="text-success shrink-0" />
              ) : item.status === 'overdue' ? (
                <AlertTriangle size={15} className="text-error shrink-0" />
              ) : (
                <Circle size={15} className="text-muted-foreground/50 shrink-0" />
              )}
              <span className={item.status === 'complete' ? 'text-muted-foreground' : 'text-foreground'}>
                {item.item}
              </span>
              {item.status === 'overdue' && <Badge variant="error">Overdue</Badge>}
            </div>
          ))}
          {!checklist.length && <p className="text-sm text-muted-foreground py-2">No checklist items.</p>}
        </div>
      </Card>

      {/* Staff actions */}
      {!withdrew && (
        <Card className="p-5">
          <p className="text-sm font-medium text-foreground mb-3">Actions</p>
          <div className="flex flex-wrap items-center gap-2">
            {!enrolled && (
              <Button
                variant="secondary"
                size="sm"
                loading={confirmMut.isPending && confirmMut.variables === false}
                onClick={() => confirmMut.mutate(false)}
              >
                <CheckCircle2 size={15} className="mr-1" /> Mark enrollment confirmed
              </Button>
            )}
            {!enrolled && (
              <Button
                variant="tertiary"
                size="sm"
                loading={confirmMut.isPending && confirmMut.variables === true}
                onClick={() => confirmMut.mutate(true)}
              >
                Mark as enrolled
              </Button>
            )}
            {deferralPending && (
              <>
                <Button variant="secondary" size="sm" loading={deferralMut.isPending} onClick={() => deferralMut.mutate(true)}>
                  Approve deferral
                </Button>
                <Button variant="ghost" size="sm" onClick={() => deferralMut.mutate(false)}>
                  Decline deferral
                </Button>
              </>
            )}
            {/* Reason-coded nudge (§3.1) — routes to the Spec 29 inbox where the
                InstitutionReplyDrafter composes the reminder. */}
            <Button
              variant="ghost"
              size="sm"
              onClick={() => navigate('/i/communications?tab=inbox')}
            >
              <Send size={14} className="mr-1" /> Send nudge
            </Button>
          </div>
          <p className="text-xs text-muted-foreground mt-2">
            Send a confirmation reminder from the inbox (reason-coded, AI-draftable).
          </p>
          {deferralPending && e.deferral?.to_term && (
            <p className="text-xs text-muted-foreground mt-2">
              Requested term: {e.deferral.to_term.season} {e.deferral.to_term.year}
            </p>
          )}
        </Card>
      )}

      {/* Timeline */}
      {(e.timeline?.length ?? 0) > 0 && (
        <Card className="p-5">
          <p className="text-eyebrow font-semibold uppercase tracking-[0.22em] text-muted-foreground mb-2">
            Timeline
          </p>
          <ul className="space-y-2">
            {e.timeline!.map((ev, i) => (
              <li key={i} className="flex items-center gap-2 text-sm">
                <Clock size={13} className="text-muted-foreground shrink-0" />
                <span className="text-foreground">{ev.label}</span>
                {ev.at && <span className="text-xs text-muted-foreground">· {formatDate(ev.at)}</span>}
              </li>
            ))}
          </ul>
        </Card>
      )}
    </div>
  )
}
