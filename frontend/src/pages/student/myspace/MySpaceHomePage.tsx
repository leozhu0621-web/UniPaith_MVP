import { useEffect, useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  Mail, FolderKanban, Compass, Target,
  MessageSquare, GraduationCap, ArrowRight, Send,
} from 'lucide-react'
import { PageContainer, PageHeader, SectionHeader, ListRow, StatTile } from '../../../components/student/density'
import EnrichWidget from '../../../components/student/EnrichWidget'
import Card from '../../../components/ui/Card'
import Badge from '../../../components/ui/Badge'
import Button from '../../../components/ui/Button'
import Skeleton from '../../../components/ui/Skeleton'
import { showToast } from '../../../stores/toast-store'
import { listMyApplications } from '../../../api/applications'
import { getCalendar, type CalendarItem } from '../../../api/calendar'
import { listSaved } from '../../../api/saved-lists'
import { qk } from '../../../api/queryKeys'
import { listRecommendations, sendRecommendationRequest } from '../../../api/recommendations'
import { listWorkshopRuns } from '../../../api/workshops-feedback'
import { getThreads } from '../../../api/inbox'
import { listClarifications } from '../../../api/intake'
import { getProfile, getOnboarding } from '../../../api/students'
import Coachmark from '../../../components/ui/Coachmark'
import { buildUpNext } from './home/upNext'
import TodaysFocus from './home/TodaysFocus'
import MomentumBand from './home/MomentumBand'
import StrategySnapshot from './home/StrategySnapshot'
import TopMatchesPeek from './home/TopMatchesPeek'
import ScholarshipsPeek from './home/ScholarshipsPeek'
import { freshWinIds, markCelebrated } from './home/celebrate'
import { DeadlinePill } from '../../../utils/deadline'
import type { Application, WorkshopFeedbackRun, OnboardingStatus } from '../../../types'

// My Space · Home — mission control (Spec 2026-06-10 §4, redesigned 2026-06-14).
// Focus → momentum → density: a Today's-focus hero, a momentum band (journey
// map + this-week ribbon + onboarding ring), then the dense dashboard. Pure
// client-side composition of endpoints that already exist; no aggregate backend.

const STALE = 60_000

