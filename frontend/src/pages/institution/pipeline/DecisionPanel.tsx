import { useMemo, useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Award, Brain, CalendarClock, CheckCircle2, Clock, XCircle } from 'lucide-react'
import {
  releaseDecision,
  getOfferStatus,
  extendOfferDeadline,
  rescindOffer,
} from '../../../api/applications-admin'
import { generateAIDraft } from '../../../api/institutions'
import Card from '../../../components/ui/Card'
import Badge from '../../../components/ui/Badge'
import Button from '../../../components/ui/Button'
import Input from '../../../components/ui/Input'
import Select from '../../../components/ui/Select'
import Textarea from '../../../components/ui/Textarea'
import Skeleton from '../../../components/ui/Skeleton'
import { showToast } from '../../../stores/toast-store'
import { formatDate } from '../../../utils/format'
import type { Application, InstitutionDecision, OfferType } from '../../../types'

// Decision vocabulary (spec 34 §2). Color-coded but restrained — no celebratory
// gold on the institution side; the student sees the celebration (§10).
const DECISIONS: { value: InstitutionDecision; label: string; tone: 'success' | 'info' | 'danger' | 'warning' | 'neutral' }[] = [
  { value: 'admitted', label: 'Admit', tone: 'success' },
  { value: 'conditional_admission', label: 'Conditional admit', tone: 'info' },
  { value: 'waitlisted', label: 'Waitlist', tone: 'warning' },
  { value: 'deferred', label: 'Defer', tone: 'neutral' },
  { value: 'rejected', label: 'Reject', tone: 'danger' },
]

const OFFER_TYPES: { value: OfferType; label: string }[] = [
  { value: 'full_admission', label: 'Full admission' },
  { value: 'partial', label: 'Partial' },
  { value: 'transfer_credit_offer', label: 'Transfer credit' },
  { value: 'waitlist_to_admit', label: 'Waitlist → admit' },
]

const RESPONSE_STATE_META: Record<string, { label: string; tone: 'success' | 'danger' | 'warning' | 'neutral' }> = {
  accepted: { label: 'Accepted', tone: 'success' },
  declined: { label: 'Declined', tone: 'danger' },
  awaiting_response: { label: 'Awaiting response', tone: 'warning' },
  deadline_passed: { label: 'Deadline passed', tone: 'danger' },
  rescinded: { label: 'Rescinded', tone: 'neutral' },
  no_offer: { label: 'No offer', tone: 'neutral' },
}

const AI_DRAFT_TYPE: Record<InstitutionDecision, string> = {
  admitted: 'decision_admit',
  conditional_admission: 'decision_admit',
  rejected: 'decision_reject',
  waitlisted: 'decision_waitlist',
  deferred: 'decision_waitlist',
}

const num = (s: string): number | null => (s.trim() === '' ? null : Number(s))

