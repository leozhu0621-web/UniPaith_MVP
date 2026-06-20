import { lazy, Suspense, useMemo, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { listMyApplications } from '../../api/applications'
import Card from '../../components/ui/Card'
import Badge from '../../components/ui/Badge'
import Button from '../../components/ui/Button'
import Select from '../../components/ui/Select'
import EmptyState from '../../components/ui/EmptyState'
import QueryError from '../../components/ui/QueryError'
import { SkeletonCard } from '../../components/ui/Skeleton'
import { PageContainer, PageHeader, SectionHeader, StatTile } from '../../components/student/density'
import BandBalanceBar from '../../components/student/BandBalanceBar'
import { useCountUp } from '../../hooks/useCountUp'
import usePageTitle from '../../hooks/usePageTitle'
import { formatDate } from '../../utils/format'

/** Bucket counter numeral — counts up on mount, consistent with the My Space
 *  home pipeline tiles (reduced-motion → instant via useCountUp). */
function BucketCount({ value }: { value: number }) {
  const n = useCountUp(value)
  return <div className="text-lg font-semibold text-foreground">{n}</div>
}
import { STATUS_COLORS } from '../../utils/constants'
import { FileText, Star, ChevronRight, CalendarClock, CheckCircle2, ArrowRight, Mail } from 'lucide-react'
import DecisionComparison from './apply/offer/DecisionComparison'
import OfferComparisonTable from './apply/offer/OfferComparisonTable'
import { hasPendingOfferResponse } from './apply/offer/offerFormat'
import { daysUntil, deadlineTone, DEADLINE_TONE_CLASS } from '../../utils/deadline'
import type { Application } from '../../types'

// My Space › Applications views (Spec 2026-06-10 §5): All · Offers · Costs & aid.
const CostsAidTab = lazy(() => import('./myspace/applications/CostsAidTab'))

type AppView = 'all' | 'offers' | 'costs'

const APP_VIEWS: { key: AppView; label: string }[] = [
  { key: 'all', label: 'All applications' },
  { key: 'offers', label: 'Offers' },
  { key: 'costs', label: 'Costs & aid' },
]

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

type RowModel = {
  bucket: Bucket
  label: string
  action: { label: string; href: string } | null
  href: string
  score: number
}

/** ONE source of truth per row — bucket + offer state derived once, then the
 *  human "Next:" label, the single inline action, the card-click destination,
 *  and the ★ Next-actions priority score all read from the same derivation.
 *
 *  The `href` (card-click) now follows `action`: it lands on the Offer tab when
 *  there's an offer to read, the checklist tab when there's a checklist action,
 *  else the detail page — so a row's card-click and its inline button can no
 *  longer disagree.
 *
 *  Every action target is one UniPaith owns: Resume + Submit open the checklist
 *  tab where those gated flows live (submit blockers, the fee-clear gate, and
 *  the Spec 39 checkout); View offer is inform-only — the school owns
 *  accept/decline, so the row only routes you to READ the terms. `action` is
 *  null when the next move isn't ours (under review, a final decision with no
 *  offer to read). */
function rowModel(app: Application): RowModel {
  const bucket = bucketOf(app)
  const pct = app.readiness_pct ?? 0

  // label — human "Next: <action>" string (spec 15 §2).
  let label: string
  switch (bucket) {
    case 'ready':
      label = 'Ready now — submit your application'
      break
    case 'in_progress':
      label = `Finish your checklist (${pct}%)`
      break
    case 'not_started':
      label = 'Start your checklist'
      break
    case 'submitted':
      label = 'Submitted — awaiting review'
      break
    case 'under_review':
      label = app.status === 'interview' ? 'Prepare for your interview' : 'Under review'
      break
    case 'decided':
      if (hasPendingOfferResponse(app)) {
        const school = app.program?.institution_name
        label = school ? `Respond to ${school}'s offer` : 'Respond to the offer'
      } else {
        label = `Decision: ${app.decision ?? app.decision_state ?? 'received'}`
      }
      break
  }

  // action — the one inline affordance a row offers.
  const hasOfferToRead = hasPendingOfferResponse(app) || (bucket === 'decided' && !!app.offer)
  let action: { label: string; href: string } | null
  if (hasOfferToRead) {
    action = { label: 'View offer', href: `/s/applications/${app.id}?tab=offer` }
  } else if (bucket === 'ready') {
    action = { label: 'Submit', href: `/s/applications/${app.id}?tab=checklist` }
  } else if (bucket === 'in_progress') {
    action = { label: 'Resume', href: `/s/applications/${app.id}?tab=checklist` }
  } else if (bucket === 'not_started') {
    action = { label: 'Start', href: `/s/applications/${app.id}?tab=checklist` }
  } else {
    action = null
  }

  // href — card-click follows the action so the two can never diverge.
  const href = action ? action.href : `/s/applications/${app.id}`

  // score — priority for the ★ Next actions rail; higher = more urgent.
  const d = daysUntil(app.program?.application_deadline)
  const offerDays = daysUntil(app.offer?.response_deadline)
  let score = 0
  if (bucket === 'ready') score += 100
  if (hasPendingOfferResponse(app)) {
    score += 95
    if (offerDays != null && offerDays >= 0 && offerDays <= 14) score += 40 - offerDays
  } else if (bucket === 'decided' && app.decision === 'admitted' && app.offer?.status !== 'accepted')
    score += 90
  if (app.status === 'interview') score += 80
  if (bucket === 'in_progress') score += 40
  if (d != null && d >= 0 && d <= 14) score += 30 - d // deadline pressure
  if (d != null && d < 0 && (bucket === 'not_started' || bucket === 'in_progress' || bucket === 'ready'))
    score += 25 // overdue & not yet submitted

  return { bucket, label, action, href, score }
}

export default function ApplicationsPage() {
  usePageTitle('Applications')
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const rawView = searchParams.get('tab')
  const view: AppView = rawView === 'offers' ? 'offers' : rawView === 'costs' ? 'costs' : 'all'
  // ?status= deep links (the home pipeline tiles) pre-select a bucket filter.
  const [statusFilter, setStatusFilter] = useState<'all' | Bucket>(() => {
    const s = searchParams.get('status')
    return s && BUCKET_ORDER.includes(s as Bucket) ? (s as Bucket) : 'all'
  })
  const [institution, setInstitution] = useState('all')
  const [deadlineWindow, setDeadlineWindow] = useState('all')
  const [priorityFilter, setPriorityFilter] = useState<'all' | 'reach' | 'target' | 'safer'>('all')
  const [sort, setSort] = useState<'deadline' | 'readiness' | 'fit'>('deadline')
  const [showCompare, setShowCompare] = useState(false)

  const { data, isLoading, isError, refetch } = useQuery({ queryKey: ['my-applications'], queryFn: listMyApplications })
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

  // Portfolio balance — derive each app's band the same way the priority filter
  // does (fit_band low/medium/high → reach/target/safer). Apps with no band are
  // simply uncounted, never assumed.
  const bandCounts = useMemo(() => {
    const counts = { reach: 0, target: 0, safer: 0 }
    const fromBand: Record<string, 'reach' | 'target' | 'safer'> = {
      low: 'reach',
      medium: 'target',
      high: 'safer',
    }
    apps.forEach(a => {
      const band = a.fit_band ? fromBand[a.fit_band] : undefined
      if (band) counts[band] += 1
    })
    return counts
  }, [apps])

  const institutions = useMemo(() => {
    const set = new Set<string>()
    apps.forEach(a => { if (a.program?.institution_name) set.add(a.program.institution_name) })
    return Array.from(set).sort()
  }, [apps])

  const topActions = useMemo(
    () =>
      apps
        .map(a => ({ app: a, score: rowModel(a).score }))
        .filter(x => x.score > 0)
        .sort((a, b) => b.score - a.score)
        .slice(0, 3)
        .map(x => x.app),
    [apps],
  )

  const filtered = useMemo(() => {
    let list = apps
    if (statusFilter !== 'all') list = list.filter(a => bucketOf(a) === statusFilter)
    if (institution !== 'all') list = list.filter(a => a.program?.institution_name === institution)
    if (priorityFilter !== 'all') {
      // Map reach/target/safer to fit_band values (low/medium/high).
      const bandMap: Record<string, string> = { reach: 'low', target: 'medium', safer: 'high' }
      const band = bandMap[priorityFilter]
      list = list.filter(a => a.fit_band === band)
    }
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
    // Read dual-score fitness first; fall back to legacy match_score (Phase E
    // drop) so the Fit sort doesn't zero out when fitness_score is the only field.
    const fitOf = (a: Application) => Number(a.fitness_score ?? a.match_score ?? 0)
    sorted.sort((a, b) => {
      if (sort === 'readiness') return (b.readiness_pct ?? 0) - (a.readiness_pct ?? 0)
      if (sort === 'fit') return fitOf(b) - fitOf(a)
      // deadline (default): soonest first, nulls last
      const da = daysUntil(a.program?.application_deadline)
      const db = daysUntil(b.program?.application_deadline)
      if (da == null && db == null) return 0
      if (da == null) return 1
      if (db == null) return -1
      return da - db
    })
    return sorted
  }, [apps, statusFilter, institution, deadlineWindow, priorityFilter, sort])

  // Hidden on lg+ where the My Space rail's Workspace group lists these views flat
  // (Spec 2026-06-15 §2.2); kept below lg where the rail collapses to pills.
  const viewSwitcher = (
    <div role="tablist" aria-label="Applications views" className="lg:hidden mb-4 flex gap-1 border-b border-border">
      {APP_VIEWS.map(v => (
        <button
          key={v.key}
          role="tab"
          aria-selected={view === v.key}
          tabIndex={view === v.key ? 0 : -1}
          onClick={() => navigate(v.key === 'all' ? '/s/applications' : `/s/applications?tab=${v.key}`, { replace: true })}
          className={`border-b-2 px-3 py-2 text-sm font-medium transition-colors ${
            view === v.key
              ? 'border-secondary text-foreground'
              : 'border-transparent text-muted-foreground hover:text-foreground'
          }`}
        >
          {v.label}
          {v.key === 'offers' && offerApps.length > 0 && (
            <span className="ml-1.5 text-xs text-muted-foreground">{offerApps.length}</span>
          )}
        </button>
      ))}
    </div>
  )

  // Costs & aid stands alone — it draws on saved programs and preferences,
  // so it renders even when the portfolio is empty or failed to load.
  if (view === 'costs')
    return (
      <PageContainer>
        <PageHeader eyebrow="My Space" title="Costs & aid" />
        {viewSwitcher}
        <Suspense fallback={<SkeletonCard />}>
          <CostsAidTab />
        </Suspense>
      </PageContainer>
    )

  if (isLoading)
    return <PageContainer className="space-y-4">{Array.from({ length: 3 }).map((_, i) => <SkeletonCard key={i} />)}</PageContainer>

  // A failed fetch must not read as "No applications yet" (empty state).
  if (isError)
    return (
      <PageContainer>
        <PageHeader eyebrow="My Space" title="Applications" />
        {viewSwitcher}
        <QueryError detail="We couldn't load your applications." onRetry={() => refetch()} />
      </PageContainer>
    )

  if (view === 'offers')
    return (
      <PageContainer>
        <PageHeader
          eyebrow="My Space"
          title="Offers"
          count={offerApps.length}
        />
        {viewSwitcher}
        {offerApps.length === 0 ? (
          <EmptyState
            icon={<Mail size={48} />}
            title="No offers yet"
          />
        ) : (
          <div className="stagger-list space-y-2">
            {offerApps.map(a => {
              const responded = a.offer?.student_response || a.student_decision
              return (
                <Card pad={false}
                  key={a.id}
                  className="p-4 flex items-center justify-between gap-3 cursor-pointer hover:border-secondary/40 transition-colors"
                  onClick={() => navigate(`/s/applications/${a.id}?tab=offer`)}
                >
                  <div className="min-w-0">
                    <p className="truncate text-sm font-semibold text-foreground">{a.program?.program_name ?? 'Program'}</p>
                    <p className="truncate text-xs text-muted-foreground">{a.program?.institution_name ?? ''}</p>
                  </div>
                  <div className="flex shrink-0 items-center gap-2">
                    {/* One earned beat as a fresh offer lands (Ship B milestone moment). */}
                    <Badge variant={responded ? 'neutral' : 'warning'} className={responded ? undefined : 'animate-beat'}>
                      {a.student_decision === 'accepted_by_student'
                        ? 'accepted'
                        : a.student_decision === 'declined_by_student'
                          ? 'declined'
                          : responded
                            ? String(responded).replace(/_/g, ' ')
                            : 'response needed'}
                    </Badge>
                    <ChevronRight size={16} className="text-muted-foreground" />
                  </div>
                </Card>
              )
            })}
          </div>
        )}
        {offerApps.length >= 2 && (
          <section className="mt-8">
            <SectionHeader>Compare offers</SectionHeader>
            <OfferComparisonTable />
          </section>
        )}
      </PageContainer>
    )

  if (apps.length === 0)
    return (
      <PageContainer>
        <PageHeader eyebrow="My Space" title="Applications" />
        {viewSwitcher}
        <EmptyState
          icon={<FileText size={48} />}
          title="No applications yet"
          action={{ label: 'Explore programs', onClick: () => navigate('/s/explore') }}
        />
      </PageContainer>
    )

  return (
    <PageContainer>
      <PageHeader
        eyebrow="My Space"
        title="Applications"
        count={apps.length}
      />
      {viewSwitcher}

      {/* Spec 18 — "You're in" celebration once an offer is accepted (§6/§13) */}
      {acceptedApp && (
        <Card pad={false} className="animate-beat p-4 mb-6 bg-success-soft border-0 flex items-center gap-3">
          <div className="w-10 h-10 rounded-full bg-success/15 flex items-center justify-center shrink-0">
            <CheckCircle2 size={20} className="text-success" />
          </div>
          <div className="min-w-0">
            <p className="text-lg font-semibold text-foreground">You're in!</p>
            <p className="text-sm text-foreground truncate">
              You accepted {acceptedApp.program?.program_name || 'your offer'}
              {acceptedApp.program?.institution_name ? ` at ${acceptedApp.program.institution_name}` : ''}.
            </p>
          </div>
        </Card>
      )}

      {/* Spec 18 — no offers yet, decisions pending (§8) */}
      {!acceptedApp && offerApps.length === 0 && awaitingDecisionApps.length > 0 && (
        <Card pad={false} className="p-4 mb-6 bg-muted border-0 flex items-center justify-between gap-4">
          <p className="text-sm text-foreground">
            Decisions usually arrive 4–8 weeks after submission.
          </p>
          <div className="shrink-0">
            <StatTile label="Awaiting a decision" value={awaitingDecisionApps.length} />
          </div>
        </Card>
      )}

      {/* Spec 18 — offer-received banner + compare CTA (§5/§8) */}
      {!acceptedApp && offerApps.length > 0 && (
        <Card pad={false} className="p-4 mb-6 flex items-center gap-3">
          <div className="w-10 h-10 rounded-full bg-secondary/10 flex items-center justify-center shrink-0">
            <Mail size={20} className="text-secondary" />
          </div>
          <div className="min-w-0 flex-1">
            <p className="text-sm font-semibold text-foreground">
              {pendingOfferApps.length > 0
                ? `You have ${pendingOfferApps.length} offer${pendingOfferApps.length !== 1 ? 's' : ''} to respond to`
                : `${offerApps.length} offer${offerApps.length !== 1 ? 's' : ''} on the table`}
            </p>
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

      {/* Portfolio balance — reach/target/safer mix of the applications at a glance. */}
      <BandBalanceBar {...bandCounts} className="mb-6" />

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
            <BucketCount value={counts[b]} />
            <div className="text-[11px] leading-tight text-foreground">{BUCKET_LABELS[b]}</div>
          </button>
        ))}
      </div>

      {/* Next actions */}
      {topActions.length > 0 && (
        <Card pad={false} className="p-4 mb-6">
          <h2 className="text-xs font-semibold uppercase tracking-wider text-foreground mb-3">Next actions</h2>
          <div className="space-y-2">
            {topActions.map(a => {
              const rm = rowModel(a)
              const d = daysUntil(a.program?.application_deadline)
              return (
                <button
                  key={a.id}
                  onClick={() => navigate(rm.href)}
                  className="w-full flex items-center gap-2 text-left text-sm hover:bg-muted rounded-lg px-2 py-1.5"
                >
                  <Star size={14} className="text-secondary flex-shrink-0" fill="currentColor" />
                  <span className="flex-1 min-w-0 truncate text-foreground">
                    {rm.label} — <span className="text-foreground">{a.program?.program_name}</span>
                  </span>
                  {d != null && d >= 0 && d <= 30 && (
                    <span className={`text-xs flex-shrink-0 ${DEADLINE_TONE_CLASS[deadlineTone(d)]}`}>
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
        <div className="w-full sm:w-40">
          <Select
            aria-label="Filter by status"
            value={statusFilter}
            onChange={e => setStatusFilter(e.target.value as 'all' | Bucket)}
            options={[{ value: 'all', label: 'All statuses' }, ...BUCKET_ORDER.map(b => ({ value: b, label: BUCKET_LABELS[b] }))]}
          />
        </div>
        {institutions.length > 0 && (
          <div className="w-full sm:w-52">
            <Select
              aria-label="Filter by institution"
              value={institution}
              onChange={e => setInstitution(e.target.value)}
              options={[{ value: 'all', label: 'All institutions' }, ...institutions.map(i => ({ value: i, label: i }))]}
            />
          </div>
        )}
        <div className="w-full sm:w-40">
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
        </div>
        <div className="w-full sm:w-40">
          <Select
            aria-label="Filter by priority"
            value={priorityFilter}
            onChange={e => setPriorityFilter(e.target.value as 'all' | 'reach' | 'target' | 'safer')}
            options={[
              { value: 'all', label: 'Any priority' },
              { value: 'reach', label: 'Reach' },
              { value: 'target', label: 'Target' },
              { value: 'safer', label: 'Safer' },
            ]}
          />
        </div>
        <div className="w-full sm:w-44">
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
      <div className="stagger-list space-y-3">
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
            const rm = rowModel(app)
            return (
              <Card pad={false}
                key={app.id}
                onClick={() => navigate(rm.href)}
                className="p-4 hover:shadow-sm transition-shadow cursor-pointer"
              >
                <div className="flex justify-between items-start gap-3">
                  <div className="flex-1 min-w-0">
                    <p className="font-semibold text-sm text-foreground truncate">
                      {app.program?.program_name || 'Program'}
                    </p>
                    {app.program?.institution_name && (
                      <p className="text-xs text-muted-foreground mt-0.5">{app.program.institution_name}</p>
                    )}
                    <div className="flex items-center gap-2 mt-2 flex-wrap">
                      <Badge variant={(STATUS_COLORS[app.status] || 'neutral') as never}>
                        {BUCKET_LABELS[rm.bucket]}
                      </Badge>
                      {app.submission_mode === 'external' && (
                        <Badge variant="neutral">External</Badge>
                      )}
                      {app.decision && (
                        <Badge
                          variant={(STATUS_COLORS[app.decision] || 'neutral') as never}
                          // Admit chips get one earned-gold beat on reveal (Ship B).
                          className={app.decision === 'admitted' ? 'animate-beat' : undefined}
                        >
                          {app.decision}
                        </Badge>
                      )}
                      {isDraft && (
                        <span className="text-xs text-muted-foreground">{pct}% ready</span>
                      )}
                      {d != null && d >= 0 && d <= 30 && isDraft && (
                        <span className={`text-xs font-medium inline-flex items-center gap-1 ${DEADLINE_TONE_CLASS[deadlineTone(d)]}`}>
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
                    {/* The next step is the button now; keep the prose line only
                        where the next move isn't ours to act on (under review, a
                        final decision with no offer to read). */}
                    {!rm.action && (
                      <p className="text-xs text-muted-foreground mt-2">Next: {rm.label}</p>
                    )}
                    {app.submitted_at && (
                      <p className="text-[11px] text-muted-foreground mt-1">Submitted {formatDate(app.submitted_at)}</p>
                    )}
                  </div>
                  {rm.action ? (
                    <Button
                      size="sm"
                      variant="secondary"
                      className="flex-shrink-0"
                      onClick={e => { e.stopPropagation(); navigate(rm.action!.href) }}
                    >
                      {rm.action.label}
                    </Button>
                  ) : (
                    <span className="text-xs text-secondary font-medium flex-shrink-0 inline-flex items-center gap-0.5">
                      Open <ChevronRight size={13} />
                    </span>
                  )}
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
    </PageContainer>
  )
}
