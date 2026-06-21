import { useEffect, useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  AlertTriangle,
  ArrowRight,
  BookOpenCheck,
  CalendarClock,
  CheckCircle2,
  Clock3,
  FileText,
  FileUp,
  Mail,
  MessageCircle,
  RotateCcw,
  ShieldCheck,
  Target,
} from 'lucide-react'
import { PageContainer, PageHeader, SectionHeader, StatTile } from '../../../components/student/density'
import Card from '../../../components/ui/Card'
import Badge from '../../../components/ui/Badge'
import Skeleton from '../../../components/ui/Skeleton'
import { getMySpaceOverview, patchMySpaceTask, type MySpaceModuleItem, type MySpaceProvenance, type MySpaceReadiness, type MySpaceTask, type MySpaceUrgency } from '../../../api/my-space'
import { qk } from '../../../api/queryKeys'
import { track } from '../../../lib/analytics'
import { useAuthStore } from '../../../stores/auth-store'

const STALE = 60_000

const urgencyLabel: Record<MySpaceUrgency, string> = {
  focus_now: 'focus now',
  priority_window: 'priority',
  gentle_attention: 'attention',
  neutral: 'normal',
}

const urgencyTone: Record<MySpaceUrgency, 'error' | 'warning' | 'success' | 'neutral'> = {
  focus_now: 'error',
  priority_window: 'warning',
  gentle_attention: 'neutral',
  neutral: 'success',
}

function formatDate(iso: string | null): string | null {
  if (!iso) return null
  const date = new Date(iso)
  if (Number.isNaN(date.getTime())) return null
  return date.toLocaleDateString(undefined, { month: 'short', day: 'numeric' })
}

function sourceLine(item: { provenance?: { source: string; label: string; confidence: number | null }[] }) {
  const source = item.provenance?.[0]
  if (!source) return 'Source unavailable'
  const confidence = source.confidence == null ? '' : ` · ${source.confidence}% confidence`
  return `${source.label} · ${source.source.split('_').join(' ')}${confidence}`
}

function primarySource(item: { provenance?: MySpaceProvenance[] }) {
  return item.provenance?.[0] ?? null
}

function ownerLabel(owner: string | null | undefined) {
  if (owner === 'student') return 'you'
  if (owner === 'recommender') return 'recommender'
  if (owner === 'institution') return 'school'
  if (owner === 'system') return 'system'
  return 'tracked'
}

function uniHandoffProps(route: string) {
  if (!route.startsWith('/s?')) return null
  const params = new URLSearchParams(route.slice(route.indexOf('?') + 1))
  const intent = params.get('intent')
  if (!intent) return null
  return {
    route,
    intent,
    source_task: params.get('source_task'),
    return_to: params.get('return_to'),
    artifact_destination: params.get('artifact_destination'),
  }
}