export default function DecisionPanel({ applicationId, app }: { applicationId: string; app: Application }) {
  const queryClient = useQueryClient()
  const statusQ = useQuery({
    queryKey: ['offer-status', applicationId],
    queryFn: () => getOfferStatus(applicationId),
  })
  const status = statusQ.data

  const initialDecision = (DECISIONS.find(d => d.value === app.decision)?.value
    ?? (app.decision === 'accepted' ? 'admitted' : 'admitted')) as InstitutionDecision
  const [decision, setDecision] = useState<InstitutionDecision>(initialDecision)
  const [notes, setNotes] = useState('')
  const [offerType, setOfferType] = useState<OfferType>('full_admission')
  const [scholarship, setScholarship] = useState('')
  const [tuitionEst, setTuitionEst] = useState('')
  const [totalCost, setTotalCost] = useState('')
  const [deadline, setDeadline] = useState('')
  const [season, setSeason] = useState('Fall')
  const [year, setYear] = useState('')
  const [conditions, setConditions] = useState('')
  const [message, setMessage] = useState('')
  const [drafting, setDrafting] = useState(false)
  const [extendDate, setExtendDate] = useState('')

  const isOfferDecision = decision === 'admitted' || decision === 'conditional_admission'
  const studentResponded = status?.response_state === 'accepted' || status?.response_state === 'declined'

  const invalidate = () => {
    queryClient.invalidateQueries({ queryKey: ['offer-status', applicationId] })
    queryClient.invalidateQueries({ queryKey: ['application-review', applicationId] })
  }

  const releaseMut = useMutation({
    mutationFn: () =>
      releaseDecision(applicationId, {
        decision,
        decision_notes: notes || null,
        message: message || null,
        offer: isOfferDecision
          ? {
              offer_type: decision === 'conditional_admission' ? 'conditional' : offerType,
              scholarship_amount: num(scholarship),
              tuition_estimate: num(tuitionEst),
              total_cost_estimate: num(totalCost),
              response_deadline: deadline || null,
              start_term: { season, year: num(year) },
              conditions: conditions ? { summary: conditions } : null,
            }
          : null,
      }),
    onSuccess: () => {
      showToast('Decision released — the applicant has been notified', 'success')
      invalidate()
    },
    onError: () => showToast('Failed to release decision', 'error'),
  })

  const extendMut = useMutation({
    mutationFn: () => extendOfferDeadline(status!.offer_id!, extendDate),
    onSuccess: () => {
      showToast('Deadline extended', 'success')
      setExtendDate('')
      invalidate()
    },
    onError: () => showToast('Failed to extend deadline', 'error'),
  })

  const rescindMut = useMutation({
    mutationFn: () => rescindOffer(status!.offer_id!),
    onSuccess: () => {
      showToast('Offer rescinded', 'success')
      invalidate()
    },
    onError: () => showToast('Failed to rescind offer', 'error'),
  })

  const draftNotice = async () => {
    setDrafting(true)
    try {
      const result = await generateAIDraft(applicationId, AI_DRAFT_TYPE[decision])
      setMessage(result.body)
      showToast('AI draft inserted — edit before releasing', 'success')
    } catch {
      showToast('Draft generation failed', 'error')
    } finally {
      setDrafting(false)
    }
  }

  const stateMeta = useMemo(
    () => (status ? RESPONSE_STATE_META[status.response_state] ?? RESPONSE_STATE_META.no_offer : null),
    [status],
  )

  return (
    <div className="space-y-4">
      {/* --- Current decision + offer status (§7/§8) --- */}
      <Card className="p-5 space-y-3">
        <div className="flex items-center justify-between">
          <h3 className="font-semibold text-gray-900">Current decision</h3>
          {app.decision ? (
            <Badge variant={(DECISIONS.find(d => d.value === app.decision)?.tone as any) ?? 'neutral'}>
              {DECISIONS.find(d => d.value === app.decision)?.label ?? app.decision}
            </Badge>
          ) : (
            <Badge variant="neutral">Not released</Badge>
          )}
        </div>

        {statusQ.isLoading ? (
          <Skeleton className="h-16" />
        ) : status && status.has_offer ? (
          <div className="space-y-3">
            <div className="flex flex-wrap items-center gap-x-6 gap-y-2 text-sm">
              <div className="flex items-center gap-2">
                <span className="text-gray-500">Response</span>
                <Badge variant={(stateMeta?.tone as any) ?? 'neutral'}>{stateMeta?.label}</Badge>
              </div>
              {status.response_deadline && (
                <div className="flex items-center gap-1.5 text-gray-600">
                  <CalendarClock size={14} className="text-cobalt" />
                  <span>Respond by {formatDate(status.response_deadline)}</span>
                  {status.days_remaining != null && !studentResponded && (
                    <span className={status.deadline_passed ? 'text-error font-medium' : 'text-gray-400'}>
                      ({status.deadline_passed ? `${Math.abs(status.days_remaining)}d overdue` : `${status.days_remaining}d left`})
                    </span>
                  )}
                </div>
              )}
              {status.response_at && (
                <span className="text-gray-500">Responded {formatDate(status.response_at)}</span>
              )}
            </div>

            {!studentResponded && status.offer_id && (
              <div className="flex flex-wrap items-end gap-2 pt-1 border-t border-gray-100">
                <Input
                  label="Extend deadline"
                  type="date"
                  value={extendDate}
                  onChange={e => setExtendDate(e.target.value)}
                  className="w-44"
                />
                <Button
                  variant="secondary"
                  size="sm"
                  disabled={!extendDate || extendMut.isPending}
                  onClick={() => extendMut.mutate()}
                  className="flex items-center gap-1"
                >
                  <Clock size={14} /> {extendMut.isPending ? 'Extending…' : 'Extend'}
                </Button>
                {status.deadline_passed && (
                  <Button
                    variant="danger"
                    size="sm"
                    disabled={rescindMut.isPending}
                    onClick={() => rescindMut.mutate()}
                    className="flex items-center gap-1"
                  >
                    <XCircle size={14} /> {rescindMut.isPending ? 'Rescinding…' : 'Rescind offer'}
                  </Button>
                )}
              </div>
            )}
          </div>
        ) : (
          <p className="text-sm text-gray-500">
            No offer issued yet. Release an admit or conditional decision below to create one.
          </p>
        )}
      </Card>

      {/* --- Release / re-release (§3) --- */}
      <Card className="p-5 space-y-4">
        <div className="flex items-center gap-2">
          <Award size={18} className="text-cobalt" />
          <h3 className="font-semibold text-gray-900">
            {app.decision ? 'Re-release decision' : 'Release decision'}
          </h3>
        </div>

        {status?.response_state === 'accepted' ? (
          <div className="flex items-center gap-2 rounded-lg bg-success-soft px-3 py-2 text-sm text-success">
            <CheckCircle2 size={16} />
            The applicant has accepted this offer — the decision is locked.
          </div>
        ) : (
          <>
            <div className="grid grid-cols-2 sm:grid-cols-5 gap-2">
              {DECISIONS.map(d => (
                <button
                  key={d.value}
                  type="button"
                  onClick={() => setDecision(d.value)}
                  className={`rounded-lg border px-3 py-2 text-sm font-medium transition-colors ${
                    decision === d.value
                      ? 'border-cobalt bg-cobalt/10 text-cobalt'
                      : 'border-border bg-transparent text-gray-600 hover:bg-muted'
                  }`}
                >
                  {d.label}
                </button>
              ))}
            </div>

            {isOfferDecision && (
              <div className="space-y-3 rounded-lg border border-border p-3">
                <p className="text-xs font-medium text-gray-500">Offer terms</p>
                {decision === 'admitted' && (
                  <Select
                    label="Offer type"
                    options={OFFER_TYPES}
                    value={offerType}
                    onChange={e => setOfferType(e.target.value as OfferType)}
                  />
                )}
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                  <Input label="Scholarship ($)" type="number" value={scholarship} onChange={e => setScholarship(e.target.value)} />
                  <Input label="Tuition estimate ($)" type="number" value={tuitionEst} onChange={e => setTuitionEst(e.target.value)} />
                  <Input label="Total cost estimate ($)" type="number" value={totalCost} onChange={e => setTotalCost(e.target.value)} />
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                  <Input label="Response deadline" type="date" value={deadline} onChange={e => setDeadline(e.target.value)} />
                  <Select
                    label="Start term"
                    options={[{ value: 'Fall', label: 'Fall' }, { value: 'Spring', label: 'Spring' }, { value: 'Summer', label: 'Summer' }, { value: 'Winter', label: 'Winter' }]}
                    value={season}
                    onChange={e => setSeason(e.target.value)}
                  />
                  <Input label="Start year" type="number" placeholder="2027" value={year} onChange={e => setYear(e.target.value)} />
                </div>
                {decision === 'conditional_admission' && (
                  <Textarea
                    label="Conditions"
                    value={conditions}
                    onChange={e => setConditions(e.target.value)}
                    rows={2}
                    placeholder="e.g. Maintain a 3.5 GPA in your final term"
                  />
                )}
              </div>
            )}

            <Textarea label="Internal decision notes (not sent)" value={notes} onChange={e => setNotes(e.target.value)} rows={2} />

            <div>
              <div className="flex items-center justify-between mb-1">
                <label className="text-sm font-medium text-gray-700">Notice to applicant (optional)</label>
                <Button variant="tertiary" size="sm" disabled={drafting} onClick={draftNotice} className="flex items-center gap-1">
                  <Brain size={14} /> {drafting ? 'Drafting…' : 'AI draft'}
                </Button>
              </div>
              <Textarea
                label=""
                value={message}
                onChange={e => setMessage(e.target.value)}
                rows={4}
                placeholder="Leave blank to send the standard notice for this decision."
              />
            </div>

            <div className="flex justify-end">
              <Button
                variant="secondary"
                disabled={releaseMut.isPending}
                onClick={() => releaseMut.mutate()}
                className="flex items-center gap-2"
              >
                <Award size={16} />
                {releaseMut.isPending ? 'Releasing…' : 'Release decision'}
              </Button>
            </div>
          </>
        )}
      </Card>
    </div>
  )
}
