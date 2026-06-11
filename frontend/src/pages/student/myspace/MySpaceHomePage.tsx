import { useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import {
  PenLine, Calendar as CalendarIcon, Mail, FolderKanban, Compass, Target,
  AlertTriangle, Award, MessageSquare, GraduationCap, ArrowRight,
} from 'lucide-react'
import { PageHeader, SectionHeader, ListRow, StatTile } from '../../../components/student/density'
import Card from '../../../components/ui/Card'
import Badge from '../../../components/ui/Badge'
import Skeleton from '../../../components/ui/Skeleton'
import { listMyApplications } from '../../../api/applications'
import { getCalendar, type CalendarItem } from '../../../api/calendar'
import { listSaved } from '../../../api/saved-lists'
import { listRecommendations } from '../../../api/recommendations'
import { listWorkshopRuns } from '../../../api/workshops-feedback'
import { getThreads } from '../../../api/inbox'
import { listClarifications } from '../../../api/intake'
import { useAuthStore } from '../../../stores/auth-store'
import type { Application, WorkshopFeedbackRun } from '../../../types'

// My Space · Home — mission control (Spec 2026-06-10 §4). Answers "what do I
// do next?" by composing endpoints that already exist; no aggregate backend.
// Panes: Up next · Pipeline · Deadlines · Waiting on others · Latest feedback.

const STALE = 60_000

type NextAction = {
  key: string
  icon: typeof PenLine
  title: string
  sub: string
  urgency: 'danger' | 'warning' | 'neutral'
  chip: string
  to: string
}

function daysUntil(iso: string): number {
  return Math.ceil((new Date(iso).getTime() - Date.now()) / 86_400_000)
}

function programLabel(app: Application): string {
  return app.program?.program_name ?? 'your program'
}

export default function MySpaceHomePage() {
  const navigate = useNavigate()
  const { user } = useAuthStore()

  const apps = useQuery({ queryKey: ['applications'], queryFn: listMyApplications, staleTime: STALE })
  const saved = useQuery({ queryKey: ['saved-programs'], queryFn: listSaved, staleTime: STALE })
  const fortnight = useMemo(() => {
    const from = new Date().toISOString().slice(0, 10)
    const to = new Date(Date.now() + 14 * 86_400_000).toISOString().slice(0, 10)
    return { from, to }
  }, [])
  const calendar = useQuery({
    queryKey: ['calendar', 'home', fortnight],
    queryFn: () => getCalendar(fortnight),
    staleTime: STALE,
  })
  const recs = useQuery({ queryKey: ['recommendations'], queryFn: listRecommendations, staleTime: STALE })
  const runs = useQuery({ queryKey: ['workshop-runs', 'home'], queryFn: () => listWorkshopRuns(), staleTime: STALE })
  const threads = useQuery({ queryKey: ['inbox-threads', 'home'], queryFn: () => getThreads(), staleTime: STALE })
  const clarifications = useQuery({
    queryKey: ['intake-clarifications'],
    queryFn: listClarifications,
    staleTime: STALE,
  })

  const appList: Application[] = Array.isArray(apps.data) ? apps.data : []
  const savedList: unknown[] = Array.isArray(saved.data) ? saved.data : []
  const calItems: CalendarItem[] = Array.isArray(calendar.data) ? calendar.data : []
  const recList: any[] = Array.isArray(recs.data) ? recs.data : []
  const runList: WorkshopFeedbackRun[] = (Array.isArray(runs.data) ? runs.data : [])
    .slice()
    .sort((a, b) => (b.created_at || '').localeCompare(a.created_at || ''))
  const threadList: any[] = Array.isArray(threads.data) ? threads.data : []
  const pendingClarifications = clarifications.data?.clarifications?.length ?? 0
  const unreadThreads = threadList.filter(t => t.unread || (t.unread_count ?? 0) > 0).length

  // ── Pipeline counts ───────────────────────────────────────────────────────
  const drafts = appList.filter(a => a.status === 'draft')
  const inFlight = appList.filter(a => ['submitted', 'under_review', 'interview'].includes(a.status))
  const offers = appList.filter(
    a => a.status === 'decision_made'
      && ['admitted', 'accepted', 'conditional_admission'].includes(a.decision ?? ''),
  )

  // ── Up next — most important actions across the cycle, max 5.
  // Plain computation (cheap, derived) — no memo, so no stale-deps risk.
  const upNext: NextAction[] = (() => {
    const actions: NextAction[] = []
    for (const item of calItems.filter(i => i.status === 'overdue').slice(0, 2)) {
      actions.push({
        key: `overdue-${item.id}`,
        icon: AlertTriangle,
        title: item.title,
        sub: item.subtitle ?? item.institution_name ?? 'Overdue',
        urgency: 'danger',
        chip: 'overdue',
        to: '/s/calendar',
      })
    }
    for (const app of offers.filter(a => !a.student_decision)) {
      actions.push({
        key: `offer-${app.id}`,
        icon: Award,
        title: `Respond to your offer — ${programLabel(app)}`,
        sub: app.program?.institution_name ?? 'Decision needed',
        urgency: 'warning',
        chip: 'offer in',
        to: `/s/applications/${app.id}?tab=offer`,
      })
    }
    for (const item of calItems.filter(i => i.can_confirm)) {
      actions.push({
        key: `interview-${item.id}`,
        icon: CalendarIcon,
        title: item.title,
        sub: 'Pick a time that works for you',
        urgency: 'warning',
        chip: 'slots held',
        to: '/s/calendar',
      })
    }
    for (const app of drafts
      .slice()
      .sort((a, b) => (b.readiness_pct ?? 0) - (a.readiness_pct ?? 0))) {
      actions.push({
        key: `draft-${app.id}`,
        icon: PenLine,
        title: `Continue ${programLabel(app)}`,
        sub: app.readiness_pct != null ? `${Math.round(app.readiness_pct)}% ready to submit` : 'In progress',
        urgency: 'neutral',
        chip: 'draft',
        to: `/s/applications/${app.id}`,
      })
    }
    if (pendingClarifications > 0) {
      actions.push({
        key: 'clarifications',
        icon: Compass,
        title: `Answer ${pendingClarifications} quick question${pendingClarifications === 1 ? '' : 's'} from Uni`,
        sub: 'Sharpens your matches and readiness',
        urgency: 'neutral',
        chip: 'quick win',
        to: '/s',
      })
    }
    return actions.slice(0, 5)
  })()

  const waitingRecs = recList.filter(r => r.status === 'requested')
  const deadlines = calItems
    .filter(i => i.status !== 'cancelled' && i.status !== 'completed')
    .slice()
    .sort((a, b) => a.start_at.localeCompare(b.start_at))
    .slice(0, 5)

  const anyLoading = apps.isLoading || calendar.isLoading
  const brandNew = !anyLoading && appList.length === 0 && savedList.length === 0

  const hour = new Date().getHours()
  const greeting = hour < 12 ? 'Good morning' : hour < 18 ? 'Good afternoon' : 'Good evening'
  const firstName = user?.email?.split('@')[0] ?? ''

  return (
    <div className="w-full px-4 sm:px-6 py-5">
      <PageHeader
        eyebrow="My Space"
        title={`${greeting}${firstName ? `, ${firstName}` : ''}`}
        sub="Everything about your applications, in one place"
      />

      {anyLoading ? (
        <div className="space-y-3 mt-4">
          <Skeleton className="h-16" />
          <Skeleton className="h-40" />
        </div>
      ) : brandNew ? (
        // Empty state — a brand-new student's space fills as they work.
        <Card className="p-6 mt-2">
          <p className="text-sm font-medium text-foreground">Your space fills as you work.</p>
          <p className="text-xs text-muted-foreground mt-1 mb-4">
            Start with Uni to build your profile, then save programs you like — applications,
            deadlines and prep will all show up here.
          </p>
          <div className="flex flex-wrap gap-2">
            <button
              onClick={() => navigate('/s')}
              className="ui-btn inline-flex items-center gap-1.5 rounded-md bg-secondary px-3 py-1.5 text-xs font-medium text-secondary-foreground"
            >
              <Compass size={13} /> Talk to Uni
            </button>
            <button
              onClick={() => navigate('/s/explore')}
              className="ui-btn inline-flex items-center gap-1.5 rounded-md border border-border px-3 py-1.5 text-xs font-medium text-foreground hover:bg-muted"
            >
              <Target size={13} /> Browse matches
            </button>
          </div>
        </Card>
      ) : (
        <>
          {/* Pipeline — counts linking into the rooms. */}
          <div className="grid grid-cols-4 gap-3 rounded-lg border border-border bg-card px-4 py-3">
            <button onClick={() => navigate('/s/saved')} className="text-left" aria-label="Saved programs">
              <StatTile label="Saved" value={savedList.length} />
            </button>
            <button onClick={() => navigate('/s/applications')} className="text-left" aria-label="Applications in progress">
              <StatTile label="In progress" value={drafts.length} />
            </button>
            <button onClick={() => navigate('/s/applications')} className="text-left" aria-label="Submitted applications">
              <StatTile label="Submitted" value={inFlight.length} />
            </button>
            <button onClick={() => navigate('/s/applications')} className="text-left" aria-label="Offers">
              <StatTile label="Offers" value={offers.length} />
            </button>
          </div>

          {/* Up next */}
          <div className="mt-5">
            <SectionHeader>Up next</SectionHeader>
            {upNext.length === 0 ? (
              <p className="py-2 text-sm text-muted-foreground">
                Nothing urgent. Check your <button className="text-secondary hover:underline" onClick={() => navigate('/s/calendar')}>calendar</button> or
                keep prepping in <button className="text-secondary hover:underline" onClick={() => navigate('/s/prep')}>Prep</button>.
              </p>
            ) : (
              upNext.map(a => (
                <ListRow
                  key={a.key}
                  media={<a.icon size={15} className={a.urgency === 'danger' ? 'text-error' : a.urgency === 'warning' ? 'text-warning' : 'text-muted-foreground'} />}
                  title={a.title}
                  sub={a.sub}
                  trailing={
                    <Badge variant={a.urgency === 'danger' ? 'error' : a.urgency === 'warning' ? 'warning' : 'neutral'}>
                      {a.chip}
                    </Badge>
                  }
                  onClick={() => navigate(a.to)}
                />
              ))
            )}
          </div>

          <div className="mt-5 grid gap-6 md:grid-cols-2">
            {/* Deadlines — next 14 days */}
            <div>
              <SectionHeader
                action={
                  <button onClick={() => navigate('/s/calendar')} className="inline-flex items-center gap-1 text-xs text-secondary hover:underline">
                    Calendar <ArrowRight size={12} />
                  </button>
                }
              >
                Deadlines · next 14 days
              </SectionHeader>
              {calendar.isError ? (
                <p className="py-2 text-sm text-muted-foreground">Couldn't load your calendar.</p>
              ) : deadlines.length === 0 ? (
                <p className="py-2 text-sm text-muted-foreground">Nothing due in the next two weeks.</p>
              ) : (
                deadlines.map(item => {
                  const d = daysUntil(item.start_at)
                  return (
                    <ListRow
                      key={item.id}
                      title={item.title}
                      sub={item.subtitle ?? item.institution_name ?? undefined}
                      trailing={
                        <span className={`text-xs ${d <= 3 ? 'text-error font-medium' : 'text-muted-foreground'}`}>
                          {new Date(item.start_at).toLocaleDateString(undefined, { month: 'short', day: 'numeric' })}
                        </span>
                      }
                      onClick={() => navigate('/s/calendar')}
                    />
                  )
                })
              )}
            </div>

            {/* Waiting on others + latest feedback */}
            <div>
              <SectionHeader>Waiting on others</SectionHeader>
              {waitingRecs.length === 0 ? (
                <p className="py-2 text-sm text-muted-foreground">No outstanding requests.</p>
              ) : (
                waitingRecs.slice(0, 3).map(r => (
                  <ListRow
                    key={r.id}
                    media={<Mail size={15} className="text-muted-foreground" />}
                    title={`Rec letter — ${r.recommender_name}`}
                    sub={r.requested_at ? `Requested ${new Date(r.requested_at).toLocaleDateString(undefined, { month: 'short', day: 'numeric' })}` : 'Requested'}
                    trailing={<Badge variant="neutral">waiting</Badge>}
                    onClick={() => navigate('/s/prep?tab=recommenders')}
                  />
                ))
              )}

              <div className="mt-4">
                <SectionHeader
                  action={
                    unreadThreads > 0 ? (
                      <button onClick={() => navigate('/s/messages')} className="inline-flex items-center gap-1 text-xs text-secondary hover:underline">
                        <MessageSquare size={12} /> {unreadThreads} unread
                      </button>
                    ) : undefined
                  }
                >
                  Latest feedback
                </SectionHeader>
                {runList.length === 0 ? (
                  <p className="py-2 text-sm text-muted-foreground">
                    No workshop runs yet — get feedback on an essay draft in{' '}
                    <button className="text-secondary hover:underline" onClick={() => navigate('/s/prep?tab=workshops')}>Prep</button>.
                  </p>
                ) : (
                  runList.slice(0, 3).map(run => (
                    <ListRow
                      key={run.id}
                      media={<GraduationCap size={15} className="text-muted-foreground" />}
                      title={`${run.domain === 'essay' ? 'Essay' : run.domain === 'interview' ? 'Interview' : 'Test'} feedback`}
                      sub={new Date(run.created_at).toLocaleDateString(undefined, { month: 'short', day: 'numeric' })}
                      onClick={() => navigate('/s/prep?tab=workshops')}
                    />
                  ))
                )}
              </div>
            </div>
          </div>

          {/* Quiet footer link into the portfolio. */}
          <div className="mt-6 flex justify-end">
            <button
              onClick={() => navigate('/s/applications')}
              className="inline-flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground"
            >
              <FolderKanban size={12} /> All applications <ArrowRight size={12} />
            </button>
          </div>
        </>
      )}
    </div>
  )
}
