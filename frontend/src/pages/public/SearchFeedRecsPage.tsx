import { useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import {
  ArrowRight,
  Bell,
  CircleCheck,
  Clock,
  FlaskConical,
  Layers,
  ListChecks,
  Network,
  Rss,
  Search,
  Settings2,
  SlidersHorizontal,
  Sparkles,
  Telescope,
  Wand2,
} from 'lucide-react'

import { getSearchBuild } from '../../api/build'
import type {
  ReadinessStatus,
  SearchAcceptanceItem,
  SearchBuildTask,
  SearchCapability,
  SearchConfigKnob,
} from '../../types/build'
import Button from '../../components/ui/Button'
import Card from '../../components/ui/Card'
import usePageTitle from '../../hooks/usePageTitle'
import {
  CardSkeleton,
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

// Spec 56 — the search / feed / recommendations substrate, read from
// GET /api/v1/build/search. Each capability (full-text search, NL query, facets,
// hybrid fusion, the Connect feed, recommendations, saved-search alerts, A/B) is
// honestly classified live·partial·planned; the backing-route counts are resolved
// from the running route table, the saved-searches table presence is read from the
// live SQLAlchemy metadata, and the interpreter / connect-ranker flags plus the new
// alert caps are read off the running settings — so the page can't claim a surface
// the deployed app doesn't serve. Built to the bar it documents: skeletons (never a
// blank flash), motion on the design-system tokens, keyboard-accessible filters.

// §1 — the bar. Static spec text so the lede never flashes empty.
const THE_BAR =
  'Discovery is good when a student can describe what they want in their own words and ' +
  'get back relevant programs, refine with live filters, follow institutions and see what ' +
  'changed, and save a search that keeps watching for them — with every ranking explainable ' +
  'and fairness-gated.'

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

const CAPABILITY_ICONS: Record<string, typeof Search> = {
  fts: Search,
  nl_interpret: Sparkles,
  facets: SlidersHorizontal,
  hybrid: Layers,
  feed: Rss,
  recs: Wand2,
  saved_search: Bell,
  experimentation: FlaskConical,
}

function StatusChip({ status }: { status: ReadinessStatus }) {
  return <Chip tone={STATUS_TONE[status]}>{STATUS_LABEL[status]}</Chip>
}

function CapabilityCard({ capability }: { capability: SearchCapability }) {
  const Icon = CAPABILITY_ICONS[capability.key] ?? Search
  return (
    <Card className="flex h-full flex-col gap-3 p-5">
      <div className="flex items-start justify-between gap-3">
        <span className="inline-flex items-center gap-2 text-h3 leading-snug text-foreground">
          <Icon size={18} className="shrink-0 text-secondary" />
          {capability.title}
        </span>
        <StatusChip status={capability.status} />
      </div>

      <div className="flex flex-wrap items-center gap-1.5">
        <Chip tone="neutral">Spec 56 {capability.section}</Chip>
      </div>
      <p className="text-sm text-muted-foreground">{capability.blurb}</p>

      <div className="space-y-1.5">
        <p className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">
          Live today
        </p>
        <ul className="space-y-1.5">
          {capability.built.map(item => (
            <li key={item} className="flex gap-2 text-sm text-foreground">
              <CircleCheck
                size={15}
                className="mt-0.5 shrink-0 text-success dark:text-success-dark"
              />
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
            {capability.planned.map(item => (
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

function KnobRow({ knob }: { knob: SearchConfigKnob }) {
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

function TaskRow({ task }: { task: SearchBuildTask }) {
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

function AcceptanceRow({ item }: { item: SearchAcceptanceItem }) {
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
  icon: typeof Search
  title: string
  routes: string[] | undefined
}) {
  return (
    <Card className="flex flex-col gap-3 p-5">
      <h3 className="inline-flex items-center gap-2 text-h3 text-foreground">
        <Icon size={18} className="text-secondary" />
        {title}
        {routes && <Chip tone="cobalt">{routes.length}</Chip>}
      </h3>
      <ul className="space-y-1.5">
        {(routes ?? []).map(p => (
          <li key={p} className="flex items-start gap-2 font-mono text-[12px] text-foreground">
            <CircleCheck size={13} className="mt-0.5 shrink-0 text-success dark:text-success-dark" />
            <span className="break-all">{p}</span>
          </li>
        ))}
        {!routes && [0, 1, 2].map(i => <li key={i} className="h-4 w-2/3 animate-pulse rounded bg-muted" />)}
      </ul>
    </Card>
  )
}

export default function SearchFeedRecsPage() {
  usePageTitle('Search, feed & recommendations · Spec 56')
  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ['build-search'],
    queryFn: getSearchBuild,
    staleTime: 5 * 60_000,
  })

  const [status, setStatus] = useState<string>('all')

  const capabilities = useMemo(() => {
    const list = data?.capabilities ?? []
    return status === 'all' ? list : list.filter(c => c.status === status)
  }, [data, status])

  const statusFilters = useMemo(() => {
    const present = new Set((data?.capabilities ?? []).map(c => c.status))
    const ordered = STATUS_ORDER.filter(s => present.has(s))
    return [{ key: 'all', label: 'All' }, ...ordered.map(s => ({ key: s, label: STATUS_LABEL[s] }))]
  }, [data])

  return (
    <GoalShell>
      <Hero
        eyebrow="Search, feed & recommendations · Spec 56"
        title="The discovery substrate, in the open."
        lede={THE_BAR}
      >
        {data && (
          <span className="inline-flex items-center gap-1.5 rounded-pill border border-primary/40 px-3 py-1 text-[13px] font-semibold text-foreground">
            <span className="h-1.5 w-1.5 rounded-full bg-primary" aria-hidden />
            Saved-search alerts {data.summary.saved_searches_table_present ? 'wired' : 'pending'} ·{' '}
            {data.summary.saved_search_route_count} live endpoints
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
      <StatBand>
        {isLoading || !data ? (
          [0, 1, 2, 3].map(i => <StatSkeleton key={i} />)
        ) : (
          <>
            <Stat
              value={`${data.summary.capabilities_live}/${data.summary.capability_count}`}
              label="Capabilities fully live"
            />
            <Stat
              value={
                <span className="inline-flex items-center gap-1.5">
                  <Search className="text-secondary" size={24} />
                  {data.summary.search_route_count}
                </span>
              }
              label="Search endpoints (live routes)"
            />
            <Stat
              value={
                <span className="inline-flex items-center gap-1.5">
                  <Rss className="text-secondary" size={22} />
                  {data.summary.feed_route_count}
                </span>
              }
              label="Connect feed endpoints"
            />
            <Stat
              value={
                <span className="inline-flex items-center gap-1.5">
                  <Bell className="text-secondary" size={22} />
                  {data.summary.saved_search_route_count}
                </span>
              }
              label="Saved-search endpoints"
            />
          </>
        )}
      </StatBand>

      {/* §2–§7 — the capabilities */}
      <section id="capabilities" className="mt-16 scroll-mt-20">
        <SectionHeading
          icon={Telescope}
          title="Eight discovery capabilities"
          sub="Each capability is honestly classified — live, in progress, or planned. The routes, config flags and saved-searches table behind them are read straight from the running app, so the status is evidence, not a claim."
        />

        <div className="mt-6">
          <FilterRow options={statusFilters} value={status} onChange={setStatus} />
        </div>

        {isError ? (
          <ErrorState
            onRetry={() => refetch()}
            label="We couldn't load the search & feed substrate just now."
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
                ? capabilities.map(c => <CapabilityCard key={c.key} capability={c} />)
                : [0, 1, 2, 3, 4, 5].map(i => <CardSkeleton key={i} className="h-72" />)}
            </div>
            {data && capabilities.length === 0 && (
              <p className="mt-6 text-center text-muted-foreground">
                No capabilities match this filter.
              </p>
            )}
          </>
        )}
      </section>

      {/* Backing routes — the self-verifying proof, read from the route table */}
      <section className="mt-16">
        <SectionHeading
          icon={Network}
          title="Backed by live routes"
          sub="Resolved straight from the running route table — the page can only list a surface the deployed app actually serves."
        />
        <div className="mt-6 grid gap-4 lg:grid-cols-3">
          <RouteList icon={Search} title="Search & compare" routes={data?.routes.search} />
          <RouteList icon={Rss} title="Connect feed" routes={data?.routes.feed} />
          <RouteList icon={Bell} title="Saved searches" routes={data?.routes.saved_search} />
        </div>
      </section>

      {/* Live configuration — read off the running settings */}
      <section className="mt-16">
        <SectionHeading
          icon={Settings2}
          title="Live configuration"
          sub="The deployed values, read straight off the running settings — the NL-interpreter and connect-ranker flags, and the saved-search alert caps."
        />
        <Card className="mt-6 p-5">
          <dl className="divide-y divide-border">
            {data
              ? data.config_knobs.map(k => <KnobRow key={k.name} knob={k} />)
              : [0, 1, 2, 3].map(i => (
                  <div key={i} className="py-2">
                    <div className="h-4 w-1/2 animate-pulse rounded bg-muted" />
                  </div>
                ))}
          </dl>
        </Card>
      </section>

      {/* §8 — build-task checklist */}
      <section className="mt-16">
        <SectionHeading
          icon={ListChecks}
          title="Build-task checklist"
          sub="Spec 56 §8 — each task classified by what's shipped versus what's next. The embedding-dependent halves (pgvector fusion, Qwen3-Reranker, the A/B harness) are named as planned, not hidden."
        />
        <Card className="mt-6 p-2 sm:p-5">
          <ul className="divide-y divide-border">
            {(data?.build_tasks ?? []).map(t => (
              <TaskRow key={`${t.section}-${t.text}`} task={t} />
            ))}
            {!data &&
              [0, 1, 2, 3, 4].map(i => (
                <li key={i} className="py-3">
                  <div className="h-5 w-3/4 animate-pulse rounded bg-muted" />
                </li>
              ))}
          </ul>
        </Card>
      </section>

      {/* §9 — acceptance */}
      <section className="mt-16">
        <SectionHeading
          icon={CircleCheck}
          title="Acceptance"
          sub="Spec 56 §9 — the definition of done, with each criterion held to the same honest live/in-progress/planned bar."
        />
        <Card className="mt-6 p-2 sm:p-5">
          <ul className="divide-y divide-border">
            {(data?.acceptance ?? []).map(a => (
              <AcceptanceRow key={a.text} item={a} />
            ))}
            {!data &&
              [0, 1, 2].map(i => (
                <li key={i} className="py-3">
                  <div className="h-5 w-2/3 animate-pulse rounded bg-muted" />
                </li>
              ))}
          </ul>
        </Card>
      </section>

      {/* §10 — open questions */}
      {data && data.open_questions.length > 0 && (
        <section className="mt-16">
          <SectionHeading
            icon={Sparkles}
            title="Open questions"
            sub="The deliberate calls behind the substrate — spec 56 §10."
          />
          <div className="mt-6 grid gap-4 sm:grid-cols-3">
            {data.open_questions.map(q => (
              <Card key={q.q} className="flex h-full flex-col gap-2 p-5">
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
          <Telescope className="text-secondary" size={24} />
          Honest about what's live, and what's next.
        </p>
        <p className="mx-auto mt-2 max-w-xl text-muted-foreground">
          The capability statuses, route counts and config flags above are read straight from the
          running backend — never asserted in a doc. Saved-search alerts are the net-new build;
          hybrid semantic fusion and the A/B harness are named as planned.
        </p>
        <div className="mt-5 flex flex-wrap items-center justify-center gap-3">
          <Link to="/goal">
            <Button size="lg" variant="secondary">
              Back to the build hub
            </Button>
          </Link>
          <Link to="/goal/backend">
            <Button size="lg" variant="tertiary">
              See the backend posture
            </Button>
          </Link>
        </div>
      </section>
    </GoalShell>
  )
}
