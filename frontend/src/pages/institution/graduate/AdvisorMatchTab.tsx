import { useEffect, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Check, GraduationCap, Heart, Sparkles, Star, UserCheck } from 'lucide-react'
import {
  confirmRecommendation,
  flagAdvisorInterest,
  getAdvisorMatches,
  getApplicationReview,
  recommendApplication,
  upsertIntent,
  type AdvisorMatch,
  type RecommendedDecision,
} from '../../../api/graduate'
import Card from '../../../components/ui/Card'
import Badge from '../../../components/ui/Badge'
import Button from '../../../components/ui/Button'
import Select from '../../../components/ui/Select'
import Textarea from '../../../components/ui/Textarea'
import Skeleton from '../../../components/ui/Skeleton'
import AIBadge from '../../../components/ui/AIBadge'
import { Toggle } from '../program-editor/widgets'
import { showToast } from '../../../stores/toast-store'
import { CENTRAL_STATUS_LABEL, DECISION_LABELS, DECISION_OPTIONS, alignmentBand } from './constants'
import { TagInput } from './GradWidgets'
import FundingBuilder from './FundingBuilder'

function apiError(e: unknown, fallback: string): string {
  const detail = (e as { response?: { data?: { detail?: unknown } } })?.response?.data?.detail
  if (typeof detail === 'string') return detail
  if (detail && typeof detail === 'object' && 'message' in detail)
    return String((detail as { message?: string }).message)
  return fallback
}

function AlignmentBar({ score }: { score: number }) {
  const band = alignmentBand(score)
  const color = band === 'strong' ? 'bg-secondary' : band === 'moderate' ? 'bg-secondary/60' : 'bg-muted-foreground/40'
  return (
    <div className="flex items-center gap-2">
      <div className="h-1.5 w-24 overflow-hidden rounded-full bg-muted">
        <div className={`h-full rounded-full ${color}`} style={{ width: `${Math.max(2, score)}%` }} />
      </div>
      <span className="w-9 text-right text-sm font-semibold tabular-nums text-foreground">
        {Math.round(score)}
      </span>
    </div>
  )
}

function AdvisorRow({
  match,
  applicationId,
}: {
  match: AdvisorMatch
  applicationId: string
}) {
  const qc = useQueryClient()
  const flagMut = useMutation({
    mutationFn: (flagged: boolean) => flagAdvisorInterest(applicationId, match.faculty_id, flagged),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['advisor-matches', applicationId] }),
    onError: e => showToast(apiError(e, 'Could not update interest'), 'error'),
  })
  return (
    <div
      className={`rounded-lg border p-4 ${
        match.mutual ? 'border-secondary/40 bg-secondary/5' : 'border-border bg-background'
      }`}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            <span className="font-medium text-foreground">{match.faculty_name}</span>
            {match.title && <span className="text-xs text-muted-foreground">{match.title}</span>}
            {match.mutual && (
              <Badge variant="info">
                <Heart size={11} className="-mt-px" /> Mutual interest
              </Badge>
            )}
            {match.applicant_named_advisor && !match.mutual && (
              <Badge variant="neutral">Named by applicant</Badge>
            )}
            {match.accepting_students ? (
              <Badge variant="success">
                <Check size={11} /> Accepting
              </Badge>
            ) : (
              <Badge variant="neutral">Not accepting</Badge>
            )}
            {match.funding_available && <Badge variant="info">Funding available</Badge>}
          </div>
          {match.shared_interests.length > 0 && (
            <div className="mt-2 flex flex-wrap gap-1">
              {match.shared_interests.map((s, i) => (
                <span key={i} className="rounded bg-muted px-2 py-0.5 text-xs text-muted-foreground">
                  {s}
                </span>
              ))}
            </div>
          )}
          {match.rationale && (
            <p className="mt-1.5 flex items-start gap-1 text-xs text-muted-foreground">
              <Sparkles size={11} className="mt-0.5 shrink-0 text-secondary" /> {match.rationale}
            </p>
          )}
        </div>
        <div className="flex shrink-0 flex-col items-end gap-2">
          <AlignmentBar score={match.alignment_score} />
          <Toggle
            checked={match.advisor_flagged_interest}
            onChange={v => flagMut.mutate(v)}
            label="Flag interest"
          />
        </div>
      </div>
    </div>
  )
}

