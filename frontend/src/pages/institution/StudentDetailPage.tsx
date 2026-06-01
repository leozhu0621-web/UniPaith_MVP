import { useState, useEffect, type ReactNode, type KeyboardEvent, Fragment } from 'react'
import { useParams, useSearchParams } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  User, Star, Brain, ClipboardCheck, Award, FileText, RefreshCw, Shield, Eye, EyeOff,
  Lock, FileCheck, Globe, Send, AlertTriangle, CheckCircle2, Clock,
} from 'lucide-react'
import { reviewApplication } from '../../api/applications-admin'
import { generateAIDraft } from '../../api/institutions'
import {
  assignReviewer, scoreApplication, getRubrics, regenerateAIPacketSummary, getAIPrefill,
  scanIntegrity, getMatchRationaleFull, getReviewPacket, synthesizeReviews,
  reviewAssistantChat, revealApplicantIdentity, actOnIntegritySignal,
} from '../../api/reviews'
import DecisionPanel from './pipeline/DecisionPanel'
import InstitutionPageHeader from '../../components/institution/InstitutionPageHeader'
import { getInterviewsByApplication } from '../../api/interviews-admin'
import Card from '../../components/ui/Card'
import Badge from '../../components/ui/Badge'
import Button from '../../components/ui/Button'
import Tabs from '../../components/ui/Tabs'
import Modal from '../../components/ui/Modal'
import Input from '../../components/ui/Input'
import Textarea from '../../components/ui/Textarea'
import Select from '../../components/ui/Select'
import Skeleton from '../../components/ui/Skeleton'
import AIBadge from '../../components/ui/AIBadge'
import RubricSlider from '../../components/ui/RubricSlider'
import { showToast } from '../../stores/toast-store'
import { formatDate, formatDateTime } from '../../utils/format'
import { STATUS_COLORS, INTERVIEW_TYPE_LABELS } from '../../utils/constants'
import type {
  Rubric, ReviewPacket, ReviewSynthesis, InstitutionMatchRationale, IntegrityAction, Interview, InstitutionDecision,
} from '../../types'

const SEVERITY_DOT: Record<string, string> = { high: 'bg-error', medium: 'bg-warning', low: 'bg-cobalt' }

