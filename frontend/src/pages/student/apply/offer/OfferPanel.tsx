import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import Card from '../../../../components/ui/Card'
import Button from '../../../../components/ui/Button'
import Badge from '../../../../components/ui/Badge'
import Textarea from '../../../../components/ui/Textarea'
import { showToast } from '../../../../stores/toast-store'
import { respondToOfferV2 } from '../../../../api/offers'
import type { Application, OfferKeyTerm, OfferNextStep } from '../../../../types'
import {
  money,
  daysUntil,
  deadlineTone,
  DEADLINE_TONE_CLASS,
  formatTermDate,
  OFFER_TYPE_LABEL,
} from './offerFormat'
import RecordExternalOfferModal from './RecordExternalOfferModal'
import AcceptOfferModal from './AcceptOfferModal'
import DecisionComparison from './DecisionComparison'
import { Star, ArrowRight, Inbox, Clock } from 'lucide-react'

/** Derive key terms / next steps from the offer when the structured brief is
 * absent (flag off + uncached), so the panel always has content. */
function deriveKeyTerms(app: Application): OfferKeyTerm[] {
  const o = app.offer
  if (!o) return []
  const cur = o.scholarship_currency || 'USD'
  const terms: OfferKeyTerm[] = []
  if (o.scholarship_amount)
    terms.push({ label: 'Scholarship', value: money(o.scholarship_amount, cur) || '' })
  const tuition = o.tuition_amount ?? o.tuition_estimate
  if (tuition) terms.push({ label: 'Tuition estimate', value: `${money(tuition, cur)}/yr` })
  const total = o.total_cost_estimate ?? o.financial_package_total
  if (total) terms.push({ label: 'Total cost estimate', value: money(total, cur) || '' })
  if (o.start_term_season && o.start_term_year)
    terms.push({ label: 'Start term', value: `${o.start_term_season} ${o.start_term_year}` })
  return terms
}