export default function AdvisorMatchTab({ applicationId }: { applicationId: string }) {
  const qc = useQueryClient()
  const matchesQ = useQuery({
    queryKey: ['advisor-matches', applicationId],
    queryFn: () => getAdvisorMatches(applicationId),
  })
  const reviewQ = useQuery({
    queryKey: ['grad-review', applicationId],
    queryFn: () => getApplicationReview(applicationId),
  })

  const [interests, setInterests] = useState<string[]>([])
  const [advisorNames, setAdvisorNames] = useState<string[]>([])
  const [sop, setSop] = useState('')
  const [fundingRequired, setFundingRequired] = useState(true)
  const [decision, setDecision] = useState<RecommendedDecision>('admitted')
  const [committeeNotes, setCommitteeNotes] = useState('')

  useEffect(() => {
    const intent = matchesQ.data?.intent
    if (intent) {
      setInterests(intent.research_interests ?? [])
      setAdvisorNames(intent.target_advisor_names ?? [])
      setSop(intent.statement_of_purpose ?? '')
      setFundingRequired(intent.funding_required ?? true)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [matchesQ.dataUpdatedAt])

  useEffect(() => {
    const rec = reviewQ.data?.recommended_decision
    if (rec) setDecision(rec)
    if (reviewQ.data?.committee_notes) setCommitteeNotes(reviewQ.data.committee_notes)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [reviewQ.dataUpdatedAt])

  const saveIntentMut = useMutation({
    mutationFn: () =>
      upsertIntent(applicationId, {
        research_interests: interests,
        target_advisor_names: advisorNames,
        statement_of_purpose: sop,
        funding_required: fundingRequired,
      }),
    onSuccess: () => {
      showToast('Research intent saved', 'success')
      qc.invalidateQueries({ queryKey: ['advisor-matches', applicationId] })
    },
    onError: e => showToast(apiError(e, 'Could not save intent'), 'error'),
  })

  const recommendMut = useMutation({
    mutationFn: () =>
      recommendApplication(applicationId, { decision, committee_notes: committeeNotes || null }),
    onSuccess: () => {
      showToast('Recommendation recorded', 'success')
      qc.invalidateQueries({ queryKey: ['grad-review', applicationId] })
    },
    onError: e => showToast(apiError(e, 'Could not recommend'), 'error'),
  })

  const confirmMut = useMutation({
    mutationFn: () => confirmRecommendation(applicationId, {}),
    onSuccess: res => {
      showToast(`Released: ${DECISION_LABELS[res.decision as RecommendedDecision] ?? res.decision}`, 'success')
      qc.invalidateQueries({ queryKey: ['grad-review', applicationId] })
      qc.invalidateQueries({ queryKey: ['review-packet', applicationId] })
    },
    onError: e => showToast(apiError(e, 'Could not release — central office only'), 'error'),
  })

  if (matchesQ.isLoading) return <Skeleton className="h-96" />
  if (matchesQ.isError)
    return (
      <Card pad={false} className="p-6 text-center text-sm text-muted-foreground">
        Advisor matching is available for graduate programs only.
      </Card>
    )

  const data = matchesQ.data!
  const review = reviewQ.data
  const intent = data.intent
  const central = review?.central_status

  return (
    <div className="space-y-4">
      {/* Research intent (§2.2) */}
      <Card pad={false} className="p-5">
        <div className="mb-4 flex items-center gap-2">
          <span className="text-secondary">
            <GraduationCap size={16} />
          </span>
          <h3 className="text-sm font-semibold text-foreground">Research intent</h3>
          {intent?.extracted_interests && intent.extracted_interests.length > 0 && <AIBadge />}
        </div>
        <div className="space-y-4">
          <TagInput
            label="Research interests"
            values={interests}
            onChange={setInterests}
            placeholder="Add an interest and press Enter"
          />
          <TagInput
            label="Target advisors"
            values={advisorNames}
            onChange={setAdvisorNames}
            placeholder="Name an advisor and press Enter"
          />
          <Textarea
            label="Statement of purpose"
            value={sop}
            onChange={e => setSop(e.target.value)}
            rows={4}
            placeholder="Paste the applicant's statement of purpose — interests are auto-tagged."
          />
          {intent?.alignment_summary && (
            <p className="rounded-lg bg-muted/40 px-3 py-2 text-xs text-muted-foreground">
              {intent.alignment_summary}
            </p>
          )}
          <div className="flex items-center justify-between">
            <Toggle
              checked={fundingRequired}
              onChange={setFundingRequired}
              label="Applicant requires funding"
            />
            <Button variant="secondary" size="sm" loading={saveIntentMut.isPending} onClick={() => saveIntentMut.mutate()}>
              Save intent
            </Button>
          </div>
        </div>
      </Card>

      {/* Advisor matches (§2.1) */}
      <Card pad={false} className="p-5">
        <div className="mb-4 flex items-center justify-between gap-2">
          <div className="flex items-center gap-2">
            <span className="text-secondary">
              <UserCheck size={16} />
            </span>
            <h3 className="text-sm font-semibold text-foreground">Advisors who fit this applicant</h3>
          </div>
          {data.matches.some(m => m.mutual) && (
            <span className="text-xs text-secondary">
              {data.matches.filter(m => m.mutual).length} mutual
            </span>
          )}
        </div>
        {data.matches.length === 0 ? (
          <p className="text-sm italic text-muted-foreground">
            No faculty in this department yet. Add faculty from the department portal to surface
            advisor matches.
          </p>
        ) : (
          <div className="space-y-2.5">
            {data.matches.map(m => (
              <AdvisorRow key={m.faculty_id} match={m} applicationId={applicationId} />
            ))}
          </div>
        )}
      </Card>

      {/* Funding package (§2.3) */}
      <FundingBuilder applicationId={applicationId} />

      {/* Two-stage review (§2.4) */}
      <Card pad={false} className="p-5">
        <div className="mb-4 flex items-center gap-2">
          <span className="text-secondary">
            <Star size={16} />
          </span>
          <h3 className="text-sm font-semibold text-foreground">Department recommendation</h3>
          {central && (
            <Badge variant={central === 'pending' ? 'warning' : 'success'}>
              {CENTRAL_STATUS_LABEL[central] ?? central}
            </Badge>
          )}
        </div>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
          <Select
            label="Recommended decision"
            options={DECISION_OPTIONS}
            value={decision}
            onChange={e => setDecision(e.target.value as RecommendedDecision)}
          />
          <div className="sm:col-span-2">
            <Textarea
              label="Committee notes"
              value={committeeNotes}
              onChange={e => setCommitteeNotes(e.target.value)}
              rows={2}
              placeholder="Why the committee recommends this decision…"
            />
          </div>
        </div>
        <div className="mt-4 flex flex-wrap items-center justify-end gap-2">
          <Button variant="tertiary" size="sm" loading={recommendMut.isPending} onClick={() => recommendMut.mutate()}>
            {central ? 'Update recommendation' : 'Recommend'}
          </Button>
          {central === 'pending' && (
            <Button variant="secondary" size="sm" loading={confirmMut.isPending} onClick={() => confirmMut.mutate()}>
              Confirm &amp; release
            </Button>
          )}
        </div>
        {central === 'pending' && (
          <p className="mt-2 text-right text-xs text-muted-foreground">
            Recommended by department — awaiting central confirmation. Only central office can
            release.
          </p>
        )}
      </Card>
    </div>
  )
}
