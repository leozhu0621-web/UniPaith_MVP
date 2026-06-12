import { useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import {
  ArrowLeftRight,
  ArrowRight,
  Bell,
  BookMarked,
  CircleCheck,
  Clock,
  ListChecks,
  Mailbox,
  Network,
  Radio,
  Send,
  Settings2,
  ShieldCheck,
  SlidersHorizontal,
  Sparkles,
  Waypoints,
  Zap,
} from 'lucide-react'

import { getRealtimeBuild } from '../../api/build'
import { qk } from '../../api/queryKeys'
import type {
  ReadinessStatus,
  RealtimeAcceptanceItem,
  RealtimeBuildTask,
  RealtimeCapability,
  RealtimeCatalogEntry,
  RealtimeConfigKnob,
} from '../../types/build'
import Button from '../../components/ui/Button'
import Card from '../../components/ui/Card'
import usePageTitle from '../../hooks/usePageTitle'
import {
  CardSkeleton,
  CardTitle,
  Chip,
  ErrorState,
  FilterRow,
  GoalShell,
  Hero,
  SectionHeading,
  Stat,
  StatBand,
  StatSkeleton,
} from './goalUi'

// Spec 57 — the realtime & notifications system, read from GET /api/v1/build/realtime.
// Each capability (SSE stream, WebSocket messaging, the pub/sub broker, the typed
// event catalog, multi-channel delivery, preferences, the notification center,
// digest batching, delivery reliability) is honestly classified live·partial·planned;
// the transport-route counts are resolved from the running route table, the catalog
// event-type count from the live registry, the broker backend from the running broker,
// and the realtime / digest / delivery / web-push flags off the running settings — so
// the page can't claim a transport the deployed app doesn't serve.

const THE_BAR =
  'Realtime is good when a decision, a message, or a deadline reaches the student the ' +
  'moment it happens — the bell counts up live, the message thread shows typing and read ' +
  'receipts, and the same event reaches every open tab and device — while low-urgency ' +
  'noise batches into a digest and nothing is ever silently dropped.'

const STATUS_TONE: Record<ReadinessStatus, 'success' | 'cobalt' | 'neutral'> = {
  live: 'success',
  partial: 'cobalt',
  planned: 'neutral',
}
const STATUS_LABEL: Record<ReadinessStatus, string> = {
  live: 'Live',
  partial: 'In progress',
  planned: 'Planned',
}
const STATUS_ORDER: ReadinessStatus[] = ['live', 'partial', 'planned']

const CAPABILITY_ICONS: Record<string, typeof Bell> = {
  sse: Radio,
  ws: ArrowLeftRight,
  broker: Waypoints,
  catalog: BookMarked,
  channels: Send,
  preferences: SlidersHorizontal,
  center: Bell,
  digest: Mailbox,
  reliability: ShieldCheck,
}

function StatusChip({ status }: { status: ReadinessStatus }) {
  return <Chip tone={STATUS_TONE[status]}>{STATUS_LABEL[status]}</Chip>
}

function CapabilityCard({ capability }: { capability: RealtimeCapability }) {
  const Icon = CAPABILITY_ICONS[capability.key] ?? Bell
  return (
    <Card pad={false} className="flex h-full flex-col gap-3 p-5">
      <div className="flex items-start justify-between gap-3">
        <CardTitle icon={Icon} className="leading-snug">
          {capability.title}
        </CardTitle>
        <StatusChip status={capability.status} />
      </div>

      <div className="flex flex-wrap items-center gap-1.5">
        <Chip tone="neutral">Spec 57 {capability.section}</Chip>
      </div>
      <p className="text-sm text-muted-foreground">{capability.blurb}</p>

      <div className="space-y-1.5">
        <p className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">
          Live today
        </p>
        <ul className="space-y-1.5">
          {capability.built.map((item) => (
            <li key={item} className="flex gap-2 text-sm text-foreground">
              <CircleCheck size={15} className="mt-0.5 shrink-0 text-success dark:text-success-dark" />
              <span>{item}</span>
            </li>
          ))}
        </ul>
      </div>

      {capability.planned.length > 0 && (
        <div className="mt-auto space-y-1.5 pt-1">
          <p className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">
            Planned
          </p>
          <ul className="space-y-1.5">
            {capability.planned.map((item) => (
              <li key={item} className="flex gap-2 text-sm text-muted-foreground">
                <Clock size={14} className="mt-0.5 shrink-0" />
                <span>{item}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </Card>
  )
}

function KnobValue({ value }: { value: string | number | boolean }) {
  if (typeof value === 'boolean') {
    return <Chip tone={value ? 'success' : 'neutral'}>{value ? 'on' : 'off'}</Chip>
  }
  return <span className="font-mono text-[13px] text-foreground">{String(value)}</span>
}

function KnobRow({ knob }: { knob: RealtimeConfigKnob }) {
  return (
    <div className="flex items-center justify-between gap-3 py-1.5">
      <dt className="flex items-center gap-2">
        <span className="font-mono text-[12px] text-muted-foreground">{knob.name}</span>
        <Chip tone="neutral">{knob.section}</Chip>
      </dt>
      <dd>
        <KnobValue value={knob.value} />
      </dd>
    </div>
  )
}

function TaskRow({ task }: { task: RealtimeBuildTask }) {
  return (
    <li className="flex flex-col gap-1 py-3 sm:flex-row sm:items-start sm:gap-3">
      <div className="flex shrink-0 items-center gap-2 sm:w-36">
        <StatusChip status={task.status} />
        <span className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">
          {task.section}
        </span>
      </div>
      <div>
        <p className="text-sm text-foreground">{task.text}</p>
        <p className="mt-0.5 text-[12px] text-muted-foreground">{task.evidence}</p>
      </div>
    </li>
  )
}

function AcceptanceRow({ item }: { item: RealtimeAcceptanceItem }) {
  return (
    <li className="flex items-start gap-3 py-3">
      <StatusChip status={item.status} />
      <span className="text-sm text-foreground">{item.text}</span>
    </li>
  )
}

function RouteList({
  icon: Icon,
  title,
  routes,
}: {
  icon: typeof Bell
  title: string
  routes: string[] | undefined
}) {
  return (
    <Card pad={false} className="flex flex-col gap-3 p-5">
      <h3 className="inline-flex items-center gap-2 text-h3 text-foreground">
        <Icon size={18} className="text-secondary" />
        {title}
        {routes && <Chip tone="cobalt">{routes.length}</Chip>}
      </h3>
      <ul className="space-y-1.5">
        {(routes ?? []).map((p) => (
          <li key={p} className="flex items-start gap-2 font-mono text-[12px] text-foreground">
            <CircleCheck size={13} className="mt-0.5 shrink-0 text-success dark:text-success-dark" />
            <span className="break-all">{p}</span>
          </li>
        ))}
        {!routes && [0, 1].map((i) => <li key={i} className="h-4 w-2/3 animate-pulse rounded bg-muted" />)}
      </ul>
    </Card>
  )
}

function CatalogEntry({ entry }: { entry: RealtimeCatalogEntry }) {
  return (
    <div className="flex items-center justify-between gap-2 py-1.5">
      <span className="truncate font-mono text-[12px] text-foreground">{entry.event_type}</span>
      <div className="flex shrink-0 items-center gap-1.5">
        <Chip tone={entry.urgency === 'urgent' ? 'cobalt' : 'neutral'}>{entry.urgency}</Chip>
        {!entry.silenceable && <Chip tone="warning">essential</Chip>}
      </div>
    </div>
  )
}

export default function RealtimeNotificationsPage() {
  usePageTitle('Realtime & notifications · Spec 57')
  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: qk.buildRealtime(),
    queryFn: getRealtimeBuild,
    staleTime: 5 * 60_000,
  })

  const [status, setStatus] = useState<string>('all')

  const capabilities = useMemo(() => {
    const list = data?.capabilities ?? []
    return status === 'all' ? list : list.filter((c) => c.status === status)
  }, [data, status])

  const statusFilters = useMemo(() => {
    const present = new Set((data?.capabilities ?? []).map((c) => c.status))
    const ordered = STATUS_ORDER.filter((s) => present.has(s))
    return [{ key: 'all', label: 'All' }, ...ordered.map((s) => ({ key: s, label: STATUS_LABEL[s] }))]
  }, [data])

  return (
    <GoalShell>
      <Hero
        eyebrow="Realtime & notifications · Spec 57"
        title="Live the moment it happens — in the open."
        lede={THE_BAR}
      >
        {data && (
          <span className="inline-flex items-center gap-1.5 rounded-pill border border-primary/40 px-3 py-1 text-[13px] font-semibold text-foreground">
            <span className="h-1.5 w-1.5 rounded-full bg-primary" aria-hidden />
            {data.summary.event_type_count} notification events · broker{' '}
            {data.summary.broker_backend}
          </span>
        )}
        <a
          href="#capabilities"
          className="inline-flex items-center gap-1 text-[13px] font-semibold text-secondary hover:underline"
        >
          Jump to the capabilities <ArrowRight size={14} />
        </a>
      </Hero>

      {/* Headline stats — read live from the running backend */}
      <StatBand isError={isError}>
        {isLoading || !data ? (
          [0, 1, 2, 3].map((i) => <StatSkeleton key={i} />)
        ) : (
          <>
            <Stat
              value={`${data.summary.capabilities_live}/${data.summary.capability_count}`}
              label="Capabilities fully live"
            />
            <Stat
              value={
                <span className="inline-flex items-center gap-1.5">
                  <Radio className="text-secondary" size={24} />
                  {data.summary.sse_route_count}
                </span>
              }
              label="SSE stream endpoints"
            />
            <Stat
              value={
                <span className="inline-flex items-center gap-1.5">
                  <ArrowLeftRight className="text-secondary" size={22} />
                  {data.summary.ws_route_count}
                </span>
              }
              label="WebSocket endpoints"
            />
            <Stat
              value={
                <span className="inline-flex items-center gap-1.5">
                  <Bell className="text-secondary" size={22} />
                  {data.summary.event_type_count}
                </span>
              }
              label="Catalogued events"
            />
          </>
        )}
      </StatBand>

      {/* §2–§6 — the capabilities */}
      <section id="capabilities" className="mt-16 scroll-mt-20">
        <SectionHeading
          icon={Zap}
          title="Nine realtime capabilities"
          sub="Each capability is honestly classified — live, in progress, or planned. The transport routes, the event catalog, the broker backend and the config flags behind them are read straight from the running app, so the status is evidence, not a claim."
        />

        <div className="mt-6">
          <FilterRow options={statusFilters} value={status} onChange={setStatus} />
        </div>

        {isError ? (
          <ErrorState
            onRetry={() => refetch()}
            label="We couldn't load the realtime & notifications system just now."
          />
        ) : (
          <>
            {data && (
              <p className="mt-5 text-sm text-muted-foreground">
                Showing {capabilities.length} of {data.summary.capability_count} capabilities ·{' '}
                {data.summary.capabilities_live} live · {data.summary.capabilities_partial} in
                progress · {data.summary.capabilities_planned} planned
              </p>
            )}
            <div className="mt-3 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {data
                ? capabilities.map((c) => <CapabilityCard key={c.key} capability={c} />)
                : [0, 1, 2, 3, 4, 5].map((i) => <CardSkeleton key={i} className="h-72" />)}
            </div>
            {data && capabilities.length === 0 && (
              <p className="mt-6 text-center text-muted-foreground">
                No capabilities match this filter.
              </p>
            )}
          </>
        )}
      </section>

      {/* Transport — the self-verifying proof, read from the route table */}
      <section className="mt-16">
        <SectionHeading
          icon={Network}
          title="Backed by live transport routes"
          sub="Resolved straight from the running route table — the page can only list a transport the deployed app actually serves."
        />
        <div className="mt-6 grid gap-4 lg:grid-cols-3">
          <RouteList icon={Radio} title="SSE stream" routes={data?.routes.sse} />
          <RouteList icon={ArrowLeftRight} title="WebSocket" routes={data?.routes.ws} />
          <RouteList icon={Bell} title="Notification center" routes={data?.routes.notifications} />
        </div>
      </section>

      {/* Event catalog — the typed registry behind every notification */}
      <section className="mt-16">
        <SectionHeading
          icon={BookMarked}
          title="The event catalog"
          sub="One registry maps every event type to its preference category, urgency and whether it can be fully silenced. Transactional events (decision · interview · deadline) are marked essential — down-ranked but never silenced (§4)."
        />
        <Card pad={false} className="mt-6 p-5">
          <div className="grid gap-x-8 sm:grid-cols-2">
            {data
              ? data.catalog.map((e) => <CatalogEntry key={e.event_type} entry={e} />)
              : [0, 1, 2, 3, 4, 5].map((i) => (
                  <div key={i} className="py-2">
                    <div className="h-4 w-1/2 animate-pulse rounded bg-muted" />
                  </div>
                ))}
          </div>
        </Card>
      </section>

      {/* Live configuration — read off the running settings */}
      <section className="mt-16">
        <SectionHeading
          icon={Settings2}
          title="Live configuration"
          sub="The deployed values, read straight off the running settings — the realtime + heartbeat knobs, the digest cadence, the delivery retry budget and the web-push fast-follow flag."
        />
        <Card pad={false} className="mt-6 p-5">
          <dl className="divide-y divide-border">
            {data
              ? data.config_knobs.map((k) => <KnobRow key={k.name} knob={k} />)
              : [0, 1, 2, 3].map((i) => (
                  <div key={i} className="py-2">
                    <div className="h-4 w-1/2 animate-pulse rounded bg-muted" />
                  </div>
                ))}
          </dl>
        </Card>
      </section>

      {/* §7 — build-task checklist */}
      <section className="mt-16">
        <SectionHeading
          icon={ListChecks}
          title="Build-task checklist"
          sub="Spec 57 §7 — each task classified by what's shipped versus what's next. The cross-task Redis fan-out, web-push and the durable queue worker are named as the planned halves, not hidden."
        />
        <Card pad={false} className="mt-6 p-2 sm:p-5">
          <ul className="divide-y divide-border">
            {(data?.build_tasks ?? []).map((t) => (
              <TaskRow key={`${t.section}-${t.text}`} task={t} />
            ))}
            {!data &&
              [0, 1, 2, 3, 4].map((i) => (
                <li key={i} className="py-3">
                  <div className="h-5 w-3/4 animate-pulse rounded bg-muted" />
                </li>
              ))}
          </ul>
        </Card>
      </section>

      {/* §8 — acceptance */}
      <section className="mt-16">
        <SectionHeading
          icon={CircleCheck}
          title="Acceptance"
          sub="Spec 57 §8 — the definition of done, held to the same honest live/in-progress/planned bar."
        />
        <Card pad={false} className="mt-6 p-2 sm:p-5">
          <ul className="divide-y divide-border">
            {(data?.acceptance ?? []).map((a) => (
              <AcceptanceRow key={a.text} item={a} />
            ))}
            {!data &&
              [0, 1, 2].map((i) => (
                <li key={i} className="py-3">
                  <div className="h-5 w-2/3 animate-pulse rounded bg-muted" />
                </li>
              ))}
          </ul>
        </Card>
      </section>

      {/* §9 — open questions */}
      {data && data.open_questions.length > 0 && (
        <section className="mt-16">
          <SectionHeading
            icon={Sparkles}
            title="Open questions"
            sub="The deliberate calls behind the realtime layer — spec 57 §9."
          />
          <div className="mt-6 grid gap-4 sm:grid-cols-3">
            {data.open_questions.map((q) => (
              <Card pad={false} key={q.q} className="flex h-full flex-col gap-2 p-5">
                <h3 className="text-h3 text-foreground">{q.q}</h3>
                <p className="text-sm text-muted-foreground">{q.a}</p>
              </Card>
            ))}
          </div>
        </section>
      )}

      {/* Closing — the page practices what it documents */}
      <section className="mt-16 rounded-xl border border-border bg-card p-8 text-center">
        <p className="inline-flex items-center justify-center gap-2 text-h2 text-foreground">
          <Zap className="text-secondary" size={24} />
          Honest about what's live, and what's next.
        </p>
        <p className="mx-auto mt-2 max-w-xl text-muted-foreground">
          The capability statuses, transport-route counts, event catalog and config flags above are
          read straight from the running backend — never asserted in a doc. The SSE bell, WebSocket
          messaging, the catalog and the digest are live; cross-task Redis fan-out and web push are
          named as planned.
        </p>
        <div className="mt-5 flex flex-wrap items-center justify-center gap-3">
          <Link to="/goal">
            <Button size="lg" variant="secondary">
              Back to the build hub
            </Button>
          </Link>
          <Link to="/goal/search">
            <Button size="lg" variant="tertiary">
              See the discovery substrate
            </Button>
          </Link>
        </div>
      </section>
    </GoalShell>
  )
}