export default function MySpaceHomePage() {
  const navigate = useNavigate()
  const qc = useQueryClient()
  const { user } = useAuthStore()

  const overview = useQuery({
    queryKey: qk.mySpaceOverview(),
    queryFn: getMySpaceOverview,
    staleTime: STALE,
  })

  const taskMutation = useMutation({
    mutationFn: ({ key, dismissed, snoozed_until }: { key: string; dismissed?: boolean; snoozed_until?: string | null }) =>
      patchMySpaceTask(key, { dismissed, snoozed_until }),
    onSuccess: () => qc.invalidateQueries({ queryKey: qk.mySpaceOverview() }),
  })

  useEffect(() => {
    if (overview.data) {
      track('my_space_viewed', {
        task_count: overview.data.tasks.filter(t => t.active).length,
        generated_at: overview.data.generated_at,
      })
    }
  }, [overview.data])

  const data = overview.data
  const activeTasks = useMemo(() => data?.tasks.filter(t => t.active) ?? [], [data])
  const hiddenTasks = useMemo(() => data?.tasks.filter(t => !t.active) ?? [], [data])
  const focus = activeTasks[0] ?? null
  const firstName = data?.student.first_name || user?.email?.split('@')[0] || ''
  const hour = new Date().getHours()
  const greeting = hour < 12 ? 'Good morning' : hour < 18 ? 'Good afternoon' : 'Good evening'

  const go = (route: string, event: string, props: Record<string, string | number | boolean | null | undefined> = {}) => {
    track(event, { route, ...props })
    const handoff = uniHandoffProps(route)
    if (handoff) track('uni_chat_handoff_started', handoff)
    navigate(route)
  }

  const dismissTask = (task: MySpaceTask) => {
    taskMutation.mutate({ key: task.key, dismissed: true })
  }

  const snoozeTask = (task: MySpaceTask) => {
    const snoozed = new Date(Date.now() + 7 * 86_400_000).toISOString()
    taskMutation.mutate({ key: task.key, snoozed_until: snoozed })
  }

  const restoreTask = (task: MySpaceTask) => {
    track('my_space_task_restored', { task_key: task.key, category: task.category })
    taskMutation.mutate({ key: task.key, dismissed: false, snoozed_until: null })
  }

  return (
    <PageContainer>
      <PageHeader
        eyebrow="My Space"
        title={`${greeting}${firstName ? `, ${firstName}` : ''}`}
        sub="Admissions command center"
      />

      {overview.isLoading ? (
        <LoadingState />
      ) : overview.isError || !data ? (
        <Card pad={false} className="mt-4 p-5">
          <div className="flex items-start gap-3">
            <AlertTriangle size={18} className="mt-0.5 text-error" />
            <div>
              <p className="text-sm font-medium text-foreground">My Space did not load.</p>
              <p className="mt-1 text-xs text-muted-foreground">Refresh this view or open Uni if the issue continues.</p>
              <button
                type="button"
                onClick={() => overview.refetch()}
                className="ui-btn mt-3 rounded-md border border-border px-3 py-1.5 text-xs font-medium hover:bg-muted"
              >
                Retry
              </button>
            </div>
          </div>
        </Card>
      ) : (
        <div className="stagger-list mt-4 space-y-5">
          {data.access_issues.length > 0 && (
            <div className="rounded-md border border-warning/30 bg-warning/10 px-3 py-2 text-xs text-foreground">
              Some My Space modules are using fallback data. {data.access_issues[0].label}.
            </div>
          )}

          <FocusPanel
            task={focus}
            onGo={(task) => go(task.cta_route, 'my_space_task_clicked', { task_key: task.key, category: task.category })}
            onReviewSource={(task, route) => go(route, 'readiness_explanation_opened', { task_key: task.key, category: task.category, source: 'provenance' })}
            onDismiss={dismissTask}
            onSnooze={snoozeTask}
            busy={taskMutation.isPending}
          />

          <PipelineStrip items={data.pipeline} onGo={(route, key) => go(route, key === 'offers' ? 'offer_compare_opened' : 'my_space_task_clicked', { module: 'pipeline', key })} />

          <div className="grid gap-5 xl:grid-cols-[minmax(0,1.1fr)_minmax(320px,0.9fr)]">
            <ReadinessLedger readiness={data.readiness} onGo={(row) => go(row.route, 'readiness_explanation_opened', { key: row.key, status: row.status })} />
            <ImportCard item={data.import_status} onGo={(route) => go(route, 'my_space_empty_cta_clicked', { module: 'import' })} />
          </div>

          <div className="grid gap-5 xl:grid-cols-2">
            <ItemModule
              title="Application portfolio"
              items={data.application_portfolio}
              icon={<FileText size={15} />}
              emptyTitle="No applications yet."
              emptyText="Start from a saved program when you are ready; every application becomes a tracked project here."
              emptyRoute="/s/applications"
              emptyCtaLabel="Open applications"
              onGo={(item) => go(item.route, 'my_space_task_clicked', { module: 'application_portfolio', key: item.key })}
              onReviewSource={(item, route) => go(route, 'readiness_explanation_opened', { module: 'application_portfolio', key: item.key, source: 'provenance' })}
              onEmpty={() => go('/s/applications', 'my_space_empty_cta_clicked', { module: 'application_portfolio' })}
            />
            <TaskModule
              title="Evidence gaps"
              tasks={data.evidence_gaps.filter(t => t.active)}
              emptyTitle="Evidence is clear for now."
              emptyText="New gaps appear when Uni extracts uncertain data or an application needs more evidence."
              emptyRoute="/s/import"
              emptyCtaLabel="Review imports"
              onGo={(task) => go(task.cta_route, 'my_space_task_clicked', { task_key: task.key, category: task.category })}
              onReviewSource={(task, route) => go(route, 'readiness_explanation_opened', { task_key: task.key, category: task.category, source: 'provenance' })}
              onEmpty={() => go('/s/import', 'my_space_empty_cta_clicked', { module: 'evidence_gaps' })}
              onDismiss={dismissTask}
              onSnooze={snoozeTask}
              busy={taskMutation.isPending}
            />
            <ItemModule
              title="Deadlines"
              items={data.deadlines}
              icon={<CalendarClock size={15} />}
              emptyTitle="No near deadlines."
              emptyText="Calendar items appear from applications, interviews, recommenders, offers, and your reminders."
              emptyRoute="/s/calendar"
              emptyCtaLabel="Open calendar"
              onGo={(item) => go(item.route, 'my_space_task_clicked', { module: 'deadlines', key: item.key })}
              onReviewSource={(item, route) => go(route, 'readiness_explanation_opened', { module: 'deadlines', key: item.key, source: 'provenance' })}
              onEmpty={() => go('/s/calendar', 'my_space_empty_cta_clicked', { module: 'deadlines' })}
            />
            <ItemModule
              title="Waiting on others"
              items={data.waiting_on}
              icon={<Mail size={15} />}
              emptyTitle="No one is blocking you."
              emptyText="Recommender requests and admissions-office replies will appear here."
              emptyRoute="/s/prep?tab=recommenders"
              emptyCtaLabel="Review recommenders"
              onGo={(item) => go(item.route, item.owner === 'recommender' ? 'recommender_nudge_clicked' : 'my_space_task_clicked', { module: 'waiting_on', key: item.key })}
              onReviewSource={(item, route) => go(route, 'readiness_explanation_opened', { module: 'waiting_on', key: item.key, source: 'provenance' })}
              onEmpty={() => go('/s/prep?tab=recommenders', 'my_space_empty_cta_clicked', { module: 'waiting_on' })}
            />
            <ItemModule
              title="Messages"
              items={data.messages}
              icon={<MessageCircle size={15} />}
              emptyTitle="No admissions messages need review."
              emptyText="Threads from schools, recommenders, and support teams will appear here with who owns the next reply."
              emptyRoute="/s/messages"
              emptyCtaLabel="Open messages"
              onGo={(item) => go(item.route, 'my_space_task_clicked', { module: 'messages', key: item.key })}
              onReviewSource={(item, route) => go(route, 'readiness_explanation_opened', { module: 'messages', key: item.key, source: 'provenance' })}
              onEmpty={() => go('/s/messages', 'my_space_empty_cta_clicked', { module: 'messages' })}
            />
            <ItemModule
              title="Latest feedback"
              items={data.feedback}
              icon={<BookOpenCheck size={15} />}
              emptyTitle="No workshop feedback yet."
              emptyText="Use Prep to get feedback on essays, interviews, and test plans."
              emptyRoute="/s/prep?tab=workshops"
              emptyCtaLabel="Open Prep"
              onGo={(item) => go(item.route, 'my_space_task_clicked', { module: 'feedback', key: item.key })}
              onReviewSource={(item, route) => go(route, 'readiness_explanation_opened', { module: 'feedback', key: item.key, source: 'provenance' })}
              onEmpty={() => go('/s/prep?tab=workshops', 'my_space_empty_cta_clicked', { module: 'feedback' })}
            />
          </div>

          <div className="grid gap-5 xl:grid-cols-3">
            <StrategyCard
              strategy={data.strategy}
              onGo={(route) => go(route, 'strategy_refine_clicked')}
              onReviewSource={(item, route) => go(route, 'readiness_explanation_opened', { module: 'strategy', key: item.key, source: 'provenance' })}
            />
            <PrepCard readiness={data.prep_readiness} onGo={(row) => go(row.route, 'readiness_explanation_opened', { key: row.key, status: row.status })} />
            <ItemModule
              title="Offers & costs"
              items={data.offers}
              icon={<ShieldCheck size={15} />}
              emptyTitle="No active offers."
              emptyText="Admits, deposits, conditions, and external offers will become compare rows here."
              emptyRoute="/s/applications?tab=offers"
              emptyCtaLabel="Compare offers"
              onGo={(item) => go(item.route, 'offer_compare_opened', { key: item.key })}
              onReviewSource={(item, route) => go(route, 'readiness_explanation_opened', { module: 'offers', key: item.key, source: 'provenance' })}
              onEmpty={() => go('/s/applications?tab=offers', 'my_space_empty_cta_clicked', { module: 'offers' })}
            />
          </div>

          <div className="grid gap-5 xl:grid-cols-2">
            <ItemModule
              title="Saved targets"
              items={data.saved_targets}
              icon={<Target size={15} />}
              emptyTitle="No saved programs yet."
              emptyText="Save programs from Discover to build a shortlist, compare fit, and start applications."
              emptyRoute="/s/explore"
              emptyCtaLabel="Open Discover"
              onGo={(item) => go(item.route, 'my_space_task_clicked', { module: 'saved_targets', key: item.key })}
              onReviewSource={(item, route) => go(route, 'readiness_explanation_opened', { module: 'saved_targets', key: item.key, source: 'provenance' })}
              onEmpty={() => go('/s/explore', 'my_space_empty_cta_clicked', { module: 'saved_targets' })}
            />
            <ItemModule
              title="Recent changes"
              items={data.recent_changes}
              icon={<Clock3 size={15} />}
              emptyTitle="No recent movement."
              emptyText="Updates appear after imports, saved programs, application edits, feedback, and offer changes."
              emptyRoute="/s"
              emptyCtaLabel="Open Uni"
              onGo={(item) => go(item.route, 'my_space_task_clicked', { module: 'recent_changes', key: item.key })}
              onReviewSource={(item, route) => go(route, 'readiness_explanation_opened', { module: 'recent_changes', key: item.key, source: 'provenance' })}
              onEmpty={() => go('/s', 'my_space_empty_cta_clicked', { module: 'recent_changes' })}
            />
          </div>

          <HiddenTasksPanel tasks={hiddenTasks} onRestore={restoreTask} busy={taskMutation.isPending} />
        </div>
      )}
    </PageContainer>
  )
}

