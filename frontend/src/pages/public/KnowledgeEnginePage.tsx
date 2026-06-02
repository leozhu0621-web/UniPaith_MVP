import { useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import {
  ArrowRight,
  Banknote,
  CircleCheck,
  Clock,
  Database,
  GitCompareArrows,
  Globe2,
  GraduationCap,
  Landmark,
  Layers,
  ListChecks,
  Network,
  Plane,
  Radar,
  ScrollText,
  Settings2,
  ShieldCheck,
  Sparkles,
  Telescope,
  Trophy,
} from 'lucide-react'

import { getKnowledgeBuild } from '../../api/build'
import type {
  KnowledgeAcceptanceItem,
  KnowledgeCapability,
  KnowledgeConfigKnob,
  KnowledgePhase,
  KnowledgeRefDomain,
  ReadinessStatus,
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

// Spec 60 — the data-crawler & knowledge-base engine, read from
// GET /api/v1/build/knowledge. The governed engine that enriches the platform
// with a source-cited picture of the world (careers, tests, visas, cost, majors,
// rankings, scholarships). Each capability is classified live·partial·planned;
// the source count, reference-table presence and backing-route counts are read
// straight from the running app, so the page can't claim what the deploy lacks.

const THE_BAR =
  'The platform should reason against a rich, current, source-cited picture of the world — ' +
  'real salaries behind a career goal, real score ranges behind a test, real requirements ' +
  'behind a visa, real cost behind a budget — not just the sparse data an institution typed in.'

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

const MATERIALITY_TONE: Record<string, 'warning' | 'cobalt' | 'neutral'> = {
  high: 'warning',
  medium: 'cobalt',
  low: 'neutral',
}

const REF_ICONS: Record<string, typeof Database> = {
  occupations: Banknote,
  tests: GraduationCap,
  visas: Plane,
  cost: Globe2,
  majors: ScrollText,
  rankings: Trophy,
  accreditation: Landmark,
  scholarships: Sparkles,
}

const CAPABILITY_ICONS: Record<string, typeof Database> = {
  registry: ShieldCheck,
  skeleton: Network,
  reference: Database,
  extraction: ScrollText,
  provenance: GitCompareArrows,
  idempotent: Layers,
  proactive: Radar,
  governance: ShieldCheck,
  scheduling: Clock,
  feeds_output: ArrowRight,
  chatbot: Sparkles,
}

function StatusChip({ status }: { status: ReadinessStatus }) {
  return <Chip tone={STATUS_TONE[status]}>{STATUS_LABEL[status]}</Chip>
}

function CapabilityCard({ capability }: { capability: KnowledgeCapability }) {
  const Icon = CAPABILITY_ICONS[capability.key] ?? Database
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
        <Chip tone="neutral">Spec 60 {capability.section}</Chip>
      </div>
      <p className="text-sm text-muted-foreground">{capability.blurb}</p>

      <div className="space-y-1.5">
        <p className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">
          Live today
        </p>
        <ul className="space-y-1.5">
          {capability.built.map(item => (
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

function RefDomainCard({ domain }: { domain: KnowledgeRefDomain }) {
  const Icon = REF_ICONS[domain.key] ?? Database
  return (
    <Card className="flex h-full flex-col gap-2 p-5">
      <div className="flex items-start justify-between gap-3">
        <span className="inline-flex items-center gap-2 text-h3 leading-snug text-foreground">
          <Icon size={18} className="shrink-0 text-secondary" />
          {domain.title}
        </span>
        {domain.table_present && (
          <CircleCheck size={16} className="mt-1 shrink-0 text-success dark:text-success-dark" />
        )}
      </div>
      <div className="flex flex-wrap items-center gap-1.5">
        <Chip tone="neutral">Spec 60 {domain.section}</Chip>
        <code className="rounded bg-muted px-1.5 py-0.5 font-mono text-[11px] text-muted-foreground">
          {domain.table}
        </code>
      </div>
      <p className="text-sm text-foreground">
        <span className="text-muted-foreground">Sources:</span> {domain.sources}
      </p>
      <p className="text-sm text-foreground">
        <span className="text-muted-foreground">Feeds:</span> {domain.feeds}
      </p>
    </Card>
  )
}

function KnobValue({ value }: { value: string | number | boolean }) {
  if (typeof value === 'boolean') {
    return <Chip tone={value ? 'success' : 'neutral'}>{value ? 'on' : 'off'}</Chip>
  }
  return <span className="font-mono text-[13px] text-foreground">{String(value)}</span>
}

function KnobRow({ knob }: { knob: KnowledgeConfigKnob }) {
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

function AcceptanceRow({ item }: { item: KnowledgeAcceptanceItem }) {
  return (
    <li className="flex items-start gap-3 py-3">
      <StatusChip status={item.status} />
      <span className="text-sm text-foreground">{item.text}</span>
    </li>
  )
}

function PhaseCard({ phase }: { phase: KnowledgePhase }) {
  return (
    <Card className="flex h-full flex-col gap-2 p-5">
      <div className="flex items-center justify-between gap-3">
        <span className="inline-flex items-center gap-2 text-h3 text-foreground">
          <span className="inline-flex h-6 w-6 items-center justify-center rounded-full border border-secondary/40 font-mono text-[12px] text-secondary">
            {phase.key}
          </span>
          {phase.title}
        </span>
        <StatusChip status={phase.status} />
      </div>
      <p className="text-sm text-muted-foreground">{phase.detail}</p>
    </Card>
  )
}

function RouteList({
  icon: Icon,
  title,
  routes,
}: {
  icon: typeof Database
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

export default function KnowledgeEnginePage() {
  usePageTitle('Data crawler & knowledge engine · Spec 60')
  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ['build-knowledge'],
    queryFn: getKnowledgeBuild,
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
        eyebrow="Data crawler & knowledge engine · Spec 60"
        title="The world-side knowledge graph, in the open."
        lede={THE_BAR}
      >
        {data && (
          <span className="inline-flex items-center gap-1.5 rounded-pill border border-primary/40 px-3 py-1 text-[13px] font-semibold text-foreground">
            <span className="h-1.5 w-1.5 rounded-full bg-primary" aria-hidden />
            {data.summary.registered_source_count} allowlisted sources ·{' '}
            {data.summary.reference_domain_count} reference domains
          </span>
        )}
        <a
          href="#benchmark"
          className="inline-flex items-center gap-1 text-[13px] font-semibold text-secondary hover:underline"
        >
          See how we beat Kollegio <ArrowRight size={14} />
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
                  <ShieldCheck className="text-secondary" size={24} />
                  {data.summary.registered_source_count}
                </span>
              }
              label="Allowlisted sources"
            />
            <Stat
              value={
                <span className="inline-flex items-center gap-1.5">
                  <Database className="text-secondary" size={22} />
                  {data.summary.reference_tables_present}
                </span>
              }
              label="Reference tables live"
            />
            <Stat
              value={
                <span className="inline-flex items-center gap-1.5">
                  <Network className="text-secondary" size={22} />
                  {data.summary.reference_route_count}
                </span>
              }
              label="Reference endpoints"
            />
          </>
        )}
      </StatBand>

      {/* §1A — the Kollegio benchmark (the asset) */}
      <section id="benchmark" className="mt-16 scroll-mt-20">
        <SectionHeading
          icon={Telescope}
          title="Improving on Kollegio"
          sub="Kollegio is the closest analog — a free AI college counselor over ~1,650 US schools. Here's where this engine is built to beat it."
        />
        <Card className="mt-6 overflow-hidden p-0">
          <div className="overflow-x-auto">
            <table className="w-full border-collapse text-left text-sm">
              <thead>
                <tr className="border-b border-border bg-muted/40">
                  <th className="px-4 py-3 font-semibold text-muted-foreground">Dimension</th>
                  <th className="px-4 py-3 font-semibold text-muted-foreground">Kollegio (the gap)</th>
                  <th className="px-4 py-3 font-semibold text-foreground">UniPaith</th>
                </tr>
              </thead>
              <tbody>
                {(data?.benchmark ?? []).map(b => (
                  <tr key={b.dimension} className="border-b border-border last:border-0">
                    <td className="px-4 py-3 align-top font-semibold text-foreground">{b.dimension}</td>
                    <td className="px-4 py-3 align-top text-muted-foreground">
                      {b.kollegio}
                      <span className="mt-1 block text-[12px] italic text-muted-foreground/80">
                        {b.gap}
                      </span>
                    </td>
                    <td className="px-4 py-3 align-top text-foreground">
                      <span className="inline-flex items-start gap-2">
                        <CircleCheck
                          size={15}
                          className="mt-0.5 shrink-0 text-success dark:text-success-dark"
                        />
                        {b.unipaith}
                      </span>
                    </td>
                  </tr>
                ))}
                {!data &&
                  [0, 1, 2, 3].map(i => (
                    <tr key={i} className="border-b border-border last:border-0">
                      <td className="px-4 py-3" colSpan={3}>
                        <div className="h-4 w-full animate-pulse rounded bg-muted" />
                      </td>
                    </tr>
                  ))}
              </tbody>
            </table>
          </div>
        </Card>
      </section>

      {/* §3 — the reference graph */}
      <section className="mt-16">
        <SectionHeading
          icon={Database}
          title="The reference graph"
          sub="A typed, normalized, provenance-carrying table per domain — the clean projection the consuming surfaces read. Each card's check means the table exists in the running schema."
        />
        <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {data
            ? data.reference_graph.map(d => <RefDomainCard key={d.key} domain={d} />)
            : [0, 1, 2, 3, 4, 5, 6, 7].map(i => <CardSkeleton key={i} className="h-44" />)}
        </div>
      </section>

      {/* §6 — the pipeline */}
      <section className="mt-16">
        <SectionHeading
          icon={GitCompareArrows}
          title="The pipeline"
          sub="Source → discover → fetch → extract → normalize → resolve → enrich-write. Idempotent on content hash; the extractor is grounded and never invents."
        />
        <div className="mt-6 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          {(data?.pipeline ?? []).map(stage => (
            <Card key={stage.n} className="flex flex-col gap-2 p-4">
              <span className="inline-flex h-7 w-7 items-center justify-center rounded-full bg-secondary/10 font-mono text-[13px] font-semibold text-secondary">
                {stage.n}
              </span>
              <h3 className="text-sm font-semibold text-foreground">{stage.name}</h3>
              <p className="text-[13px] text-muted-foreground">{stage.detail}</p>
            </Card>
          ))}
          {!data && [0, 1, 2, 3, 4, 5, 6].map(i => <CardSkeleton key={i} className="h-32" />)}
        </div>
      </section>

      {/* §2–§13 — the capabilities */}
      <section className="mt-16">
        <SectionHeading
          icon={ListChecks}
          title="Eleven engine capabilities"
          sub="Each is classified live, in progress, or planned. The source registry, reference tables and routes behind them are read straight from the running app — status is evidence, not a claim."
        />
        <div className="mt-6">
          <FilterRow options={statusFilters} value={status} onChange={setStatus} />
        </div>

        {isError ? (
          <ErrorState onRetry={() => refetch()} label="We couldn't load the knowledge engine just now." />
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

      {/* §4/§8 — provenance & authority */}
      <section className="mt-16 grid gap-6 lg:grid-cols-2">
        <div>
          <SectionHeading
            icon={GitCompareArrows}
            title="Provenance & authority"
            sub="Every crawled fact carries its source. When data conflicts, higher authority wins — verified first-party data is never overwritten by a crawl."
          />
          <Card className="mt-6 p-2 sm:p-5">
            <ol className="divide-y divide-border">
              {(data?.authority_ladder ?? []).map(r => (
                <li key={r.rank} className="flex items-start gap-3 py-3">
                  <span className="inline-flex h-6 w-6 shrink-0 items-center justify-center rounded-full border border-secondary/40 font-mono text-[12px] text-secondary">
                    {r.rank}
                  </span>
                  <div>
                    <p className="font-mono text-[13px] text-foreground">{r.source}</p>
                    <p className="text-[13px] text-muted-foreground">{r.note}</p>
                  </div>
                </li>
              ))}
              {!data &&
                [0, 1, 2, 3, 4].map(i => (
                  <li key={i} className="py-3">
                    <div className="h-5 w-3/4 animate-pulse rounded bg-muted" />
                  </li>
                ))}
            </ol>
          </Card>
        </div>

        {/* §3B — change-event taxonomy */}
        <div>
          <SectionHeading
            icon={Radar}
            title="Proactive change detection"
            sub="A real diff in a real source becomes a materiality-classified change_event, routed to the students who saved, applied or follow the affected entity — consent-gated and capped."
          />
          <Card className="mt-6 p-2 sm:p-5">
            <ul className="divide-y divide-border">
              {(data?.change_event_types ?? []).map(c => (
                <li key={c.type} className="flex items-center justify-between gap-3 py-2.5">
                  <span className="flex items-center gap-2">
                    <Chip tone={MATERIALITY_TONE[c.materiality] ?? 'neutral'}>{c.materiality}</Chip>
                    <span className="font-mono text-[13px] text-foreground">{c.type}</span>
                  </span>
                  <span className="text-right text-[12px] text-muted-foreground">{c.routes_to}</span>
                </li>
              ))}
              {!data &&
                [0, 1, 2, 3, 4].map(i => (
                  <li key={i} className="py-2.5">
                    <div className="h-5 w-2/3 animate-pulse rounded bg-muted" />
                  </li>
                ))}
            </ul>
          </Card>
        </div>
      </section>

      {/* Backing routes — the self-verifying proof */}
      <section className="mt-16">
        <SectionHeading
          icon={Network}
          title="Backed by live routes"
          sub="Resolved from the running route table — the page can only list a surface the deployed app actually serves."
        />
        <div className="mt-6 grid gap-4 lg:grid-cols-3">
          <RouteList icon={Database} title="Reference (public)" routes={data?.routes.reference} />
          <RouteList icon={Settings2} title="Crawler ops (system)" routes={data?.routes.crawler_ops} />
          <RouteList icon={ShieldCheck} title="Enrichment review" routes={data?.routes.enrichment} />
        </div>
      </section>

      {/* Live configuration */}
      <section className="mt-16">
        <SectionHeading
          icon={Settings2}
          title="Live configuration"
          sub="The deployed values, read straight off the running settings — the extraction flag, the live-fetch gate, the allowlist-only switch, the auto-apply floors and the change-event cap."
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

      {/* §14 — phasing */}
      <section className="mt-16">
        <SectionHeading icon={Layers} title="Phasing" sub="Spec 60 §14 — institutional core, student-facing reference, then the long tail + proactive layer." />
        <div className="mt-6 grid gap-4 sm:grid-cols-3">
          {(data?.phases ?? []).map(p => <PhaseCard key={p.key} phase={p} />)}
          {!data && [0, 1, 2].map(i => <CardSkeleton key={i} className="h-32" />)}
        </div>
      </section>

      {/* §15 — acceptance */}
      <section className="mt-16">
        <SectionHeading
          icon={CircleCheck}
          title="Acceptance"
          sub="Spec 60 §15 — the definition of done, each criterion held to the same honest live/in-progress/planned bar and backed by a contract test."
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

      {/* §16 — open questions */}
      {data && data.open_questions.length > 0 && (
        <section className="mt-16">
          <SectionHeading
            icon={Sparkles}
            title="Open questions"
            sub="The deliberate calls behind the engine — spec 60 §16."
          />
          <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {data.open_questions.map(q => (
              <Card key={q.q} className="flex h-full flex-col gap-2 p-5">
                <h3 className="text-h3 text-foreground">{q.q}</h3>
                <p className="text-sm text-muted-foreground">{q.a}</p>
              </Card>
            ))}
          </div>
        </section>
      )}

      {/* Closing */}
      <section className="mt-16 rounded-xl border border-border bg-card p-8 text-center">
        <p className="inline-flex items-center justify-center gap-2 text-h2 text-foreground">
          <ShieldCheck className="text-secondary" size={24} />
          Public, non-personal, and source-cited.
        </p>
        <p className="mx-auto mt-2 max-w-xl text-muted-foreground">
          The engine builds the world; the student builds their record; matching joins them. Every
          crawled fact is provisional until confidence-gated or institution-confirmed — and nothing
          is ever fabricated.
        </p>
        <div className="mt-5 flex flex-wrap items-center justify-center gap-3">
          <Link to="/goal">
            <Button size="lg" variant="secondary">
              Back to the build hub
            </Button>
          </Link>
          <Link to="/goal/search">
            <Button size="lg" variant="tertiary">
              See search, feed & recs
            </Button>
          </Link>
        </div>
      </section>
    </GoalShell>
  )
}