export default function MySpaceHomePage() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  // Nudge a recommender from the home dashboard — same action as the
  // Applications → Recommenders tab (POST /students/me/recommendations/:id/send).
  const nudge = useMutation({
    mutationFn: (id: string) => sendRecommendationRequest(id),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['recommendations'] }); showToast('Reminder sent', 'success') },
    onError: () => showToast("We couldn't send the reminder. Please try again.", 'error'),
  })

  // Query keys are shared with their primary consumers so navigating between
  // rooms reuses cache.
  const apps = useQuery({ queryKey: ['my-applications'], queryFn: listMyApplications, staleTime: STALE })
  const profile = useQuery({ queryKey: ['profile'], queryFn: getProfile, staleTime: 300_000 })
  const onboarding = useQuery<OnboardingStatus>({ queryKey: ['onboarding'], queryFn: getOnboarding, staleTime: STALE })
  const saved = useQuery({ queryKey: qk.savedPrograms(), queryFn: listSaved, staleTime: STALE })
  const fortnight = useMemo(() => {
    const from = new Date().toISOString().slice(0, 10)
    const to = new Date(Date.now() + 14 * 86_400_000).toISOString().slice(0, 10)
    return { from, to }
  }, [])
  const calendar = useQuery({ queryKey: ['calendar', 'home', fortnight], queryFn: () => getCalendar(fortnight), staleTime: STALE })
  const recs = useQuery({ queryKey: ['recommendations'], queryFn: listRecommendations, staleTime: STALE })
  const runs = useQuery({ queryKey: ['workshop-runs', 'home'], queryFn: () => listWorkshopRuns(), staleTime: STALE })
  const threads = useQuery({ queryKey: ['inbox-threads-unread'], queryFn: () => getThreads(), staleTime: 30_000 })
  const clarifications = useQuery({ queryKey: ['intake-clarifications'], queryFn: listClarifications, staleTime: STALE })

  const appList: Application[] = Array.isArray(apps.data) ? apps.data : []
  const savedList: any[] = Array.isArray(saved.data) ? saved.data : []
  const calItems: CalendarItem[] = Array.isArray(calendar.data) ? calendar.data : []
  const recList: any[] = Array.isArray(recs.data) ? recs.data : []
  const runList: WorkshopFeedbackRun[] = (Array.isArray(runs.data) ? runs.data : []).slice().sort((a, b) => (b.created_at || '').localeCompare(a.created_at || ''))
  const threadList: any[] = Array.isArray(threads.data) ? threads.data : []
  const pendingClarifications = clarifications.data?.clarifications?.length ?? 0
  const unreadThreads = threadList.filter(t => t.unread || (t.unread_count ?? 0) > 0).length

  // ── Pipeline counts ───────────────────────────────────────────────────────
  const drafts = appList.filter(a => a.status === 'draft')
  const inFlight = appList.filter(a => ['submitted', 'under_review', 'interview'].includes(a.status))
  const offers = appList.filter(a => a.status === 'decision_made' && ['admitted', 'accepted', 'conditional_admission'].includes(a.decision ?? ''))

  // ── Up next → Today's focus (the top action) + the rest ───────────────────
  const upNext = buildUpNext({ calItems, offers, drafts, pendingClarifications })
  const focus = upNext[0] ?? null
  const restUpNext = upNext.slice(1)

  const waitingRecs = recList.filter(r => r.status === 'requested')
  const deadlines = calItems.filter(i => i.status !== 'cancelled' && i.status !== 'completed').slice().sort((a, b) => a.start_at.localeCompare(b.start_at)).slice(0, 5)

  // ── Momentum inputs (real data only) ──────────────────────────────────────
  const stage = { savedCount: savedList.length, appCount: appList.length, hasOffer: offers.length > 0, hasDecision: appList.some(a => a.status === 'decision_made') }
  const week = { saved: savedList, runs: runList, apps: appList }

  // Earned-gold win beat: a fresh offer fires one gold pulse on the Offers tile.
  const offersEarned = offers.length > 0
  const freshOffer = useMemo(() => freshWinIds(offers.map(o => `offer-${o.id}`)).length > 0, [offers])
  useEffect(() => {
    if (offers.length) markCelebrated(offers.map(o => `offer-${o.id}`))
  }, [offers])

  const anyLoading = apps.isLoading || calendar.isLoading
  const brandNew = !anyLoading && appList.length === 0 && savedList.length === 0
  const onboardingComplete = (onboarding.data?.completion_percentage ?? 0) >= 100

  const hour = new Date().getHours()
  const greeting = hour < 12 ? 'Good morning' : hour < 18 ? 'Good afternoon' : 'Good evening'
  // Never greet by the email local-part — "Good afternoon, maya.student.1782…"
  // reads as a bug. With no real first name the header is just the greeting (the
  // `firstName ? …` guard below already handles the empty case).
  const firstName = profile.data?.first_name?.trim() || ''

  return (
    <PageContainer>
      <Coachmark
        id="myspace-home"
        title="Your new home base"
        body="Everything personal lives here — applications, prep, calendar, messages, saved programs, and your profile."
        placement="bottom"
      >
        <PageHeader eyebrow="My Space" title={`${greeting}${firstName ? `, ${firstName}` : ''}`} />
      </Coachmark>

      {anyLoading ? (
        <div className="mt-4 space-y-3">
          <Skeleton className="h-16" />
          <Skeleton className="h-40" />
        </div>
      ) : brandNew ? (
        // Empty state — the momentum band (with its setup ring) is the primary
        // content for a brand-new student; the CTA card follows as a second beat.
        <div className="stagger-list mt-2 space-y-4">
          <MomentumBand stage={stage} week={week} />
          <Card pad={false} className="p-6">
            <p className="mb-4 text-sm font-medium text-foreground">Your space fills as you work.</p>
            <div className="flex flex-wrap gap-2">
              <button onClick={() => navigate('/s')} className="ui-btn inline-flex items-center gap-1.5 rounded-md bg-secondary px-3 py-1.5 text-xs font-medium text-secondary-foreground"><Compass size={13} /> Talk to Uni</button>
              <button onClick={() => navigate('/s/explore')} className="ui-btn inline-flex items-center gap-1.5 rounded-md border border-border px-3 py-1.5 text-xs font-medium text-foreground hover:bg-muted"><Target size={13} /> Browse programs</button>
            </div>
          </Card>
        </div>
      ) : (
        <div className="stagger-list">
          {/* C — one focal point. */}
          <TodaysFocus action={focus} onboardingComplete={onboardingComplete} />

          {/* A — momentum band. */}
          <MomentumBand stage={stage} week={week} className="mt-5" />

          {/* B — dense dashboard. Pipeline with an earned-gold Offers tile. */}
          <div className="mt-5 grid grid-cols-2 sm:grid-cols-4 gap-3 rounded-lg border border-border bg-card px-4 py-3">
            <button onClick={() => navigate('/s/saved')} className="text-left" aria-label="Saved programs"><StatTile label="Saved" value={savedList.length} /></button>
            <button onClick={() => navigate('/s/applications?status=draft')} className="text-left" aria-label="Applications in progress"><StatTile label="In progress" value={drafts.length} /></button>
            <button onClick={() => navigate('/s/applications?status=in_flight')} className="text-left" aria-label="Submitted applications"><StatTile label="Submitted" value={inFlight.length} /></button>
            <button
              onClick={() => navigate('/s/applications?tab=offers')}
              aria-label="Offers"
              className={`text-left transition-shadow ${offersEarned ? '-mx-2 rounded-md px-2 ring-1 ring-primary/40' : ''} ${offersEarned && freshOffer ? 'motion-safe:animate-beat' : ''}`}
            >
              <StatTile label="Offers" value={offers.length} tone={offersEarned ? 'gold' : 'default'} />
            </button>
          </div>

          {/* Up next — everything after the promoted focus. */}
          {restUpNext.length > 0 && (
            <div className="stagger-list mt-5">
              <SectionHeader>Up next</SectionHeader>
              {restUpNext.map(a => (
                <ListRow
                  key={a.key}
                  media={<a.icon size={15} className={a.urgency === 'danger' ? 'text-error' : a.urgency === 'warning' ? 'text-warning' : 'text-muted-foreground'} />}
                  title={a.title}
                  sub={a.sub}
                  trailing={<Badge variant={a.urgency === 'danger' ? 'error' : a.urgency === 'warning' ? 'warning' : 'neutral'}>{a.chip}</Badge>}
                  onClick={() => navigate(a.to)}
                />
              ))}
            </div>
          )}

          {/* Your top matches — a discovery peek that deep-links to /s/explore. */}
          <TopMatchesPeek className="mt-5" />

          {/* AI Structure (Spec 1) — the next signal to enrich; renders nothing
              once the profile is full. Deeper profile → sharper matches. */}
          <div className="mt-5">
            <EnrichWidget />
          </div>

          <div className="mt-5 grid gap-6 md:grid-cols-2">
            {/* Deadlines — next 14 days */}
            <div>
              <SectionHeader action={<button onClick={() => navigate('/s/calendar')} className="inline-flex items-center gap-1 text-xs text-secondary hover:underline">Calendar <ArrowRight size={12} /></button>}>Deadlines · next 14 days</SectionHeader>
              {calendar.isError ? (
                <p className="py-2 text-sm text-muted-foreground">Couldn't load your calendar.</p>
              ) : deadlines.length === 0 ? (
                <p className="py-2 text-sm text-muted-foreground">Nothing due in the next two weeks.</p>
              ) : (
                deadlines.map(item => (
                  <ListRow
                    key={item.id}
                    title={item.title}
                    sub={item.subtitle ?? item.institution_name ?? undefined}
                    trailing={<DeadlinePill date={item.start_at} />}
                    onClick={() => navigate('/s/calendar')}
                  />
                ))
              )}
            </div>

            {/* Waiting on others + latest feedback */}
            <div>
              <SectionHeader>Waiting on others</SectionHeader>
              {waitingRecs.length === 0 ? (
                <p className="py-2 text-sm text-muted-foreground">No pending requests.</p>
              ) : (
                waitingRecs.slice(0, 3).map(r => (
                  <ListRow
                    key={r.id}
                    media={<Mail size={15} className="text-muted-foreground" />}
                    title={`Rec letter — ${r.recommender_name}`}
                    sub={r.requested_at ? `Requested ${new Date(r.requested_at).toLocaleDateString(undefined, { month: 'short', day: 'numeric' })}` : 'Requested'}
                    trailing={
                      <Button
                        size="sm"
                        variant="tertiary"
                        onClick={() => nudge.mutate(r.id)}
                        disabled={nudge.isPending && nudge.variables === r.id}
                      >
                        <Send size={12} className="mr-1" /> Nudge
                      </Button>
                    }
                  />
                ))
              )}

              <div className="mt-4">
                <SectionHeader action={unreadThreads > 0 ? <button onClick={() => navigate('/s/messages')} className="inline-flex items-center gap-1 text-xs text-secondary hover:underline"><MessageSquare size={12} /> {unreadThreads} unread</button> : undefined}>Latest feedback</SectionHeader>
                {runList.length === 0 ? (
                  <p className="py-2 text-sm text-muted-foreground">No workshop runs yet.</p>
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

          {/* Opportunity row — strategy + scholarships you may qualify for.
              ScholarshipsPeek self-hides when there are no matches, so this
              collapses to a single full-width strategy card. */}
          <div className="mt-5 grid gap-6 md:grid-cols-2">
            <StrategySnapshot />
            <ScholarshipsPeek />
          </div>

          {/* Quiet footer link into the portfolio. */}
          <div className="mt-6 flex justify-end">
            <button onClick={() => navigate('/s/applications')} className="inline-flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground"><FolderKanban size={12} /> All applications <ArrowRight size={12} /></button>
          </div>
        </div>
      )}
    </PageContainer>
  )
}
