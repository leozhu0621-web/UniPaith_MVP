import { useState, useCallback, useEffect } from 'react'
import { useParams, useNavigate, useSearchParams } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  getMyApplication, submitApplication, getChecklist, generateChecklist,
  getReadiness, patchApplication, guardrailScan, toggleChecklistItem,
} from '../../api/applications'
import { listEssays, createEssay, updateEssay, requestEssayFeedback } from '../../api/essays'
import { listResumes, generateResume } from '../../api/resumes'
import { requestUpload, uploadToS3, confirmUpload, listDocuments } from '../../api/documents'
import { listRecommendations, sendRecommendationRequest } from '../../api/recommendations'
import Button from '../../components/ui/Button'
import Card from '../../components/ui/Card'
import Badge from '../../components/ui/Badge'
import Tabs from '../../components/ui/Tabs'
import Modal from '../../components/ui/Modal'
import Textarea from '../../components/ui/Textarea'
import Select from '../../components/ui/Select'
import ProgressBar from '../../components/ui/ProgressBar'
import Skeleton from '../../components/ui/Skeleton'
import { showToast } from '../../stores/toast-store'
import type { Interview } from '../../types'
import { STATUS_COLORS } from '../../utils/constants'
import { getMyInterviews } from '../../api/interviews'
import InterviewRespondPanel from './interviews/InterviewRespondPanel'
import {
  ArrowLeft, Check, Circle, Upload, Sparkles, AlertCircle, FileCheck, ListChecks,
  Users, AlertTriangle, ShieldCheck, Award, Send, Building2, CreditCard, Receipt, HandCoins, Download,
} from 'lucide-react'
import Breadcrumbs from '../../components/ui/Breadcrumbs'
import usePageTitle from '../../hooks/usePageTitle'
import OfferPanel from './apply/offer/OfferPanel'
import ApplyReadyChecklist from './apply/ApplyReadyChecklist'
import GraduateIntentCard from './apply/GraduateIntentCard'
import StudentAdvisorFit from './apply/StudentAdvisorFit'
import EnrollmentPanel from './apply/enrollment/EnrollmentPanel'
import { DECISION_STATE_LABEL } from './apply/offer/offerFormat'
import PaymentCheckout from '../../components/student/PaymentCheckout'
import {
  getCostTracker, payApplicationFee, requestFeeWaiver, isFeeClear, formatMoney, downloadReceipt,
  type CheckoutSession, type FeeView,
} from '../../api/payments'
import type { Application, Essay, Resume, ChecklistItem } from '../../types'

const STATUS_STEPS = ['draft', 'submitted', 'under_review', 'interview', 'decision_made']
const STATUS_STEP_LABELS: Record<string, string> = {
  draft: 'Draft',
  submitted: 'Submitted',
  under_review: 'Under review',
  interview: 'Interview',
  decision_made: 'Decision',
}

// Spec 15 §6.5 intent enum → friendly labels.
const INTENT_OPTIONS: { value: string; label: string }[] = [
  { value: 'career_fit', label: 'Career fit' },
  { value: 'dream', label: 'Dream school' },
  { value: 'back_up', label: 'Back-up option' },
  { value: 'cultural_fit', label: 'Cultural fit' },
  { value: 'family_input', label: 'Family input' },
  { value: 'other', label: 'Other' },
]
const RATIONALE_REQUIRED = ['back_up', 'other']