function LoadingState() {
  return (
    <div className="mt-4 space-y-4">
      <Skeleton className="h-28" />
      <Skeleton className="h-20" />
      <div className="grid gap-4 md:grid-cols-2">
        <Skeleton className="h-56" />
        <Skeleton className="h-56" />
      </div>
    </div>
  )
}

function FocusPanel({
  task,
  onGo,
  onReviewSource,
  onDismiss,
  onSnooze,
  busy,
}: {
  task: MySpaceTask | null
  onGo: (task: MySpaceTask) => void
  onReviewSource: (task: MySpaceTask, route: string) => void
  onDismiss: (task: MySpaceTask) => void
  onSnooze: (task: MySpaceTask) => void
  busy: boolean
}) {
  if (!task) {
    return (
      <Card pad={false} className="p-5">
        <div className="flex items-start gap-3">
          <CheckCircle2 size={18} className="mt-0.5 text-success" />
          <div>
            <p className="text-sm font-medium text-foreground">No urgent task right now.</p>
            <p className="mt-1 text-xs text-muted-foreground">Use the readiness ledger below to decide where to strengthen your profile next.</p>
          </div>
        </div>
      </Card>
    )
  }
  const due = formatDate(task.due_at)
  return (
    <Card pad={false} className="p-5">
      <div className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_auto] lg:items-start">
        <div className="min-w-0">
          <div className="mb-2 flex flex-wrap items-center gap-2">
            <Badge variant={urgencyTone[task.urgency]}>{urgencyLabel[task.urgency]}</Badge>
            <Badge variant="neutral">{ownerLabel(task.owner)}</Badge>
            {due && <span className="text-xs text-muted-foreground">Due {due}</span>}
          </div>
          <p className="text-base font-semibold text-foreground">{task.title}</p>
          <p className="mt-1 max-w-3xl text-sm text-muted-foreground">{task.description}</p>
          <p className="mt-2 text-xs text-muted-foreground">{sourceLine(task)}</p>
          {(task.blocker || task.missing_field) && (
            <p className="mt-2 text-xs text-foreground">
              {task.blocker ? `${task.blocker}` : 'Missing'}{task.missing_field ? ` · ${task.missing_field}` : ''}
            </p>
          )}
          <EvidenceDisclosure item={task} onReviewSource={(route) => onReviewSource(task, route)} />
        </div>
        <div className="flex flex-wrap gap-2 lg:justify-end">
          <button
            type="button"
            onClick={() => onGo(task)}
            aria-label={`${task.cta_label}: ${task.title}`}
            className="ui-btn inline-flex items-center gap-1.5 rounded-md bg-secondary px-3 py-2 text-sm font-medium text-secondary-foreground"
          >
            {task.cta_label} <ArrowRight size={14} />
          </button>
          {task.dismissible && (
            <>
              <button
                type="button"
                disabled={busy}
                onClick={() => onSnooze(task)}
                aria-label={`Snooze ${task.title}`}
                className="ui-btn rounded-md border border-border px-3 py-2 text-sm font-medium text-foreground hover:bg-muted disabled:opacity-50"
              >
                Snooze
              </button>
              <button
                type="button"
                disabled={busy}
                onClick={() => onDismiss(task)}
                aria-label={`Dismiss ${task.title}`}
                className="ui-btn rounded-md border border-border px-3 py-2 text-sm font-medium text-foreground hover:bg-muted disabled:opacity-50"
              >
                Dismiss
              </button>
            </>
          )}
        </div>
      </div>
    </Card>
  )
}

