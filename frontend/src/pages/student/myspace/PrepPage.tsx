import { useState, useEffect, useRef, useMemo, lazy, Suspense } from 'react'
import { useSearchParams, useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { ArrowRight, CalendarClock, FileText, GraduationCap, Mail, NotebookPen } from 'lucide-react'
import { PageHeader } from '../../../components/student/density'
import Badge from '../../../components/ui/Badge'
import Button from '../../../components/ui/Button'
import Skeleton from '../../../components/ui/Skeleton'
import { getSummary } from '../../../api/prompt-library'
import { listDocuments } from '../../../api/documents'
import { getMyInterviews } from '../../../api/interviews'
import { listRecommendations } from '../../../api/recommendations'
import type { Interview, RecommendationRequest } from '../../../types'
import type { PromptLibrarySummary } from '../../../types/promptLibrary'

// My Space › Prep (Spec 2026-06-10 §5) — the preparation room. Gathers
// Workshops + Prompts (from /s/manage) and Interviews + Recommenders +
// Documents (from Profile › Preparation). Workshops stay feedback-only by spec.

const WorkshopsTab = lazy(() => import('../apply/WorkshopsTab'))
const PromptLibraryTab = lazy(() => import('../apply/promptlibrary/PromptLibraryTab'))
const InterviewsTab = lazy(() => import('./prep/InterviewsTab'))
const RecommendersTab = lazy(() => import('./prep/RecommendersTab'))
const DocumentsTab = lazy(() => import('./prep/DocumentsTab'))

type Tab = 'workshops' | 'prompts' | 'interviews' | 'recommenders' | 'documents'

const TABS: { key: Tab; label: string; icon: typeof GraduationCap }[] = [
  { key: 'workshops', label: 'Workshops', icon: GraduationCap },
  { key: 'prompts', label: 'Prompts', icon: NotebookPen },
  { key: 'interviews', label: 'Interviews', icon: CalendarClock },
  { key: 'recommenders', label: 'Recommenders', icon: Mail },
  { key: 'documents', label: 'Documents', icon: FileText },
]

type PrepSignalStatus = 'ready' | 'watch' | 'attention' | 'loading' | 'unavailable'
type PrepSignal = {
  key: string
  label: string
  tab: Tab
  status: PrepSignalStatus
  value: string
  detail: string
  cta: string
}
type PrepDocument = { verification_status?: string | null }

const DAY_MS = 24 * 60 * 60 * 1000
const INTERVIEW_RESPONSE_STATUSES = new Set(['proposed', 'reschedule_requested'])
const INTERVIEW_SCHEDULED_STATUSES = new Set(['scheduled', 'confirmed'])

const statusBadge: Record<PrepSignalStatus, 'success' | 'warning' | 'error' | 'neutral'> = {
  ready: 'success',
  watch: 'warning',
  attention: 'error',
  loading: 'neutral',
  unavailable: 'neutral',
}

const statusLabel: Record<PrepSignalStatus, string> = {
  ready: 'Ready',
  watch: 'Watch',
  attention: 'Needs attention',
  loading: 'Loading',
  unavailable: 'Unavailable',
}

function formatCount(count: number, singular: string, plural = `${singular}s`) {
  return `${count} ${count === 1 ? singular : plural}`
}

function isDueSoon(dueDate: string | null | undefined) {
  if (!dueDate) return false
  const due = new Date(dueDate).getTime()
  if (Number.isNaN(due)) return false
  const now = Date.now()
  return due >= now - DAY_MS && due <= now + 7 * DAY_MS
}

function promptSignal(summary: PromptLibrarySummary | undefined, loading: boolean, error: boolean): PrepSignal {
  if (loading) {
    return { key: 'prompts', label: 'Prompts', tab: 'prompts', status: 'loading', value: 'Loading', detail: 'Checking prompt coverage.', cta: 'Review prompts' }
  }
  if (error) {
    return { key: 'prompts', label: 'Prompts', tab: 'prompts', status: 'unavailable', value: 'Not loaded', detail: "Couldn't load prompt readiness.", cta: 'Review prompts' }
  }

  const total = summary?.total_prompts ?? 0
  const answered = summary?.answered_count ?? 0
  const score = summary?.interview_readiness_score
  const pct = score != null ? Math.round(score) : total > 0 ? Math.round((answered / total) * 100) : 0
  const gaps = summary?.competency_coverage_gaps ?? []
  const status: PrepSignalStatus =
    summary?.interview_readiness_band === 'high' || pct >= 80
      ? 'ready'
      : summary?.interview_readiness_band === 'medium' || pct >= 50
        ? 'watch'
        : 'attention'
  const detail = gaps.length > 0
    ? `Missing coverage: ${gaps.slice(0, 2).join(', ')}${gaps.length > 2 ? ` +${gaps.length - 2}` : ''}`
    : total > 0
      ? `${answered} of ${total} prompts answered`
      : 'Answer core prompts so interviews and short answers have evidence.'

  return { key: 'prompts', label: 'Prompts', tab: 'prompts', status, value: `${pct}%`, detail, cta: 'Review prompts' }
}

function documentSignal(documents: PrepDocument[] | undefined, loading: boolean, error: boolean): PrepSignal {
  if (loading) {
    return { key: 'documents', label: 'Documents', tab: 'documents', status: 'loading', value: 'Loading', detail: 'Checking uploaded materials.', cta: 'Review documents' }
  }
  if (error) {
    return { key: 'documents', label: 'Documents', tab: 'documents', status: 'unavailable', value: 'Not loaded', detail: "Couldn't load documents.", cta: 'Review documents' }
  }

  const docs = Array.isArray(documents) ? documents : []
  const verified = docs.filter(doc => doc?.verification_status === 'verified').length
  if (docs.length === 0) {
    return { key: 'documents', label: 'Documents', tab: 'documents', status: 'attention', value: '0 files', detail: 'Upload transcripts, test scores, portfolios, or certificates.', cta: 'Upload documents' }
  }
  const pending = docs.length - verified
  return {
    key: 'documents',
    label: 'Documents',
    tab: 'documents',
    status: pending === 0 ? 'ready' : 'watch',
    value: `${verified}/${docs.length} verified`,
    detail: pending === 0
      ? 'All uploaded materials are verified.'
      : pending === 1
        ? '1 file still needs confirmation.'
        : `${pending} files still need confirmation.`,
    cta: 'Review documents',
  }
}

function interviewSignal(interviews: Interview[] | undefined, loading: boolean, error: boolean): PrepSignal {
  if (loading) {
    return { key: 'interviews', label: 'Interviews', tab: 'interviews', status: 'loading', value: 'Loading', detail: 'Checking invitations and scheduled interviews.', cta: 'Review interviews' }
  }
  if (error) {
    return { key: 'interviews', label: 'Interviews', tab: 'interviews', status: 'unavailable', value: 'Not loaded', detail: "Couldn't load interviews.", cta: 'Review interviews' }
  }

  const list = Array.isArray(interviews) ? interviews : []
  const needsResponse = list.filter(iv => INTERVIEW_RESPONSE_STATUSES.has(String(iv.status)) && !iv.async_expired).length
  const scheduled = list.filter(iv => INTERVIEW_SCHEDULED_STATUSES.has(String(iv.status))).length
  if (needsResponse > 0) {
    return {
      key: 'interviews',
      label: 'Interviews',
      tab: 'interviews',
      status: 'attention',
      value: formatCount(needsResponse, 'response'),
      detail: needsResponse === 1 ? '1 invitation needs your answer.' : `${needsResponse} invitations need your answer.`,
      cta: 'Respond to interviews',
    }
  }
  if (scheduled > 0) {
    return { key: 'interviews', label: 'Interviews', tab: 'interviews', status: 'ready', value: formatCount(scheduled, 'scheduled'), detail: 'No interview invitations are waiting on you.', cta: 'Review interviews' }
  }
  return { key: 'interviews', label: 'Interviews', tab: 'interviews', status: 'watch', value: 'No invites', detail: 'New invitations will appear here and in applications.', cta: 'Review interviews' }
}

function recommenderSignal(recommendations: RecommendationRequest[] | undefined, loading: boolean, error: boolean): PrepSignal {
  if (loading) {
    return { key: 'recommenders', label: 'Recommenders', tab: 'recommenders', status: 'loading', value: 'Loading', detail: 'Checking request status and deadlines.', cta: 'Review recommenders' }
  }
  if (error) {
    return { key: 'recommenders', label: 'Recommenders', tab: 'recommenders', status: 'unavailable', value: 'Not loaded', detail: "Couldn't load recommender requests.", cta: 'Review recommenders' }
  }

  const recs = Array.isArray(recommendations) ? recommendations : []
  const drafts = recs.filter(rec => rec.status === 'draft').length
  const dueSoon = recs.filter(rec => rec.status !== 'received' && isDueSoon(rec.due_date)).length
  const received = recs.filter(rec => rec.status === 'received').length
  const waiting = recs.filter(rec => rec.status === 'requested' || rec.status === 'submitted').length

  if (drafts > 0) {
    return { key: 'recommenders', label: 'Recommenders', tab: 'recommenders', status: 'attention', value: formatCount(drafts, 'draft'), detail: 'Send drafted requests before deadlines compress.', cta: 'Send requests' }
  }
  if (dueSoon > 0) {
    return { key: 'recommenders', label: 'Recommenders', tab: 'recommenders', status: 'attention', value: formatCount(dueSoon, 'deadline'), detail: 'Letter deadlines are close; nudge or confirm a backup.', cta: 'Nudge recommenders' }
  }
  if (waiting > 0) {
    return { key: 'recommenders', label: 'Recommenders', tab: 'recommenders', status: 'watch', value: formatCount(waiting, 'waiting'), detail: `${formatCount(received, 'letter')} received so far.`, cta: 'Review recommenders' }
  }
  if (received > 0) {
    return { key: 'recommenders', label: 'Recommenders', tab: 'recommenders', status: 'ready', value: formatCount(received, 'received'), detail: 'No recommender action is waiting on you.', cta: 'Review recommenders' }
  }
  return { key: 'recommenders', label: 'Recommenders', tab: 'recommenders', status: 'attention', value: '0 requests', detail: 'Add recommenders before applications require letters.', cta: 'Add recommenders' }
}

function pickNextAction(signals: PrepSignal[]): PrepSignal {
  const priority = ['interviews', 'recommenders', 'prompts', 'documents']
  return (
    priority.map(key => signals.find(signal => signal.key === key && signal.status === 'attention')).find(Boolean) ??
    priority.map(key => signals.find(signal => signal.key === key && signal.status === 'watch')).find(Boolean) ??
    priority.map(key => signals.find(signal => signal.key === key && signal.status === 'unavailable')).find(Boolean) ??
    signals[0] ??
    { key: 'prompts', label: 'Prompts', tab: 'prompts', status: 'unavailable', value: 'Not loaded', detail: 'Open prompts to review prep readiness.', cta: 'Review prompts' }
  )
}

export default function PrepPage() {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const rawTab = searchParams.get('tab') as Tab | null
  const [tab, setTab] = useState<Tab>(rawTab && TABS.some(t => t.key === rawTab) ? rawTab : 'workshops')
  const tablistRef = useRef<HTMLDivElement>(null)
  const promptSummary = useQuery({ queryKey: ['prompt-library', 'summary'], queryFn: getSummary, staleTime: 60_000, retry: false })
  const documents = useQuery({ queryKey: ['documents'], queryFn: listDocuments, staleTime: 60_000, retry: false })
  const interviews = useQuery({ queryKey: ['interviews', 'prep'], queryFn: getMyInterviews, staleTime: 60_000, retry: false })
  const recommenders = useQuery({ queryKey: ['recommendations'], queryFn: listRecommendations, staleTime: 60_000, retry: false })

  const prepSignals = useMemo(() => [
    promptSignal(promptSummary.data, promptSummary.isLoading, promptSummary.isError),
    documentSignal(documents.data as PrepDocument[] | undefined, documents.isLoading, documents.isError),
    interviewSignal(interviews.data, interviews.isLoading, interviews.isError),
    recommenderSignal(recommenders.data as RecommendationRequest[] | undefined, recommenders.isLoading, recommenders.isError),
  ], [
    promptSummary.data,
    promptSummary.isLoading,
    promptSummary.isError,
    documents.data,
    documents.isLoading,
    documents.isError,
    interviews.data,
    interviews.isLoading,
    interviews.isError,
    recommenders.data,
    recommenders.isLoading,
    recommenders.isError,
  ])
  const nextAction = pickNextAction(prepSignals)
  const hasAttention = prepSignals.some(signal => signal.status === 'attention')
  const hasWatch = prepSignals.some(signal => signal.status === 'watch' || signal.status === 'unavailable')
  const anyLoading = prepSignals.some(signal => signal.status === 'loading')
  const overallStatus: PrepSignalStatus = anyLoading ? 'loading' : hasAttention ? 'attention' : hasWatch ? 'watch' : 'ready'

  useEffect(() => {
    if (rawTab && TABS.some(t => t.key === rawTab) && rawTab !== tab) setTab(rawTab)
  }, [rawTab, tab])

  const switchTab = (t: Tab) => {
    setTab(t)
    // Preserve deep-link params other than tab (e.g. prompts ?view=major).
    const params = new URLSearchParams(searchParams)
    params.delete('view')
    if (t === 'workshops') params.delete('tab')
    else params.set('tab', t)
    const qs = params.toString()
    navigate(qs ? `/s/prep?${qs}` : '/s/prep', { replace: true })
  }

  // Roving-tabindex arrow navigation (mirrors the ProfilePage tablist pattern).
  const handleTabKeyDown = (e: React.KeyboardEvent) => {
    const idx = TABS.findIndex(t => t.key === tab)
    let next = -1
    if (e.key === 'ArrowRight') next = (idx + 1) % TABS.length
    else if (e.key === 'ArrowLeft') next = (idx - 1 + TABS.length) % TABS.length
    else if (e.key === 'Home') next = 0
    else if (e.key === 'End') next = TABS.length - 1
    if (next === -1) return
    e.preventDefault()
    switchTab(TABS[next].key)
    const buttons = tablistRef.current?.querySelectorAll<HTMLButtonElement>('[role="tab"]')
    buttons?.[next]?.focus()
  }

  return (
    <div className="flex min-h-0 flex-1 flex-col">
      {/* Room header — consistent with the other My Space rooms (eyebrow = surface). */}
      <div className="flex-shrink-0 px-4 sm:px-6 pt-5">
        <PageHeader
          eyebrow="My Space"
          title="Prep"
          sub="Get application-ready — feedback, practice, and the assets behind every submission"
        />
      </div>

      <section aria-label="Prep readiness" className="flex-shrink-0 border-y border-border bg-muted/30 px-4 py-4 sm:px-6">
        <div className="flex flex-col gap-3 xl:flex-row xl:items-center xl:justify-between">
          <div className="min-w-0">
            <div className="flex flex-wrap items-center gap-2">
              <p className="text-eyebrow uppercase text-muted-foreground">Readiness header</p>
              <Badge variant={statusBadge[overallStatus]}>{statusLabel[overallStatus]}</Badge>
            </div>
            <h2 className="mt-1 text-lg font-semibold text-foreground">Prep readiness across prompts, materials, interviews, and letters</h2>
            <p className="mt-1 max-w-3xl text-sm text-muted-foreground">
              Based on the Prompt Library, uploaded documents, interview invitations, and recommender requests. Open the highest-risk item first.
            </p>
          </div>
          <Button
            size="sm"
            variant={overallStatus === 'ready' ? 'tertiary' : 'secondary'}
            onClick={() => switchTab(nextAction.tab)}
            aria-label={`${nextAction.cta}: ${nextAction.detail}`}
            className="w-full sm:w-fit"
          >
            {nextAction.cta}
            <ArrowRight size={14} />
          </Button>
        </div>

        <div className="mt-4 grid gap-2 md:grid-cols-2 xl:grid-cols-4">
          {prepSignals.map(signal => (
            <button
              type="button"
              key={signal.key}
              onClick={() => switchTab(signal.tab)}
              className={`rounded-lg border bg-card p-3 text-left transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring ${
                tab === signal.tab ? 'border-secondary' : 'border-border hover:border-secondary/50'
              }`}
              aria-label={`${signal.label}: ${signal.detail}`}
            >
              <div className="flex items-start justify-between gap-2">
                <p className="text-sm font-semibold text-foreground">{signal.label}</p>
                <Badge variant={statusBadge[signal.status]}>{statusLabel[signal.status]}</Badge>
              </div>
              {signal.status === 'loading' ? (
                <div className="mt-3 space-y-2">
                  <Skeleton className="h-4 w-20" />
                  <Skeleton className="h-3 w-full" />
                </div>
              ) : (
                <>
                  <p className="mt-3 text-xl font-semibold text-foreground">{signal.value}</p>
                  <p className="mt-1 min-h-[2.5rem] text-xs leading-5 text-muted-foreground">{signal.detail}</p>
                </>
              )}
            </button>
          ))}
        </div>
      </section>

      {/* Hidden on lg+ where the My Space rail's Workspace group lists these tabs
          flat (Spec 2026-06-15 §2.2); kept below lg where the rail collapses to pills. */}
      <div className="lg:hidden flex-shrink-0 border-b border-border bg-card px-4 sm:px-6">
        {/* 5 tabs must survive 360px — scroll horizontally instead of wrapping. */}
        <div
          ref={tablistRef}
          role="tablist"
          aria-label="Prep"
          className="flex flex-nowrap gap-0.5 overflow-x-auto whitespace-nowrap no-scrollbar"
          onKeyDown={handleTabKeyDown}
        >
          {TABS.map(t => (
            <button
              key={t.key}
              role="tab"
              id={`prep-tab-${t.key}`}
              aria-selected={tab === t.key}
              aria-controls={`prep-panel-${t.key}`}
              tabIndex={tab === t.key ? 0 : -1}
              onClick={() => switchTab(t.key)}
              className={`flex shrink-0 items-center gap-1.5 border-b-2 px-4 py-3 text-sm font-medium transition-colors ${
                tab === t.key
                  ? 'border-secondary text-foreground'
                  : 'border-transparent text-muted-foreground hover:text-foreground'
              }`}
            >
              <t.icon size={15} />
              {t.label}
            </button>
          ))}
        </div>
      </div>

      <div
        role="tabpanel"
        id={`prep-panel-${tab}`}
        aria-labelledby={`prep-tab-${tab}`}
        tabIndex={0}
        className="min-h-0 flex-1 overflow-y-auto focus-visible:outline-none"
      >
        <Suspense fallback={<div className="p-6 text-center text-muted-foreground">Loading...</div>}>
          {tab === 'workshops' && <WorkshopsTab />}
          {tab === 'prompts' && <PromptLibraryTab />}
          {tab === 'interviews' && <InterviewsTab />}
          {tab === 'recommenders' && <RecommendersTab />}
          {tab === 'documents' && <DocumentsTab />}
        </Suspense>
      </div>
    </div>
  )
}
