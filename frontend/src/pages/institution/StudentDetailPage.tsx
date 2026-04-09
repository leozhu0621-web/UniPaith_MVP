import { useState } from 'react'
import { useParams } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { User, Star, Brain, ClipboardCheck, Calendar, Award, FileText, RefreshCw, Shield } from 'lucide-react'
import { reviewApplication, makeDecision, createOffer } from '../../api/applications-admin'
import { chatInstitutionAssistant, generateAIDraft, sendFromTemplate } from '../../api/institutions'
import { getScores, getAISummary, assignReviewer, scoreApplication, getRubrics, getAIPacketSummary, regenerateAIPacketSummary, getAIPrefill, scanIntegrity, getIntegritySignals, resolveIntegritySignal } from '../../api/reviews'
import Card from '../../components/ui/Card'
import Badge from '../../components/ui/Badge'
import Button from '../../components/ui/Button'
import Tabs from '../../components/ui/Tabs'
import Modal from '../../components/ui/Modal'
import Input from '../../components/ui/Input'
import Textarea from '../../components/ui/Textarea'
import Select from '../../components/ui/Select'
import Skeleton from '../../components/ui/Skeleton'
import { showToast } from '../../stores/toast-store'
import { formatDate, formatScore } from '../../utils/format'
import { STATUS_COLORS, DECISION_OPTIONS } from '../../utils/constants'
import type { AIPacketSummary, ApplicationScore, AIReviewSummary, IntegritySignal, Rubric } from '../../types'