export default function StudentDetailPage() {
  const { appId, studentId } = useParams<{ appId?: string; studentId?: string }>()
  const applicationId = appId ?? studentId
  const queryClient = useQueryClient()
  const [searchParams, setSearchParams] = useSearchParams()
  const [activeTab, setActiveTab] = useState(searchParams.get('tab') ?? 'overview')
  const [revealed, setRevealed] = useState(false)

  const [showScoringModal, setShowScoringModal] = useState(false)
  const [showDraftModal, setShowDraftModal] = useState(false)
  const [showRevealModal, setShowRevealModal] = useState(false)

  const [selectedRubric, setSelectedRubric] = useState('')
  const [criterionScores, setCriterionScores] = useState<Record<string, number>>({})
  const [criterionNotes, setCriterionNotes] = useState<Record<string, string>>({})
  const [reviewerNotes, setReviewerNotes] = useState('')
  const [prefilling, setPrefilling] = useState(false)

  const [draftType, setDraftType] = useState('missing_items')
  const [draftSubject, setDraftSubject] = useState('')
  const [draftBody, setDraftBody] = useState('')
  const [draftLoading, setDraftLoading] = useState(false)

  const [revealReason, setRevealReason] = useState('')

  const [assistantPrompt, setAssistantPrompt] = useState('')
  const [assistantReply, setAssistantReply] = useState<{ answer: string; fallback: boolean } | null>(null)

  const [synthesis, setSynthesis] = useState<ReviewSynthesis | null>(null)
  const [synthLoading, setSynthLoading] = useState(false)

  const handleTabChange = (tab: string) => {
    setActiveTab(tab)
    setSearchParams(prev => { const next = new URLSearchParams(prev); next.set('tab', tab); return next })
  }
  useEffect(() => {
    const t = searchParams.get('tab')
    if (t && t !== activeTab) setActiveTab(t)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [searchParams])

  const packetQ = useQuery({
    queryKey: ['review-packet', applicationId, revealed],
    queryFn: () => getReviewPacket(applicationId!, { reveal: revealed }),
    enabled: !!applicationId,
  })
  const packet = packetQ.data

  // Spec 34 — DecisionPanel consumes the application detail; fetched lazily.
  const appDetailQ = useQuery({
    queryKey: ['application-review', applicationId],
    queryFn: () => reviewApplication(applicationId!),
    enabled: !!applicationId && activeTab === 'decision',
  })

  const rubricsQ = useQuery({ queryKey: ['rubrics'], queryFn: () => getRubrics(), enabled: showScoringModal })
  const rubrics: Rubric[] = Array.isArray(rubricsQ.data) ? rubricsQ.data : []

  const matchRationaleQ = useQuery({
    queryKey: ['match-rationale-full', applicationId],
    queryFn: () => getMatchRationaleFull(applicationId!),
    enabled: !!applicationId,
  })

  // Spec 33 §3 step 6 — interview results feed the review packet.
  const interviewsQ = useQuery({
    queryKey: ['application-interviews', applicationId],
    queryFn: () => getInterviewsByApplication(applicationId!),
    enabled: !!applicationId && activeTab === 'interview',
  })
  const interviews: Interview[] = Array.isArray(interviewsQ.data) ? interviewsQ.data : []

  const invalidatePacket = () => queryClient.invalidateQueries({ queryKey: ['review-packet', applicationId] })

  const regenMut = useMutation({
    mutationFn: () => regenerateAIPacketSummary(applicationId!, packet?.rubric_id || undefined),
    onSuccess: () => { invalidatePacket(); showToast('AI summary regenerated', 'success') },
    onError: () => showToast('Could not regenerate summary', 'error'),
  })
  const scanMut = useMutation({
    mutationFn: () => scanIntegrity(applicationId!),
    onSuccess: () => { invalidatePacket(); showToast('Integrity scan complete', 'success') },
    onError: () => showToast('Integrity scan failed', 'error'),
  })
  const integrityActionMut = useMutation({
    mutationFn: ({ id, action }: { id: string; action: IntegrityAction }) => actOnIntegritySignal(id, action),
    onSuccess: (r) => { invalidatePacket(); showToast(r.rejected_application ? 'Application rejected' : `Signal ${r.status}`, r.rejected_application ? 'warning' : 'success') },
    onError: () => showToast('Action failed', 'error'),
  })
  const assignMut = useMutation({
    mutationFn: () => assignReviewer(applicationId!),
    onSuccess: () => { showToast('Reviewer assigned', 'success'); invalidatePacket() },
    onError: () => showToast('Failed to assign reviewer', 'error'),
  })
  const scoreMut = useMutation({
    mutationFn: () => scoreApplication(applicationId!, { rubric_id: selectedRubric, criterion_scores: criterionScores, reviewer_notes: composeNotes() }),
    onSuccess: () => { showToast('Score submitted', 'success'); setShowScoringModal(false); setSynthesis(null); invalidatePacket() },
    onError: (e: unknown) => showToast(errDetail(e) ?? 'Failed to submit score', 'error'),
  })
  const assistantMut = useMutation({
    mutationFn: () => reviewAssistantChat(applicationId!, assistantPrompt),
    onSuccess: (data) => setAssistantReply({ answer: data.answer, fallback: data.model_used === 'rule_based' }),
    onError: () => showToast('Assistant request failed', 'error'),
  })

  const markForCommittee = () => {
    setSearchParams(prev => {
      const next = new URLSearchParams(prev)
      next.set('tab', 'decision')
      next.set('decision', 'deferred')
      return next
    })
    setActiveTab('decision')
    showToast('Marked for committee — defer when ready', 'info')
  }

  const composeNotes = () => {
    const perCrit = Object.entries(criterionNotes).filter(([, v]) => v?.trim()).map(([k, v]) => `${k}: ${v.trim()}`).join(' · ')
    return [reviewerNotes.trim(), perCrit].filter(Boolean).join('\n')
  }

  const criteriaFullyScored = (rubric: Rubric | undefined, scores: Record<string, number>) => {
    if (!rubric?.criteria?.length) return false
    return rubric.criteria.every(c => {
      const s = scores[c.name]
      return s != null && s >= 1
    })
  }

  const doReveal = async () => {
    try {
      await revealApplicantIdentity(applicationId!, revealReason || undefined)
      setRevealed(true); setShowRevealModal(false); setRevealReason('')
      showToast('Identity revealed — action logged', 'success')
    } catch { showToast('Reveal failed', 'error') }
  }

  const runSynthesis = async () => {
    setSynthLoading(true)
    try { setSynthesis(await synthesizeReviews(applicationId!, packet?.rubric_id || undefined)) }
    catch { showToast('Synthesis failed', 'error') }
    finally { setSynthLoading(false) }
  }

  useEffect(() => {
    const p = packetQ.data
    if (activeTab !== 'scores' || !p || p.reviewer_count < 2 || synthesis || synthLoading) return
    void runSynthesis()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeTab, packetQ.data?.reviewer_count, applicationId])

  if (packetQ.isLoading) {
    return <div className="p-6 space-y-4"><Skeleton className="h-12 w-80" /><Skeleton className="h-64" /></div>
  }
  if (!packet) {
    return <div className="p-6"><p className="text-muted-foreground">Application not found.</p></div>
  }

  const blind = packet.blind_review.enabled && !packet.blind_review.revealed
  const locked = packet.locked
  const openSignals = packet.integrity_signals.filter(s => s.status === 'open').length
  const tabs = [
    { id: 'overview', label: 'Overview' },
    { id: 'scores', label: 'Scores' },
    { id: 'ai', label: 'AI Summary' },
    { id: 'integrity', label: `Integrity${openSignals ? ` (${openSignals})` : ''}` },
    { id: 'decision', label: 'Decision' },
    { id: 'documents', label: 'Documents' },
    { id: 'essays', label: 'Essays' },
    { id: 'interview', label: 'Interviews' },
    { id: 'timeline', label: 'Timeline' },
  ]
  const currentRubric = rubrics.find(r => r.id === selectedRubric)
  const matchRationale = matchRationaleQ.data
  const fitness = matchRationale?.fitness_score ?? packet.match_score
  const confidence = matchRationale?.confidence_score

  return (
    <div className="p-6 space-y-4">
      <InstitutionPageHeader
        title={packet.student.display_name}
        description={packet.program.label}
        badge={
          <div className="flex items-center gap-2">
            {blind && <EyeOff size={16} className="text-warning" />}
            <Badge variant={(STATUS_COLORS[packet.status ?? ''] as 'success' | 'warning' | 'info' | 'neutral') ?? 'neutral'}>{(packet.status ?? 'unknown').replace(/_/g, ' ')}</Badge>
            {packet.decision?.decision && (
              <Badge variant={packet.decision.decision === 'admitted' ? 'success' : packet.decision.decision === 'rejected' ? 'error' : 'warning'}>{packet.decision.decision}</Badge>
            )}
          </div>
        }
      />
      <p className="text-xs uppercase tracking-wide text-muted-foreground -mt-2">Applicant review packet</p>

      {/* Banners */}
      {blind && (
        <div className="flex flex-wrap items-center justify-between gap-3 rounded-lg border border-warning/40 bg-warning-soft px-4 py-2.5">
          <div className="flex items-center gap-2 text-sm text-warning">
            <EyeOff size={16} className="shrink-0" />
            <span>Blind review — identity-revealing fields are hidden so you score on substance. Reveal only after scoring, per policy.</span>
          </div>
          <Button variant="tertiary" size="sm" onClick={() => setShowRevealModal(true)} className="flex items-center gap-1 shrink-0"><Eye size={14} /> Reveal identity</Button>
        </div>
      )}
      {locked && (
        <div className="flex items-center gap-2 rounded-lg border border-border bg-muted px-4 py-2.5 text-sm text-foreground">
          <Lock size={16} className="text-muted-foreground" /> A decision has been released — scoring is read-only for this applicant.
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left */}
        <div className="lg:col-span-1 space-y-4">
          <Card className="p-5">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-12 h-12 bg-cobalt/10 rounded-full flex items-center justify-center shrink-0"><User size={22} className="text-cobalt" /></div>
              <div className="min-w-0">
                <p className="font-semibold text-foreground truncate">{packet.student.display_name}</p>
                <p className="text-sm text-muted-foreground truncate">{packet.program.program_name}</p>
              </div>
            </div>
            {fitness != null && (
              <div className="flex items-center justify-center gap-4 mb-4">
                <ScoreRing label="Fit" value={fitness} />
                {confidence != null && <ScoreRing label="Confidence" value={confidence} />}
              </div>
            )}
            <div className="space-y-2 text-sm">
              <Row label="Completeness" value={packet.completeness_status ?? '—'} />
              <Row label="Reviewers" value={String(packet.reviewer_count)} />
              <Row label="Submitted" value={formatDate(packet.submitted_at)} />
            </div>
          </Card>

          <Card className="p-4 space-y-2">
            <div className="flex items-center gap-2"><Globe size={15} className="text-cobalt" /><h3 className="text-sm font-semibold text-foreground">Context</h3></div>
            {packet.holistic_context.standard.length === 0 ? (
              <p className="text-xs text-muted-foreground">No additional context flags.</p>
            ) : (
              <div className="flex flex-wrap gap-1.5">
                {packet.holistic_context.standard.map(f => (
                  <span key={f.key} className="inline-flex items-center rounded-full border border-cobalt/20 bg-cobalt/5 px-2 py-0.5 text-xs text-cobalt" title={`${f.label}: ${f.value}`}>{f.label}{f.value ? `: ${f.value}` : ''}</span>
                ))}
              </div>
            )}
            {packet.holistic_context.high_sensitivity.length > 0 && (
              <div className="rounded-md border border-warning/30 bg-warning-soft/40 p-2 space-y-1">
                <p className="text-[11px] font-medium text-warning">Policy-gated context</p>
                <div className="flex flex-wrap gap-1.5">
                  {packet.holistic_context.high_sensitivity.map(f => (
                    <span key={f.key} className="inline-flex items-center rounded-full border border-warning/30 bg-warning-soft px-2 py-0.5 text-xs text-warning" title={`${f.label}: ${f.value}`}>{f.label}</span>
                  ))}
                </div>
              </div>
            )}
            <p className="text-[11px] leading-snug text-muted-foreground">{packet.holistic_context.note}</p>
          </Card>

          <Card className="p-4 space-y-1.5">
            <div className="flex items-center gap-2"><FileCheck size={15} className="text-cobalt" /><h3 className="text-sm font-semibold text-foreground">Test policy</h3><Badge variant="neutral">{packet.test_optional.policy.replace(/_/g, '-')}</Badge></div>
            <p className="text-xs text-foreground">{packet.test_optional.recommendation}</p>
            <p className="text-[11px] text-muted-foreground">{packet.test_optional.guardrail}</p>
          </Card>

          <Card className="p-4 space-y-2">
            <h3 className="text-sm font-medium text-muted-foreground mb-1">Actions</h3>
            <Button variant="secondary" className="w-full flex items-center justify-center gap-2" onClick={() => assignMut.mutate()} disabled={assignMut.isPending}><ClipboardCheck size={16} /> Assign reviewer</Button>
            <Button variant="secondary" className="w-full flex items-center justify-center gap-2" onClick={() => setShowScoringModal(true)} disabled={locked} title={locked ? 'Scoring is read-only after a decision' : undefined}><Star size={16} /> Score this applicant</Button>
            <Button variant="secondary" className="w-full flex items-center justify-center gap-2" onClick={() => setShowDraftModal(true)}><Brain size={16} /> Generate AI message</Button>
            <Button variant="tertiary" className="w-full flex items-center justify-center gap-2" onClick={markForCommittee}><Clock size={16} /> Mark for committee</Button>
            <Button className="w-full flex items-center justify-center gap-2" onClick={() => handleTabChange('decision')}><Award size={16} /> Decision &amp; offer</Button>
          </Card>
        </div>

        {/* Right */}
        <div className="lg:col-span-2">
          <Tabs tabs={tabs} activeTab={activeTab} onChange={handleTabChange} />
          <div className="mt-4 space-y-4">
            {activeTab === 'overview' && <OverviewTab packet={packet} />}
            {activeTab === 'scores' && <ScoresTab packet={packet} synthesis={synthesis} onSynthesize={runSynthesis} synthLoading={synthLoading} />}
            {activeTab === 'ai' && (
              <AISummaryTab packet={packet} regen={() => regenMut.mutate()} regenPending={regenMut.isPending}
                matchRationale={matchRationaleQ.data} matchLoading={matchRationaleQ.isLoading}
                assistantPrompt={assistantPrompt} setAssistantPrompt={setAssistantPrompt}
                onAsk={() => assistantMut.mutate()} asking={assistantMut.isPending} reply={assistantReply} />
            )}
            {activeTab === 'integrity' && (
              <IntegrityTab packet={packet} onScan={() => scanMut.mutate()} scanning={scanMut.isPending}
                onAction={(id, action) => integrityActionMut.mutate({ id, action })} actionPending={integrityActionMut.isPending} locked={locked} />
            )}
            {activeTab === 'decision' && (
              appDetailQ.isLoading || !appDetailQ.data
                ? <Skeleton className="h-64" />
                : <DecisionPanel applicationId={applicationId!} app={appDetailQ.data} prefillDecision={(['admitted','conditional_admission','waitlisted','deferred','rejected'] as const).includes(searchParams.get('decision') as InstitutionDecision) ? searchParams.get('decision') as InstitutionDecision : null} />
            )}
            {activeTab === 'documents' && <DocumentsTab packet={packet} />}
            {activeTab === 'essays' && <EssaysTab packet={packet} />}
            {activeTab === 'interview' && (
              <Card className="p-5">
                <h3 className="font-semibold text-foreground mb-3">Interviews</h3>
                {interviewsQ.isLoading ? (
                  <Skeleton className="h-24" />
                ) : interviews.length === 0 ? (
                  <p className="text-sm text-muted-foreground">
                    No interviews yet. Propose one from <span className="font-medium">Admissions → Interviews</span>.
                  </p>
                ) : (
                  <div className="space-y-3">
                    {interviews.map(iv => (
                      <div key={iv.id} className="rounded-lg border border-border p-4">
                        <div className="flex items-center justify-between gap-2 mb-2">
                          <div className="flex items-center gap-2">
                            <Badge variant="info">
                              {INTERVIEW_TYPE_LABELS[iv.interview_type] || iv.interview_type}
                            </Badge>
                            {iv.async_expired ? (
                              <Badge variant="danger">No submission received</Badge>
                            ) : iv.status === 'proposed' ? (
                              <Badge variant="warning">Awaiting student</Badge>
                            ) : (
                              <Badge variant={(STATUS_COLORS[iv.status] as 'neutral') ?? 'neutral'}>
                                {iv.status.replace(/_/g, ' ')}
                              </Badge>
                            )}
                          </div>
                          <span className="text-xs text-muted-foreground whitespace-nowrap">
                            {iv.scheduled_at
                              ? formatDateTime(iv.scheduled_at)
                              : iv.async_window_end
                                ? `By ${formatDateTime(iv.async_window_end)}`
                                : ''}
                          </span>
                        </div>
                        {iv.recommendation && (
                          <p className="text-sm text-foreground">
                            Recommendation:{' '}
                            <span className="font-medium">{iv.recommendation.replace(/_/g, ' ')}</span>
                          </p>
                        )}
                        {iv.scores.length > 0 && (
                          <div className="mt-2 space-y-1.5">
                            {iv.scores.map((s, i) => (
                              <div key={i} className="text-sm text-muted-foreground">
                                {s.total_weighted_score != null && (
                                  <span className="text-foreground font-medium">
                                    Score {s.total_weighted_score}
                                  </span>
                                )}
                                {s.notes && <span className="block text-xs">{s.notes}</span>}
                              </div>
                            ))}
                          </div>
                        )}
                        {iv.recording_url && (
                          <a
                            href={iv.recording_url}
                            target="_blank"
                            rel="noreferrer"
                            className="text-sm text-cobalt hover:underline mt-2 inline-block"
                          >
                            View recording
                          </a>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </Card>
            )}
            {activeTab === 'timeline' && <TimelineTab packet={packet} />}
          </div>
        </div>
      </div>

      {/* Reveal modal */}
      <Modal isOpen={showRevealModal} onClose={() => setShowRevealModal(false)} title="Reveal applicant identity">
        <div className="space-y-4">
          <p className="text-sm text-muted-foreground">Revealing identity is audit-logged. Provide a reason (e.g. "scoring complete").</p>
          <Textarea label="Reason" value={revealReason} onChange={e => setRevealReason(e.target.value)} rows={2} placeholder="Reason for revealing identity…" />
          <div className="flex justify-end gap-2"><Button variant="ghost" onClick={() => setShowRevealModal(false)}>Cancel</Button><Button onClick={doReveal}>Reveal &amp; log</Button></div>
        </div>
      </Modal>

      {/* AI Draft modal */}
      <Modal isOpen={showDraftModal} onClose={() => setShowDraftModal(false)} title="AI communication draft" size="lg">
        <div className="space-y-4">
          <div className="flex items-center gap-2"><AIBadge /> <span className="text-xs text-muted-foreground">Drafts only — review &amp; edit before sending.</span></div>
          <div className="flex items-end gap-3">
            <div className="flex-1">
              <Select label="Message type" options={[
                { value: 'missing_items', label: 'Missing items request' },
                { value: 'interview_invite', label: 'Interview invitation' },
                { value: 'clarification', label: 'Clarification request' },
                { value: 'decision_admit', label: 'Admission letter' },
                { value: 'decision_reject', label: 'Rejection letter' },
                { value: 'decision_waitlist', label: 'Waitlist notice' },
              ]} value={draftType} onChange={e => setDraftType(e.target.value)} />
            </div>
            <Button variant="secondary" disabled={draftLoading} onClick={async () => {
              setDraftLoading(true)
              try { const r = await generateAIDraft(applicationId!, draftType); setDraftSubject(r.subject); setDraftBody(r.body); showToast('AI draft generated — edit before sending', 'success') }
              catch { showToast('Draft generation failed', 'error') } finally { setDraftLoading(false) }
            }} className="flex items-center gap-1 whitespace-nowrap"><Brain size={14} /> {draftLoading ? 'Generating…' : 'Generate draft'}</Button>
          </div>
          <Input label="Subject" value={draftSubject} onChange={e => setDraftSubject(e.target.value)} />
          <Textarea label="Message body (editable)" value={draftBody} onChange={e => setDraftBody(e.target.value)} rows={8} />
          <div className="flex justify-end gap-2"><Button variant="ghost" onClick={() => setShowDraftModal(false)}>Cancel</Button><Button disabled={!draftSubject.trim() || !draftBody.trim()} onClick={() => { showToast('Draft ready — send from the Communications inbox', 'success'); setShowDraftModal(false) }}>Done editing</Button></div>
        </div>
      </Modal>

      {/* Scoring modal */}
      <Modal isOpen={showScoringModal} onClose={() => setShowScoringModal(false)} title="Score this applicant" size="lg">
        <div className="space-y-4">
          <div className="flex items-end gap-3">
            <div className="flex-1">
              <Select label="Rubric" options={rubrics.map(r => ({ value: r.id, label: r.rubric_name }))} placeholder="Select rubric"
                value={selectedRubric} onChange={e => { setSelectedRubric(e.target.value); setCriterionScores({}); setCriterionNotes({}) }} />
            </div>
            {selectedRubric && (
              <Button variant="secondary" size="sm" disabled={prefilling} onClick={async () => {
                setPrefilling(true)
                try {
                  const result = await getAIPrefill(applicationId!, selectedRubric)
                  const scores: Record<string, number> = {}; const notes: Record<string, string> = {}
                  for (const [name, data] of Object.entries(result.prefill)) {
                    if (data.suggested_score != null) scores[name] = clampScore(data.suggested_score, currentRubric, name)
                    if (data.suggested_note) notes[name] = data.suggested_note
                  }
                  setCriterionScores(scores); setCriterionNotes(notes)
                  if (result.overall_note) setReviewerNotes(result.overall_note)
                  showToast('AI pre-fill applied — review and adjust', 'success')
                } catch { showToast('AI pre-fill failed', 'error') } finally { setPrefilling(false) }
              }} className="flex items-center gap-1 whitespace-nowrap"><Brain size={14} /> {prefilling ? 'Filling…' : 'AI pre-fill'}</Button>
            )}
          </div>
          {selectedRubric && <div className="flex items-center gap-2"><AIBadge label="AI pre-fill available" /><span className="text-xs text-muted-foreground">Reviewer edits before saving — humans keep the final score.</span></div>}
          {currentRubric?.criteria && (
            <div className="space-y-3">
              {currentRubric.criteria.map(c => {
                const max = c.max_score ?? c.scale_max ?? 5
                return (
                  <div key={c.name} className="rounded-lg border border-border p-3">
                    <div className="flex items-center justify-between mb-2 gap-2">
                      <span className="text-sm font-medium text-foreground">{c.name}{c.weight != null ? <span className="text-muted-foreground"> · {Math.round(c.weight * 100)}%</span> : null}</span>
                    </div>
                    <RubricSlider value={criterionScores[c.name] ?? null} min={1} max={max} label={c.name} onChange={v => setCriterionScores({ ...criterionScores, [c.name]: v })} />
                    <Textarea label="" value={criterionNotes[c.name] ?? ''} onChange={e => setCriterionNotes({ ...criterionNotes, [c.name]: e.target.value })} rows={2} placeholder={`Notes for ${c.name}…`} className="mt-2 text-xs" />
                  </div>
                )
              })}
            </div>
          )}
          <Textarea label="Overall reviewer notes" value={reviewerNotes} onChange={e => setReviewerNotes(e.target.value)} rows={3} />
          <div className="flex justify-end gap-2"><Button variant="ghost" onClick={() => setShowScoringModal(false)}>Cancel</Button><Button onClick={() => scoreMut.mutate()} disabled={!selectedRubric || !criteriaFullyScored(currentRubric, criterionScores) || scoreMut.isPending}>{scoreMut.isPending ? 'Submitting…' : 'Submit score'}</Button></div>
        </div>
      </Modal>
    </div>
  )
}

// ── helpers ──────────────────────────────────────────────────────────────────

function pctScore(v: number): number { const n = v > 1 ? v : v * 100; return Math.round(Math.max(0, Math.min(100, n))) }

function ScoreRing({ label, value }: { label: string; value: number }) {
  const pct = pctScore(value)
  return (
    <div className="text-center">
      <div className="relative w-16 h-16 mx-auto">
        <svg className="w-full h-full -rotate-90" viewBox="0 0 36 36">
          <path d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" fill="none" stroke="currentColor" className="text-muted" strokeWidth="3" />
          <path d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" fill="none" stroke="#2A6BD4" strokeWidth="3" strokeDasharray={`${pct}, 100`} strokeLinecap="round" />
        </svg>
        <span className="absolute inset-0 flex items-center justify-center text-xs font-bold text-cobalt">{pct}</span>
      </div>
      <p className="text-[10px] text-muted-foreground mt-1">{label}</p>
    </div>
  )
}
function clampScore(v: number, rubric: Rubric | undefined, name: string): number {
  const max = rubric?.criteria?.find(c => c.name === name)?.max_score ?? rubric?.criteria?.find(c => c.name === name)?.scale_max ?? 5
  return Math.max(0, Math.min(max, Math.round(v)))
}
function prettyField(path: string): string { const last = path.split('.').pop() ?? path; const w = last.replace(/_/g, ' ').trim(); return w.charAt(0).toUpperCase() + w.slice(1) }
function errDetail(e: unknown): string | undefined {
  const detail = (e as { response?: { data?: { detail?: unknown } } })?.response?.data?.detail
  return typeof detail === 'string' ? detail : undefined
}

function Row({ label, value }: { label: string; value: string }) {
  return <div className="flex justify-between"><span className="text-muted-foreground">{label}</span><span className="text-foreground">{value}</span></div>
}
function Section({ title, children }: { title: string; children: ReactNode }) {
  return <div><h4 className="text-sm font-medium text-muted-foreground mb-1">{title}</h4>{children}</div>
}
function CitationChips({ title, items, tone }: { title: string; items: string[]; tone: 'green' | 'slate' }) {
  const cls = tone === 'green' ? 'border-success/30 bg-success-soft text-success' : 'border-cobalt/30 bg-cobalt/5 text-cobalt'
  return (
    <div>
      <div className="text-xs font-medium text-muted-foreground mb-1.5">{title}</div>
      <div className="flex flex-wrap gap-1.5">{items.map(p => <span key={p} className={`inline-flex items-center rounded-full border px-2 py-0.5 text-xs ${cls}`} title={p}>{prettyField(p)}</span>)}</div>
    </div>
  )
}

// ── tabs ───────────────────────────────────────────────────────────────────

function OverviewTab({ packet }: { packet: ReviewPacket }) {
  const s = packet.student
  return (
    <Card className="p-5 space-y-4">
      <h3 className="font-semibold text-foreground">Application overview</h3>
      <div className="grid grid-cols-2 gap-4 text-sm">
        <div><span className="text-muted-foreground">Status:</span> <span className="ml-1 text-foreground">{packet.status}</span></div>
        <div><span className="text-muted-foreground">Decision:</span> <span className="ml-1 text-foreground">{packet.decision?.decision ?? 'Pending'}</span></div>
        <div><span className="text-muted-foreground">Completeness:</span> <span className="ml-1 text-foreground">{packet.completeness_status ?? 'N/A'}</span></div>
        <div><span className="text-muted-foreground">Match:</span> <span className="ml-1 text-foreground">{packet.match_score != null ? pctScore(packet.match_score) : '—'}</span></div>
      </div>
      {s.bio && <Section title="Bio"><p className="text-sm text-foreground whitespace-pre-wrap">{s.bio}</p></Section>}
      {s.goals && <Section title="Goals"><p className="text-sm text-foreground whitespace-pre-wrap">{s.goals}</p></Section>}
      {s.academics.length > 0 && (
        <Section title="Academics">
          <div className="space-y-1.5">
            {s.academics.map((a, i) => (
              <div key={i} className="flex items-center justify-between text-sm">
                <span className="text-foreground">{[a.degree, a.field].filter(Boolean).join(', ') || '—'} <span className="text-muted-foreground">· {a.institution ?? '—'}</span></span>
                {a.gpa && <span className="font-mono text-muted-foreground">GPA {a.gpa}</span>}
              </div>
            ))}
          </div>
        </Section>
      )}
      {s.activities.length > 0 && (
        <Section title="Activities">
          <ul className="list-disc list-inside text-sm text-foreground space-y-0.5">
            {s.activities.map((a, i) => <li key={i}>{a.title ?? a.type} {a.organization ? <span className="text-muted-foreground">· {a.organization}</span> : null}</li>)}
          </ul>
        </Section>
      )}
    </Card>
  )
}

function ScoresTab({ packet, synthesis, onSynthesize, synthLoading }: { packet: ReviewPacket; synthesis: ReviewSynthesis | null; onSynthesize: () => void; synthLoading: boolean }) {
  const rows = packet.rubric_scores
  const reviewers = packet.reviewer_notes
  const [expandedCriterion, setExpandedCriterion] = useState<string | null>(null)
  if (packet.reviewer_count === 0) {
    return <Card className="p-6"><p className="text-sm text-muted-foreground text-center">No one has scored this applicant yet.</p></Card>
  }
  return (
    <div className="space-y-4">
      <Card className="p-0 overflow-x-auto">
        <table className="w-full text-sm border-collapse">
          <thead>
            <tr className="border-b border-border bg-muted/50">
              <th className="text-left px-3 py-2 font-medium text-muted-foreground sticky left-0 bg-muted/50">Criterion</th>
              {reviewers.map(r => <th key={r.reviewer_id} className="text-center px-3 py-2 font-medium text-foreground min-w-[90px]">{r.reviewer_name}</th>)}
              <th className="text-center px-3 py-2 font-medium text-muted-foreground">Δ</th>
            </tr>
          </thead>
          <tbody>
            {rows.map(row => (
              <Fragment key={row.criterion}>
                <tr className={`border-b border-border ${row.divergent ? 'bg-warning-soft/50' : ''}`}>
                  <td className="px-3 py-2 sticky left-0 bg-card">
                    <button type="button" onClick={() => setExpandedCriterion(expandedCriterion === row.criterion ? null : row.criterion)} className="text-left">
                      <span className="font-medium text-foreground">{row.criterion}</span>
                      {row.weight != null && <span className="text-muted-foreground"> · {Math.round(row.weight * 100)}%</span>}
                      {row.per_reviewer.some(p => p.note) && (
                        <span className="ml-1 text-[10px] text-cobalt">{expandedCriterion === row.criterion ? '▼ notes' : '▶ notes'}</span>
                      )}
                    </button>
                  </td>
                  {reviewers.map(rv => {
                    const cell = row.per_reviewer.find(p => p.reviewer_id === rv.reviewer_id)
                    const isMax = cell && cell.score === row.max_score
                    return <td key={rv.reviewer_id} className={`text-center px-3 py-2 font-semibold tabular-nums ${isMax ? 'text-gold-hover' : 'text-cobalt'}`}>{cell ? cell.score : '—'}</td>
                  })}
                  <td className="text-center px-3 py-2">
                    {row.divergent
                      ? <span className="inline-flex items-center gap-1 text-warning text-xs font-medium"><AlertTriangle size={12} />{row.variance}</span>
                      : <span className="text-muted-foreground text-xs tabular-nums">{row.variance}</span>}
                  </td>
                </tr>
                {expandedCriterion === row.criterion && row.per_reviewer.some(p => p.note) && (
                  <tr key={`${row.criterion}-notes`} className="border-b border-border bg-muted/30">
                    <td colSpan={reviewers.length + 2} className="px-3 py-2">
                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                        {row.per_reviewer.filter(p => p.note).map(p => (
                          <div key={p.reviewer_id} className="text-xs">
                            <span className="font-medium text-foreground">{p.reviewer_name}:</span>{' '}
                            <span className="text-muted-foreground">{p.note}</span>
                          </div>
                        ))}
                      </div>
                    </td>
                  </tr>
                )}
              </Fragment>
            ))}
          </tbody>
        </table>
      </Card>

      {reviewers.some(r => r.note) && (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          {reviewers.filter(r => r.note).map(r => (
            <Card key={r.reviewer_id} className="p-3">
              <div className="flex items-center justify-between mb-1">
                <span className="text-sm font-medium text-foreground">{r.reviewer_name}</span>
                {r.total_weighted_score != null && <Badge variant="info">{r.total_weighted_score.toFixed(1)}</Badge>}
              </div>
              <p className="text-xs text-muted-foreground whitespace-pre-wrap">{r.note}</p>
            </Card>
          ))}
        </div>
      )}

      {packet.reviewer_count >= 2 && (
        <Card className="p-4 space-y-3">
          <div className="flex items-center justify-between gap-2 flex-wrap">
            <div className="flex items-center gap-2">
              <AIBadge label="AI synthesis" fallback={synthesis?.model_used === 'rule_based'} />
              <h3 className="text-sm font-semibold text-foreground">Synthesized recommendation</h3>
              {synthesis && <Badge variant={synthesis.agreement === 'divergent' ? 'warning' : synthesis.agreement === 'high' ? 'success' : 'info'}>{synthesis.agreement}</Badge>}
            </div>
            <Button variant="secondary" size="sm" onClick={onSynthesize} disabled={synthLoading} className="flex items-center gap-1"><RefreshCw size={13} className={synthLoading ? 'animate-spin' : ''} />{synthesis ? 'Re-synthesize' : 'Synthesize'}</Button>
          </div>
          {!synthesis ? (
            <p className="text-sm text-muted-foreground">Generate a balanced cross-reviewer recommendation. Advisory only — the committee decides.</p>
          ) : (
            <>
              <p className="text-sm text-foreground whitespace-pre-wrap">{synthesis.overall_recommendation}</p>
              {synthesis.per_criterion.length > 0 && (
                <div className="space-y-1.5 border-t border-border pt-2">
                  {synthesis.per_criterion.map((p, i) => (
                    <div key={i} className="text-xs"><span className={`font-medium ${p.divergent ? 'text-warning' : 'text-foreground'}`}>{p.criterion_name}:</span> <span className="text-muted-foreground">{p.synthesis}</span></div>
                  ))}
                </div>
              )}
            </>
          )}
        </Card>
      )}
    </div>
  )
}

function AISummaryTab({ packet, regen, regenPending, matchRationale, matchLoading, assistantPrompt, setAssistantPrompt, onAsk, asking, reply }: {
  packet: ReviewPacket; regen: () => void; regenPending: boolean; matchRationale?: InstitutionMatchRationale; matchLoading: boolean
  assistantPrompt: string; setAssistantPrompt: (v: string) => void; onAsk: () => void; asking: boolean; reply: { answer: string; fallback: boolean } | null
}) {
  const p = packet.ai_packet_summary
  const isFallback = !p || p.model_used === 'rule_based'
  return (
    <>
      <Card className="p-5 space-y-4">
        <div className="flex items-center justify-between gap-2 flex-wrap">
          <div className="flex items-center gap-2">
            <AIBadge label="AI packet summary" fallback={isFallback} />
            {p?.confidence_level && <Badge variant={p.confidence_level === 'high' ? 'success' : p.confidence_level === 'medium' ? 'info' : 'warning'}><Shield size={10} className="mr-1" />{p.confidence_level} confidence</Badge>}
          </div>
          <Button variant="ghost" size="sm" onClick={regen} disabled={regenPending} className="flex items-center gap-1"><RefreshCw size={14} className={regenPending ? 'animate-spin' : ''} /> {regenPending ? 'Generating…' : 'Regenerate'}</Button>
        </div>
        {isFallback && p && (
          <div className="flex items-center gap-2 rounded-md border border-warning/30 bg-warning-soft px-3 py-2 text-xs text-warning"><AlertTriangle size={13} /> Showing a rule-based summary. Enable the review model for the full Opus summary.</div>
        )}
        {!p ? (
          <p className="text-sm text-muted-foreground">No AI summary yet. Click Regenerate to create one.</p>
        ) : (
          <div className="space-y-4">
            <div className="rounded-lg bg-muted/60 p-4"><p className="text-sm text-foreground whitespace-pre-wrap">{p.overall_summary}</p></div>
            {p.recommended_score != null && <div className="flex items-center gap-2 text-sm"><span className="text-muted-foreground">Recommended score:</span><span className="text-lg font-bold text-cobalt">{p.recommended_score.toFixed(1)}</span><span className="text-muted-foreground">/ 10</span></div>}
            {p.strengths && p.strengths.length > 0 && (
              <div>
                <h4 className="text-sm font-medium text-success mb-2">Signal strengths</h4>
                <div className="space-y-2">{p.strengths.map((s, i) => <div key={i} className="rounded bg-success-soft px-2.5 py-2"><p className="text-sm text-foreground">{s.text}</p>{s.evidence && <p className="text-xs text-success mt-1 font-mono">{s.source_field}: {s.evidence}</p>}</div>)}</div>
              </div>
            )}
            {p.concerns && p.concerns.length > 0 && (
              <div>
                <h4 className="text-sm font-medium text-error mb-2">Signal weaknesses</h4>
                <div className="space-y-2">{p.concerns.map((c, i) => <div key={i} className="rounded bg-error-soft px-2.5 py-2"><p className="text-sm text-foreground">{c.text}</p>{c.evidence && <p className="text-xs text-error mt-1 font-mono">{c.source_field}: {c.evidence}</p>}</div>)}</div>
              </div>
            )}
            {p.criterion_assessments && p.criterion_assessments.length > 0 && (
              <div>
                <h4 className="text-sm font-medium text-muted-foreground mb-2">Rubric notes (AI-prefilled, editable when scoring)</h4>
                <div className="rounded-lg border border-border overflow-hidden">
                  {p.criterion_assessments.map((ca, i) => (
                    <div key={i} className={`p-3 ${i > 0 ? 'border-t border-border' : ''}`}>
                      <div className="flex items-center justify-between mb-1"><span className="text-sm font-medium text-foreground">{ca.criterion_name}</span>{ca.score != null && <Badge variant={ca.score >= 7 ? 'success' : ca.score >= 4 ? 'info' : 'warning'}>{ca.score}/10</Badge>}</div>
                      <p className="text-sm text-muted-foreground">{ca.assessment}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}
            {p.model_used && <p className="text-xs text-muted-foreground">Model: {p.model_used} · Generated: {p.generated_at ? new Date(p.generated_at).toLocaleString() : 'N/A'}</p>}
          </div>
        )}

        <div className="border-t border-border pt-4">
          <div className="flex items-center gap-2 mb-2"><AIBadge label="AI assistant" /><h4 className="text-sm font-medium text-foreground">Ask about this applicant</h4></div>
          <div className="flex gap-2">
            <Input value={assistantPrompt} onChange={e => setAssistantPrompt(e.target.value)} placeholder="e.g. What's their strongest signal?" className="flex-1"
              onKeyDown={(e: KeyboardEvent) => { if (e.key === 'Enter' && assistantPrompt.trim()) onAsk() }} />
            <Button onClick={onAsk} disabled={asking || !assistantPrompt.trim()} className="flex items-center gap-1"><Send size={14} />{asking ? 'Thinking…' : 'Ask'}</Button>
          </div>
          {reply && (
            <div className="mt-3 rounded border border-border bg-muted/60 p-3">
              {reply.fallback && <div className="mb-1 text-[11px] text-warning">Showing a rule-based answer.</div>}
              <p className="text-sm text-foreground whitespace-pre-wrap">{reply.answer}</p>
            </div>
          )}
        </div>
      </Card>

      <Card className="p-5 space-y-3">
        <div className="flex items-center gap-2"><Brain size={18} className="text-cobalt" /><h3 className="font-semibold text-foreground">Match rationale — full evidence view</h3><Badge variant="info"><Shield size={10} className="mr-1" />Reviewer-only</Badge></div>
        <p className="text-xs text-muted-foreground">The applicant sees a redacted version of this. Comparative and internal matching signals shown here are withheld from the student (Spec 06 §3).</p>
        {matchLoading ? <Skeleton className="h-24" /> : !matchRationale?.available ? (
          <p className="text-sm text-muted-foreground">No match rationale yet — the applicant hasn't completed Discovery / matching.</p>
        ) : (
          <div className="space-y-3">
            <p className="text-sm text-foreground whitespace-pre-wrap">{matchRationale.rationale_text}</p>
            <div className="flex flex-wrap gap-4 text-sm">
              {matchRationale.fitness_score != null && <span className="text-muted-foreground">Fitness: <b className="text-cobalt">{pctScore(matchRationale.fitness_score)}</b></span>}
              {matchRationale.confidence_score != null && <span className="text-muted-foreground">Confidence: <b className="text-cobalt">{pctScore(matchRationale.confidence_score)}</b></span>}
              {!matchRationale.grounded && <Badge variant="warning">Ungrounded — verify before relying</Badge>}
            </div>
            {matchRationale.cited_student_fields?.length > 0 && <CitationChips title="Cited student signals" items={matchRationale.cited_student_fields} tone="green" />}
            {matchRationale.cited_program_fields?.length > 0 && <CitationChips title="Cited program signals (incl. comparative)" items={matchRationale.cited_program_fields} tone="slate" />}
          </div>
        )}
      </Card>
    </>
  )
}

function IntegrityTab({ packet, onScan, scanning, onAction, actionPending, locked }: {
  packet: ReviewPacket; onScan: () => void; scanning: boolean; onAction: (id: string, action: IntegrityAction) => void; actionPending: boolean; locked: boolean
}) {
  const signals = packet.integrity_signals
  const open = signals.filter(s => s.status === 'open').length
  return (
    <Card className="p-5 space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2"><Shield size={18} className="text-warning" /><h3 className="font-semibold text-foreground">Integrity signals</h3>{open > 0 && <Badge variant="warning">{open} open</Badge>}</div>
        <Button variant="secondary" size="sm" onClick={onScan} disabled={scanning} className="flex items-center gap-1"><RefreshCw size={14} className={scanning ? 'animate-spin' : ''} />{scanning ? 'Scanning…' : 'Run scan'}</Button>
      </div>
      {signals.length === 0 ? (
        <div className="text-center py-8"><CheckCircle2 size={32} className="mx-auto mb-2 text-success" /><p className="text-sm text-muted-foreground">No integrity signals detected. Run a scan to check.</p></div>
      ) : (
        <div className="space-y-2">
          {signals.map(sig => (
            <div key={sig.id} className={`rounded-lg border border-border p-3 ${sig.status !== 'open' ? 'opacity-70' : ''}`}>
              <div className="flex items-center gap-2 flex-wrap mb-1">
                <span className={`w-2 h-2 rounded-full ${SEVERITY_DOT[sig.severity] ?? 'bg-muted'}`} />
                <span className="text-sm font-medium text-foreground">{sig.title}</span>
                <Badge variant={sig.severity === 'high' ? 'error' : sig.severity === 'medium' ? 'warning' : 'neutral'}>{sig.severity}</Badge>
                <Badge variant="neutral">{sig.signal_type.replace(/_/g, ' ')}</Badge>
                {sig.status !== 'open' && <Badge variant={sig.status === 'rejected' ? 'error' : 'info'}>{sig.status}</Badge>}
              </div>
              <p className="text-sm text-muted-foreground ml-4">{sig.description}</p>
              {sig.status === 'open' && (
                <div className="ml-4 mt-2 flex flex-wrap gap-2">
                  <Button variant="tertiary" size="sm" disabled={actionPending} onClick={() => onAction(sig.id, 'acknowledge')}>Acknowledge</Button>
                  <Button variant="tertiary" size="sm" disabled={actionPending} onClick={() => onAction(sig.id, 'clarify')}>Request clarification</Button>
                  <Button variant="destructive" size="sm" disabled={actionPending || locked} onClick={() => onAction(sig.id, 'reject_application')}>Reject application</Button>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </Card>
  )
}

function DocumentsTab({ packet }: { packet: ReviewPacket }) {
  if (packet.documents.length === 0) return <Card className="p-6"><p className="text-sm text-muted-foreground text-center">No documents uploaded.</p></Card>
  return (
    <Card className="p-4 space-y-2">
      {packet.documents.map(d => (
        <div key={d.id} className="flex items-center justify-between rounded-lg border border-border px-3 py-2">
          <div className="flex items-center gap-2 min-w-0">
            <FileText size={16} className="text-cobalt shrink-0" />
            <div className="min-w-0"><p className="text-sm text-foreground truncate">{d.file_name}</p><p className="text-xs text-muted-foreground">{d.document_type?.replace(/_/g, ' ')} · {d.uploaded_at ? formatDate(d.uploaded_at) : ''}</p></div>
          </div>
          {d.file_url && <a href={d.file_url} target="_blank" rel="noreferrer" className="text-sm text-cobalt hover:underline shrink-0">Open</a>}
        </div>
      ))}
    </Card>
  )
}

function EssaysTab({ packet }: { packet: ReviewPacket }) {
  if (packet.essays.length === 0) return <Card className="p-6"><p className="text-sm text-muted-foreground text-center">No essays submitted for this program.</p></Card>
  return (
    <div className="space-y-3">
      {packet.essays.map(e => (
        <Card key={e.id} className="p-4 space-y-2">
          <div className="flex items-center justify-between gap-2">
            <p className="text-sm font-medium text-foreground">{e.prompt_text ?? 'Essay'}</p>
            <div className="flex items-center gap-2 shrink-0">{e.status && <Badge variant="neutral">{e.status}</Badge>}{e.word_count != null && <span className="text-xs text-muted-foreground">{e.word_count} words</span>}</div>
          </div>
          {e.content && <p className="text-sm text-foreground whitespace-pre-wrap border-t border-border pt-2">{e.content}</p>}
        </Card>
      ))}
    </div>
  )
}

function TimelineTab({ packet }: { packet: ReviewPacket }) {
  const events: { at: string | null; label: string; icon: typeof Send }[] = []
  if (packet.submitted_at) events.push({ at: packet.submitted_at, label: 'Application submitted', icon: Send })
  for (const r of packet.reviewer_notes) if (r.scored_at) events.push({ at: r.scored_at, label: `Scored by ${r.reviewer_name}${r.total_weighted_score != null ? ` (${r.total_weighted_score.toFixed(1)})` : ''}`, icon: Star })
  if (packet.decision?.decision_at) events.push({ at: packet.decision.decision_at, label: `Decision: ${packet.decision.decision}`, icon: Award })
  events.sort((a, b) => (a.at ?? '').localeCompare(b.at ?? ''))
  if (events.length === 0) return <Card className="p-6"><p className="text-sm text-muted-foreground text-center">No timeline events yet.</p></Card>
  return (
    <Card className="p-5">
      <ol className="relative border-l border-border ml-3 space-y-5">
        {events.map((ev, i) => {
          const Icon = ev.icon
          return (
            <li key={i} className="ml-5">
              <span className="absolute -left-[9px] flex h-4 w-4 items-center justify-center rounded-full bg-cobalt"><Icon size={9} className="text-white" /></span>
              <p className="text-sm text-foreground">{ev.label}</p>
              <p className="text-xs text-muted-foreground">{ev.at ? new Date(ev.at).toLocaleString() : ''}</p>
            </li>
          )
        })}
      </ol>
    </Card>
  )
}
