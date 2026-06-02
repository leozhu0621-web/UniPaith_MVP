import { useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import {
  Activity,
  ArrowRight,
  CircleCheck,
  Clock,
  Cpu,
  Database,
  Gauge,
  HeartPulse,
  ListChecks,
  Network,
  Server,
  Settings2,
  ShieldCheck,
  Workflow,
} from 'lucide-react'

import { getProduction } from '../../api/build'
import type { ConfigGroup, ProductionBuildTask, ProductionPillar, ReadinessStatus } from '../../types/build'
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

// Spec 55 — the backend production-readiness surface, read from
// GET /api/v1/build/production. Each pillar (observability / cache / queue /
// rate-limit / resilience / database / health) is honestly classified
// live·partial·planned; the config knobs, middleware count, health-probe routes
// and read-cache hit-rate are introspected from the running app, so the page
// mirrors the deployed backend and can't claim what isn't wired. The page is
// itself built to the bar it documents: skeletons (never a blank flash), motion
// on the design-system tokens, and keyboard-accessible filters.

// §1 — the bar. Static spec text so the lede never flashes empty.
const THE_BAR =
  'A backend is production-grade when it stays up, stays honest, and stays fast under ' +
  'load: structured logs and health probes you can act on, a version-keyed read cache, ' +
  'graceful degradation instead of 5xxes, a pooled database, and migrations that run ' +
  'before the new version serves.'

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

const PILLAR_ICONS: Record<string, typeof Server> = {
  observability: Activity,
  caching: Cpu,
  queue: Workflow,
  rate_limiting: ShieldCheck,
  resilience: HeartPulse,
  database: Database,
  health: Server,
}

function pct(rate: number): string {
  return `${Math.round(rate * 100)}%`
}

function StatusChip({ status }: { status: ReadinessStatus }) {
  return <Chip tone={STATUS_TONE[status]}>{STATUS_LABEL[status]}</Chip>
}

function PillarCard({ pillar }: { pillar: ProductionPillar }) {
  const Icon = PILLAR_ICONS[pillar.key] ?? Server
  return (
    <Card className="flex h-full flex-col gap-3 p-5">
      <div className="flex items-start justify-between gap-3">
        <span className="inline-flex items-center gap-2 text-h3 leading-snug text-foreground">
          <Icon size={18} className="shrink-0 text-secondary" />
          {pillar.title}
        </span>
        <StatusChip status={pillar.status} />
      </div>

      <div className="flex flex-wrap items-center gap-1.5">
        <Chip tone="neutral">Spec 55 {pillar.section}</Chip>
      </div>
      <p className="text-sm text-muted-foreground">{pillar.blurb}</p>

      <div className="space-y-1.5">
        <p className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">
          Live today
        </p>
        <ul className="space-y-1.5">
          {pillar.built.map(item => (
            <li key={item} className="flex gap-2 text-sm text-foreground">
              <CircleCheck size={15} className="mt-0.5 shrink-0 text-success dark:text-success-dark" />
              <span>{item}</span>
            </li>
          ))}
        </ul>
      </div>

      {pillar.planned.length > 0 && (
        <div className="mt-auto space-y-1.5 pt-1">
          <p className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">
            Planned
          </p>
          <ul className="space-y-1.5">
            {pillar.planned.map(item => (
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
    return (
      <Chip tone={value ? 'success' : 'neutral'}>{value ? 'on' : 'off'}</Chip>
    )
  }
  return <span className="font-mono text-[13px] text-foreground">{String(value)}</span>
}

function ConfigCard({ group }: { group: ConfigGroup }) {
  return (
    <Card className="flex h-full flex-col gap-3 p-5">
      <div className="flex items-center justify-between gap-2">
        <h3 className="text-h3 text-foreground">{group.title}</h3>
        <Chip tone="neutral">Spec 55 {group.section}</Chip>
      </div>
      <dl className="divide-y divide-border">
        {group.knobs.map(k => (
          <div key={k.name} className="flex items-center justify-between gap-3 py-1.5">
            <dt className="font-mono text-[12px] text-muted-foreground">{k.name}</dt>
            <dd>
              <KnobValue value={k.value} />
            </dd>
          </div>
        ))}
      </dl>
    </Card>
  )
}

function TaskRow({ task }: { task: ProductionBuildTask }) {
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

export default function ProductionReadinessPage() {
  usePageTitle('Production readiness · Spec 55')
  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ['build-production'],
    queryFn: getProduction,
    staleTime: 5 * 60_000,
  })

  const [status, setStatus] = useState<string>('all')

  const pillars = useMemo(() => {
    const list = data?.pillars ?? []
    return status === 'all' ? list : list.filter(p => p.status === status)
  }, [data, status])

  const statusFilters = useMemo(() => {
    const present = new Set((data?.pillars ?? []).map(p => p.status))
    const ordered = STATUS_ORDER.filter(s => present.has(s))
    return [{ key: 'all', label: 'All' }, ...ordered.map(s => ({ key: s, label: STATUS_LABEL[s] }))]
  }, [data])

  return (
    <GoalShell>
      <Hero
        eyebrow="Production readiness · Spec 55"
        title="Hardened to production-SaaS grade."
        lede={THE_BAR}
      >
        {data && (
          <span className="inline-flex items-center gap-1.5 rounded-pill border border-primary/40 px-3 py-1 text-[13px] font-semibold text-foreground">
            <span className="h-1.5 w-1.5 rounded-full bg-primary" aria-hidden />
            {data.health_probes.count} health probes live · {data.summary.middleware_count} middleware
            layers
          </span>
        )}
        <a
          href="#pillars"
          className="inline-flex items-center gap-1 text-[13px] font-semibold text-secondary hover:underline"
        >
          Jump to the pillars <ArrowRight size={14} />
        </a>
      </Hero>

      {/* Headline stats — read live from the running backend */}
      <StatBand>
        {isLoading || !data ? (
          [0, 1, 2, 3].map(i => <StatSkeleton key={i} />)
        ) : (
          <>
            <Stat
              value={`${data.summary.pillars_live}/${data.summary.pillar_count}`}
              label="Readiness pillars fully live"
            />
            <Stat
              value={
                <span className="inline-flex items-center gap-1.5">
                  <Network className="text-secondary" size={24} />
                  {data.summary.health_route_count}
                </span>
              }
              label="Health probes (live routes)"
            />
            <Stat value={data.summary.middleware_count} label="Middleware layers active" />
            <Stat value={pct(data.summary.cache_hit_rate)} label="Read-cache hit rate" />
          </>
        )}
      </StatBand>

      {/* §2–§8 — the readiness pillars */}
      <section id="pillars" className="mt-16 scroll-mt-20">
        <SectionHeading
          icon={ShieldCheck}
          title="Seven readiness pillars"
          sub="Each pillar is honestly classified — live, in progress, or planned. The config, middleware and health routes behind them are read straight from the running app, so the status is evidence, not a claim."
        />

        <div className="mt-6">
          <FilterRow options={statusFilters} value={status} onChange={setStatus} />
        </div>

        {isError ? (
          <ErrorState
            onRetry={() => refetch()}
            label="We couldn't load the production-readiness posture just now."
          />
        ) : (
          <>
            {data && (
              <p className="mt-5 text-sm text-muted-foreground">
                Showing {pillars.length} of {data.summary.pillar_count} pillars ·{' '}
                {data.summary.pillars_live} live · {data.summary.pillars_partial} in progress ·{' '}
                {data.summary.pillars_planned} planned
              </p>
            )}
            <div className="mt-3 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {data
                ? pillars.map(p => <PillarCard key={p.key} pillar={p} />)
                : [0, 1, 2, 3, 4, 5].map(i => <CardSkeleton key={i} className="h-72" />)}
            </div>
            {data && pillars.length === 0 && (
              <p className="mt-6 text-center text-muted-foreground">No pillars match this filter.</p>
            )}
          </>
        )}
      </section>

      {/* Live configuration knobs */}
      <section className="mt-16">
        <SectionHeading
          icon={Settings2}
          title="Live configuration"
          sub="The deployed values, read straight off the running settings — pool sizing, rate limits, scheduler, resilience timeouts, cache and cost guardrails."
        />
        <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {data
            ? data.config_groups.map(g => <ConfigCard key={g.key} group={g} />)
            : [0, 1, 2, 3, 4, 5].map(i => <CardSkeleton key={i} className="h-44" />)}
        </div>
      </section>

      {/* Operations — health probes · middleware · scheduler */}
      <section className="mt-16">
        <SectionHeading
          icon={Activity}
          title="Operations, read live"
          sub="The probes that keep the fleet healthy, the middleware stack on every request, and the cadence jobs the scheduler runs."
        />
        <div className="mt-6 grid gap-4 lg:grid-cols-3">
          <Card className="flex flex-col gap-3 p-5">
            <h3 className="inline-flex items-center gap-2 text-h3 text-foreground">
              <HeartPulse size={18} className="text-secondary" />
              Health probes
            </h3>
            <ul className="space-y-1.5">
              {(data?.health_probes.paths ?? []).map(p => (
                <li key={p} className="flex items-center gap-2 font-mono text-[12px] text-foreground">
                  <CircleCheck size={14} className="shrink-0 text-success dark:text-success-dark" />
                  {p}
                </li>
              ))}
              {!data && [0, 1].map(i => <li key={i} className="h-4 w-2/3 animate-pulse rounded bg-muted" />)}
            </ul>
            {data && <p className="mt-auto text-[12px] text-muted-foreground">{data.health_probes.note}</p>}
          </Card>

          <Card className="flex flex-col gap-3 p-5">
            <h3 className="inline-flex items-center gap-2 text-h3 text-foreground">
              <Network size={18} className="text-secondary" />
              Middleware stack
            </h3>
            <ul className="space-y-1.5">
              {(data?.middleware.classes ?? []).map(c => (
                <li key={c} className="font-mono text-[12px] text-muted-foreground">
                  {c}
                </li>
              ))}
              {!data && [0, 1, 2].map(i => <li key={i} className="h-4 w-1/2 animate-pulse rounded bg-muted" />)}
            </ul>
          </Card>

          <Card className="flex flex-col gap-3 p-5">
            <h3 className="inline-flex items-center gap-2 text-h3 text-foreground">
              <Workflow size={18} className="text-secondary" />
              Scheduler jobs
            </h3>
            <ul className="space-y-2">
              {(data?.scheduler.jobs ?? []).map(j => (
                <li key={j.id} className="flex items-center justify-between gap-2">
                  <span className="text-sm text-foreground">{j.name}</span>
                  <Chip tone="neutral">{j.cadence}</Chip>
                </li>
              ))}
              {!data && [0, 1, 2].map(i => <li key={i} className="h-4 w-3/4 animate-pulse rounded bg-muted" />)}
            </ul>
          </Card>
        </div>
      </section>

      {/* §8 — SLOs */}
      <section className="mt-16">
        <SectionHeading
          icon={Gauge}
          title="Service-level objectives"
          sub={data?.the_bar.slo_headline}
        />
        <Card className="mt-6 overflow-hidden p-0">
          <table className="w-full text-left text-sm">
            <thead className="border-b border-border bg-muted/40">
              <tr className="text-[11px] uppercase tracking-wider text-muted-foreground">
                <th className="px-5 py-3 font-semibold">Metric</th>
                <th className="px-5 py-3 font-semibold">Target</th>
                <th className="hidden px-5 py-3 font-semibold sm:table-cell">Note</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {(data?.slos ?? []).map(s => (
                <tr key={s.metric}>
                  <td className="px-5 py-3 text-foreground">{s.metric}</td>
                  <td className="px-5 py-3 font-mono text-[13px] font-semibold text-secondary">
                    {s.target}
                  </td>
                  <td className="hidden px-5 py-3 text-muted-foreground sm:table-cell">{s.note}</td>
                </tr>
              ))}
              {!data &&
                [0, 1, 2, 3].map(i => (
                  <tr key={i}>
                    <td className="px-5 py-3" colSpan={3}>
                      <div className="h-4 w-2/3 animate-pulse rounded bg-muted" />
                    </td>
                  </tr>
                ))}
            </tbody>
          </table>
        </Card>
      </section>

      {/* §9 — build-task checklist */}
      <section className="mt-16">
        <SectionHeading
          icon={ListChecks}
          title="Build-task checklist"
          sub="Spec 55 §9 — each task classified by what's shipped versus what's next. The infra-dependent halves (ElastiCache, arq, /metrics, PgBouncer) are named as planned, not hidden."
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

      {/* §11 — open questions */}
      {data && data.open_questions.length > 0 && (
        <section className="mt-16">
          <SectionHeading
            icon={Cpu}
            title="Open questions"
            sub="The deliberate calls behind the posture — spec 55 §11."
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
          <Server className="text-secondary" size={24} />
          Honest about what's live, and what's next.
        </p>
        <p className="mx-auto mt-2 max-w-xl text-muted-foreground">
          The pillar statuses, config values, middleware count and cache hit-rate above are read
          straight from the running backend — never asserted in a doc. Skeleton-loaded, motion on the
          design-system tokens, keyboard-accessible filters.
        </p>
        <div className="mt-5 flex flex-wrap items-center justify-center gap-3">
          <Link to="/goal">
            <Button size="lg" variant="secondary">
              Back to the build hub
            </Button>
          </Link>
          <Link to="/goal/api">
            <Button size="lg" variant="tertiary">
              See the live API contract
            </Button>
          </Link>
        </div>
      </section>
    </GoalShell>
  )
}