function PipelineStrip({ items, onGo }: { items: { key: string; label: string; value: number | string; route: string; status?: string | null }[]; onGo: (route: string, key: string) => void }) {
  return (
    <div className="grid grid-cols-2 gap-3 rounded-lg border border-border bg-card px-4 py-3 md:grid-cols-4">
      {items.map(item => (
        <button
          key={item.key}
          type="button"
          onClick={() => onGo(item.route, item.key)}
          className={`rounded-md px-2 py-1 text-left transition-colors hover:bg-muted/50 focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 ${item.key === 'offers' && Number(item.value) > 0 ? 'ring-1 ring-primary/40' : ''}`}
        >
          <StatTile label={item.label} value={item.value} tone={item.key === 'offers' && Number(item.value) > 0 ? 'gold' : 'default'} />
        </button>
      ))}
    </div>
  )
}

function ReadinessLedger({ readiness, onGo }: { readiness: MySpaceReadiness[]; onGo: (row: MySpaceReadiness) => void }) {
  return (
    <Card pad={false} className="p-5">
      <SectionHeader>Readiness ledger</SectionHeader>
      <div className="space-y-3">
        {readiness.map(row => (
          <button
            key={row.key}
            type="button"
            onClick={() => onGo(row)}
            className="w-full rounded-md border-b border-border py-2 text-left last:border-0 hover:bg-muted/50 focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2"
          >
            <div className="flex items-center justify-between gap-3">
              <span className="text-sm font-medium text-foreground">{row.label}</span>
              <Badge variant={readinessTone(row.status)}>{row.status.replace('_', ' ')}</Badge>
            </div>
            <div
              role="progressbar"
              aria-label={`${row.label} readiness`}
              aria-valuemin={0}
              aria-valuemax={100}
              aria-valuenow={row.pct ?? 0}
              className="mt-2 h-1.5 overflow-hidden rounded-full bg-muted"
            >
              <div className="h-full rounded-full bg-secondary" style={{ width: `${row.pct ?? 0}%` }} />
            </div>
            <p className="mt-2 text-xs text-muted-foreground">{row.detail}</p>
            <p className="mt-1 text-xs text-muted-foreground">{sourceLine(row)}</p>
          </button>
        ))}
      </div>
    </Card>
  )
}

