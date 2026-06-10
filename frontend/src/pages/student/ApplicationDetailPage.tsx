import { useState, useCallback, useEffect } from 'react'
import { useParams, useNavigate, useSearchParams } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  getMyApplication, submitApplication, getChecklist, generateChecklist,
  getReadiness, patchApplication, guardrailScan, toggleChecklistItem,
} from '../../api/applications'
import { listWorkshopRuns } from '../../api/workshops-feedback'
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
import Skeleton, { SkeletonCard } from '../../components/ui/Skeleton'
import QueryError from '../../components/ui/QueryError'
import AIBadge from '../../components/ui/AIBadge'
import { RubricScores } from './apply/RubricDots'
import { showToast } from '../../stores/toast-store'
import type { Interview } from '../../types'
import { getMyInterviews } from '../../api/interviews'
import InterviewRespondPanel from './interviews/InterviewRespondPanel'
import {
  ArrowLeft, Check, Circle, Upload, Sparkles, AlertCircle, FileCheck, FileText, ListChecks,
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
import type { Application, ChecklistItem, WorkshopFeedbackRun } from '../../types'

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

// The checklist GET 404s when one hasn't been generated yet — that's the only
// case we silently fall back to POST /checklist. A transient 5xx/network error
// must surface (so the tab shows QueryError), not masquerade as "generate".
// client.ts collapses the AxiosError into Error(message) (status on 404 →
// "...status code 404"; on a backend detail → the detail text), so we sniff
// the message rather than err.response.status.
function isMissingChecklist(err: unknown): boolean {
  const msg = (err instanceof Error ? err.message : String(err)).toLowerCase()
  return msg.includes('404') || msg.includes('not found') || msg.includes('no checklist')
}

export default function ApplicationDetailPage() {
  const { appId } = useParams<{ appId: string }>()
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const checklistFocus = searchParams.get('checklist')
  const queryClient = useQueryClient()
  // Honor /s/applications/:id?tab=offer deep links (spec 18 §5).
  const [tab, setTab] = useState(searchParams.get('tab') || 'checklist')

  // Upload state
  const [uploading, setUploading] = useState(false)
  const [uploadProgress, setUploadProgress] = useState(0)
  const [dragOver, setDragOver] = useState(false)

  // Readiness + submit gate state
  const [readiness, setReadiness] = useState<any>(null)
  const [showReadiness, setShowReadiness] = useState(false)
  const [markedReady, setMarkedReady] = useState(false)
  const [submitBlockers, setSubmitBlockers] = useState<string[] | null>(null)

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

  const { data: app, isLoading, isError: appError, refetch: refetchApp } = useQuery({ queryKey: ['application', appId], queryFn: () => getMyApplication(appId!) })
  const { data: checklist, isError: checklistError, refetch: refetchChecklist } = useQuery({
    queryKey: ['checklist', appId],
    queryFn: () =>
      getChecklist(appId!).catch(err => {
        // Only auto-generate when there genuinely isn't one yet; let a transient
        // 5xx/network error propagate so we render an error, not a stale generate.
        if (isMissingChecklist(err)) return generateChecklist(appId!)
        throw err
      }),
  })
  // Essays tab — workshop feedback runs (feedback-only by spec). The legacy
  // /students/me/essays endpoints are Phase-E deletion targets; drafting lives
  // with the student, feedback lives in Apply → Workshops.
  const { data: essayRuns, isLoading: essayRunsLoading, isError: essayRunsError, refetch: refetchEssayRuns } = useQuery({
    queryKey: ['workshop-runs', 'essay'],
    queryFn: () => listWorkshopRuns('essay'),
    enabled: tab === 'essays',
  })
  const { data: documents, isError: documentsError, refetch: refetchDocuments } = useQuery({ queryKey: ['documents'], queryFn: listDocuments, enabled: tab === 'documents' })
  const { data: interviews, isLoading: interviewsLoading, isError: interviewsError, refetch: refetchInterviews } = useQuery({ queryKey: ['interviews', appId], queryFn: getMyInterviews, enabled: tab === 'interviews' })
  const { data: recommenders, isLoading: recommendersLoading, isError: recommendersError, refetch: refetchRecommenders } = useQuery({ queryKey: ['recommendations'], queryFn: listRecommendations, enabled: tab === 'recommenders' })
  const { data: cost, isError: costError, refetch: refetchCost } = useQuery({ queryKey: ['payment', appId], queryFn: () => getCostTracker(appId!), enabled: !!appId })

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

  usePageTitle(app?.program?.program_name || 'Application')

  if (isLoading) return <div className="p-6"><Skeleton className="h-64" /></div>
  // A failed fetch is retryable — don't conflate it with a genuine 404.
  if (appError)
    return (
      <div className="p-6 max-w-5xl w-full mx-auto">
        <QueryError detail="We couldn't load this application." onRetry={() => refetchApp()} />
      </div>
    )
  if (!app) return <div className="p-6 text-center text-foreground">Application not found.</div>

  const application: Application = app
  const currentStepIdx = STATUS_STEPS.indexOf(application.status)
  const checklistItems: ChecklistItem[] = checklist?.items ?? []
  const completionPct = checklist?.completion_percentage ?? application.readiness_pct ?? 0
  const documentsList: any[] = Array.isArray(documents) ? documents : []
  const resumeDocs = documentsList.filter((d: any) => d.document_type === 'resume')
  // Essay workshop runs relevant to this application — program-specific runs
  // targeting this program, plus general (untargeted) runs. Newest first.
  const essayRunsList: WorkshopFeedbackRun[] = (Array.isArray(essayRuns) ? essayRuns : [])
    .filter(r => !r.target_program_id || r.target_program_id === application.program_id)
    .sort((a, b) => (b.created_at || '').localeCompare(a.created_at || ''))
  const recommendersList: any[] = Array.isArray(recommenders) ? recommenders : []
  const isExternal = application.submission_mode === 'external'
  // Fitness on a 0-100 scale (score stored 0-1). Spec 15 §6.5 low-fit ≤ 30.
  // Read dual-score fitness first; fall back to legacy match_score (dropped in
  // Phase E) so this doesn't zero out. `app` is the untyped query payload.
  const rawFitness = app.fitness_score ?? application.match_score
  const fitnessPct = rawFitness != null ? Math.round(Number(rawFitness) * 100) : null
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
    <div className="p-6 max-w-5xl w-full mx-auto">
      <Breadcrumbs
        className="mb-4"
        items={[{ label: 'Apply', to: '/s/manage' }, { label: 'Applications', to: '/s/manage' }, { label: programName }]}
      />
      <button onClick={() => navigate('/s/manage')} className="flex items-center gap-1 text-sm text-muted-foreground hover:text-secondary mb-4">
        <ArrowLeft size={16} /> Back to Apply
      </button>

      <div className="flex items-start justify-between gap-3 flex-wrap">
        <div>
          <h1 className="text-xl font-bold text-foreground mb-1">{programName}</h1>
          {application.program?.institution_name && (
            <p className="text-sm text-muted-foreground flex items-center gap-1"><Building2 size={13} /> {application.program.institution_name}</p>
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
            <p className="text-sm font-medium text-foreground">
              {DECISION_STATE_LABEL[application.decision_state || application.decision] ||
                `Decision: ${application.decision}`}
            </p>
            {application.decision === 'admitted' && application.student_decision !== 'accepted_by_student' && (
              <p className="text-xs text-muted-foreground">Review your offer in the Offer tab.</p>
            )}
            {application.student_decision === 'accepted_by_student' && (
              <p className="text-xs text-muted-foreground">You&apos;re in — enrollment steps are on your calendar.</p>
            )}
          </div>
          {application.decision === 'admitted' && application.student_decision !== 'accepted_by_student' && (
            <button
              onClick={() => setTab('offer')}
              className="text-xs text-secondary font-medium shrink-0 hover:underline"
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
                  done ? 'bg-success text-white' : current ? 'bg-secondary text-secondary-foreground' : 'bg-muted text-muted-foreground'
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
            <span key={step} className={`text-[11px] ${i === currentStepIdx ? 'text-secondary font-medium' : 'text-muted-foreground'}`}>
              {STATUS_STEP_LABELS[step]}
            </span>
          ))}
        </div>
      </div>

      <div className="flex flex-col gap-6 lg:flex-row">
        {/* Sidebar — stacks full-width above the tabs on narrow viewports,
            becomes the 240px column from lg up. */}
        <div className="w-full space-y-4 lg:w-60 lg:flex-shrink-0">
          <Card className="p-4">
            <h3 className="font-medium text-sm text-foreground mb-3">Checklist</h3>
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
                  <span className={item.status === 'completed' ? 'text-muted-foreground line-through' : 'text-foreground'}>
                    {item.name}
                  </span>
                </div>
              ))}
              {checklistItems.length === 0 && (
                checklistError ? (
                  <QueryError
                    variant="inline"
                    detail="We couldn't load your checklist."
                    onRetry={() => refetchChecklist()}
                  />
                ) : (
                  <p className="text-xs text-muted-foreground">Generating checklist…</p>
                )
              )}
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
          {/* Fee info is money-critical — surface a load failure rather than
              silently hiding a fee the student may owe. */}
          {costError && (
            <Card className="p-4">
              <QueryError
                variant="inline"
                detail="We couldn't load fee details."
                onRetry={() => refetchCost()}
              />
            </Card>
          )}

          {/* Submission mode (§7) */}
          {application.status === 'draft' && (
            <Card className="p-4">
              <h3 className="font-medium text-sm text-foreground mb-2">How will you submit?</h3>
              <div className="flex rounded-lg border border-border overflow-hidden text-xs">
                <button
                  onClick={() => !isExternal || modeMut.mutate('internal')}
                  className={`flex-1 px-2 py-1.5 ${!isExternal ? 'bg-secondary text-secondary-foreground' : 'text-foreground hover:bg-muted'}`}
                >
                  Through UniPaith
                </button>
                <button
                  onClick={() => isExternal || modeMut.mutate('external')}
                  className={`flex-1 px-2 py-1.5 ${isExternal ? 'bg-secondary text-secondary-foreground' : 'text-foreground hover:bg-muted'}`}
                >
                  Their portal
                </button>
              </div>
              <p className="text-[11px] text-muted-foreground mt-2">
                {isExternal
                  ? "You'll submit on the institution's portal. Mark items complete here and attach confirmation evidence."
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
                {checklistError && checklistItems.length === 0 ? (
                  <QueryError
                    variant="inline"
                    detail="We couldn't load your checklist."
                    onRetry={() => refetchChecklist()}
                  />
                ) : (
                  <ChecklistTab
                    items={checklistItems}
                    completionPct={completionPct}
                    isExternal={isExternal}
                    canToggle={application.status === 'draft'}
                    onToggle={(key, completed) => toggleMut.mutate({ key, completed })}
                  />
                )}
              </>
            )}

            {tab === 'documents' && (
              <div className="space-y-4">
                <div
                  onDragOver={e => { e.preventDefault(); setDragOver(true) }}
                  onDragLeave={() => setDragOver(false)}
                  onDrop={handleDrop}
                  className={`border-2 border-dashed rounded-lg p-6 text-center transition-colors ${dragOver ? 'border-secondary bg-muted' : 'border-border hover:border-secondary/40'}`}
                >
                  <Upload size={24} className="mx-auto text-foreground mb-2" />
                  <p className="text-sm text-foreground mb-1">Drag & drop files here, or</p>
                  <label className="inline-block">
                    <input type="file" multiple className="hidden" onChange={e => e.target.files && handleFileUpload(e.target.files)} />
                    <span className="text-sm font-medium text-secondary underline cursor-pointer">browse files</span>
                  </label>
                  <p className="text-xs text-muted-foreground mt-1">PDF, DOC, DOCX up to 10MB</p>
                </div>

                {uploading && (
                  <div className="space-y-1">
                    <div className="flex justify-between text-xs text-muted-foreground"><span>Uploading…</span><span>{uploadProgress}%</span></div>
                    <ProgressBar value={uploadProgress} />
                  </div>
                )}

                {documentsError && (
                  <QueryError
                    variant="inline"
                    detail="We couldn't load your uploaded documents."
                    onRetry={() => refetchDocuments()}
                  />
                )}

                {documentsList.length > 0 && (
                  <div className="space-y-2">
                    <h3 className="text-sm font-medium text-muted-foreground">Uploaded documents</h3>
                    {documentsList.map((doc: any) => (
                      <div key={doc.id} className="flex justify-between items-center p-3 rounded-lg border border-border text-sm">
                        <div className="flex items-center gap-2"><FileCheck size={16} className="text-success" /><span className="text-foreground">{doc.file_name}</span></div>
                        <Badge variant="neutral">{doc.document_type}</Badge>
                      </div>
                    ))}
                  </div>
                )}

                {/* Resume / CV (a document — upload it via the dropzone above) */}
                <div className="flex items-center justify-between gap-3 p-3 rounded-lg border border-border">
                  <div className="text-sm text-foreground">
                    Resume / CV {resumeDocs.length > 0 && <Badge variant="success">On file</Badge>}
                  </div>
                  {resumeDocs.length === 0 && (
                    <span className="text-xs text-muted-foreground">Upload your resume or CV above.</span>
                  )}
                </div>

                {documentsList.length === 0 && !uploading && (
                  <p className="text-sm text-muted-foreground">Upload transcripts, recommendations, and other required documents above.</p>
                )}
              </div>
            )}

            {tab === 'essays' && (
              <div className="space-y-4">
                {/* Workshops are feedback-only by spec — no drafting here. This
                    tab shows past essay-feedback runs relevant to this program;
                    new feedback happens in Apply → Workshops. */}
                <Card className="p-4 flex items-center justify-between gap-3 flex-wrap">
                  <div className="min-w-0">
                    <p className="text-sm font-medium text-foreground">Essay feedback</p>
                    <p className="text-xs text-muted-foreground mt-0.5">
                      Workshops score your draft and flag what's missing — they never write it for you.
                    </p>
                  </div>
                  <Button size="sm" variant="secondary" className="shrink-0" onClick={() => navigate('/s/manage?tab=workshops')}>
                    <Sparkles size={14} className="mr-1" /> Get essay feedback
                  </Button>
                </Card>
                {essayRunsLoading ? (
                  <SkeletonCard />
                ) : essayRunsError && essayRunsList.length === 0 ? (
                  <QueryError
                    variant="inline"
                    detail="We couldn't load your essay feedback."
                    onRetry={() => refetchEssayRuns()}
                  />
                ) : essayRunsList.length === 0 ? (
                  <Card className="p-6 text-center">
                    <FileText size={32} className="text-muted-foreground mx-auto mb-3" />
                    <p className="text-sm text-foreground">No essay feedback yet.</p>
                    <p className="text-xs text-muted-foreground mt-1">
                      Run a draft through the essay workshop to see its feedback here.
                    </p>
                  </Card>
                ) : (
                  essayRunsList.map(run => (
                    <Card key={run.id} className="p-4">
                      <div className="flex justify-between items-start gap-3 mb-3 flex-wrap">
                        <div className="min-w-0">
                          <p className="font-medium text-sm text-foreground">{run.prompt_text || 'Essay draft'}</p>
                          <div className="flex items-center gap-2 mt-1">
                            <span className="text-xs text-muted-foreground">
                              {new Date(run.created_at).toLocaleDateString()}
                            </span>
                            <Badge variant={run.target_program_id ? 'info' : 'neutral'}>
                              {run.target_program_id ? 'This program' : 'General'}
                            </Badge>
                          </div>
                        </div>
                        <AIBadge fallback={run.is_stub} />
                      </div>
                      <RubricScores scores={run.rubric_scores} />
                      {((run.structural_issues?.length ?? 0) > 0 || (run.missing_elements?.length ?? 0) > 0) && (
                        <p className="text-xs text-muted-foreground mt-3">
                          {run.structural_issues?.length ?? 0} structural issue{(run.structural_issues?.length ?? 0) !== 1 ? 's' : ''}
                          {' · '}
                          {run.missing_elements?.length ?? 0} missing element{(run.missing_elements?.length ?? 0) !== 1 ? 's' : ''}
                        </p>
                      )}
                    </Card>
                  ))
                )}
              </div>
            )}

            {tab === 'recommenders' && (
              recommendersLoading ? (
                <SkeletonCard />
              ) : recommendersError && recommendersList.length === 0 ? (
                <QueryError
                  variant="inline"
                  detail="We couldn't load your recommenders."
                  onRetry={() => refetchRecommenders()}
                />
              ) : (
                <RecommendersTab
                  recommenders={recommendersList}
                  programId={application.program_id}
                  onNudge={async (id) => { await sendRecommendationRequest(id); queryClient.invalidateQueries({ queryKey: ['recommendations'] }); showToast('Reminder sent', 'success') }}
                />
              )
            )}

            {tab === 'interviews' && (() => {
              const interviewList = Array.isArray(interviews)
                ? interviews.filter((i: { application_id: string }) => i.application_id === appId)
                : []
              return (
                <div className="space-y-4">
                  {interviewsLoading ? (
                    <SkeletonCard />
                  ) : interviewList.length > 0 ? (
                    interviewList.map((iv: Interview) => (
                      <InterviewRespondPanel key={iv.id} interview={iv} />
                    ))
                  ) : interviewsError ? (
                    <Card className="p-6">
                      <QueryError
                        variant="inline"
                        detail="We couldn't load your interviews."
                        onRetry={() => refetchInterviews()}
                      />
                    </Card>
                  ) : (
                    <Card className="p-6 text-center">
                      <Users size={32} className="text-muted-foreground mx-auto mb-3" />
                      <p className="text-sm text-foreground">No interviews scheduled yet.</p>
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
                      <p className="text-sm font-medium text-foreground">Low-fit warning</p>
                      <p className="text-xs text-muted-foreground mt-0.5">
                        {fitnessPct != null ? `This program's fitness is ${fitnessPct}%.` : 'This program may be a low-fit option.'} Review your Match analysis before committing effort here.
                      </p>
                    </div>
                  </div>
                )}

                <Card className="p-4">
                  <div className="flex items-center gap-2 mb-3"><ShieldCheck size={16} className="text-secondary" /><h3 className="text-sm font-medium text-foreground">Why are you applying?</h3></div>
                  <div className="flex flex-wrap gap-2 mb-3">
                    {INTENT_OPTIONS.map(opt => (
                      <button
                        key={opt.value}
                        onClick={() => setIntentReason(opt.value)}
                        className={`px-3 py-1.5 text-xs rounded-full border transition-colors ${
                          (intentReason || application.intent_picker) === opt.value
                            ? 'bg-foreground text-background border-foreground' : 'bg-card text-foreground border-border hover:bg-muted'
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
                      <p className="text-[11px] text-foreground mt-1 text-right">{(rationale || application.intent_rationale || '').length}/80</p>
                    </div>
                  )}
                  <Button
                    size="sm"
                    variant="tertiary"
                    disabled={
                      (!intentReason && !application.intent_picker) ||
                      (RATIONALE_REQUIRED.includes(intentReason || application.intent_picker || '') &&
                        (rationale || application.intent_rationale || '').trim().length < 80)
                    }
                    loading={intentMut.isPending}
                    onClick={() => intentMut.mutate()}
                  >
                    Save intent
                  </Button>
                </Card>

                <Card className="p-4">
                  <div className="flex items-center justify-between mb-2">
                    <h3 className="text-sm font-medium text-foreground">Guardrail scan</h3>
                    <Button size="sm" onClick={runGuardrailScan} loading={scanning}>Run scan</Button>
                  </div>
                  <p className="text-xs text-muted-foreground mb-3">Checks fit and flags anything to reconsider before you apply.</p>
                  {(guardrailResult || application.fit_band) && (
                    <div className={`rounded-lg p-3 ${
                      (guardrailResult?.fit_band || application.fit_band) === 'high' ? 'bg-success-soft'
                        : (guardrailResult?.fit_band || application.fit_band) === 'low' ? 'bg-warning-soft' : 'bg-muted'
                    }`}>
                      <div className="flex items-center gap-2 mb-1">
                        <Badge variant={(guardrailResult?.fit_band || application.fit_band) === 'high' ? 'success' : (guardrailResult?.fit_band || application.fit_band) === 'low' ? 'warning' : 'info'}>
                          {(guardrailResult?.fit_band || application.fit_band)} fit
                        </Badge>
                        {guardrailResult?.recommended_action && <span className="text-xs text-muted-foreground">Recommended: {guardrailResult.recommended_action}</span>}
                        {guardrailResult?.is_rule_based && <span className="text-[10px] text-muted-foreground">Showing rule-based result</span>}
                      </div>
                      {(guardrailResult?.blockers || application.guardrail_blockers || []).length > 0 ? (
                        <ul className="mt-2 space-y-1">
                          {(guardrailResult?.blockers || application.guardrail_blockers || []).map((b: string, i: number) => (
                            <li key={i} className="text-xs text-foreground flex items-start gap-1"><AlertCircle size={11} className="mt-0.5 flex-shrink-0" /> {b}</li>
                          ))}
                        </ul>
                      ) : (
                        <p className="text-xs text-foreground mt-1">No blockers — you're clear to proceed.</p>
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

      {/* Readiness Check Modal */}
      <Modal isOpen={showReadiness} onClose={() => setShowReadiness(false)} title="Application readiness">
        {readiness && (
          <div className="space-y-4">
            <div className="flex items-center gap-3">
              <div className={`w-12 h-12 rounded-full flex items-center justify-center ${readiness.is_ready ? 'bg-success-soft' : 'bg-warning-soft'}`}>
                {readiness.is_ready ? <Check size={24} className="text-success" /> : <AlertCircle size={24} className="text-warning" />}
              </div>
              <div>
                <p className="font-medium text-foreground">{readiness.is_ready ? 'Ready to submit!' : 'Almost there'}</p>
                <p className="text-sm text-muted-foreground">{readiness.completion_percentage}% complete</p>
              </div>
            </div>
            <ProgressBar value={readiness.completion_percentage} />
            {readiness.missing_items?.length > 0 && (
              <div>
                <h4 className="text-sm font-medium text-foreground mb-2">Missing items:</h4>
                <ul className="space-y-1">
                  {readiness.missing_items.map((item: string, i: number) => (
                    <li key={i} className="flex items-center gap-2 text-sm text-foreground"><Circle size={8} className="text-muted-foreground flex-shrink-0" /> {item}</li>
                  ))}
                </ul>
              </div>
            )}
            {readiness.warnings?.length > 0 && (
              <div>
                <h4 className="text-sm font-medium text-foreground mb-2">Warnings:</h4>
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
      <Modal isOpen={!!submitBlockers} onClose={() => setSubmitBlockers(null)} title="A few items still need attention">
        <ul className="space-y-2">
          {(submitBlockers || []).map((b, i) => (
            <li key={i} className="flex items-center gap-2 text-sm text-foreground"><AlertCircle size={14} className="text-warning flex-shrink-0" /> {b}</li>
          ))}
        </ul>
        <div className="flex gap-2 mt-4">
          <Button className="flex-1" variant="secondary" onClick={() => { setSubmitBlockers(null); setTab('checklist') }}>Go to checklist</Button>
          <Button className="flex-1" variant="tertiary" onClick={() => setSubmitBlockers(null)}>Got it</Button>
        </div>
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
          <p className="text-sm text-foreground">
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
        <HandCoins size={15} className="text-secondary" />
        <h3 className="font-medium text-sm text-foreground">Application fee</h3>
      </div>
      <p className="text-2xl font-bold text-foreground tabular-nums mb-2">{money}</p>

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
            <div className="rounded-lg bg-muted px-3 py-2 text-xs text-foreground">
              Refunded {formatMoney(fee.refunded_amount || 0, fee.currency)} of {money}.
            </div>
          )}
          <button onClick={receipt} className="text-xs text-secondary hover:underline inline-flex items-center gap-1">
            <Download size={12} /> Download receipt
          </button>
        </div>
      )}
      {waived && <Badge variant="info">Fee waived</Badge>}
      {processing && <p className="text-xs text-foreground">Confirming your payment…</p>}
      {failed && (
        <p className="text-xs text-warning">That payment didn't go through. Try again or request a waiver.</p>
      )}
      {waiverPending && (
        <div className="space-y-1.5">
          <Badge variant="warning">Waiver requested — the school will review it</Badge>
          {fee.waiver_policy === 'allow_and_reconcile' && (
            <p className="text-xs text-foreground">You can submit now; the school reconciles the fee.</p>
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
        <p className="text-xs text-foreground mt-1">Fee status: {fee.status.replace(/_/g, ' ')}.</p>
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
          <div className="flex items-center gap-2"><ListChecks size={16} className="text-secondary" /><span className="text-sm font-medium text-foreground">Readiness: {completionPct}%</span></div>
          {completionPct >= 100 && <Badge variant="success">Ready to submit</Badge>}
        </div>
        <ProgressBar value={completionPct} />
        {isExternal && <p className="text-xs text-muted-foreground mt-2">External submission — check items off as you complete them on the institution's portal.</p>}
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
                    aria-label={item.name}
                    checked={item.status === 'completed'}
                    disabled={!canToggle || (!isExternal && item.owner === 'recommender')}
                    onChange={e => item.key && onToggle(item.key, e.target.checked)}
                    className="rounded border-border text-secondary focus:ring-secondary"
                  />
                  <div className="min-w-0">
                    <p className="text-sm text-foreground">{item.name}</p>
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
        <Card className="p-6 text-center"><ListChecks size={32} className="text-muted-foreground mx-auto mb-3" /><p className="text-sm text-foreground">No checklist items yet.</p></Card>
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
        <p className="text-sm text-foreground">No recommenders yet.</p>
        <p className="text-xs text-muted-foreground mt-1">Add recommenders from your Profile to request letters for this program.</p>
      </Card>
    )
  return (
    <div className="space-y-3">
      {relevant.map(r => (
        <Card key={r.id} className="p-4 flex items-center justify-between gap-3">
          <div className="min-w-0">
            <p className="text-sm font-medium text-foreground">{r.recommender_name}</p>
            <p className="text-xs text-muted-foreground">{r.recommender_title || r.relationship || r.recommender_institution || 'Recommender'}</p>
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
