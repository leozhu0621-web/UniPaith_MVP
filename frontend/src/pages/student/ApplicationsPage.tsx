import { useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { listMyApplications } from '../../api/applications'
import Card from '../../components/ui/Card'
import Badge from '../../components/ui/Badge'
import Select from '../../components/ui/Select'
import EmptyState from '../../components/ui/EmptyState'
import { SkeletonCard } from '../../components/ui/Skeleton'
import { formatDate } from '../../utils/format'
import { STATUS_COLORS } from '../../utils/constants'
import { FileText, Star, ChevronRight, CalendarClock, PartyPopper, ArrowRight, Mail } from 'lucide-react'
import DecisionComparison from './apply/offer/DecisionComparison'
import { deadlineTone, DEADLINE_TONE_CLASS, hasPendingOfferResponse } from './apply/offer/offerFormat'
import type { Application } from '../../types'

type Bucket =
  | 'not_started'
  | 'in_progress'
  | 'ready'
  | 'submitted'
  | 'under_review'
  | 'decided'

const BUCKET_LABELS: Record<Bucket, string> = {
  not_started: 'Not started',
  in_progress: 'In progress',
  ready: 'Ready to submit',
  submitted: 'Submitted',
  under_review: 'Under review',
  decided: 'Decided',
}

const BUCKET_ORDER: Bucket[] = [
  'not_started',
  'in_progress',
  'ready',
  'submitted',
  'under_review',
  'decided',
]

function bucketOf(app: Application): Bucket {
  const pct = app.readiness_pct ?? 0
  switch (app.status) {
    case 'submitted':
      return 'submitted'
    case 'under_review':
    case 'interview':
      return 'under_review'
    case 'decision_made':
      return 'decided'
    default: // draft
      if (pct >= 100) return 'ready'
      if (pct > 0) return 'in_progress'
      return 'not_started'
  }
}

function daysUntil(deadline?: string | null): number | null {
  if (!deadline) return null
  return Math.ceil((new Date(deadline).getTime() - Date.now()) / 86400000)
}

/** Human "Next: <action>" string for a row (spec 15 §2). */
function nextAction(app: Application): string {
  const b = bucketOf(app)
  const pct = app.readiness_pct ?? 0
  switch (b) {
    case 'ready':
      return 'Ready now — submit your application'
    case 'in_progress':
      return `Finish your checklist (${pct}%)`
    case 'not_started':
      return 'Start your checklist'
    case 'submitted':
      return 'Submitted — awaiting review'
    case 'under_review':
      return app.status === 'interview' ? 'Prepare for your interview' : 'Under review'
    case 'decided':
      if (hasPendingOfferResponse(app)) return 'Respond to your offer'
      return `Decision: ${app.decision ?? app.decision_state ?? 'received'}`
  }
}

function appHref(app: Application): string {
  if (hasPendingOfferResponse(app) || app.offer) return `/s/applications/${app.id}?tab=offer`
  return `/s/applications/${app.id}`
}

/** Priority score for the ★ Next actions rail — higher = more urgent. */
function actionScore(app: Application): number {
  const b = bucketOf(app)
  const d = daysUntil(app.program?.application_deadline)
  const offerDays = daysUntil(app.offer?.response_deadline)
  let score = 0
  if (b === 'ready') score += 100
  if (hasPendingOfferResponse(app)) {
    score += 95
    if (offerDays != null && offerDays >= 0 && offerDays <= 14) score += 40 - offerDays
  } else if (b === 'decided' && app.decision === 'admitted' && app.offer?.status !== 'accepted')
    score += 90
  if (app.status === 'interview') score += 80
  if (b === 'in_progress') score += 40
  if (d != null && d >= 0 && d <= 14) score += 30 - d // deadline pressure
  if (d != null && d < 0 && (b === 'not_started' || b === 'in_progress' || b === 'ready'))
    score += 25 // overdue & not yet submitted
  return score
}

export default function ApplicationsPage() {
  const navigate = useNavigate()
  const [statusFilter, setStatusFilter] = useState<'all' | Bucket>('all')
  const [institution, setInstitution] = useState('all')
  const [deadlineWindow, setDeadlineWindow] = useState('all')
  const [sort, setSort] = useState<'deadline' | 'readiness' | 'fit'>('deadline')
  const [showCompare, setShowCompare] = useState(false)

  const { data, isLoading } = useQuery({ queryKey: ['my-applications'], queryFn: listMyApplications })
  const apps: Application[] = useMemo(() => (Array.isArray(data) ? data : []), [data])

  // Spec 18 — offer/decision summary for the portfolio banners.
  const acceptedApp = useMemo(
    () => apps.find(a => a.student_decision === 'accepted_by_student'),
    [apps],
  )
  const offerApps = useMemo(() => apps.filter(a => a.offer), [apps])
  const pendingOfferApps = useMemo(
    () => offerApps.filter(a => !a.offer?.student_response && a.student_decision == null),
    [offerApps],
  )
  const awaitingDecisionApps = useMemo(
    () =>
      apps.filter(
        a =>
          !a.offer &&
          a.student_decision == null &&
          ['submitted', 'under_review', 'interview'].includes(a.status || ''),
      ),
    [apps],
  )

  const counts = useMemo(() => {
    const c: Record<Bucket, number> = {
      not_started: 0,
      in_progress: 0,
      ready: 0,
      submitted: 0,
      under_review: 0,
      decided: 0,
    }
    apps.forEach(a => { c[bucketOf(a)] += 1 })
    return c
  }, [apps])

  const institutions = useMemo(() => {
    const set = new Set<string>()
    apps.forEach(a => { if (a.program?.institution_name) set.add(a.program.institution_name) })
    return Array.from(set).sort()
  }, [apps])

  const topActions = useMemo(
    () => [...apps].sort((a, b) => actionScore(b) - actionScore(a)).filter(a => actionScore(a) > 0).slice(0, 3),
    [apps],
  )

  const filtered = useMemo(() => {
    let list = apps
    if (statusFilter !== 'all') list = list.filter(a => bucketOf(a) === statusFilter)
    if (institution !== 'all') list = list.filter(a => a.program?.institution_name === institution)
    if (deadlineWindow !== 'all') {
      list = list.filter(a => {
        const d = daysUntil(a.program?.application_deadline)
        if (d == null) return false
        if (deadlineWindow === 'overdue') return d < 0
        if (deadlineWindow === '7') return d >= 0 && d <= 7
        if (deadlineWindow === '30') return d >= 0 && d <= 30
        return true
      })
    }
    const sorted = [...list]
    sorted.sort((a, b) => {
      if (sort === 'readiness') return (b.readiness_pct ?? 0) - (a.readiness_pct ?? 0)
      if (sort === 'fit') return Number(b.match_score ?? 0) - Number(a.match_score ?? 0)
      // deadline (default): soonest first, nulls last
      const da = daysUntil(a.program?.application_deadline)
      const db = daysUntil(b.program?.application_deadline)
      if (da == null && db == null) return 0
      if (da == null) return 1
      if (db == null) return -1
      return da - db
    })
    return sorted
  }, [apps, statusFilter, institution, deadlineWindow, sort])

  if (isLoading)
    return <div className="p-6 space-y-4">{Array.from({ length: 3 }).map((_, i) => <SkeletonCard key={i} />)}</div>

  if (apps.length === 0)
    return (
      <div className="p-6 max-w-3xl mx-auto">
        <h1 className="text-2xl font-semibold text-foreground mb-1">Your portfolio</h1>
        <p className="text-sm text-foreground mb-6">Turn saved targets into application projects.</p>
        <EmptyState
          icon={<FileText size={48} />}
          title="No applications yet"
          description="Start one from your Saved list or Match when you're ready."
          action={{ label: 'Explore programs', onClick: () => navigate('/s/explore') }}
        />
      </div>
    )

  return (
    <div className="p-6 max-w-3xl mx-auto">
      <h1 className="text-2xl font-semibold text-foreground mb-1">Your portfolio</h1>
      <p className="text-sm text-foreground mb-5">
        {apps.length} application{apps.length !== 1 ? 's' : ''} across your journey.
      </p>

      {/* Spec 18 — "You're in" celebration once an offer is accepted (§6/§13) */}
      {acceptedApp && (
        <Card className="p-4 mb-6 bg-success-soft border-0 flex items-center gap-3">
          <div className="w-10 h-10 rounded-full bg-success/15 flex items-center justify-center shrink-0">
            <PartyPopper size={20} className="text-success" />
          </div>
          <div className="min-w-0">
            <p className="text-base font-bold text-foreground">You're in. Congrats.</p>
            <p className="text-sm text-foreground truncate">
              You accepted {acceptedApp.program?.program_name || 'your offer'}
              {acceptedApp.program?.institution_name ? ` at ${acceptedApp.program.institution_name}` : ''}.
            </p>
          </div>
        </Card>
      )}

      {/* Spec 18 — no offers yet, decisions pending (§8) */}
      {!acceptedApp && offerApps.length === 0 && awaitingDecisionApps.length > 0 && (
        <Card className="p-4 mb-6 bg-muted border-0">
          <p className="text-sm text-foreground">
            Decisions usually arrive within 4–8 weeks of submission. You'll be notified here.
          </p>
          <p className="text-xs text-foreground mt-1">
            {awaitingDecisionApps.length} application
            {awaitingDecisionApps.length !== 1 ? 's' : ''} awaiting a decision.
          </p>
        </Card>
      )}

      {/* Spec 18 — offer-received banner + compare CTA (§5/§8) */}
      {!acceptedApp && offerApps.length > 0 && (
        <Card className="p-4 mb-6 flex items-center gap-3">
          <div className="w-10 h-10 rounded-full bg-secondary/10 flex items-center justify-center shrink-0">
            <Mail size={20} className="text-secondary" />
          </div>
          <div className="min-w-0 flex-1">
            <p className="text-sm font-semibold text-foreground">
              {pendingOfferApps.length > 0
                ? `You have ${pendingOfferApps.length} offer${pendingOfferApps.length !== 1 ? 's' : ''} to respond to`
                : `${offerApps.length} offer${offerApps.length !== 1 ? 's' : ''} on the table`}
            </p>
            <p className="text-xs text-foreground">Weigh cost, fit, and deadlines side by side.</p>
          </div>
          {offerApps.length >= 2 ? (
            <button
              onClick={() => setShowCompare(true)}
              className="text-sm text-secondary font-medium inline-flex items-center gap-1 hover:underline shrink-0"
            >
              Compare your {offerApps.length} offers <ArrowRight size={14} />
            </button>
          ) : (
            <button
              onClick={() => navigate(`/s/applications/${offerApps[0].id}?tab=offer`)}
              className="text-sm text-secondary font-medium inline-flex items-center gap-1 hover:underline shrink-0"
            >
              Review your offer <ArrowRight size={14} />
            </button>
          )}
        </Card>
      )}

      {/* Counts */}
      <div className="grid grid-cols-3 sm:grid-cols-6 gap-2 mb-6">
        {BUCKET_ORDER.map(b => (
          <button
            key={b}
            onClick={() => setStatusFilter(statusFilter === b ? 'all' : b)}
            className={`rounded-xl border px-3 py-2.5 text-left transition-colors ${
              statusFilter === b
                ? 'border-secondary bg-secondary/5'
                : 'border-border hover:border-secondary/40'
            }`}
          >
            <div className="text-lg font-semibold text-foreground">{counts[b]}</div>
            <div className="text-[11px] leading-tight text-foreground">{BUCKET_LABELS[b]}</div>
          </button>
        ))}
      </div>

      {/* Next actions */}
      {topActions.length > 0 && (
        <Card className="p-4 mb-6">
          <h2 className="text-xs font-semibold uppercase tracking-wider text-foreground mb-3">Next actions</h2>
          <div className="space-y-2">
            {topActions.map(a => {
              const d = daysUntil(a.program?.application_deadline)
              return (
                <button
                  key={a.id}
                  onClick={() => navigate(appHref(a))}
                  className="w-full flex items-center gap-2 text-left text-sm hover:bg-muted rounded-lg px-2 py-1.5"
                >
                  <Star size={14} className="text-primary flex-shrink-0" fill="currentColor" />
                  <span className="flex-1 min-w-0 truncate text-foreground">
                    {nextAction(a)} — <span className="text-foreground">{a.program?.program_name}</span>
                  </span>
                  {d != null && d >= 0 && d <= 30 && (
                    <span className={`text-xs flex-shrink-0 ${d <= 7 ? 'text-destructive' : 'text-warning'}`}>
                      {d === 0 ? 'today' : `${d}d`}
                    </span>
                  )}
                  <ChevronRight size={14} className="text-foreground flex-shrink-0" />
                </button>
              )
            })}
          </div>
        </Card>
      )}

      {/* Filters + sort */}
      <div className="flex flex-wrap items-center gap-2 mb-4">
        <Select
          aria-label="Filter by status"
          value={statusFilter}
          onChange={e => setStatusFilter(e.target.value as 'all' | Bucket)}
          options={[{ value: 'all', label: 'All statuses' }, ...BUCKET_ORDER.map(b => ({ value: b, label: BUCKET_LABELS[b] }))]}
        />
        {institutions.length > 0 && (
          <Select
            aria-label="Filter by institution"
            value={institution}
            onChange={e => setInstitution(e.target.value)}
            options={[{ value: 'all', label: 'All institutions' }, ...institutions.map(i => ({ value: i, label: i }))]}
          />
        )}
        <Select
          aria-label="Filter by deadline"
          value={deadlineWindow}
          onChange={e => setDeadlineWindow(e.target.value)}
          options={[
            { value: 'all', label: 'Any deadline' },
            { value: '7', label: 'Due in 7 days' },
            { value: '30', label: 'Due in 30 days' },
            { value: 'overdue', label: 'Overdue' },
          ]}
        />
        <div className="ml-auto">
          <Select
            aria-label="Sort"
            value={sort}
            onChange={e => setSort(e.target.value as 'deadline' | 'readiness' | 'fit')}
            options={[
              { value: 'deadline', label: 'Sort: Deadline' },
              { value: 'readiness', label: 'Sort: Readiness' },
              { value: 'fit', label: 'Sort: Fit' },
            ]}
          />
        </div>
      </div>

      {/* List */}
      <div className="space-y-3">
        {filtered.length === 0 ? (
          <p className="text-sm text-foreground py-8 text-center">No applications match these filters.</p>
        ) : (
          filtered.map(app => {
            const pct = app.readiness_pct ?? 0
            const d = daysUntil(app.program?.application_deadline)
            const offerDays = daysUntil(app.offer?.response_deadline)
            const offerTone = deadlineTone(offerDays)
            const isDraft = app.status === 'draft'
            const pendingOffer = hasPendingOfferResponse(app)
            return (
              <Card
                key={app.id}
                onClick={() => navigate(appHref(app))}
                className="p-4 hover:shadow-sm transition-shadow cursor-pointer"
              >
                <div className="flex justify-between items-start gap-3">
                  <div className="flex-1 min-w-0">
                    <p className="font-semibold text-sm text-foreground truncate">
                      {app.program?.program_name || 'Program'}
                    </p>
                    {app.program?.institution_name && (
                      <p className="text-xs text-foreground mt-0.5">{app.program.institution_name}</p>
                    )}
                    <div className="flex items-center gap-2 mt-2 flex-wrap">
                      <Badge variant={(STATUS_COLORS[app.status] || 'neutral') as never}>
                        {BUCKET_LABELS[bucketOf(app)]}
                      </Badge>
                      {app.submission_mode === 'external' && (
                        <Badge variant="neutral">External</Badge>
                      )}
                      {app.decision && (
                        <Badge variant={(STATUS_COLORS[app.decision] || 'neutral') as never}>{app.decision}</Badge>
                      )}
                      {isDraft && (
                        <span className="text-xs text-foreground">{pct}% ready</span>
                      )}
                      {d != null && d >= 0 && d <= 30 && isDraft && (
                        <span className={`text-xs font-medium inline-flex items-center gap-1 ${d <= 7 ? 'text-destructive' : 'text-warning'}`}>
                          <CalendarClock size={11} />{d === 0 ? 'Due today' : `${d}d left`}
                        </span>
                      )}
                      {pendingOffer && offerDays != null && offerDays >= 0 && (
                        <span
                          className={`text-xs font-medium inline-flex items-center gap-1 ${DEADLINE_TONE_CLASS[offerTone]}`}
                        >
                          <CalendarClock size={11} />
                          Offer: {offerDays === 0 ? 'due today' : `${offerDays}d to respond`}
                        </span>
                      )}
                    </div>
                    <p className="text-xs text-foreground mt-2">Next: {nextAction(app)}</p>
                    {app.submitted_at && (
                      <p className="text-[11px] text-muted-foreground mt-1">Submitted {formatDate(app.submitted_at)}</p>
                    )}
                  </div>
                  <span className="text-xs text-secondary font-medium flex-shrink-0 inline-flex items-center gap-0.5">
                    Open <ChevronRight size={13} />
                  </span>
                </div>
                {isDraft && (
                  <div className="mt-3 h-1.5 rounded-full bg-muted overflow-hidden">
                    <div
                      className={`h-full rounded-full ${pct >= 100 ? 'bg-success' : 'bg-secondary'}`}
                      style={{ width: `${pct}%` }}
                    />
                  </div>
                )}
              </Card>
            )
          })
        )}
      </div>

      <DecisionComparison isOpen={showCompare} onClose={() => setShowCompare(false)} />
    </div>
  )
}