function readinessTone(status: MySpaceReadiness['status']): 'success' | 'warning' | 'error' | 'neutral' {
  if (status === 'ready') return 'success'
  if (status === 'blocked') return 'error'
  if (status === 'needs_attention') return 'warning'
  return 'neutral'
}

function ImportCard({ item, onGo }: { item: MySpaceModuleItem; onGo: (route: string) => void }) {
  return (
    <Card pad={false} className="p-5">
      <SectionHeader>Import & clarification</SectionHeader>
      <div className="flex items-start gap-3">
        <FileUp size={17} className="mt-0.5 text-muted-foreground" />
        <div className="min-w-0 flex-1">
          <p className="text-sm font-medium text-foreground">{item.title}</p>
          <p className="mt-1 text-xs text-muted-foreground">{item.description}</p>
          <p className="mt-2 text-xs text-muted-foreground">{sourceLine(item)}</p>
          <button
            type="button"
            onClick={() => onGo(item.route)}
            className="ui-btn mt-3 inline-flex items-center gap-1.5 rounded-md border border-border px-3 py-1.5 text-xs font-medium hover:bg-muted"
          >
            Open import <ArrowRight size={12} />
          </button>
        </div>
      </div>
    </Card>
  )
}

function TaskModule({
  title,
  tasks,
  emptyTitle,
  emptyText,
  emptyRoute,
  emptyCtaLabel,
  onGo,
  onReviewSource,
  onEmpty,
  onDismiss,
  onSnooze,
  busy,
}: {
  title: string
  tasks: MySpaceTask[]
  emptyTitle: string
  emptyText: string
  emptyRoute: string
  emptyCtaLabel: string
  onGo: (task: MySpaceTask) => void
  onReviewSource: (task: MySpaceTask, route: string) => void
  onEmpty: () => void
  onDismiss: (task: MySpaceTask) => void
  onSnooze: (task: MySpaceTask) => void
  busy: boolean
}) {
  return (
    <Card pad={false} className="p-5">
      <SectionHeader count={tasks.length}>{title}</SectionHeader>
      {tasks.length === 0 ? (
        <EmptyAction title={emptyTitle} text={emptyText} route={emptyRoute} ctaLabel={emptyCtaLabel} onClick={onEmpty} />
      ) : (
        <div className="divide-y divide-border">
          {tasks.slice(0, 5).map(task => (
            <TaskRow key={task.key} task={task} onGo={onGo} onReviewSource={onReviewSource} onDismiss={onDismiss} onSnooze={onSnooze} busy={busy} />
          ))}
        </div>
      )}
    </Card>
  )
}