export default function StudentDetailPage() {
  const { appId, studentId } = useParams<{ appId?: string; studentId?: string }>()
  const applicationId = appId ?? studentId
  const queryClient = useQueryClient()
  const [activeTab, setActiveTab] = useState('overview')
  const [showDecisionModal, setShowDecisionModal] = useState(false)
  const [showOfferModal, setShowOfferModal] = useState(false)
  const [showScoringModal, setShowScoringModal] = useState(false)
  const [decision, setDecision] = useState('')
  const [decisionNotes, setDecisionNotes] = useState('')
  const [offerType, setOfferType] = useState('full_admission')
  const [tuitionAmount, setTuitionAmount] = useState('')
  const [scholarshipAmount, setScholarshipAmount] = useState('')
  const [responseDeadline, setResponseDeadline] = useState('')
  const [selectedRubric, setSelectedRubric] = useState('')
  const [criterionScores, setCriterionScores] = useState<Record<string, number>>({})
  const [criterionNotes, setCriterionNotes] = useState<Record<string, string>>({})
  const [reviewerNotes, setReviewerNotes] = useState('')
  const [prefilling, setPrefilling] = useState(false)
  const [assistantPrompt, setAssistantPrompt] = useState('')
  const [assistantReply, setAssistantReply] = useState<string | null>(null)
  const [showDraftModal, setShowDraftModal] = useState(false)
  const [draftType, setDraftType] = useState('missing_items')
  const [draftSubject, setDraftSubject] = useState('')
  const [draftBody, setDraftBody] = useState('')
  const [draftLoading, setDraftLoading] = useState(false)

  const applicationQ = useQuery({
    queryKey: ['application-review', applicationId],
    queryFn: () => reviewApplication(applicationId!),
    enabled: !!applicationId,
  })

  const scoresQ = useQuery({
    queryKey: ['application-scores', applicationId],
    queryFn: () => getScores(applicationId!),
    enabled: !!applicationId && activeTab === 'scores',
  })

  const aiQ = useQuery({
    queryKey: ['ai-summary', applicationId],
    queryFn: () => getAISummary(applicationId!),
    enabled: !!applicationId && activeTab === 'ai',
  })

  const rubricsQ = useQuery({
    queryKey: ['rubrics'],
    queryFn: () => getRubrics(),
    enabled: showScoringModal,
  })

  const [packetRubricId, setPacketRubricId] = useState<string>('')

  const packetQ = useQuery({
    queryKey: ['ai-packet', applicationId, packetRubricId],
    queryFn: () => getAIPacketSummary(applicationId!, packetRubricId || undefined),
    enabled: !!applicationId && activeTab === 'ai',
  })
  const packet: AIPacketSummary | undefined = packetQ.data

  const regenMut = useMutation({
    mutationFn: () => regenerateAIPacketSummary(applicationId!, packetRubricId || undefined),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['ai-packet'] })
      showToast('AI summary regenerated', 'success')
    },
  })

  const integrityQ = useQuery({
    queryKey: ['integrity-signals', applicationId],
    queryFn: () => getIntegritySignals(applicationId!),
    enabled: !!applicationId && activeTab === 'integrity',
  })
  const integritySignals: IntegritySignal[] = Array.isArray(integrityQ.data) ? integrityQ.data : []

  const scanMut = useMutation({
    mutationFn: () => scanIntegrity(applicationId!),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['integrity-signals'] })
      showToast('Integrity scan complete', 'success')
    },
  })

  const resolveMut = useMutation({
    mutationFn: (signalId: string) => resolveIntegritySignal(signalId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['integrity-signals'] })
      showToast('Signal resolved', 'success')
    },
  })

  const app = applicationQ.data
  const scores: ApplicationScore[] = Array.isArray(scoresQ.data) ? scoresQ.data : []
  const aiSummary: AIReviewSummary | undefined = aiQ.data
  const rubrics: Rubric[] = Array.isArray(rubricsQ.data) ? rubricsQ.data : []

  const assignMut = useMutation({
    mutationFn: () => assignReviewer(applicationId!),
    onSuccess: () => { showToast('Reviewer assigned', 'success'); queryClient.invalidateQueries({ queryKey: ['application-review', applicationId] }) },
    onError: () => showToast('Failed to assign reviewer', 'error'),
  })

  const decisionMut = useMutation({
    mutationFn: () => makeDecision(applicationId!, { decision: decision as any, decision_notes: decisionNotes || null }),
    onSuccess: () => {
      showToast('Decision recorded', 'success')
      setShowDecisionModal(false)
      queryClient.invalidateQueries({ queryKey: ['application-review', applicationId] })
    },
    onError: () => showToast('Failed to record decision', 'error'),
  })

  const offerMut = useMutation({
    mutationFn: () => createOffer(applicationId!, {
      offer_type: offerType as any,
      tuition_amount: tuitionAmount ? Number(tuitionAmount) : null,
      scholarship_amount: scholarshipAmount ? Number(scholarshipAmount) : 0,
      response_deadline: responseDeadline || null,
    }),
    onSuccess: () => {
      showToast('Offer created', 'success')
      setShowOfferModal(false)
    },
    onError: () => showToast('Failed to create offer', 'error'),
  })

  const scoreMut = useMutation({
    mutationFn: () => scoreApplication(applicationId!, { rubric_id: selectedRubric, criterion_scores: criterionScores, reviewer_notes: reviewerNotes || null }),
    onSuccess: () => {
      showToast('Score submitted', 'success')
      setShowScoringModal(false)
      queryClient.invalidateQueries({ queryKey: ['application-scores', applicationId] })
    },
    onError: () => showToast('Failed to submit score', 'error'),
  })
  const assistantMut = useMutation({
    mutationFn: () => chatInstitutionAssistant(assistantPrompt, app?.program_id),
    onSuccess: (data) => setAssistantReply(data.reply),
    onError: () => showToast('Assistant request failed', 'error'),
  })

  if (applicationQ.isLoading) {
    return <div className="p-6 space-y-4"><Skeleton className="h-10 w-64" /><Skeleton className="h-64" /></div>
  }

  if (!app) {
    return <div className="p-6"><p className="text-gray-500">Application not found.</p></div>
  }

  const tabs = [
    { id: 'overview', label: 'Overview' },
    { id: 'scores', label: 'Scores' },
    { id: 'interview', label: 'Interview' },
    { id: 'ai', label: 'AI Insights' },
    { id: 'integrity', label: 'Integrity' },
  ]

  const currentRubric = rubrics.find(r => r.id === selectedRubric)

  return (
    <div className="p-6">
      <div className="grid grid-cols-3 gap-6">
        {/* Left: Snapshot */}
        <div className="col-span-1 space-y-4">
          <Card className="p-5">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-12 h-12 bg-brand-slate-100 rounded-full flex items-center justify-center">
                <User size={24} className="text-brand-slate-600" />
              </div>
              <div>
                <p className="font-semibold text-gray-900">{app.student_id.slice(0, 12)}...</p>
                <p className="text-sm text-gray-500">{app.program?.program_name ?? 'Program'}</p>
              </div>
            </div>

            {/* Match Score */}
            {app.match_score != null && (
              <div className="flex items-center justify-center mb-4">
                <div className="relative w-20 h-20">
                  <svg className="w-full h-full -rotate-90" viewBox="0 0 36 36">
                    <path d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" fill="none" stroke="#e5e7eb" strokeWidth="3" />
                    <path d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" fill="none" stroke="#6366f1" strokeWidth="3" strokeDasharray={`${app.match_score}, 100`} />
                  </svg>
                  <span className="absolute inset-0 flex items-center justify-center text-sm font-bold text-brand-slate-600">
                    {formatScore(app.match_score / 100)}
                  </span>
                </div>
              </div>
            )}

            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-500">Status</span>
                <Badge variant={(STATUS_COLORS[app.status] as any) ?? 'neutral'}>{app.status.replace('_', ' ')}</Badge>
              </div>
              {app.decision && (
                <div className="flex justify-between">
                  <span className="text-gray-500">Decision</span>
                  <Badge variant={(STATUS_COLORS[app.decision] as any) ?? 'neutral'}>{app.decision}</Badge>
                </div>
              )}
              <div className="flex justify-between">
                <span className="text-gray-500">Submitted</span>
                <span className="text-gray-700">{formatDate(app.submitted_at)}</span>
              </div>
            </div>
          </Card>

          {/* Actions */}
          <Card className="p-4 space-y-2">
            <h3 className="text-sm font-medium text-gray-700 mb-2">Actions</h3>
            <Button variant="secondary" className="w-full flex items-center gap-2" onClick={() => assignMut.mutate()} disabled={assignMut.isPending}>
              <ClipboardCheck size={16} /> Assign Reviewer
            </Button>
            <Button variant="secondary" className="w-full flex items-center gap-2" onClick={() => setShowScoringModal(true)}>
              <Star size={16} /> Score Application
            </Button>
            <Button variant="secondary" className="w-full flex items-center gap-2" onClick={() => {}}>
              <Calendar size={16} /> Schedule Interview
            </Button>
            <Button className="w-full flex items-center gap-2" onClick={() => setShowDecisionModal(true)}>
              <Award size={16} /> Make Decision
            </Button>
            <Button variant="secondary" className="w-full flex items-center gap-2" onClick={() => setShowDraftModal(true)}>
              <Brain size={16} /> AI Message Draft
            </Button>
            {app.decision === 'admitted' && (
              <Button variant="secondary" className="w-full flex items-center gap-2" onClick={() => setShowOfferModal(true)}>
                <FileText size={16} /> Create Offer
              </Button>
            )}
          </Card>
        </div>

        {/* Right: Tabs */}
        <div className="col-span-2">
          <Tabs tabs={tabs} activeTab={activeTab} onChange={setActiveTab} />
          <div className="mt-4">
            {activeTab === 'overview' && (
              <Card className="p-5 space-y-4">
                <h3 className="font-semibold text-gray-900">Application Overview</h3>
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div><span className="text-gray-500">Status:</span> <span className="ml-2 text-gray-900">{app.status}</span></div>
                  <div><span className="text-gray-500">Decision:</span> <span className="ml-2 text-gray-900">{app.decision ?? 'Pending'}</span></div>
                  <div><span className="text-gray-500">Completeness:</span> <span className="ml-2 text-gray-900">{app.completeness_status ?? 'N/A'}</span></div>
                </div>
                {app.match_reasoning_text && (
                  <div>
                    <h4 className="text-sm font-medium text-gray-700 mb-1">Match Reasoning</h4>
                    <p className="text-sm text-gray-600 bg-gray-50 rounded p-3">{app.match_reasoning_text}</p>
                  </div>
                )}
                {app.missing_items && app.missing_items.length > 0 && (
                  <div>
                    <h4 className="text-sm font-medium text-gray-700 mb-1">Missing Items</h4>
                    <ul className="list-disc list-inside text-sm text-red-600">
                      {app.missing_items.map((item, i) => <li key={i}>{item}</li>)}
                    </ul>
                  </div>
                )}
              </Card>
            )}

            {activeTab === 'scores' && (
              <Card className="p-5 space-y-4">
                <h3 className="font-semibold text-gray-900">Scores</h3>
                {scoresQ.isLoading ? (
                  <Skeleton className="h-32" />
                ) : scores.length === 0 ? (
                  <p className="text-sm text-gray-500">No scores yet.</p>
                ) : (
                  <div className="space-y-3">
                    {scores.map(s => (
                      <div key={s.id} className="border rounded p-3">
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-sm font-medium text-gray-900">Score: {s.total_weighted_score ?? 'N/A'}</span>
                          <Badge variant={s.scored_by_type === 'ai' ? 'info' : 'neutral'}>{s.scored_by_type ?? 'human'}</Badge>
                        </div>
                        {s.criterion_scores && (
                          <div className="grid grid-cols-2 gap-1 text-xs text-gray-600">
                            {Object.entries(s.criterion_scores).map(([k, v]) => (
                              <div key={k}>{k}: <strong>{v}</strong></div>
                            ))}
                          </div>
                        )}
                        {s.reviewer_notes && <p className="text-xs text-gray-500 mt-2">{s.reviewer_notes}</p>}
                      </div>
                    ))}
                  </div>
                )}
              </Card>
            )}

            {activeTab === 'interview' && (
              <Card className="p-5">
                <h3 className="font-semibold text-gray-900 mb-2">Interview</h3>
                <p className="text-sm text-gray-500">Interview management coming soon. Use the Schedule Interview action to propose times.</p>
              </Card>
            )}

            {activeTab === 'ai' && (
              <Card className="p-5 space-y-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Brain size={20} className="text-brand-slate-600" />
                    <h3 className="font-semibold text-gray-900">AI Packet Summary</h3>
                    {packet?.confidence_level && (
                      <Badge variant={packet.confidence_level === 'high' ? 'success' : packet.confidence_level === 'medium' ? 'info' : 'warning'}>
                        <Shield size={10} className="mr-1" />{packet.confidence_level} confidence
                      </Badge>
                    )}
                  </div>
                  <div className="flex items-center gap-2">
                    <Select label="" options={[{ value: '', label: 'No rubric' }, ...rubrics.map(r => ({ value: r.id, label: r.rubric_name }))]} value={packetRubricId} onChange={e => setPacketRubricId(e.target.value)} />
                    <Button variant="ghost" size="sm" onClick={() => regenMut.mutate()} disabled={regenMut.isPending} className="flex items-center gap-1">
                      <RefreshCw size={14} className={regenMut.isPending ? 'animate-spin' : ''} /> {regenMut.isPending ? 'Generating...' : 'Regenerate'}
                    </Button>
                  </div>
                </div>

                {packetQ.isLoading ? (
                  <Skeleton className="h-40" />
                ) : !packet ? (
                  <p className="text-sm text-gray-500">AI packet summary not available. Click Regenerate to create one.</p>
                ) : (
                  <div className="space-y-4">
                    <div className="bg-gray-50 rounded-lg p-4">
                      <p className="text-sm text-gray-700 whitespace-pre-wrap">{packet.overall_summary}</p>
                    </div>

                    {packet.recommended_score != null && (
                      <div className="flex items-center gap-2">
                        <span className="text-sm text-gray-500">Recommended Score:</span>
                        <span className="text-lg font-bold text-brand-slate-700">{packet.recommended_score.toFixed(1)}</span>
                        <span className="text-sm text-gray-400">/ 10</span>
                      </div>
                    )}

                    {packet.strengths && packet.strengths.length > 0 && (
                      <div>
                        <h4 className="text-sm font-medium text-green-700 mb-2">Strengths (with evidence)</h4>
                        <div className="space-y-2">
                          {packet.strengths.map((s, i) => (
                            <div key={i} className="bg-green-50 rounded p-2.5">
                              <p className="text-sm text-gray-800">{s.text}</p>
                              {s.evidence && <p className="text-xs text-green-600 mt-1 font-mono">{s.source_field}: {s.evidence}</p>}
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {packet.concerns && packet.concerns.length > 0 && (
                      <div>
                        <h4 className="text-sm font-medium text-red-700 mb-2">Concerns (with evidence)</h4>
                        <div className="space-y-2">
                          {packet.concerns.map((c, i) => (
                            <div key={i} className="bg-red-50 rounded p-2.5">
                              <p className="text-sm text-gray-800">{c.text}</p>
                              {c.evidence && <p className="text-xs text-red-600 mt-1 font-mono">{c.source_field}: {c.evidence}</p>}
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {packet.criterion_assessments && packet.criterion_assessments.length > 0 && (
                      <div>
                        <h4 className="text-sm font-medium text-gray-700 mb-2">Rubric Criterion Assessments</h4>
                        <div className="border rounded-lg overflow-hidden">
                          {packet.criterion_assessments.map((ca, i) => (
                            <div key={i} className={`p-3 ${i > 0 ? 'border-t' : ''}`}>
                              <div className="flex items-center justify-between mb-1">
                                <span className="text-sm font-medium text-gray-900">{ca.criterion_name}</span>
                                {ca.score != null && (
                                  <Badge variant={ca.score >= 7 ? 'success' : ca.score >= 4 ? 'info' : 'warning'}>
                                    {ca.score}/10
                                  </Badge>
                                )}
                              </div>
                              <p className="text-sm text-gray-600">{ca.assessment}</p>
                              {ca.evidence && ca.evidence.length > 0 && (
                                <div className="mt-1 flex flex-wrap gap-1">
                                  {ca.evidence.map((e, j) => (
                                    <span key={j} className="text-xs bg-blue-50 text-blue-700 px-1.5 py-0.5 rounded font-mono">
                                      {e.field}: {e.value}
                                    </span>
                                  ))}
                                </div>
                              )}
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {packet.model_used && (
                      <p className="text-xs text-gray-400">Model: {packet.model_used} | Generated: {packet.generated_at ? new Date(packet.generated_at).toLocaleString() : 'N/A'}</p>
                    )}
                  </div>
                )}

                <div className="border-t pt-4 mt-4">
                  <h4 className="text-sm font-medium text-gray-700 mb-2">Ask Institution Assistant (OpenAI)</h4>
                  <div className="flex gap-2">
                    <Input
                      value={assistantPrompt}
                      onChange={e => setAssistantPrompt(e.target.value)}
                      placeholder="Ask: How should we triage this applicant?"
                      className="flex-1"
                    />
                    <Button
                      onClick={() => assistantMut.mutate()}
                      disabled={assistantMut.isPending || !assistantPrompt.trim()}
                    >
                      {assistantMut.isPending ? 'Thinking...' : 'Ask AI'}
                    </Button>
                  </div>
                  {assistantReply && (
                    <div className="mt-3 bg-gray-50 border border-gray-200 rounded p-3">
                      <p className="text-sm text-gray-700 whitespace-pre-wrap">{assistantReply}</p>
                    </div>
                  )}
                </div>
              </Card>
            )}
          </div>
        </div>
      </div>

      {/* Integrity Tab */}
      {activeTab === 'integrity' && (
        <Card className="p-5 space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Shield size={20} className="text-amber-600" />
              <h3 className="font-semibold text-gray-900">Integrity Signals</h3>
              {integritySignals.filter(s => s.status === 'open').length > 0 && (
                <Badge variant="warning">{integritySignals.filter(s => s.status === 'open').length} open</Badge>
              )}
            </div>
            <Button variant="secondary" size="sm" onClick={() => scanMut.mutate()} disabled={scanMut.isPending} className="flex items-center gap-1">
              <RefreshCw size={14} className={scanMut.isPending ? 'animate-spin' : ''} />
              {scanMut.isPending ? 'Scanning...' : 'Run Integrity Scan'}
            </Button>
          </div>

          {integrityQ.isLoading ? (
            <Skeleton className="h-32" />
          ) : integritySignals.length === 0 ? (
            <div className="text-center py-6 text-gray-500">
              <Shield size={32} className="mx-auto mb-2 text-green-400" />
              <p className="text-sm">No integrity signals detected. Run a scan to check.</p>
            </div>
          ) : (
            <div className="space-y-2">
              {integritySignals.map(sig => (
                <div key={sig.id} className={`border rounded-lg p-3 ${sig.status === 'resolved' ? 'opacity-50' : ''}`}>
                  <div className="flex items-start justify-between mb-1">
                    <div className="flex items-center gap-2">
                      <span className={`w-2 h-2 rounded-full ${sig.severity === 'high' ? 'bg-red-500' : sig.severity === 'medium' ? 'bg-amber-500' : 'bg-blue-400'}`} />
                      <span className="text-sm font-medium text-gray-900">{sig.title}</span>
                      <Badge variant={sig.severity === 'high' ? 'warning' : 'neutral'}>{sig.severity}</Badge>
                      <Badge variant="neutral">{sig.signal_type.replace(/_/g, ' ')}</Badge>
                    </div>
                    {sig.status === 'open' && (
                      <Button variant="ghost" size="sm" onClick={() => resolveMut.mutate(sig.id)} disabled={resolveMut.isPending}>
                        Resolve
                      </Button>
                    )}
                  </div>
                  <p className="text-sm text-gray-600 ml-4">{sig.description}</p>
                  {sig.evidence && (
                    <div className="ml-4 mt-1 flex flex-wrap gap-1">
                      {Object.entries(sig.evidence).map(([k, v]) => (
                        <span key={k} className="text-xs bg-gray-100 text-gray-600 px-1.5 py-0.5 rounded font-mono">
                          {k}: {String(v)}
                        </span>
                      ))}
                    </div>
                  )}
                  {sig.status === 'resolved' && (
                    <p className="text-xs text-green-600 ml-4 mt-1">Resolved {sig.resolved_at ? new Date(sig.resolved_at).toLocaleDateString() : ''}</p>
                  )}
                </div>
              ))}
            </div>
          )}
        </Card>
      )}

      {/* AI Draft Modal */}
      <Modal isOpen={showDraftModal} onClose={() => setShowDraftModal(false)} title="AI Communication Draft" size="lg">
        <div className="space-y-4">
          <div className="flex items-end gap-3">
            <div className="flex-1">
              <Select label="Message Type" options={[
                { value: 'missing_items', label: 'Missing Items Request' },
                { value: 'interview_invite', label: 'Interview Invitation' },
                { value: 'clarification', label: 'Clarification Request' },
                { value: 'decision_admit', label: 'Admission Letter' },
                { value: 'decision_reject', label: 'Rejection Letter' },
                { value: 'decision_waitlist', label: 'Waitlist Notice' },
                { value: 'offer_notice', label: 'Offer Notice' },
              ]} value={draftType} onChange={e => setDraftType(e.target.value)} />
            </div>
            <Button
              variant="secondary"
              disabled={draftLoading}
              onClick={async () => {
                setDraftLoading(true)
                try {
                  const result = await generateAIDraft(applicationId!, draftType)
                  setDraftSubject(result.subject)
                  setDraftBody(result.body)
                  showToast('AI draft generated — edit before sending', 'success')
                } catch { showToast('Draft generation failed', 'error') }
                finally { setDraftLoading(false) }
              }}
              className="flex items-center gap-1 whitespace-nowrap"
            >
              <Brain size={14} /> {draftLoading ? 'Generating...' : 'Generate Draft'}
            </Button>
          </div>
          <Input label="Subject" value={draftSubject} onChange={e => setDraftSubject(e.target.value)} />
          <Textarea label="Message Body (editable)" value={draftBody} onChange={e => setDraftBody(e.target.value)} rows={8} />
          <p className="text-xs text-gray-400">Review and edit the AI-generated draft before sending.</p>
          <div className="flex justify-end gap-2">
            <Button variant="ghost" onClick={() => setShowDraftModal(false)}>Cancel</Button>
            <Button
              disabled={!draftSubject.trim() || !draftBody.trim()}
              onClick={() => {
                showToast('Message ready — use Send from Template to deliver', 'success')
                setShowDraftModal(false)
              }}
            >
              Done Editing
            </Button>
          </div>
        </div>
      </Modal>

      {/* Decision Modal */}
      <Modal isOpen={showDecisionModal} onClose={() => setShowDecisionModal(false)} title="Make Decision">
        <div className="space-y-4">
          <div className="space-y-2">
            {DECISION_OPTIONS.map(opt => (
              <label key={opt.value} className="flex items-center gap-2 cursor-pointer">
                <input type="radio" name="decision" value={opt.value} checked={decision === opt.value} onChange={e => setDecision(e.target.value)} />
                <span className="text-sm text-gray-700">{opt.label}</span>
              </label>
            ))}
          </div>
          <Textarea label="Notes" value={decisionNotes} onChange={e => setDecisionNotes(e.target.value)} rows={3} />
          <div className="flex justify-end gap-2">
            <Button variant="ghost" onClick={() => setShowDecisionModal(false)}>Cancel</Button>
            <Button onClick={() => decisionMut.mutate()} disabled={!decision || decisionMut.isPending}>
              {decisionMut.isPending ? 'Saving...' : 'Confirm Decision'}
            </Button>
          </div>
        </div>
      </Modal>

      {/* Offer Modal */}
      <Modal isOpen={showOfferModal} onClose={() => setShowOfferModal(false)} title="Create Offer">
        <div className="space-y-4">
          <Select
            label="Offer Type"
            options={[
              { value: 'full_admission', label: 'Full Admission' },
              { value: 'conditional', label: 'Conditional' },
              { value: 'waitlist_offer', label: 'Waitlist Offer' },
            ]}
            value={offerType}
            onChange={e => setOfferType(e.target.value)}
          />
          <Input label="Tuition Amount" type="number" value={tuitionAmount} onChange={e => setTuitionAmount(e.target.value)} />
          <Input label="Scholarship Amount" type="number" value={scholarshipAmount} onChange={e => setScholarshipAmount(e.target.value)} />
          <Input label="Response Deadline" type="date" value={responseDeadline} onChange={e => setResponseDeadline(e.target.value)} />
          <div className="flex justify-end gap-2">
            <Button variant="ghost" onClick={() => setShowOfferModal(false)}>Cancel</Button>
            <Button onClick={() => offerMut.mutate()} disabled={offerMut.isPending}>
              {offerMut.isPending ? 'Creating...' : 'Create Offer'}
            </Button>
          </div>
        </div>
      </Modal>

      {/* Scoring Modal */}
      <Modal isOpen={showScoringModal} onClose={() => setShowScoringModal(false)} title="Score Application" size="lg">
        <div className="space-y-4">
          <div className="flex items-end gap-3">
            <div className="flex-1">
              <Select
                label="Rubric"
                options={rubrics.map(r => ({ value: r.id, label: r.rubric_name }))}
                placeholder="Select rubric"
                value={selectedRubric}
                onChange={e => {
                  setSelectedRubric(e.target.value)
                  setCriterionScores({})
                  setCriterionNotes({})
                }}
              />
            </div>
            {selectedRubric && (
              <Button
                variant="secondary"
                size="sm"
                disabled={prefilling}
                onClick={async () => {
                  setPrefilling(true)
                  try {
                    const result = await getAIPrefill(applicationId!, selectedRubric)
                    const scores: Record<string, number> = {}
                    const notes: Record<string, string> = {}
                    for (const [name, data] of Object.entries(result.prefill)) {
                      if (data.suggested_score != null) scores[name] = data.suggested_score
                      if (data.suggested_note) notes[name] = data.suggested_note
                    }
                    setCriterionScores(scores)
                    setCriterionNotes(notes)
                    if (result.overall_note) setReviewerNotes(result.overall_note)
                    showToast('AI pre-fill applied — review and adjust scores', 'success')
                  } catch {
                    showToast('AI pre-fill failed', 'error')
                  } finally {
                    setPrefilling(false)
                  }
                }}
                className="flex items-center gap-1 whitespace-nowrap"
              >
                <Brain size={14} /> {prefilling ? 'AI Filling...' : 'AI Pre-fill'}
              </Button>
            )}
          </div>
          {currentRubric?.criteria && (
            <div className="space-y-3">
              {currentRubric.criteria.map(c => (
                <div key={c.name} className="border rounded-lg p-3">
                  <div className="flex items-center gap-3 mb-2">
                    <span className="text-sm font-medium text-gray-700 flex-1">{c.name} ({c.weight}%)</span>
                    <Input
                      type="number"
                      min={0}
                      max={100}
                      placeholder="0-100"
                      value={criterionScores[c.name] ?? ''}
                      onChange={e => setCriterionScores({ ...criterionScores, [c.name]: Number(e.target.value) })}
                      className="w-24"
                    />
                  </div>
                  <Textarea
                    label=""
                    value={criterionNotes[c.name] ?? ''}
                    onChange={e => setCriterionNotes({ ...criterionNotes, [c.name]: e.target.value })}
                    rows={2}
                    placeholder={`Notes for ${c.name}...`}
                    className="text-xs"
                  />
                </div>
              ))}
            </div>
          )}
          <Textarea label="Overall Reviewer Notes" value={reviewerNotes} onChange={e => setReviewerNotes(e.target.value)} rows={3} />
          <div className="flex justify-end gap-2">
            <Button variant="ghost" onClick={() => setShowScoringModal(false)}>Cancel</Button>
            <Button onClick={() => scoreMut.mutate()} disabled={!selectedRubric || scoreMut.isPending}>
              {scoreMut.isPending ? 'Submitting...' : 'Submit Score'}
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  )
}
