import { useState } from 'react'
import { useParams } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { User, Star, Brain, ClipboardCheck, Calendar, Award, FileText } from 'lucide-react'
import { reviewApplication, makeDecision, createOffer } from '../../api/applications-admin'
import { chatInstitutionAssistant } from '../../api/institutions'
import { getScores, getAISummary, assignReviewer, scoreApplication, getRubrics } from '../../api/reviews'
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
import type { ApplicationScore, AIReviewSummary, Rubric } from '../../types'

export default function StudentDetailPage() {
  const { studentId } = useParams<{ studentId: string }>()
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
  const [reviewerNotes, setReviewerNotes] = useState('')
  const [assistantPrompt, setAssistantPrompt] = useState('')
  const [assistantReply, setAssistantReply] = useState<string | null>(null)

  const applicationQ = useQuery({
    queryKey: ['application-review', studentId],
    queryFn: () => reviewApplication(studentId!),
    enabled: !!studentId,
  })

  const scoresQ = useQuery({
    queryKey: ['application-scores', studentId],
    queryFn: () => getScores(studentId!),
    enabled: !!studentId && activeTab === 'scores',
  })

  const aiQ = useQuery({
    queryKey: ['ai-summary', studentId],
    queryFn: () => getAISummary(studentId!),
    enabled: !!studentId && activeTab === 'ai',
  })

  const rubricsQ = useQuery({
    queryKey: ['rubrics'],
    queryFn: () => getRubrics(),
    enabled: showScoringModal,
  })

  const app = applicationQ.data
  const scores: ApplicationScore[] = Array.isArray(scoresQ.data) ? scoresQ.data : []
  const aiSummary: AIReviewSummary | undefined = aiQ.data
  const rubrics: Rubric[] = Array.isArray(rubricsQ.data) ? rubricsQ.data : []

  const assignMut = useMutation({
    mutationFn: () => assignReviewer(studentId!),
    onSuccess: () => { showToast('Reviewer assigned', 'success'); queryClient.invalidateQueries({ queryKey: ['application-review', studentId] }) },
    onError: () => showToast('Failed to assign reviewer', 'error'),
  })

  const decisionMut = useMutation({
    mutationFn: () => makeDecision(studentId!, { decision: decision as any, decision_notes: decisionNotes || null }),
    onSuccess: () => {
      showToast('Decision recorded', 'success')
      setShowDecisionModal(false)
      queryClient.invalidateQueries({ queryKey: ['application-review', studentId] })
    },
    onError: () => showToast('Failed to record decision', 'error'),
  })

  const offerMut = useMutation({
    mutationFn: () => createOffer(studentId!, {
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
    mutationFn: () => scoreApplication(studentId!, { rubric_id: selectedRubric, criterion_scores: criterionScores, reviewer_notes: reviewerNotes || null }),
    onSuccess: () => {
      showToast('Score submitted', 'success')
      setShowScoringModal(false)
      queryClient.invalidateQueries({ queryKey: ['application-scores', studentId] })
    },
    onError: () => showToast('Failed to submit score', 'error'),
  })
  const assistantMut = useMutation({
    mutationFn: () => chatInstitutionAssistant(assistantPrompt, app.program_id),
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
  ]

  const currentRubric = rubrics.find(r => r.id === selectedRubric)

  return (
    <div className="p-6">
      <div className="grid grid-cols-3 gap-6">
        {/* Left: Snapshot */}
        <div className="col-span-1 space-y-4">
          <Card className="p-5">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-12 h-12 bg-indigo-100 rounded-full flex items-center justify-center">
                <User size={24} className="text-indigo-600" />
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
                  <span className="absolute inset-0 flex items-center justify-center text-sm font-bold text-indigo-600">
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
                <div className="flex items-center gap-2">
                  <Brain size={20} className="text-indigo-600" />
                  <h3 className="font-semibold text-gray-900">AI Insights</h3>
                </div>
                {aiQ.isLoading ? (
                  <Skeleton className="h-32" />
                ) : !aiSummary ? (
                  <p className="text-sm text-gray-500">AI summary not available.</p>
                ) : (
                  <>
                    <p className="text-sm text-gray-700">{aiSummary.summary}</p>
                    {aiSummary.strengths.length > 0 && (
                      <div>
                        <h4 className="text-sm font-medium text-green-700 mb-1">Strengths</h4>
                        <ul className="list-disc list-inside text-sm text-gray-600">
                          {aiSummary.strengths.map((s, i) => <li key={i}>{s}</li>)}
                        </ul>
                      </div>
                    )}
                    {aiSummary.concerns.length > 0 && (
                      <div>
                        <h4 className="text-sm font-medium text-red-700 mb-1">Concerns</h4>
                        <ul className="list-disc list-inside text-sm text-gray-600">
                          {aiSummary.concerns.map((c, i) => <li key={i}>{c}</li>)}
                        </ul>
                      </div>
                    )}
                    {aiSummary.recommended_score_range && (
                      <p className="text-sm text-gray-600">
                        Recommended score range: <strong>{aiSummary.recommended_score_range.min}-{aiSummary.recommended_score_range.max}</strong>
                      </p>
                    )}
                  </>
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
          <Select
            label="Rubric"
            options={rubrics.map(r => ({ value: r.id, label: r.rubric_name }))}
            placeholder="Select rubric"
            value={selectedRubric}
            onChange={e => {
              setSelectedRubric(e.target.value)
              setCriterionScores({})
            }}
          />
          {currentRubric?.criteria && (
            <div className="space-y-2">
              {currentRubric.criteria.map(c => (
                <div key={c.name} className="flex items-center gap-3">
                  <span className="text-sm text-gray-700 w-40">{c.name} ({c.weight}%)</span>
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
              ))}
            </div>
          )}
          <Textarea label="Reviewer Notes" value={reviewerNotes} onChange={e => setReviewerNotes(e.target.value)} rows={3} />
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