function TaskRow({
  task,
  onGo,
  onReviewSource,
  onDismiss,
  onSnooze,
  busy,
}: {
  task: MySpaceTask
  onGo: (task: MySpaceTask) => void
  onReviewSource: (task: MySpaceTask, route: string) => void
  onDismiss: (task: MySpaceTask) => void
  onSnooze: (task: MySpaceTask) => void
  busy: boolean
}) {
  const due = formatDate(task.due_at)
  const blockerLine = [task.blocker, task.missing_field].filter(Boolean).join(' · ')
  return (
    <div className="flex items-start gap-3 py-3" data-task-key={task.key}>
      <div className="min-w-0 flex-1">
        <button
          type="button"
          onClick={() => onGo(task)}
          aria-label={`${task.cta_label}: ${task.title}`}
          className="w-full text-left focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2"
        >
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-sm font-medium text-foreground">{task.title}</span>
            <Badge variant={urgencyTone[task.urgency]}>{urgencyLabel[task.urgency]}</Badge>
          </div>
          <p className="mt-1 text-xs text-muted-foreground">{task.description}</p>
          {blockerLine && <p className="mt-1 text-xs text-foreground">{blockerLine}</p>}
          <p className="mt-1 text-xs text-muted-foreground">
            {ownerLabel(task.owner)}{due ? ` · due ${due}` : ''} · {sourceLine(task)}
          </p>
        </button>
        <EvidenceDisclosure item={task} onReviewSource={(route) => onReviewSource(task, route)} />
      </div>
      {task.dismissible && (
        <div className="flex shrink-0 gap-1">
          <button type="button" disabled={busy} onClick={() => onSnooze(task)} aria-label={`Snooze ${task.title}`} className="ui-btn rounded border border-border px-2 py-1 text-xs hover:bg-muted disabled:opacity-50">Snooze</button>
          <button type="button" disabled={busy} onClick={() => onDismiss(task)} aria-label={`Dismiss ${task.title}`} className="ui-btn rounded border border-border px-2 py-1 text-xs hover:bg-muted disabled:opacity-50">Dismiss</button>
        </div>
      )}
    </div>
  )
}

