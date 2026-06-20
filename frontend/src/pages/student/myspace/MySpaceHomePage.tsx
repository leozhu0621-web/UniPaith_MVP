import { useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import {
  AlertTriangle,
  ArrowRight,
  Bookmark,
  CalendarClock,
  CheckCircle2,
  CircleDashed,
  Compass,
  FileText,
  FolderKanban,
  GraduationCap,
  Mail,
  MessageSquare,
  Target,
  Upload,
} from 'lucide-react'

import { listMyApplications } from '../../../api/applications'
import { getCalendar, type CalendarItem } from '../../../api/calendar'
import { getThreads } from '../../../api/inbox'
import { listClarifications } from '../../../api/intake'
import { listRecommendations } from '../../../api/recommendations'
import { listSaved } from '../../../api/saved-lists'
import { getOnboarding, getProfile } from '../../../api/students'
import { listWorkshopRuns } from '../../../api/workshops-feedback'
import Badge from '../../../components/ui/Badge'
import Card from '../../../components/ui/Card'
import EmptyState from '../../../components/ui/EmptyState'
import Skeleton from '../../../components/ui/Skeleton'
import usePageTitle from '../../../hooks/usePageTitle'
import type { Application, OnboardingStatus, WorkshopFeedbackRun } from '../../../types'

type FocusAction = {
  title: string
  body: string
  to: string
  cta: string
  icon: typeof Compass
  tone: 'info' | 'warning' | 'success'
}

const DAY = 86_400_000

function daysUntil(date?: string | null) {
  if (!date) return null
  return Math.ceil((new Date(date).getTime() - Date.now()) / DAY)
}

function shortDate(date?: string | null) {
  if (!date) return 'No date'
  return new Date(date).toLocaleDateString(undefined, { month: 'short', day: 'numeric' })
}

function deadlineCopy(date?: string | null) {
  const days = daysUntil(date)
  if (days == null) return 'No deadline'
  if (days < 0) return `${Math.abs(days)}d overdue`
  if (days === 0) return 'Due today'
  if (days === 1) return 'Due tomorrow'
  return `${days}d left`
}

function hasPendingOffer(app: Application) {
  return Boolean(app.offer && !app.offer.student_response && app.student_decision == null)
}

function buildFocus({
  clarifications,
  offers,
  deadlines,
  drafts,
  savedCount,
}: {
  clarifications: number
  offers: Application[]
  deadlines: CalendarItem[]
  drafts: Application[]
  savedCount: number
}): FocusAction {
  const pendingOffer = offers.find(hasPendingOffer)
  if (pendingOffer) {
    return {
      title: 'Respond to your offer',
      body: `${pendingOffer.program?.institution_name ?? 'A school'} is waiting for your decision.`,
      to: '/s/applications?tab=offers',
      cta: 'Compare offers',
      icon: GraduationCap,
      tone: 'success',
    }
  }

  const urgentDeadline = deadlines.find(item => {
    const days = daysUntil(item.start_at)
    return days != null && days <= 7
  })
  if (urgentDeadline) {
    return {
      title: urgentDeadline.title,
      body: `${urgentDeadline.subtitle ?? urgentDeadline.institution_name ?? 'Admissions task'} · ${deadlineCopy(urgentDeadline.start_at)}`,
      to: '/s/calendar',
      cta: 'Open calendar',
      icon: CalendarClock,
      tone: 'warning',
    }
  }

  if (clarifications > 0) {
    return {
      title: 'Confirm uncertain profile signals',
      body: `${clarifications} signal${clarifications === 1 ? '' : 's'} need your review before Uni uses them for matching.`,
      to: '/s/import',
      cta: 'Review signals',
      icon: Upload,
      tone: 'warning',
    }
  }

  const draft = drafts[0]
  if (draft) {
    return {
      title: `Move ${draft.program?.program_name ?? 'your application'} forward`,
      body: `Readiness is ${draft.readiness_pct ?? 0}%. Finish the next checklist item before the deadline gets close.`,
      to: `/s/applications/${draft.id}`,
      cta: 'Open application',
      icon: FolderKanban,
      tone: 'info',
    }
  }

  if (savedCount === 0) {
    return {
      title: 'Build your first shortlist',
      body: 'Save a few target programs so My Space can turn them into deadlines, prep, and application tasks.',
      to: '/s/explore',
      cta: 'Discover programs',
      icon: Target,
      tone: 'info',
    }
  }

  return {
    title: 'Talk to Uni about the next decision',
    body: 'Use Chat for strategy questions; My Space keeps the plan, evidence, and deadlines organized.',
    to: '/s',
    cta: 'Open Chat',
    icon: MessageSquare,
    tone: 'info',
  }
}

export default function MySpaceHomePage() {
  usePageTitle('My Space')
  const navigate = useNavigate()
  const profile = useQuery({ queryKey: ['profile'], queryFn: getProfile, staleTime: 300_000 })
  const onboarding = useQuery<OnboardingStatus>({ queryKey: ['onboarding'], queryFn: getOnboarding, staleTime: 60_000 })
  const apps = useQuery({ queryKey: ['my-applications'], queryFn: listMyApplications, staleTime: 60_000 })
  const saved = useQuery({ queryKey: ['saved'], queryFn: listSaved, staleTime: 60_000 })
  const recs = useQuery({ queryKey: ['recommendations'], queryFn: listRecommendations, staleTime: 60_000 })
  const runs = useQuery({ queryKey: ['workshop-runs', 'home'], queryFn: () => listWorkshopRuns(), staleTime: 60_000 })
  const threads = useQuery({ queryKey: ['inbox-threads-unread'], queryFn: () => getThreads(), staleTime: 30_000 })
  const clarifications = useQuery({ queryKey: ['intake-clarifications'], queryFn: listClarifications, staleTime: 60_000 })
  const calendarWindow = useMemo(() => {
    const from = new Date().toISOString().slice(0, 10)
    const to = new Date(Date.now() + 14 * DAY).toISOString().slice(0, 10)
    return { from, to }
  }, [])
  const calendar = useQuery({
    queryKey: ['calendar', 'my-space-home', calendarWindow],
    queryFn: () => getCalendar(calendarWindow),
    staleTime: 60_000,
  })

  const appList: Application[] = Array.isArray(apps.data) ? apps.data : []
  const savedList = Array.isArray(saved.data) ? saved.data : []
  const recList = Array.isArray(recs.data) ? recs.data : []
  const runList: WorkshopFeedbackRun[] = Array.isArray(runs.data) ? runs.data : []
  const calItems: CalendarItem[] = Array.isArray(calendar.data) ? calendar.data : []
  const threadList = Array.isArray(threads.data) ? threads.data : []
  const pendingClarifications = clarifications.data?.clarifications?.length ?? 0

  const drafts = appList.filter(app => app.status === 'draft')
  const submitted = appList.filter(app => ['submitted', 'under_review', 'interview'].includes(app.status))
  const offers = appList.filter(app => app.status === 'decision_made' && ['admitted', 'accepted', 'conditional_admission'].includes(app.decision ?? ''))
  const waitingRecs = recList.filter(rec => rec.status === 'requested')
  const unreadThreads = threadList.filter(thread => thread.unread || ((thread as { unread_count?: number }).unread_count ?? 0) > 0)
  const activeDeadlines = calItems
    .filter(item => item.status !== 'cancelled' && item.status !== 'completed')
    .sort((a, b) => a.start_at.localeCompare(b.start_at))
    .slice(0, 5)
  const recentRuns = [...runList].sort((a, b) => (b.created_at || '').localeCompare(a.created_at || '')).slice(0, 3)
  const setupPct = Math.round(onboarding.data?.completion_percentage ?? 0)
  const focus = buildFocus({ clarifications: pendingClarifications, offers, deadlines: activeDeadlines, drafts, savedCount: savedList.length })
  const firstName = profile.data?.first_name || profile.data?.preferred_name || ''
  const greeting = new Date().getHours() < 12 ? 'Good morning' : new Date().getHours() < 18 ? 'Good afternoon' : 'Good evening'
  const loading = apps.isLoading || calendar.isLoading || saved.isLoading
  const brandNew = !loading && appList.length === 0 && savedList.length === 0

  return (
    <main className="mx-auto w-full max-w-6xl px-4 py-6 sm:px-6 lg:px-8">
      <header className="mb-5">
        <p className="up-eyebrow">My Space</p>
        <h1 className="text-h1 text-foreground">{greeting}{firstName ? `, ${firstName}` : ''}</h1>
        <p className="mt-2 max-w-2xl text-sm text-muted-foreground">
          Your personal admissions control room: what to do now, what is waiting, what is missing, and where each decision lives.
        </p>
      </header>

      {loading ? (
        <div className="space-y-4">
          <Skeleton className="h-24" />
          <Skeleton className="h-36" />
          <Skeleton className="h-48" />
        </div>
      ) : brandNew ? (
        <EmptyState
          icon={<Compass size={44} />}
          title="Start by talking to Uni or saving programs"
          description="My Space fills itself from your chat, imports, saved programs, applications, recommenders, deadlines, and workshop feedback."
          action={{ label: 'Open Chat', onClick: () => navigate('/s') }}
        />
      ) : (
        <div className="space-y-5">
          <FocusCard action={focus} onOpen={() => navigate(focus.to)} />

          <section className="grid gap-4 lg:grid-cols-[0.95fr_1.05fr]">
            <MomentumCard setupPct={setupPct} saved={savedList.length} applications={appList.length} workshops={runList.length} clarifications={pendingClarifications} />
            <PipelineGrid
              saved={savedList.length}
              drafts={drafts.length}
              submitted={submitted.length}
              offers={offers.length}
              onNavigate={navigate}
            />
          </section>

          <section className="grid gap-5 lg:grid-cols-3">
            <DashboardPanel
              title="Up next"
              actionLabel="Open workspace"
              onAction={() => navigate('/s/prep')}
            >
              <ActionRow
                icon={pendingClarifications > 0 ? AlertTriangle : CheckCircle2}
                title={pendingClarifications > 0 ? 'Profile confirmations' : 'Profile signals clear'}
                detail={pendingClarifications > 0 ? `${pendingClarifications} uncertain signal${pendingClarifications === 1 ? '' : 's'}` : 'No confirmation tasks waiting'}
                tone={pendingClarifications > 0 ? 'warning' : 'success'}
                onClick={() => navigate('/s/import')}
              />
              <ActionRow
                icon={waitingRecs.length ? Mail : CircleDashed}
                title={waitingRecs.length ? 'Recommenders waiting' : 'No pending recommenders'}
                detail={waitingRecs.length ? `${waitingRecs.length} request${waitingRecs.length === 1 ? '' : 's'} need follow-up` : 'Add recommenders when programs ask for letters'}
                onClick={() => navigate('/s/prep?tab=recommenders')}
              />
              <ActionRow
                icon={unreadThreads.length ? MessageSquare : CheckCircle2}
                title={unreadThreads.length ? 'Unread messages' : 'Inbox clear'}
                detail={unreadThreads.length ? `${unreadThreads.length} conversation${unreadThreads.length === 1 ? '' : 's'} need attention` : 'Messages will surface here'}
                onClick={() => navigate('/s/messages')}
              />
            </DashboardPanel>

            <DashboardPanel
              title="Deadlines"
              actionLabel="Calendar"
              onAction={() => navigate('/s/calendar')}
            >
              {activeDeadlines.length === 0 ? (
                <p className="py-4 text-sm text-muted-foreground">Nothing due in the next two weeks.</p>
              ) : (
                activeDeadlines.slice(0, 4).map(item => (
                  <ActionRow
                    key={item.id}
                    icon={CalendarClock}
                    title={item.title}
                    detail={`${shortDate(item.start_at)} · ${item.subtitle ?? item.institution_name ?? 'Admissions timeline'}`}
                    badge={deadlineCopy(item.start_at)}
                    tone={(daysUntil(item.start_at) ?? 99) <= 7 ? 'warning' : 'default'}
                    onClick={() => navigate('/s/calendar')}
                  />
                ))
              )}
            </DashboardPanel>

            <DashboardPanel
              title="Latest feedback"
              actionLabel="Workshops"
              onAction={() => navigate('/s/prep?tab=workshops')}
            >
              {recentRuns.length === 0 ? (
                <p className="py-4 text-sm text-muted-foreground">No workshop feedback yet. Bring a draft or practice response when you are ready.</p>
              ) : (
                recentRuns.map(run => (
                  <ActionRow
                    key={run.id}
                    icon={GraduationCap}
                    title={`${run.domain === 'essay' ? 'Essay' : run.domain === 'interview' ? 'Interview' : 'Test'} feedback`}
                    detail={`${shortDate(run.created_at)} · feedback-only coaching`}
                    onClick={() => navigate('/s/prep?tab=workshops')}
                  />
                ))
              )}
            </DashboardPanel>
          </section>

          <section className="grid gap-5 lg:grid-cols-2">
            <Card className="p-5">
              <div className="mb-3 flex items-center justify-between gap-3">
                <div>
                  <h2 className="text-h3 text-foreground">Strategy snapshot</h2>
                  <p className="mt-1 text-sm text-muted-foreground">The living document connects career, degree, academic, financial, and geographic paths.</p>
                </div>
                <ButtonLink onClick={() => navigate('/s/profile?tab=strategy')}>Open strategy</ButtonLink>
              </div>
              <div className="grid gap-3 sm:grid-cols-3">
                <StrategyTile label="Reach" value={appList.filter(app => app.fit_band === 'high').length || savedList.length} />
                <StrategyTile label="Target" value={drafts.length + submitted.length} />
                <StrategyTile label="Decision" value={offers.length} />
              </div>
            </Card>

            <Card className="p-5">
              <div className="mb-3 flex items-center justify-between gap-3">
                <div>
                  <h2 className="text-h3 text-foreground">Evidence depth</h2>
                  <p className="mt-1 text-sm text-muted-foreground">Prompt Library and intake confidence become readiness states, not raw schema work.</p>
                </div>
                <ButtonLink onClick={() => navigate('/s/import')}>Review evidence</ButtonLink>
              </div>
              <div className="space-y-3">
                <ReadinessLine label="Onboarding" value={setupPct} />
                <ReadinessLine label="Applications" value={Math.min(100, appList.length * 25)} />
                <ReadinessLine label="Workshop practice" value={Math.min(100, runList.length * 34)} />
              </div>
            </Card>
          </section>
        </div>
      )}
    </main>
  )
}

function FocusCard({ action, onOpen }: { action: FocusAction; onOpen: () => void }) {
  const toneClass = action.tone === 'warning' ? 'border-warning/40 bg-warning-soft/30' : action.tone === 'success' ? 'border-success/30 bg-success-soft/40' : 'border-secondary/20 bg-secondary/5'
  return (
    <Card className={`p-5 ${toneClass}`}>
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div className="flex min-w-0 gap-3">
          <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-background text-secondary">
            <action.icon size={19} />
          </span>
          <div className="min-w-0">
            <p className="up-eyebrow">Today&apos;s focus</p>
            <h2 className="mt-1 text-h2 text-foreground">{action.title}</h2>
            <p className="mt-1 max-w-2xl text-sm text-muted-foreground">{action.body}</p>
          </div>
        </div>
        <button onClick={onOpen} className="ui-btn inline-flex min-h-10 items-center gap-2 rounded-lg bg-secondary px-4 text-sm font-semibold text-secondary-foreground">
          {action.cta} <ArrowRight size={15} />
        </button>
      </div>
    </Card>
  )
}

function MomentumCard({ setupPct, saved, applications, workshops, clarifications }: { setupPct: number; saved: number; applications: number; workshops: number; clarifications: number }) {
  const radius = 44
  const circumference = 2 * Math.PI * radius
  const offset = circumference - (setupPct / 100) * circumference
  return (
    <Card className="p-5">
      <div className="grid gap-4 sm:grid-cols-[116px_1fr]">
        <div className="relative h-28 w-28">
          <svg viewBox="0 0 104 104" className="h-28 w-28 -rotate-90" aria-label={`Setup ${setupPct}% complete`}>
            <circle cx="52" cy="52" r={radius} fill="none" stroke="currentColor" strokeWidth="8" className="text-muted" />
            <circle
              cx="52"
              cy="52"
              r={radius}
              fill="none"
              stroke="currentColor"
              strokeWidth="8"
              strokeLinecap="round"
              strokeDasharray={circumference}
              strokeDashoffset={offset}
              className="text-secondary transition-all"
            />
          </svg>
          <div className="absolute inset-0 flex flex-col items-center justify-center">
            <span className="text-2xl font-semibold tabular-nums text-foreground">{setupPct}%</span>
            <span className="text-xs text-muted-foreground">setup</span>
          </div>
        </div>
        <div>
          <h2 className="text-h3 text-foreground">Momentum</h2>
          <p className="mt-1 text-sm text-muted-foreground">
            Current movement across discovery, preparation, and applications.
          </p>
          <div className="mt-4 grid grid-cols-2 gap-3">
            <MiniMetric label="Saved" value={saved} />
            <MiniMetric label="Applications" value={applications} />
            <MiniMetric label="Feedback runs" value={workshops} />
            <MiniMetric label="To confirm" value={clarifications} />
          </div>
        </div>
      </div>
    </Card>
  )
}

function PipelineGrid({ saved, drafts, submitted, offers, onNavigate }: { saved: number; drafts: number; submitted: number; offers: number; onNavigate: (to: string) => void }) {
  return (
    <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
      <StatButton label="Saved" value={saved} icon={Bookmark} onClick={() => onNavigate('/s/saved')} />
      <StatButton label="In progress" value={drafts} icon={FolderKanban} onClick={() => onNavigate('/s/applications?status=in_progress')} />
      <StatButton label="Submitted" value={submitted} icon={FileText} onClick={() => onNavigate('/s/applications?status=submitted')} />
      <StatButton label="Offers" value={offers} icon={GraduationCap} onClick={() => onNavigate('/s/applications?tab=offers')} earned={offers > 0} />
    </div>
  )
}

function StatButton({ label, value, icon: Icon, onClick, earned }: { label: string; value: number; icon: typeof Bookmark; onClick: () => void; earned?: boolean }) {
  return (
    <button
      onClick={onClick}
      className={`ui-btn rounded-lg border p-4 text-left transition-colors hover:bg-muted/70 ${earned ? 'border-primary/50 bg-primary/10' : 'border-border bg-card'}`}
    >
      <Icon size={18} className={earned ? 'text-primary' : 'text-secondary'} />
      <p className="mt-3 text-2xl font-semibold tabular-nums text-foreground">{value}</p>
      <p className="text-xs font-medium text-muted-foreground">{label}</p>
    </button>
  )
}

function DashboardPanel({ title, actionLabel, onAction, children }: { title: string; actionLabel: string; onAction: () => void; children: React.ReactNode }) {
  return (
    <Card className="p-5">
      <div className="mb-3 flex items-center justify-between gap-3">
        <h2 className="text-h3 text-foreground">{title}</h2>
        <ButtonLink onClick={onAction}>{actionLabel}</ButtonLink>
      </div>
      <div className="space-y-2">{children}</div>
    </Card>
  )
}

function ActionRow({ icon: Icon, title, detail, badge, tone = 'default', onClick }: { icon: typeof Compass; title: string; detail: string; badge?: string; tone?: 'default' | 'warning' | 'success'; onClick: () => void }) {
  const iconClass = tone === 'warning' ? 'text-warning' : tone === 'success' ? 'text-success' : 'text-muted-foreground'
  return (
    <button onClick={onClick} className="ui-btn flex w-full items-center gap-3 rounded-md px-2 py-2 text-left transition-colors hover:bg-muted/70">
      <Icon size={16} className={iconClass} />
      <span className="min-w-0 flex-1">
        <span className="block truncate text-sm font-semibold text-foreground">{title}</span>
        <span className="block truncate text-xs text-muted-foreground">{detail}</span>
      </span>
      {badge && <Badge variant={tone === 'warning' ? 'warning' : 'neutral'}>{badge}</Badge>}
    </button>
  )
}

function MiniMetric({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-md border border-border bg-background px-3 py-2">
      <p className="text-lg font-semibold tabular-nums text-foreground">{value}</p>
      <p className="text-xs text-muted-foreground">{label}</p>
    </div>
  )
}

function StrategyTile({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-lg border border-border bg-background p-3">
      <p className="text-xs text-muted-foreground">{label}</p>
      <p className="mt-1 text-xl font-semibold tabular-nums text-foreground">{value}</p>
    </div>
  )
}

function ReadinessLine({ label, value }: { label: string; value: number }) {
  const normalized = Math.max(0, Math.min(100, value))
  return (
    <div>
      <div className="mb-1 flex items-center justify-between gap-3 text-sm">
        <span className="font-medium text-foreground">{label}</span>
        <span className="tabular-nums text-muted-foreground">{normalized}%</span>
      </div>
      <div className="h-2 overflow-hidden rounded-pill bg-muted">
        <div className="h-full rounded-pill bg-secondary transition-all" style={{ width: `${normalized}%` }} />
      </div>
    </div>
  )
}

function ButtonLink({ onClick, children }: { onClick: () => void; children: React.ReactNode }) {
  return (
    <button onClick={onClick} className="ui-btn inline-flex items-center gap-1 text-xs font-semibold text-secondary hover:underline">
      {children} <ArrowRight size={12} />
    </button>
  )
}