export default function ApplicationDetailPage() {
  const { appId } = useParams<{ appId: string }>()
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const checklistFocus = searchParams.get('checklist')
  const queryClient = useQueryClient()
  // Honor /s/applications/:id?tab=offer deep links (spec 18 §5).
  const [tab, setTab] = useState(searchParams.get('tab') || 'checklist')
  const [showEssayModal, setShowEssayModal] = useState(false)
  const [editingEssay, setEditingEssay] = useState<Essay | null>(null)
  const [essayContent, setEssayContent] = useState('')
  const [essayPrompt, setEssayPrompt] = useState('')
  const [essayType, setEssayType] = useState('personal_statement')

  // Upload state
  const [uploading, setUploading] = useState(false)
  const [uploadProgress, setUploadProgress] = useState(0)
  const [dragOver, setDragOver] = useState(false)

  // Readiness + submit gate state
  const [readiness, setReadiness] = useState<any>(null)
  const [showReadiness, setShowReadiness] = useState(false)
  const [markedReady, setMarkedReady] = useState(false)
  const [submitBlockers, setSubmitBlockers] = useState<string[] | null>(null)

  // Essay feedback state
  const [feedbackLoading, setFeedbackLoading] = useState<string | null>(null)
  const [feedbackResults, setFeedbackResults] = useState<Record<string, any>>({})

  // Guardrails state (G-S4)
  const [guardrailResult, setGuardrailResult] = useState<any>(null)
  const [intentReason, setIntentReason] = useState('')
  const [rationale, setRationale] = useState('')
  const [scanning, setScanning] = useState(false)

  // Spec 39 — fees & payments (pay step + cost tracker)
  const [checkout, setCheckout] = useState<CheckoutSession | null>(null)
  const [waiverOpen, setWaiverOpen] = useState(false)
  const [waiverBasis, setWaiverBasis] = useState('first_gen')
  const [waiverNote, setWaiverNote] = useState('')

  useEffect(() => {
    const qTab = searchParams.get('tab')
    if (qTab) setTab(qTab)
  }, [searchParams])

  const { data: app, isLoading } = useQuery({ queryKey: ['application', appId], queryFn: () => getMyApplication(appId!) })
  const { data: checklist } = useQuery({ queryKey: ['checklist', appId], queryFn: () => getChecklist(appId!).catch(() => generateChecklist(appId!)) })
  const { data: essays } = useQuery({ queryKey: ['essays', app?.program_id], queryFn: () => listEssays(app?.program_id), enabled: !!app?.program_id && (tab === 'essays' || tab === 'documents') })
  const { data: resumes } = useQuery({ queryKey: ['resumes', app?.program_id], queryFn: () => listResumes(app?.program_id), enabled: !!app?.program_id && tab === 'documents' })
  const { data: documents } = useQuery({ queryKey: ['documents'], queryFn: listDocuments, enabled: tab === 'documents' })
  const { data: interviews } = useQuery({ queryKey: ['interviews'], queryFn: getMyInterviews, enabled: tab === 'interviews' })
  const { data: recommenders } = useQuery({ queryKey: ['recommendations'], queryFn: listRecommendations, enabled: tab === 'recommenders' })
  const { data: cost } = useQuery({ queryKey: ['payment', appId], queryFn: () => getCostTracker(appId!), enabled: !!appId })

  // Spec 39 — after a Stripe redirect-return (?paid=fee|deposit), refresh state.
  useEffect(() => {
    const paid = searchParams.get('paid')
    if (paid === 'fee' || paid === 'deposit') {
      queryClient.invalidateQueries({ queryKey: ['payment', appId] })
      queryClient.invalidateQueries({ queryKey: ['application', appId] })
      if (paid === 'deposit') queryClient.invalidateQueries({ queryKey: ['enrollment', appId] })
      showToast('Payment received — thank you.', 'success')
    }
  }, [searchParams, appId, queryClient])

  const submitMut = useMutation({
    mutationFn: () => submitApplication(appId!),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['application', appId] })
      queryClient.invalidateQueries({ queryKey: ['my-applications'] })
      showToast('Application submitted!', 'success')
    },
    onError: (err: any) => {
      const detail: string = err?.response?.data?.detail || ''
      if (detail.toLowerCase().includes('not ready') || detail.toLowerCase().includes('missing')) {
        const after = detail.split('Missing:')[1] || detail
        setSubmitBlockers(after.split(',').map(s => s.trim()).filter(Boolean))
      } else {
        showToast(detail || 'Could not submit', 'error')
      }
    },
  })
  const payFeeMut = useMutation({
    mutationFn: () => payApplicationFee(appId!),
    onSuccess: (session) => setCheckout(session),
    onError: (err: any) => showToast(err?.response?.data?.detail || err?.message || 'Could not start checkout', 'error'),
  })
  const waiverMut = useMutation({
    mutationFn: () => requestFeeWaiver(appId!, waiverBasis, waiverNote || undefined),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['payment', appId] })
      setWaiverOpen(false)
      setWaiverNote('')
      showToast('Waiver requested — the school will review it.', 'success')
    },
    onError: (err: any) => showToast(err?.response?.data?.detail || 'Could not request a waiver', 'error'),
  })
  const essayMut = useMutation({ mutationFn: (data: any) => createEssay(data), onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['essays'] }); queryClient.invalidateQueries({ queryKey: ['checklist', appId] }); setShowEssayModal(false); setEssayContent(''); setEssayPrompt(''); showToast('Essay created', 'success') } })
  const essayUpdateMut = useMutation({ mutationFn: ({ id, data }: { id: string; data: any }) => updateEssay(id, data), onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['essays'] }); setEditingEssay(null); showToast('Essay updated', 'success') } })
  const resumeGenMut = useMutation({ mutationFn: () => generateResume({ format_type: 'standard', target_program_id: app?.program_id }), onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['resumes'] }); queryClient.invalidateQueries({ queryKey: ['checklist', appId] }); showToast('Resume generated', 'success') } })
  const modeMut = useMutation({
    mutationFn: (mode: 'internal' | 'external') => patchApplication(appId!, { submission_mode: mode }),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['application', appId] }); showToast('Submission mode updated', 'success') },
  })
  const intentMut = useMutation({
    mutationFn: () => patchApplication(appId!, { intent_picker: intentReason, intent_rationale: rationale || null }),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['application', appId] }); showToast('Intent saved', 'success') },
    onError: (err: any) => showToast(err?.response?.data?.detail || 'Could not save intent', 'error'),
  })
  const toggleMut = useMutation({
    mutationFn: ({ key, completed }: { key: string; completed: boolean }) => toggleChecklistItem(appId!, key, completed),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['checklist', appId] })
      queryClient.invalidateQueries({ queryKey: ['application', appId] })
    },
  })

  // File upload handler
  const handleFileUpload = useCallback(async (files: FileList | File[]) => {
    const fileArray = Array.from(files)
    if (fileArray.length === 0) return
    setUploading(true)
    setUploadProgress(0)
    try {
      for (const file of fileArray) {
        const docType = file.name.toLowerCase().includes('transcript') ? 'transcript'
          : file.name.toLowerCase().includes('resume') || file.name.toLowerCase().includes('cv') ? 'resume'
          : file.name.toLowerCase().includes('essay') ? 'essay'
          : 'certificate'
        const { upload_url, document_id } = await requestUpload({
          document_type: docType, file_name: file.name,
          content_type: file.type || 'application/octet-stream', file_size_bytes: file.size,
        })
        await uploadToS3(upload_url, file, (pct) => setUploadProgress(pct))
        await confirmUpload(document_id)
      }
      queryClient.invalidateQueries({ queryKey: ['documents'] })
      queryClient.invalidateQueries({ queryKey: ['checklist', appId] })
      showToast(`${fileArray.length} file(s) uploaded`, 'success')
    } catch {
      showToast('Upload failed', 'error')
    } finally {
      setUploading(false)
      setUploadProgress(0)
    }
  }, [appId, queryClient])

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setDragOver(false)
    if (e.dataTransfer.files.length > 0) handleFileUpload(e.dataTransfer.files)
  }, [handleFileUpload])

  const checkReadinessFn = async () => {
    try {
      const result = await getReadiness(appId!)
      setReadiness(result)
      setShowReadiness(true)
    } catch {
      showToast('Could not check readiness', 'error')
    }
  }

  const runGuardrailScan = async () => {
    setScanning(true)
    try {
      const result = await guardrailScan(appId!)
      setGuardrailResult(result)
      queryClient.invalidateQueries({ queryKey: ['application', appId] })
    } catch {
      showToast('Could not run scan', 'error')
    } finally {
      setScanning(false)
    }
  }

  const handleEssayFeedback = async (essayId: string) => {
    setFeedbackLoading(essayId)
    try {
      const result = await requestEssayFeedback(essayId)
      setFeedbackResults(prev => ({ ...prev, [essayId]: result }))
    } catch {
      showToast('Could not get feedback', 'error')
    } finally {
      setFeedbackLoading(null)
    }
  }

  const wordCount = (text: string) => text.trim() ? text.trim().split(/\s+/).length : 0

  usePageTitle(app?.program?.program_name || 'Application')

  if (isLoading) return <div className="p-6"><Skeleton className="h-64" /></div>
  if (!app) return <div className="p-6 text-center text-student-text">Application not found.</div>

  const application: Application = app
  const currentStepIdx = STATUS_STEPS.indexOf(application.status)
  const checklistItems: ChecklistItem[] = checklist?.items ?? []
  const completionPct = checklist?.completion_percentage ?? application.readiness_pct ?? 0
  const documentsList: any[] = Array.isArray(documents) ? documents : []
  const essaysList: Essay[] = Array.isArray(essays) ? essays : []
  const resumesList: Resume[] = Array.isArray(resumes) ? resumes : []
  const recommendersList: any[] = Array.isArray(recommenders) ? recommenders : []
  const isExternal = application.submission_mode === 'external'
  // Fitness on a 0-100 scale (match_score stored 0-1). Spec 15 §6.5 low-fit ≤ 30.
  const fitnessPct = application.match_score != null ? Math.round(Number(application.match_score) * 100) : null
  const isLowFit = application.fit_band === 'low' || guardrailResult?.fit_band === 'low' || (fitnessPct != null && fitnessPct <= 30)

  const requiredItems = checklistItems.filter(i => i.required !== false)
  const incompleteRequired = requiredItems.filter(i => i.status !== 'completed')
  const allComplete = application.status === 'draft' && incompleteRequired.length === 0 && checklistItems.length > 0
  // Spec 39 — internal submission is gated on the application fee being paid or
  // waived (allow-and-reconcile lets a requested waiver through).
  const fee = cost?.fee
  const feeClear = isFeeClear(fee)
  const canSubmit = application.status === 'draft' && allComplete && (markedReady || isExternal) && feeClear

  const tabs = [
    { id: 'checklist', label: `Checklist ${completionPct}%` },
    { id: 'documents', label: 'Documents' },
    { id: 'essays', label: 'Essays' },
    { id: 'recommenders', label: 'Recommenders' },
    { id: 'interviews', label: 'Interviews' },
    { id: 'guardrails', label: 'Guardrails' },
    // Spec 18 — Offer tab once submitted (record/await an offer) or whenever one exists.
    ...(application.status !== 'draft' || application.offer ? [{ id: 'offer', label: 'Offer' }] : []),
    // Spec 35 — Enrollment tab once an offer is accepted (§7: hidden until then).
    ...(application.student_decision === 'accepted_by_student' ||
    application.offer?.student_response === 'accepted'
      ? [{ id: 'enrollment', label: 'Enrollment' }]
      : []),
  ]

  const programName = application.program?.program_name || 'Application'

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <Breadcrumbs
        className="mb-4"
        items={[{ label: 'Apply', to: '/s/manage' }, { label: 'Applications', to: '/s/manage' }, { label: programName }]}
      />
      <button onClick={() => navigate('/s/manage')} className="flex items-center gap-1 text-sm text-student-text hover:text-student-ink mb-4">
        <ArrowLeft size={16} /> Back to Apply
      </button>

      <div className="flex items-start justify-between gap-3 flex-wrap">
        <div>
          <h1 className="text-xl font-bold text-student-ink mb-1">{programName}</h1>
          {application.program?.institution_name && (
            <p className="text-sm text-student-text flex items-center gap-1"><Building2 size={13} /> {application.program.institution_name}</p>
          )}
        </div>
      </div>

      {/* Decision banner — routes to Offer tab when admitted (spec 18 §4) */}
      {application.status === 'decision_made' && application.decision && (
        <div className={`mt-4 rounded-lg px-4 py-3 flex items-center gap-3 ${
          application.decision === 'admitted' || application.student_decision === 'accepted_by_student'
            ? 'bg-success-soft'
            : application.decision === 'rejected'
              ? 'bg-destructive/10'
              : 'bg-warning-soft'
        }`}>
          <Award size={18} className={
            application.decision === 'admitted' || application.student_decision === 'accepted_by_student'
              ? 'text-success'
              : application.decision === 'rejected'
                ? 'text-destructive'
                : 'text-warning'
          } />
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-student-ink">
              {DECISION_STATE_LABEL[application.decision_state || application.decision] ||
                `Decision: ${application.decision}`}
            </p>
            {application.decision === 'admitted' && application.student_decision !== 'accepted_by_student' && (
              <p className="text-xs text-student-text">Review your offer in the Offer tab.</p>
            )}
            {application.student_decision === 'accepted_by_student' && (
              <p className="text-xs text-student-text">You're in — enrollment steps are on your calendar.</p>
            )}
          </div>
          {application.decision === 'admitted' && application.student_decision !== 'accepted_by_student' && (
            <button
              onClick={() => setTab('offer')}
              className="text-xs text-cobalt font-medium shrink-0 hover:underline"
            >
              View offer →
            </button>
          )}
        </div>
      )}

      {/* Status timeline (§4 / §12) */}
      <div className="my-5">
        <div className="flex items-center">
          {STATUS_STEPS.map((step, i) => {
            const done = i < currentStepIdx
            const current = i === currentStepIdx
            return (
              <div key={step} className="flex items-center flex-1 last:flex-none">
                <div className={`w-6 h-6 rounded-full flex items-center justify-center text-xs flex-shrink-0 ${
                  done ? 'bg-success text-white' : current ? 'bg-cobalt text-white' : 'bg-muted text-muted-foreground'
                }`}>
                  {done ? <Check size={12} /> : <Circle size={12} />}
                </div>
                {i < STATUS_STEPS.length - 1 && (
                  <div className={`h-0.5 flex-1 mx-1 ${i < currentStepIdx ? 'bg-success' : 'bg-muted'}`} />
                )}
              </div>
            )
          })}
        </div>
        <div className="flex items-center justify-between mt-1.5">
          {STATUS_STEPS.map((step, i) => (
            <span key={step} className={`text-[11px] ${i === currentStepIdx ? 'text-cobalt font-medium' : 'text-muted-foreground'}`}>
              {STATUS_STEP_LABELS[step]}
            </span>
          ))}
        </div>
      </div>

      <div className="flex gap-6">
        {/* Sidebar */}
        <div className="w-60 flex-shrink-0 space-y-4">
          <Card className="p-4">
            <h3 className="font-medium text-sm text-student-ink mb-3">Checklist</h3>
            <div className="space-y-2 mb-3">
              {checklistItems.map((item, i) => (
                <div
                  key={item.key || i}
                  className={`flex items-center gap-2 rounded-md px-1 py-0.5 text-sm ${
                    checklistFocus && item.category === checklistFocus
                      ? 'bg-warning-soft ring-1 ring-warning/40'
                      : ''
                  }`}
                >
                  {item.status === 'completed' ? (
                    <Check size={14} className="text-success flex-shrink-0" />
                  ) : item.status === 'blocked' || item.mismatch ? (
                    <AlertTriangle size={14} className="text-warning flex-shrink-0" />
                  ) : (
                    <Circle size={12} className="text-muted-foreground flex-shrink-0" />
                  )}
                  <span className={item.status === 'completed' ? 'text-muted-foreground line-through' : 'text-student-ink'}>
                    {item.name}
                  </span>
                </div>
              ))}
              {checklistItems.length === 0 && <p className="text-xs text-student-text">Generating checklist…</p>}
            </div>
            <ProgressBar value={completionPct} label="Readiness" />

            <Button className="w-full mt-3" size="sm" variant="tertiary" onClick={checkReadinessFn}>
              <FileCheck size={14} className="mr-1" /> Check readiness
            </Button>

            {/* Ready gate (§12) — gold is the earned moment */}
            {application.status === 'draft' && allComplete && !markedReady && !isExternal && (
              <Button className="w-full mt-2" size="sm" variant="primary" onClick={() => setMarkedReady(true)}>
                <Check size={14} className="mr-1" /> Mark as ready to submit
              </Button>
            )}

            {application.status === 'draft' && (
              <Button
                className="w-full mt-2"
                variant="secondary"
                size="sm"
                disabled={!canSubmit}
                loading={submitMut.isPending}
                onClick={() => submitMut.mutate()}
              >
                <Send size={14} className="mr-1" />
                {canSubmit
                  ? 'Submit application'
                  : allComplete && markedReady && !feeClear
                    ? 'Settle the fee to submit'
                    : allComplete
                      ? 'Confirm ready first'
                      : `${incompleteRequired.length} item${incompleteRequired.length !== 1 ? 's' : ''} left`}
              </Button>
            )}

            {application.status === 'draft' && incompleteRequired.length > 0 && (
              <div className="mt-2 text-xs text-warning bg-warning-soft rounded-lg px-3 py-2">
                <p className="font-medium mb-1">Complete these before submitting:</p>
                <ul className="space-y-0.5">
                  {incompleteRequired.slice(0, 5).map((item, i) => (
                    <li key={i} className="flex items-center gap-1"><AlertCircle size={9} /> {item.name}</li>
                  ))}
                  {incompleteRequired.length > 5 && <li>…and {incompleteRequired.length - 5} more</li>}
                </ul>
              </div>
            )}
            {application.status === 'draft' && allComplete && (
              <p className="text-xs text-success mt-2 flex items-center gap-1"><Check size={10} /> All required items complete</p>
            )}
          </Card>

          {/* Spec 44 §4.2 — engine apply-ready (per-program signal gate) */}
          <ApplyReadyChecklist programId={application.program_id} />

          {/* Application fee + cost tracker (Spec 39 §2.2 / §2A) */}
          {fee?.required && (
            <FeeCard
              fee={fee}
              isDraft={application.status === 'draft'}
              payPending={payFeeMut.isPending}
              onPay={() => payFeeMut.mutate()}
              onRequestWaiver={() => setWaiverOpen(true)}
              programName={application.program?.program_name ?? undefined}
              institutionName={application.program?.institution_name ?? undefined}
            />
          )}

          {/* Submission mode (§7) */}
          {application.status === 'draft' && (
            <Card className="p-4">
              <h3 className="font-medium text-sm text-student-ink mb-2">How will you submit?</h3>
              <div className="flex rounded-lg border border-divider overflow-hidden text-xs">
                <button
                  onClick={() => !isExternal || modeMut.mutate('internal')}
                  className={`flex-1 px-2 py-1.5 ${!isExternal ? 'bg-cobalt text-white' : 'text-student-text hover:bg-student-mist'}`}
                >
                  Through UniPaith
                </button>
                <button
                  onClick={() => isExternal || modeMut.mutate('external')}
                  className={`flex-1 px-2 py-1.5 ${isExternal ? 'bg-cobalt text-white' : 'text-student-text hover:bg-student-mist'}`}
                >
                  Their portal
                </button>
              </div>
              <p className="text-[11px] text-student-text mt-2">
                {isExternal
                  ? 'You\'ll submit on the institution\'s portal. Mark items complete here and attach confirmation evidence.'
                  : 'Submit directly through UniPaith once every required item is complete.'}
              </p>
            </Card>
          )}
        </div>

        {/* Main content */}
        <div className="flex-1 min-w-0">
          <Tabs tabs={tabs} activeTab={tab} onChange={setTab} />
          <div className="mt-4">
            {tab === 'checklist' && (
              <>
                <GraduateIntentCard applicationId={appId!} />
                <StudentAdvisorFit applicationId={appId!} />
                <ChecklistTab
                  items={checklistItems}
                  completionPct={completionPct}
                  isExternal={isExternal}
                  canToggle={application.status === 'draft'}
                  onToggle={(key, completed) => toggleMut.mutate({ key, completed })}
                />
              </>
            )}

            {tab === 'documents' && (
              <div className="space-y-4">
                <div
                  onDragOver={e => { e.preventDefault(); setDragOver(true) }}
                  onDragLeave={() => setDragOver(false)}
                  onDrop={handleDrop}
                  className={`border-2 border-dashed rounded-lg p-6 text-center transition-colors ${dragOver ? 'border-cobalt bg-student-mist' : 'border-divider hover:border-cobalt/40'}`}
                >
                  <Upload size={24} className="mx-auto text-student-text mb-2" />
                  <p className="text-sm text-student-text mb-1">Drag & drop files here, or</p>
                  <label className="inline-block">
                    <input type="file" multiple className="hidden" onChange={e => e.target.files && handleFileUpload(e.target.files)} />
                    <span className="text-sm font-medium text-cobalt underline cursor-pointer">browse files</span>
                  </label>
                  <p className="text-xs text-muted-foreground mt-1">PDF, DOC, DOCX up to 10MB</p>
                </div>

                {uploading && (
                  <div className="space-y-1">
                    <div className="flex justify-between text-xs text-student-text"><span>Uploading…</span><span>{uploadProgress}%</span></div>
                    <ProgressBar value={uploadProgress} />
                  </div>
                )}

                {documentsList.length > 0 && (
                  <div className="space-y-2">
                    <h3 className="text-sm font-medium text-student-ink">Uploaded documents</h3>
                    {documentsList.map((doc: any) => (
                      <div key={doc.id} className="flex justify-between items-center p-3 rounded-lg border border-divider text-sm">
                        <div className="flex items-center gap-2"><FileCheck size={16} className="text-success" /><span className="text-student-ink">{doc.file_name}</span></div>
                        <Badge variant="neutral">{doc.document_type}</Badge>
                      </div>
                    ))}
                  </div>
                )}

                {/* Resume (a document) */}
                <div className="flex items-center justify-between p-3 rounded-lg border border-divider">
                  <div className="text-sm text-student-ink">
                    Resume / CV {resumesList.length > 0 && <Badge variant="success">v{resumesList[0].resume_version}</Badge>}
                  </div>
                  {resumesList.length === 0 && (
                    <Button size="sm" variant="tertiary" onClick={() => resumeGenMut.mutate()} loading={resumeGenMut.isPending}>Generate</Button>
                  )}
                </div>

                {documentsList.length === 0 && !uploading && (
                  <p className="text-sm text-student-text">Upload transcripts, recommendations, and other required documents above.</p>
                )}
              </div>
            )}

            {tab === 'essays' && (
              <div className="space-y-4">
                <Button size="sm" onClick={() => setShowEssayModal(true)}>+ New essay</Button>
                {essaysList.length === 0 ? (
                  <p className="text-sm text-student-text mt-2">No essays yet for this application.</p>
                ) : (
                  essaysList.map((e: Essay) => (
                    <Card key={e.id} className="p-4">
                      <div className="flex justify-between items-start mb-2">
                        <div>
                          <p className="font-medium text-sm text-student-ink">{e.prompt_text || 'Essay'}</p>
                          <div className="flex items-center gap-2 mt-1">
                            <span className="text-xs text-student-text">{e.word_count ?? wordCount(e.content)} words</span>
                            <Badge variant={(STATUS_COLORS[e.status] || 'neutral') as never}>{e.status}</Badge>
                          </div>
                        </div>
                        <div className="flex gap-2">
                          <Button size="sm" variant="tertiary" onClick={() => handleEssayFeedback(e.id)} loading={feedbackLoading === e.id}>
                            <Sparkles size={12} className="mr-1" /> Get feedback
                          </Button>
                          <Button size="sm" variant="ghost" onClick={() => { setEditingEssay(e); setEssayContent(e.content); setEssayPrompt(e.prompt_text || '') }}>Edit</Button>
                        </div>
                      </div>
                      <p className="text-sm text-student-text line-clamp-3">{e.content}</p>
                      {feedbackResults[e.id] && (
                        <div className="mt-3 bg-student-mist rounded-lg p-3">
                          <div className="flex items-center gap-2 mb-2"><Sparkles size={14} className="text-cobalt" /><span className="text-sm font-medium text-student-ink">Feedback</span></div>
                          {feedbackResults[e.id].feedback && <p className="text-sm text-student-text whitespace-pre-wrap">{feedbackResults[e.id].feedback}</p>}
                          {feedbackResults[e.id].suggestions && (
                            <ul className="text-sm text-student-text list-disc list-inside mt-2 space-y-1">
                              {feedbackResults[e.id].suggestions.map((s: string, i: number) => <li key={i}>{s}</li>)}
                            </ul>
                          )}
                        </div>
                      )}
                    </Card>
                  ))
                )}
              </div>
            )}

            {tab === 'recommenders' && (
              <RecommendersTab
                recommenders={recommendersList}
                programId={application.program_id}
                onNudge={async (id) => { await sendRecommendationRequest(id); queryClient.invalidateQueries({ queryKey: ['recommendations'] }); showToast('Reminder sent', 'success') }}
              />
            )}

            {tab === 'interviews' && (() => {
              const interviewList = Array.isArray(interviews)
                ? interviews.filter((i: { application_id: string }) => i.application_id === appId)
                : []
              return (
                <div className="space-y-4">
                  {interviewList.length > 0 ? (
                    interviewList.map((iv: Interview) => (
                      <InterviewRespondPanel key={iv.id} interview={iv} />
                    ))
                  ) : (
                    <Card className="p-6 text-center">
                      <Users size={32} className="text-muted-foreground mx-auto mb-3" />
                      <p className="text-sm text-student-text">No interviews scheduled yet.</p>
                      <p className="text-xs text-muted-foreground mt-1">
                        You'll be notified when an interview is requested.
                      </p>
                    </Card>
                  )}
                </div>
              )
            })()}

            {tab === 'guardrails' && (
              <div className="space-y-4">
                {isLowFit && (
                  <div className="bg-warning-soft border border-warning/30 rounded-lg p-4 flex items-start gap-3">
                    <AlertTriangle size={18} className="text-warning flex-shrink-0 mt-0.5" />
                    <div>
                      <p className="text-sm font-medium text-student-ink">Low-fit warning</p>
                      <p className="text-xs text-student-text mt-0.5">
                        {fitnessPct != null ? `This program's fitness is ${fitnessPct}%.` : 'This program may be a low-fit option.'} Review your Match analysis before committing effort here.
                      </p>
                    </div>
                  </div>
                )}

                <Card className="p-4">
                  <div className="flex items-center gap-2 mb-3"><ShieldCheck size={16} className="text-cobalt" /><h3 className="text-sm font-medium text-student-ink">Why are you applying?</h3></div>
                  <div className="flex flex-wrap gap-2 mb-3">
                    {INTENT_OPTIONS.map(opt => (
                      <button
                        key={opt.value}
                        onClick={() => setIntentReason(opt.value)}
                        className={`px-3 py-1.5 text-xs rounded-full border transition-colors ${
                          (intentReason || application.intent_picker) === opt.value
                            ? 'bg-ink text-white border-ink' : 'bg-white text-student-text border-divider hover:bg-student-mist'
                        }`}
                      >
                        {opt.label}
                      </button>
                    ))}
                  </div>
                  {RATIONALE_REQUIRED.includes(intentReason || application.intent_picker || '') && (
                    <div className="mb-3">
                      <Textarea
                        label="Your rationale (required, at least 80 characters)"
                        value={rationale || application.intent_rationale || ''}
                        onChange={e => setRationale(e.target.value)}
                        placeholder="Explain why this application is worth your effort…"
                      />
                      <p className="text-[11px] text-student-text mt-1 text-right">{(rationale || application.intent_rationale || '').length}/80</p>
                    </div>
                  )}
                  <Button
                    size="sm"
                    variant="tertiary"
                    disabled={!intentReason && !application.intent_picker}
                    loading={intentMut.isPending}
                    onClick={() => intentMut.mutate()}
                  >
                    Save intent
                  </Button>
                </Card>

                <Card className="p-4">
                  <div className="flex items-center justify-between mb-2">
                    <h3 className="text-sm font-medium text-student-ink">Guardrail scan</h3>
                    <Button size="sm" onClick={runGuardrailScan} loading={scanning}>Run scan</Button>
                  </div>
                  <p className="text-xs text-student-text mb-3">Checks fit and flags anything to reconsider before you apply.</p>
                  {(guardrailResult || application.fit_band) && (
                    <div className={`rounded-lg p-3 ${
                      (guardrailResult?.fit_band || application.fit_band) === 'high' ? 'bg-success-soft'
                        : (guardrailResult?.fit_band || application.fit_band) === 'low' ? 'bg-warning-soft' : 'bg-student-mist'
                    }`}>
                      <div className="flex items-center gap-2 mb-1">
                        <Badge variant={(guardrailResult?.fit_band || application.fit_band) === 'high' ? 'success' : (guardrailResult?.fit_band || application.fit_band) === 'low' ? 'warning' : 'info'}>
                          {(guardrailResult?.fit_band || application.fit_band)} fit
                        </Badge>
                        {guardrailResult?.recommended_action && <span className="text-xs text-student-text">Recommended: {guardrailResult.recommended_action}</span>}
                        {guardrailResult?.is_rule_based && <span className="text-[10px] text-muted-foreground">Showing rule-based result</span>}
                      </div>
                      {(guardrailResult?.blockers || application.guardrail_blockers || []).length > 0 ? (
                        <ul className="mt-2 space-y-1">
                          {(guardrailResult?.blockers || application.guardrail_blockers || []).map((b: string, i: number) => (
                            <li key={i} className="text-xs text-student-text flex items-start gap-1"><AlertCircle size={11} className="mt-0.5 flex-shrink-0" /> {b}</li>
                          ))}
                        </ul>
                      ) : (
                        <p className="text-xs text-student-text mt-1">No blockers — you're clear to proceed.</p>
                      )}
                    </div>
                  )}
                </Card>
              </div>
            )}

            {tab === 'offer' && <OfferPanel application={application} />}
            {tab === 'enrollment' && <EnrollmentPanel application={application} />}
          </div>
        </div>
      </div>

      {/* New Essay Modal */}
      <Modal isOpen={showEssayModal} onClose={() => setShowEssayModal(false)} title="New essay">
        <div className="space-y-3">
          <Select label="Type" options={[
            { value: 'personal_statement', label: 'Personal Statement' },
            { value: 'diversity', label: 'Diversity Statement' },
            { value: 'why_school', label: 'Why This School' },
            { value: 'research', label: 'Research Statement' },
          ]} value={essayType} onChange={e => setEssayType(e.target.value)} />
          <Textarea label="Prompt" value={essayPrompt} onChange={e => setEssayPrompt(e.target.value)} placeholder="The essay question…" />
          <div>
            <Textarea label="Content" value={essayContent} onChange={e => setEssayContent(e.target.value)} placeholder="Write your essay…" />
            <p className="text-xs text-muted-foreground mt-1 text-right">{wordCount(essayContent)} words</p>
          </div>
          <Button onClick={() => essayMut.mutate({ program_id: application.program_id, essay_type: essayType, content: essayContent, prompt_text: essayPrompt })} loading={essayMut.isPending} className="w-full">Save essay</Button>
        </div>
      </Modal>

      {/* Edit Essay Modal */}
      <Modal isOpen={!!editingEssay} onClose={() => setEditingEssay(null)} title="Edit essay" size="lg">
        {editingEssay && (
          <div className="space-y-3">
            <Textarea label="Prompt" value={essayPrompt} onChange={e => setEssayPrompt(e.target.value)} />
            <div>
              <Textarea label="Content" value={essayContent} onChange={e => setEssayContent(e.target.value)} />
              <p className="text-xs text-muted-foreground mt-1 text-right">{wordCount(essayContent)} words</p>
            </div>
            <Button onClick={() => essayUpdateMut.mutate({ id: editingEssay.id, data: { content: essayContent, prompt_text: essayPrompt } })} loading={essayUpdateMut.isPending} className="w-full">Save changes</Button>
          </div>
        )}
      </Modal>

      {/* Readiness Check Modal */}
      <Modal isOpen={showReadiness} onClose={() => setShowReadiness(false)} title="Application readiness">
        {readiness && (
          <div className="space-y-4">
            <div className="flex items-center gap-3">
              <div className={`w-12 h-12 rounded-full flex items-center justify-center ${readiness.is_ready ? 'bg-success-soft' : 'bg-warning-soft'}`}>
                {readiness.is_ready ? <Check size={24} className="text-success" /> : <AlertCircle size={24} className="text-warning" />}
              </div>
              <div>
                <p className="font-medium text-student-ink">{readiness.is_ready ? 'Ready to submit!' : 'Almost there'}</p>
                <p className="text-sm text-student-text">{readiness.completion_percentage}% complete</p>
              </div>
            </div>
            <ProgressBar value={readiness.completion_percentage} />
            {readiness.missing_items?.length > 0 && (
              <div>
                <h4 className="text-sm font-medium text-student-ink mb-2">Missing items:</h4>
                <ul className="space-y-1">
                  {readiness.missing_items.map((item: string, i: number) => (
                    <li key={i} className="flex items-center gap-2 text-sm text-student-text"><Circle size={8} className="text-destructive flex-shrink-0" /> {item}</li>
                  ))}
                </ul>
              </div>
            )}
            {readiness.warnings?.length > 0 && (
              <div>
                <h4 className="text-sm font-medium text-student-ink mb-2">Warnings:</h4>
                <ul className="space-y-1">
                  {readiness.warnings.map((w: string, i: number) => (
                    <li key={i} className="flex items-center gap-2 text-sm text-warning"><AlertCircle size={12} className="flex-shrink-0" /> {w}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}
      </Modal>

      {/* Submit blocked modal (§10) */}
      <Modal isOpen={!!submitBlockers} onClose={() => setSubmitBlockers(null)} title="Submit blocked. Resolve these items first:">
        <ul className="space-y-2">
          {(submitBlockers || []).map((b, i) => (
            <li key={i} className="flex items-center gap-2 text-sm text-student-ink"><AlertCircle size={14} className="text-warning flex-shrink-0" /> {b}</li>
          ))}
        </ul>
        <Button className="w-full mt-4" variant="tertiary" onClick={() => setSubmitBlockers(null)}>Got it</Button>
      </Modal>

      {/* Spec 39 — fee checkout (calm, cobalt, no gold) */}
      <PaymentCheckout
        session={checkout}
        onClose={() => setCheckout(null)}
        onPaid={() => {
          setCheckout(null)
          queryClient.invalidateQueries({ queryKey: ['payment', appId] })
          queryClient.invalidateQueries({ queryKey: ['application', appId] })
        }}
      />

      {/* Spec 39 §2.2 — fee-waiver request (equally prominent to paying) */}
      <Modal isOpen={waiverOpen} onClose={() => setWaiverOpen(false)} title="Request a fee waiver" size="sm">
        <div className="space-y-3">
          <p className="text-sm text-student-text">
            Choose a basis for your request. The school reviews it — there's no fee to ask.
          </p>
          <Select
            label="Basis"
            value={waiverBasis}
            onChange={e => setWaiverBasis(e.target.value)}
            options={[
              { value: 'fee_waiver_code', label: 'I have a fee-waiver code' },
              { value: 'first_gen', label: 'First-generation student' },
              { value: 'income_band', label: 'Financial hardship / income' },
              { value: 'nacac_sram', label: 'NACAC / SRAR waiver' },
              { value: 'other', label: 'Other' },
            ]}
          />
          <Textarea
            label="Anything to add? (optional)"
            value={waiverNote}
            onChange={e => setWaiverNote(e.target.value)}
            placeholder="Context or a fee-waiver code…"
          />
          <Button
            variant="secondary"
            className="w-full"
            loading={waiverMut.isPending}
            onClick={() => waiverMut.mutate()}
          >
            Request waiver
          </Button>
        </div>
      </Modal>
    </div>
  )
}

// --- Application fee + cost tracker (Spec 39 §2.2 / §2A) ---
function FeeCard({ fee, isDraft, payPending, onPay, onRequestWaiver, programName, institutionName }: {
  fee: FeeView
  isDraft: boolean
  payPending: boolean
  onPay: () => void
  onRequestWaiver: () => void
  programName?: string
  institutionName?: string
}) {
  const money = formatMoney(fee.amount, fee.currency)
  const paid = fee.status === 'paid'
  const waived = fee.status === 'waived'
  const waiverPending = fee.status === 'waiver_pending'
  const waiverDenied = fee.status === 'waiver_denied'
  const processing = fee.status === 'processing'
  const failed = fee.status === 'failed'
  const refunded = fee.status === 'refunded' || fee.status === 'partially_refunded'
  // §7 — retry from processing/failed too, so a closed/failed checkout never strands the student.
  const canPay = isDraft && ['due', 'processing', 'failed', 'waiver_denied'].includes(fee.status)
  const canWaive = isDraft && ['due', 'failed'].includes(fee.status)
  const payLabel = processing ? 'Resume payment' : failed ? `Try again — pay ${money}` : `Pay application fee (${money})`

  const receipt = () =>
    downloadReceipt({
      kind: 'application_fee',
      amount: fee.amount,
      currency: fee.currency,
      status: fee.status,
      paidAt: fee.paid_at,
      refundedAmount: fee.refunded_amount,
      programName,
      institutionName,
      reference: fee.payment_id,
    })

  return (
    <Card className="p-4">
      <div className="flex items-center gap-2 mb-1">
        <HandCoins size={15} className="text-cobalt" />
        <h3 className="font-medium text-sm text-student-ink">Application fee</h3>
      </div>
      <p className="text-2xl font-bold text-student-ink tabular-nums mb-2">{money}</p>

      {(paid || refunded) && (
        <div className="space-y-2">
          {paid ? (
            <div className="rounded-lg bg-success-soft px-3 py-2 text-xs text-success flex items-start gap-1.5">
              <Receipt size={14} className="mt-0.5 shrink-0" />
              <span>
                Fee paid{fee.paid_at ? ` on ${new Date(fee.paid_at).toLocaleDateString()}` : ''}. Receipt saved to your record.
                {fee.refunded_amount ? ` Refunded ${formatMoney(fee.refunded_amount, fee.currency)}.` : ''}
              </span>
            </div>
          ) : (
            <div className="rounded-lg bg-student-mist px-3 py-2 text-xs text-student-text">
              Refunded {formatMoney(fee.refunded_amount || 0, fee.currency)} of {money}.
            </div>
          )}
          <button onClick={receipt} className="text-xs text-cobalt hover:underline inline-flex items-center gap-1">
            <Download size={12} /> Download receipt
          </button>
        </div>
      )}
      {waived && <Badge variant="info">Fee waived</Badge>}
      {processing && <p className="text-xs text-student-text">Confirming your payment…</p>}
      {failed && (
        <p className="text-xs text-warning">That payment didn't go through. Try again or request a waiver.</p>
      )}
      {waiverPending && (
        <div className="space-y-1.5">
          <Badge variant="warning">Waiver requested — the school will review it</Badge>
          {fee.waiver_policy === 'allow_and_reconcile' && (
            <p className="text-xs text-student-text">You can submit now; the school reconciles the fee.</p>
          )}
        </div>
      )}

      {canPay && (
        <div className="mt-3 space-y-2">
          {waiverDenied && (
            <p className="text-xs text-warning">Your waiver wasn't approved. You can pay the fee to submit.</p>
          )}
          {/* Equal prominence (Spec 39 §8): pay (cobalt) beside waiver (outline), never gold. */}
          <Button variant="secondary" size="sm" className="w-full" loading={payPending} onClick={onPay}>
            <CreditCard size={14} className="mr-1" /> {payLabel}
          </Button>
          {canWaive && (
            <Button variant="tertiary" size="sm" className="w-full" onClick={onRequestWaiver}>
              Request a fee waiver instead
            </Button>
          )}
        </div>
      )}
      {!isDraft && !paid && !waived && !refunded && (
        <p className="text-xs text-student-text mt-1">Fee status: {fee.status.replace(/_/g, ' ')}.</p>
      )}
    </Card>
  )
}

// --- Checklist tab (spec 15 §5) ---
function ChecklistTab({ items, completionPct, isExternal, canToggle, onToggle }: {
  items: ChecklistItem[]
  completionPct: number
  isExternal: boolean
  canToggle: boolean
  onToggle: (key: string, completed: boolean) => void
}) {
  const OWNER_COLORS: Record<string, 'info' | 'warning' | 'neutral'> = { student: 'info', recommender: 'warning', institution: 'neutral' }
  const grouped = items.reduce<Record<string, ChecklistItem[]>>((acc, item) => {
    const cat = item.category || 'general'
    ;(acc[cat] ||= []).push(item)
    return acc
  }, {})

  return (
    <div className="space-y-4">
      <Card className="p-4">
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-2"><ListChecks size={16} className="text-cobalt" /><span className="text-sm font-medium text-student-ink">Readiness: {completionPct}%</span></div>
          {completionPct >= 100 && <Badge variant="success">Ready to submit</Badge>}
        </div>
        <ProgressBar value={completionPct} />
        {isExternal && <p className="text-xs text-student-text mt-2">External submission — check items off as you complete them on the institution's portal.</p>}
      </Card>
      {Object.entries(grouped).map(([cat, catItems]) => (
        <div key={cat}>
          <p className="text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-2">{cat.replace(/_/g, ' ')}</p>
          <div className="space-y-2">
            {catItems.map((item, idx) => (
              <Card key={item.key || idx} className="p-3 flex items-center justify-between gap-3">
                <div className="flex items-center gap-3 min-w-0">
                  <input
                    type="checkbox"
                    checked={item.status === 'completed'}
                    disabled={!canToggle || (!isExternal && item.owner === 'recommender')}
                    onChange={e => item.key && onToggle(item.key, e.target.checked)}
                    className="rounded border-divider text-cobalt focus:ring-cobalt"
                  />
                  <div className="min-w-0">
                    <p className="text-sm text-student-ink">{item.name}</p>
                    {item.expected_format && <p className="text-xs text-muted-foreground">{item.expected_format}</p>}
                  </div>
                </div>
                <div className="flex items-center gap-2 flex-shrink-0">
                  {item.item_type && <Badge variant="neutral">{item.item_type}</Badge>}
                  {item.owner && <Badge variant={OWNER_COLORS[item.owner] || 'neutral'}>{item.owner}</Badge>}
                  {item.required !== false && <Badge variant="danger">Required</Badge>}
                  {item.mismatch && <AlertTriangle size={14} className="text-warning" />}
                </div>
              </Card>
            ))}
          </div>
        </div>
      ))}
      {items.length === 0 && (
        <Card className="p-6 text-center"><ListChecks size={32} className="text-muted-foreground mx-auto mb-3" /><p className="text-sm text-student-text">No checklist items yet.</p></Card>
      )}
    </div>
  )
}

// --- Recommenders tab (spec 15 §6.3) ---
function RecommendersTab({ recommenders, programId, onNudge }: {
  recommenders: any[]
  programId: string
  onNudge: (id: string) => void
}) {
  const relevant = recommenders.filter(r => !r.target_program_id || r.target_program_id === programId)
  const REC_STATUS: Record<string, 'neutral' | 'info' | 'warning' | 'success' | 'danger'> = {
    draft: 'neutral', requested: 'info', in_progress: 'warning', sent: 'info', submitted: 'success', received: 'success', overdue: 'danger',
  }
  if (relevant.length === 0)
    return (
      <Card className="p-6 text-center">
        <Users size={32} className="text-muted-foreground mx-auto mb-3" />
        <p className="text-sm text-student-text">No recommenders yet.</p>
        <p className="text-xs text-muted-foreground mt-1">Add recommenders from your Profile to request letters for this program.</p>
      </Card>
    )
  return (
    <div className="space-y-3">
      {relevant.map(r => (
        <Card key={r.id} className="p-4 flex items-center justify-between gap-3">
          <div className="min-w-0">
            <p className="text-sm font-medium text-student-ink">{r.recommender_name}</p>
            <p className="text-xs text-student-text">{r.recommender_title || r.relationship || r.recommender_institution || 'Recommender'}</p>
          </div>
          <div className="flex items-center gap-2 flex-shrink-0">
            <Badge variant={REC_STATUS[r.status] || 'neutral'}>{(r.status || 'draft').replace(/_/g, ' ')}</Badge>
            {['draft', 'requested', 'in_progress', 'sent', 'overdue'].includes(r.status) && (
              <Button size="sm" variant="tertiary" onClick={() => onNudge(r.id)}>
                <Send size={12} className="mr-1" /> Nudge
              </Button>
            )}
          </div>
        </Card>
      ))}
    </div>
  )
}