function hiddenReason(task: MySpaceTask) {
  if (task.dismissed) return 'Dismissed'
  if (task.snoozed_until) {
    const until = formatDate(task.snoozed_until)
    return until ? `Snoozed until ${until}` : 'Snoozed'
  }
  return 'Hidden'
}

function HiddenTasksPanel({
  tasks,
  onRestore,
  busy,
}: {
  tasks: MySpaceTask[]
  onRestore: (task: MySpaceTask) => void
  busy: boolean
}) {
  if (tasks.length === 0) return null

  return (
    <details className="rounded-lg border border-border bg-card px-4 py-3">
      <summary className="cursor-pointer list-none text-sm font-medium text-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2">
        Hidden tasks <span className="ml-1 text-xs font-normal text-muted-foreground">({tasks.length})</span>
      </summary>
      <div className="mt-3 divide-y divide-border">
        {tasks.map(task => (
          <div key={task.key} className="flex items-start justify-between gap-3 py-3">
            <div className="min-w-0">
              <div className="flex flex-wrap items-center gap-2">
                <p className="text-sm font-medium text-foreground">{task.title}</p>
                <Badge variant="neutral">{hiddenReason(task)}</Badge>
              </div>
              <p className="mt-1 text-xs text-muted-foreground">{task.description}</p>
              <p className="mt-1 text-xs text-muted-foreground">{sourceLine(task)}</p>
            </div>
            <button
              type="button"
              disabled={busy}
              onClick={() => onRestore(task)}
              aria-label={`Restore ${task.title}`}
              className="ui-btn inline-flex shrink-0 items-center gap-1.5 rounded-md border border-border px-3 py-1.5 text-xs font-medium text-foreground hover:bg-muted disabled:opacity-50"
            >
              <RotateCcw size={12} /> Restore
            </button>
          </div>
        ))}
      </div>
    </details>
  )
}

function ItemModule({
  title,
  items,
  icon,
  emptyTitle,
  emptyText,
  emptyRoute,
  emptyCtaLabel,
  onGo,
  onReviewSource,
  onEmpty,
}: {
  title: string
  items: MySpaceModuleItem[]
  icon: React.ReactNode
  emptyTitle: string
  emptyText: string
  emptyRoute: string
  emptyCtaLabel: string
  onGo: (item: MySpaceModuleItem) => void
  onReviewSource: (item: MySpaceModuleItem, route: string) => void
  onEmpty: () => void
}) {
  return (
    <Card pad={false} className="p-5">
      <SectionHeader count={items.length}>{title}</SectionHeader>
      {items.length === 0 ? (
        <EmptyAction title={emptyTitle} text={emptyText} route={emptyRoute} ctaLabel={emptyCtaLabel} onClick={onEmpty} />
      ) : (
        <div className="divide-y divide-border">
          {items.slice(0, 5).map(item => (
            <div
              key={item.key}
              className="flex w-full items-start gap-3 py-3"
            >
              <span className="mt-0.5 shrink-0 text-muted-foreground">{icon}</span>
              <div className="min-w-0 flex-1">
                <button
                  type="button"
                  onClick={() => onGo(item)}
                  className="w-full rounded-sm text-left hover:bg-muted/50 focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2"
                >
                  <span className="block text-sm font-medium text-foreground">{item.title}</span>
                  <span className="mt-1 block text-xs text-muted-foreground">{item.description}</span>
                  <span className="mt-1 block text-xs text-muted-foreground">
                    {ownerLabel(item.owner)}{formatDate(item.due_at) ? ` · ${formatDate(item.due_at)}` : ''} · {sourceLine(item)}
                  </span>
                </button>
                <EvidenceDisclosure item={item} onReviewSource={(route) => onReviewSource(item, route)} />
              </div>
              {item.status && <Badge variant={urgencyTone[item.urgency]}>{item.status.split('_').join(' ')}</Badge>}
            </div>
          ))}
        </div>
      )}
    </Card>
  )
}