export default function OfferPanel({ application }: { application: Application }) {
  const queryClient = useQueryClient()
  const offer = application.offer
  const [showDecline, setShowDecline] = useState(false)
  const [declineReason, setDeclineReason] = useState('')
  const [showAccept, setShowAccept] = useState(false)
  const [showCompare, setShowCompare] = useState(false)
  const [showRecord, setShowRecord] = useState(false)

  const institutionName = application.program?.institution_name || 'this institution'
  const respondedState =
    application.student_decision === 'accepted_by_student'
      ? 'accepted'
      : application.student_decision === 'declined_by_student'
        ? 'declined'
        : offer?.student_response || null

  const declineMut = useMutation({
    mutationFn: () => respondToOfferV2(application.id, offer!.id, 'declined', declineReason || undefined),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['application', application.id] })
      queryClient.invalidateQueries({ queryKey: ['my-applications'] })
      showToast('Offer declined', 'success')
      setShowDecline(false)
    },
    onError: () => showToast('Could not decline the offer', 'error'),
  })

  // --- No offer yet (spec 18 §8) ---
  if (!offer) {
    return (
      <>
        <Card className="p-6 text-center">
          <div className="mx-auto mb-3 w-12 h-12 rounded-full bg-student-mist flex items-center justify-center">
            <Inbox size={22} className="text-student-text" />
          </div>
          <p className="text-sm text-student-ink font-medium mb-1">No offer yet</p>
          <p className="text-sm text-student-text max-w-sm mx-auto">
            Decisions usually arrive within 4–8 weeks of submission. You'll be notified here.
          </p>
          <Button
            variant="tertiary"
            size="sm"
            className="mt-4"
            onClick={() => setShowRecord(true)}
          >
            Record an offer I received
          </Button>
        </Card>
        <RecordExternalOfferModal
          appId={application.id}
          isOpen={showRecord}
          onClose={() => setShowRecord(false)}
        />
      </>
    )
  }

  const brief = offer.plain_language_brief
  const summary = brief?.summary || offer.brief
  const keyTerms: OfferKeyTerm[] = brief?.key_terms?.length ? brief.key_terms : deriveKeyTerms(application)
  const nextSteps: OfferNextStep[] = brief?.next_steps ?? []
  const respDays = daysUntil(offer.response_deadline)
  const tone = deadlineTone(respDays)

  return (
    <div className="space-y-4">
      <Card className="p-5">
        {/* Eyebrow — OFFER from <institution> (spec 18 §4) */}
        <p className="text-eyebrow font-semibold uppercase tracking-[0.22em] text-cobalt mb-1">
          Offer from {institutionName}
        </p>
        <div className="flex items-center gap-2 flex-wrap mb-4">
          <h2 className="text-h3 font-bold text-student-ink">
            {OFFER_TYPE_LABEL[offer.offer_type || ''] || 'Admission offer'}
          </h2>
          {offer.received_externally && <Badge variant="neutral">Recorded by you</Badge>}
        </div>
        <p className="text-sm text-student-text -mt-3 mb-4">
          {offer.decision_date && <>Decision received {formatTermDate(offer.decision_date)}</>}
          {offer.decision_date && offer.response_deadline && ' · '}
          {offer.response_deadline && (
            <span className={DEADLINE_TONE_CLASS[tone]}>
              Respond by {formatTermDate(offer.response_deadline)}
              {respDays != null && respDays >= 0 && tone !== 'normal' && ` · ${respDays}d left`}
            </span>
          )}
        </p>

        {/* Deadline escalation banner (spec 18 §8) */}
        {!respondedState && tone === 'error' && respDays != null && respDays >= 0 && (
          <div className="flex items-center gap-2 rounded-lg bg-error-soft px-3 py-2 mb-4 text-sm text-destructive">
            <Clock size={14} />
            {respDays === 0
              ? 'Your response is due today.'
              : `Only ${respDays} day${respDays !== 1 ? 's' : ''} left to respond.`}
          </div>
        )}

        {/* Plain-language brief (body type; bold reserved for amounts/dates) */}
        {summary && (
          <div className="mb-5">
            <p className="text-eyebrow font-semibold uppercase tracking-[0.22em] text-student-text mb-1.5">
              Plain-language brief
            </p>
            <p className="text-base leading-relaxed text-student-ink">{summary}</p>
          </div>
        )}

        {/* Key terms */}
        {keyTerms.length > 0 && (
          <div className="mb-5">
            <p className="text-eyebrow font-semibold uppercase tracking-[0.22em] text-student-text mb-2">
              Key terms
            </p>
            <dl className="space-y-1.5">
              {keyTerms.map((t, i) => (
                <div key={i} className="flex gap-2 text-sm">
                  <dt className="text-student-text min-w-[7.5rem] shrink-0">{t.label}</dt>
                  <dd className="text-student-ink">
                    <span className="font-semibold">{t.value}</span>
                    {t.explanation && (
                      <span className="text-student-text"> — {t.explanation}</span>
                    )}
                  </dd>
                </div>
              ))}
            </dl>
          </div>
        )}

        {/* Next steps */}
        {nextSteps.length > 0 && (
          <div className="mb-5">
            <p className="text-eyebrow font-semibold uppercase tracking-[0.22em] text-student-text mb-2">
              Next steps
            </p>
            <ul className="space-y-1.5">
              {nextSteps.map((s, i) => (
                <li key={i} className="flex items-start gap-2 text-sm text-student-ink">
                  <Star size={13} className="text-student mt-0.5 shrink-0" fill="currentColor" />
                  <span>
                    {s.action}
                    {s.by_date && (
                      <span className="text-student-text"> by {formatTermDate(s.by_date)}</span>
                    )}
                  </span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Actions / status */}
        {respondedState ? (
          <div className="flex items-center gap-3 pt-1">
            <Badge variant={respondedState === 'accepted' ? 'success' : 'neutral'}>
              {respondedState === 'accepted' ? 'You accepted this offer' : 'You declined this offer'}
            </Badge>
            <button
              onClick={() => setShowCompare(true)}
              className="text-sm text-cobalt font-medium inline-flex items-center gap-1 hover:underline"
            >
              Compare offers <ArrowRight size={13} />
            </button>
          </div>
        ) : (
          <div className="flex flex-wrap items-center gap-3 pt-1">
            {/* Accept — gold, the rare earned accent (spec 18 §10) */}
            <Button variant="primary" onClick={() => setShowAccept(true)}>
              Accept offer
            </Button>
            {/* Decline — tertiary border (spec 18 §10) */}
            <Button variant="tertiary" onClick={() => setShowDecline(true)}>
              Decline offer
            </Button>
            <button
              onClick={() => setShowCompare(true)}
              className="text-sm text-cobalt font-medium inline-flex items-center gap-1 hover:underline ml-auto"
            >
              Compare with my other offers <ArrowRight size={13} />
            </button>
          </div>
        )}

        {/* Inline decline confirmation */}
        {showDecline && !respondedState && (
          <div className="mt-4 rounded-lg border border-divider p-3 space-y-2">
            <Textarea
              label="Reason (optional)"
              value={declineReason}
              onChange={e => setDeclineReason(e.target.value)}
              placeholder="Help us learn — why are you declining?"
            />
            <div className="flex justify-end gap-2">
              <Button variant="ghost" size="sm" onClick={() => setShowDecline(false)}>
                Cancel
              </Button>
              <Button
                variant="danger"
                size="sm"
                loading={declineMut.isPending}
                onClick={() => declineMut.mutate()}
              >
                Confirm decline
              </Button>
            </div>
          </div>
        )}
      </Card>

      <AcceptOfferModal
        appId={application.id}
        offerId={offer.id}
        institutionName={institutionName}
        isOpen={showAccept}
        onClose={() => setShowAccept(false)}
      />
      <DecisionComparison isOpen={showCompare} onClose={() => setShowCompare(false)} />
    </div>
  )
}