function EmptyAction({
  title,
  text,
  route,
  ctaLabel,
  onClick,
}: {
  title: string
  text: string
  route: string
  ctaLabel: string
  onClick: () => void
}) {
  return (
    <div className="rounded-md border border-dashed border-border px-3 py-4">
      <p className="text-sm font-medium text-foreground">{title}</p>
      <p className="mt-1 text-xs text-muted-foreground">{text}</p>
      <button
        type="button"
        onClick={onClick}
        aria-label={`${ctaLabel}: ${title}`}
        className="ui-btn mt-3 inline-flex items-center gap-1.5 rounded-md border border-border px-3 py-1.5 text-xs font-medium hover:bg-muted"
      >
        {ctaLabel} <span className="sr-only">{route}</span><ArrowRight size={12} />
      </button>
    </div>
  )
}

function StrategyCard({
  strategy,
  onGo,
  onReviewSource,
}: {
  strategy: MySpaceModuleItem | null
  onGo: (route: string) => void
  onReviewSource: (item: MySpaceModuleItem, route: string) => void
}) {
  return (
    <Card pad={false} className="p-5">
      <SectionHeader>Strategy living doc</SectionHeader>
      {strategy ? (
        <div>
          <p className="text-sm font-medium text-foreground">{strategy.title}</p>
          <p className="mt-1 text-xs text-muted-foreground">{strategy.description}</p>
          <p className="mt-2 text-xs text-muted-foreground">{sourceLine(strategy)}</p>
          <EvidenceDisclosure item={strategy} onReviewSource={(route) => onReviewSource(strategy, route)} />
          <button
            type="button"
            onClick={() => onGo(strategy.route)}
            className="ui-btn mt-3 inline-flex items-center gap-1.5 rounded-md border border-border px-3 py-1.5 text-xs font-medium hover:bg-muted"
          >
            Refine strategy <ArrowRight size={12} />
          </button>
        </div>
      ) : (
        <EmptyAction
          title="No active strategy yet."
          text="Create the career, degree, academic, financial, and geographic plan before applications branch too far."
          route="/s/profile?tab=strategy"
          ctaLabel="Create strategy"
          onClick={() => onGo('/s/profile?tab=strategy')}
        />
      )}
    </Card>
  )
}

function EvidenceDisclosure({
  item,
  onReviewSource,
}: {
  item: { provenance?: MySpaceProvenance[] }
  onReviewSource: (route: string) => void
}) {
  const source = primarySource(item)
  if (!source) {
    return (
      <p className="mt-2 text-xs text-muted-foreground">Why this appears: Uni could not attach a source yet.</p>
    )
  }
  return (
    <details className="mt-2 text-xs text-muted-foreground">
      <summary className="inline-flex cursor-pointer list-none rounded-sm font-medium text-foreground underline underline-offset-2 focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2">
        Why this appears
      </summary>
      <div className="mt-2 rounded-md border border-border bg-muted/30 p-3">
        <p>{sourceLine(item)}</p>
        <p className="mt-1">
          This row comes from the owning UniPaith module. Use the source record to correct the underlying data instead of dismissing the signal.
        </p>
        {source.href && (
          <button
            type="button"
            onClick={() => onReviewSource(source.href as string)}
            className="ui-btn mt-2 inline-flex items-center gap-1.5 rounded-md border border-border px-2.5 py-1.5 text-xs font-medium text-foreground hover:bg-background"
          >
            Review source <ArrowRight size={12} />
          </button>
        )}
      </div>
    </details>
  )
}

function PrepCard({ readiness, onGo }: { readiness: MySpaceReadiness[]; onGo: (row: MySpaceReadiness) => void }) {
  return (
    <Card pad={false} className="p-5">
      <SectionHeader>Prep readiness</SectionHeader>
      <div className="space-y-3">
        {readiness.map(row => (
          <button
            key={row.key}
            type="button"
            onClick={() => onGo(row)}
            aria-label={`Open ${row.label}`}
            className="w-full rounded-md py-2 text-left hover:bg-muted/50 focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2"
          >
            <div className="flex items-center justify-between gap-3">
              <span className="text-sm font-medium text-foreground">{row.label}</span>
              <Badge variant={readinessTone(row.status)}>{row.pct ?? 0}%</Badge>
            </div>
            <p className="mt-1 text-xs text-muted-foreground">{row.detail}</p>
          </button>
        ))}
      </div>
    </Card>
  )
}
