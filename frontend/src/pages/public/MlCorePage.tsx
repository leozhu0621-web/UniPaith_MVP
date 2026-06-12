import { useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import {
  ArrowRight,
  Boxes,
  CircleCheck,
  Clock,
  Cpu,
  Database,
  FlaskConical,
  Gauge,
  GitCompareArrows,
  Layers,
  ListChecks,
  MessageSquare,
  Network,
  Scale,
  Server,
  Settings2,
  ShieldCheck,
  Sparkles,
  Workflow,
} from 'lucide-react'

import { getMlCoreBuild } from '../../api/build'
import type {
  MlCoreAcceptanceItem,
  MlCoreCapability,
  MlCoreConfigKnob,
  MlCorePhase,
  ReadinessStatus,
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

// Spec 63 — ML core & knowledge processing, read from GET /api/v1/build/ml-core.
// The platform's hard model boundary: Qwen is the invisible ML backend; Claude is
// the human-facing agent, pinned by policy. Each capability is classified
// live·partial·planned; the boundary counts, the human-facing pin, the provider
// routing, the audit gate and the L3 weights are read straight from the running
// app — the page can't claim a boundary the deployed routing layer doesn't enforce.

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

const CAPABILITY_ICONS: Record<string, typeof Database> = {
  boundary: ShieldCheck,
  transport: Server,
  processing_routing: Workflow,
  embeddings: Boxes,
  extraction: GitCompareArrows,
  l3: Scale,
  synthesis: Sparkles,
  tuning: FlaskConical,
  resilience: Network,
  sovereignty: ShieldCheck,
}

function StatusChip({ status }: { status: ReadinessStatus }) {
  return <Chip tone={STATUS_TONE[status]}>{STATUS_LABEL[status]}</Chip>
}

function CapabilityCard({ capability }: { capability: MlCoreCapability }) {
  const Icon = CAPABILITY_ICONS[capability.key] ?? Cpu
  return (
    <Card pad={false} className="flex h-full flex-col gap-3 p-5">
      <div className="flex items-start justify-between gap-3">
        <CardTitle icon={Icon} className="leading-snug">
          {capability.title}
        </CardTitle>
        <StatusChip status={capability.status} />
      </div>
      <div className="flex flex-wrap items-center gap-1.5">
        <Chip tone="neutral">Spec 63 {capability.section}</Chip>
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

function KnobRow({ knob }: { knob: MlCoreConfigKnob }) {
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

function AcceptanceRow({ item }: { item: MlCoreAcceptanceItem }) {
  return (
    <li className="flex items-start gap-3 py-3">
      <StatusChip status={item.status} />
      <span className="text-sm text-foreground">{item.text}</span>
    </li>
  )
}

function PhaseCard({ phase }: { phase: MlCorePhase }) {
  return (
    <Card pad={false} className="flex h-full flex-col gap-2 p-5">
      <div className="flex items-center justify-between gap-3">
        <CardTitle>
          <span className="inline-flex h-6 w-6 items-center justify-center rounded-full border border-secondary/40 font-mono text-[12px] text-secondary">
            {phase.key}
          </span>
          {phase.title}
        </CardTitle>
        <StatusChip status={phase.status} />
      </div>
      <p className="text-sm text-muted-foreground">{phase.detail}</p>
    </Card>
  )
}

export default function MlCorePage() {
  usePageTitle('ML core & knowledge processing · Spec 63')
  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ['build-ml-core'],
    queryFn: getMlCoreBuild,
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

  const SIDE_ICON: Record<string, typeof Cpu> = { qwen: Cpu, claude: MessageSquare }

  return (
    <GoalShell>
      <Hero
        eyebrow="ML core & knowledge processing · Spec 63"
        title="Qwen processes. Claude communicates."
        lede={
          data?.the_rule.statement ??
          'The platform runs on two models with a hard, non-negotiable boundary. Qwen is the invisible ML backend; Claude is the human-facing agent, pinned by policy.'
        }
      >
        {/* The single Sunlit-Gold beat — the boundary, stated as a fact. */}
        {data && (
          <span className="inline-flex items-center gap-1.5 rounded-pill border border-primary/40 px-3 py-1 text-[13px] font-semibold text-foreground">
            <span className="h-1.5 w-1.5 rounded-full bg-primary" aria-hidden />
            {data.summary.human_facing_served_by_qwen} human-facing agents served by Qwen ·{' '}
            {data.summary.human_facing_count} pinned to Claude
          </span>
        )}
        <a
          href="#boundary"
          className="inline-flex items-center gap-1 text-[13px] font-semibold text-secondary hover:underline"
        >
          See the boundary <ArrowRight size={14} />
        </a>
      </Hero>

      {/* Headline stats — read live from the running routing layer */}
      <StatBand isError={isError}>
        {isLoading || !data ? (
          [0, 1, 2, 3].map(i => <StatSkeleton key={i} />)
        ) : (
          <>
            <Stat
              value={
                <span className="inline-flex items-center gap-1.5">
                  <MessageSquare className="text-secondary" size={24} />
                  {data.summary.human_facing_count}
                </span>
              }
              label="Agents pinned to Claude"
            />
            <Stat
              value={
                <span className="inline-flex items-center gap-1.5">
                  <ShieldCheck className="text-secondary" size={24} />
                  {data.summary.human_facing_served_by_qwen}
                </span>
              }
              label="Human-facing served by Qwen"
            />
            <Stat
              value={
                <span className="inline-flex items-center gap-1.5">
                  <Cpu className="text-secondary" size={24} />
                  {data.summary.qwen_eligible_count}
                </span>
              }
              label="Qwen-eligible jobs"
            />
            <Stat
              value={`${data.summary.capabilities_live}/${data.summary.capability_count}`}
              label="Capabilities fully live"
            />
          </>
        )}
      </StatBand>

      {/* §1 — the boundary (the rule everything follows) */}
      <section id="boundary" className="mt-16 scroll-mt-20">
        <SectionHeading
          icon={ShieldCheck}
          title="The boundary"
          sub="If an output is a conversation with, or personalized advice to, a human → Claude. If it is data processing, scoring or synthesis of informational content → Qwen. No exceptions, no per-task drift."
        />
        <div className="mt-6 grid gap-4 lg:grid-cols-2">
          {(data?.boundary_columns ?? []).map(col => {
            const Icon = SIDE_ICON[col.side] ?? Cpu
            return (
              <Card pad={false} key={col.side} className="flex h-full flex-col gap-3 p-6">
                <CardTitle>
                  <Icon size={20} className="text-secondary" />
                  {col.title}
                </CardTitle>
                <dl className="space-y-2 text-sm">
                  <div className="flex gap-2">
                    <dt className="w-20 shrink-0 text-muted-foreground">Role</dt>
                    <dd className="text-foreground">{col.role}</dd>
                  </div>
                  <div className="flex gap-2">
                    <dt className="w-20 shrink-0 text-muted-foreground">Human</dt>
                    <dd className="text-foreground">{col.human}</dd>
                  </div>
                  <div className="flex gap-2">
                    <dt className="w-20 shrink-0 text-muted-foreground">Why</dt>
                    <dd className="text-foreground">{col.why}</dd>
                  </div>
                  <div className="flex gap-2">
                    <dt className="w-20 shrink-0 text-muted-foreground">Where</dt>
                    <dd className="text-foreground">{col.where}</dd>
                  </div>
                </dl>
              </Card>
            )
          })}
          {!data && [0, 1].map(i => <CardSkeleton key={i} className="h-56" />)}
        </div>
        {data && (
          <Card pad={false} className="mt-4 flex items-start gap-3 p-5">
            <GitCompareArrows size={18} className="mt-0.5 shrink-0 text-secondary" />
            <p className="text-sm text-foreground">
              <span className="font-semibold">Seam rule.</span> {data.the_rule.seam}
            </p>
          </Card>
        )}
      </section>

      {/* §4 — the model roster */}
      <section className="mt-16">
        <SectionHeading
          icon={Cpu}
          title="Model roster"
          sub="Every task, the model that serves it, and which side of the boundary it sits on. Human-facing rows are pinned to Claude by policy — not eligible for reassignment."
        />
        <Card pad={false} className="mt-6 overflow-hidden p-0">
          <div className="overflow-x-auto">
            <table className="w-full border-collapse text-left text-sm">
              <thead>
                <tr className="border-b border-border bg-muted/40">
                  <th className="px-4 py-3 font-semibold text-muted-foreground">Task</th>
                  <th className="px-4 py-3 font-semibold text-muted-foreground">Model</th>
                  <th className="px-4 py-3 font-semibold text-muted-foreground">Transport</th>
                  <th className="px-4 py-3 font-semibold text-muted-foreground">Faces a human</th>
                </tr>
              </thead>
              <tbody>
                {(data?.model_roster ?? []).map(row => (
                  <tr key={row.task} className="border-b border-border last:border-0">
                    <td className="px-4 py-3 align-top font-semibold text-foreground">{row.task}</td>
                    <td className="px-4 py-3 align-top text-muted-foreground">{row.model}</td>
                    <td className="px-4 py-3 align-top">
                      <Chip tone={row.provider === 'anthropic' ? 'cobalt' : 'neutral'}>
                        {row.provider === 'anthropic' ? 'Claude' : 'Qwen'}
                      </Chip>
                    </td>
                    <td className="px-4 py-3 align-top">
                      {row.faces_human ? (
                        <Chip tone="cobalt" icon={MessageSquare}>
                          human-facing
                        </Chip>
                      ) : (
                        <Chip tone="neutral">backend</Chip>
                      )}
                    </td>
                  </tr>
                ))}
                {!data &&
                  [0, 1, 2, 3, 4].map(i => (
                    <tr key={i} className="border-b border-border last:border-0">
                      <td className="px-4 py-3" colSpan={4}>
                        <div className="h-4 w-full animate-pulse rounded bg-muted" />
                      </td>
                    </tr>
                  ))}
              </tbody>
            </table>
          </div>
        </Card>
      </section>

      {/* §5 — the processing pipeline */}
      <section className="mt-16">
        <SectionHeading
          icon={Workflow}
          title="Knowledge-processing pipeline"
          sub="Raw crawled fact → presented knowledge, all on Qwen: extract → normalize → resolve → embed → enrich-write → synthesize → serve. The Claude advisor reads the served RAG index; it never runs the pipeline."
        />
        <div className="mt-6 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          {(data?.pipeline ?? []).map(stage => (
            <Card pad={false} key={stage.n} className="flex flex-col gap-2 p-4">
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

      {/* Provider routing + L3 + embeddings — the live ML config */}
      <section className="mt-16 grid gap-6 lg:grid-cols-2">
        <div>
          <SectionHeading
            icon={Network}
            title="Provider routing"
            sub="Read live from the routing layer. Qwen is registered as a transport but inert until enabled per-env — the default route stays Claude until eval promotes it."
          />
          <Card pad={false} className="mt-6 flex flex-col gap-3 p-5">
            <div className="flex items-center justify-between gap-3">
              <span className="text-sm text-muted-foreground">Default provider</span>
              <Chip tone="cobalt">{data?.provider_routing.default_provider ?? '—'}</Chip>
            </div>
            <div className="flex items-center justify-between gap-3">
              <span className="text-sm text-muted-foreground">Qwen registered</span>
              <Chip tone={data?.summary.qwen_registered ? 'success' : 'neutral'}>
                {data?.summary.qwen_registered ? 'yes' : 'no'}
              </Chip>
            </div>
            <div className="flex items-center justify-between gap-3">
              <span className="text-sm text-muted-foreground">Qwen enabled / available</span>
              <span className="flex gap-1.5">
                <Chip tone={data?.summary.qwen_enabled ? 'success' : 'neutral'}>
                  {data?.summary.qwen_enabled ? 'on' : 'off'}
                </Chip>
                <Chip tone={data?.summary.qwen_available ? 'success' : 'neutral'}>
                  {data?.summary.qwen_available ? 'reachable' : 'inert'}
                </Chip>
              </span>
            </div>
            <div className="flex items-center justify-between gap-3">
              <span className="text-sm text-muted-foreground">ai_turns audits qwen</span>
              <Chip tone={data?.summary.ai_turns_accepts_qwen ? 'success' : 'neutral'}>
                {data?.summary.ai_turns_accepts_qwen ? 'yes' : 'no'}
              </Chip>
            </div>
            <div className="border-t border-border pt-3">
              <p className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">
                Failover order
              </p>
              <div className="mt-1.5 flex flex-wrap items-center gap-1.5">
                {(data?.provider_routing.failover_order ?? []).map(p => (
                  <Chip key={p} tone="neutral">
                    {p}
                  </Chip>
                ))}
              </div>
            </div>
          </Card>
        </div>

        <div className="flex flex-col gap-6">
          <div>
            <SectionHeading
              icon={Scale}
              title="L3 scoring"
              sub="Qwen embeddings + classical calibrated scoring; every tuned checkpoint is fairness-gated before real cohorts."
            />
            <Card pad={false} className="mt-6 flex flex-col gap-2 p-5">
              {Object.entries(data?.l3_scoring.weights ?? {}).map(([k, v]) => (
                <div key={k} className="flex items-center justify-between gap-3">
                  <span className="font-mono text-[13px] text-foreground">{k}</span>
                  <span className="font-mono text-[13px] text-muted-foreground">{v}</span>
                </div>
              ))}
              {data && (
                <div className="mt-1 flex items-center justify-between gap-3 border-t border-border pt-2">
                  <span className="text-sm text-muted-foreground">Σ weights</span>
                  <Chip tone="cobalt">{data.l3_scoring.weight_sum}</Chip>
                </div>
              )}
              {!data && <div className="h-16 animate-pulse rounded bg-muted" />}
            </Card>
          </div>
          <div>
            <SectionHeading
              icon={Boxes}
              title="Embeddings"
              sub="Voyage 1024-d is live today; Qwen3-Embedding (Matryoshka → the live dim) is wired behind a flag, falling back to Voyage on any failure."
            />
            <Card pad={false} className="mt-6 flex flex-col gap-2 p-5">
              <div className="flex items-center justify-between gap-3">
                <span className="text-sm text-muted-foreground">Live provider</span>
                <Chip tone="cobalt">{data?.embeddings.provider ?? '—'}</Chip>
              </div>
              <div className="flex items-center justify-between gap-3">
                <span className="text-sm text-muted-foreground">Live model · dim</span>
                <span className="font-mono text-[13px] text-foreground">
                  {data?.embeddings.live_model} · {data?.embeddings.live_dimension}d
                </span>
              </div>
              <div className="flex items-center justify-between gap-3">
                <span className="text-sm text-muted-foreground">Qwen target</span>
                <span className="font-mono text-[13px] text-muted-foreground">
                  {data?.embeddings.qwen_model} · {data?.embeddings.matryoshka_target}d
                </span>
              </div>
            </Card>
          </div>
        </div>
      </section>

      {/* §2–§13 — the capabilities */}
      <section className="mt-16">
        <SectionHeading
          icon={ListChecks}
          title="Engine capabilities"
          sub="Each is classified live, in progress, or planned. The boundary, the pin, the audit gate and the L3 weights behind them are read straight from the running app — status is evidence, not a claim."
        />
        <div className="mt-6">
          <FilterRow options={statusFilters} value={status} onChange={setStatus} />
        </div>

        {isError ? (
          <ErrorState onRetry={() => refetch()} label="We couldn't load the ML core just now." />
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

      {/* §11 — migration phasing */}
      <section className="mt-16">
        <SectionHeading
          icon={Layers}
          title="Migration phasing"
          sub="Backend-only, and no Phase D — the human-facing layer is permanently Claude. Each phase earns its Qwen role through eval; Claude is untouched throughout."
        />
        <div className="mt-6 grid gap-4 sm:grid-cols-3">
          {(data?.phases ?? []).map(p => (
            <PhaseCard key={p.key} phase={p} />
          ))}
          {!data && [0, 1, 2].map(i => <CardSkeleton key={i} className="h-32" />)}
        </div>
      </section>

      {/* §14 — observability & SLOs */}
      <section className="mt-16">
        <SectionHeading
          icon={Gauge}
          title="Observability & SLOs"
          sub="What's tracked and the bar each metric is held to. Tokens and cost split by provider on the ai_turns ledger; a Qwen outage never degrades the Claude conversation."
        />
        <Card pad={false} className="mt-6 p-2 sm:p-5">
          <ul className="divide-y divide-border">
            {(data?.slos ?? []).map(s => (
              <li key={s.metric} className="flex flex-col gap-1 py-3 sm:flex-row sm:items-center">
                <span className="flex-1 text-sm font-semibold text-foreground">{s.metric}</span>
                <span className="flex-1 text-[13px] text-muted-foreground">{s.target}</span>
                <span className="flex-1 text-right font-mono text-[12px] text-muted-foreground">
                  {s.tracked_via}
                </span>
              </li>
            ))}
            {!data &&
              [0, 1, 2, 3].map(i => (
                <li key={i} className="py-3">
                  <div className="h-5 w-2/3 animate-pulse rounded bg-muted" />
                </li>
              ))}
          </ul>
        </Card>
      </section>

      {/* Live configuration */}
      <section className="mt-16">
        <SectionHeading
          icon={Settings2}
          title="Live configuration"
          sub="The deployed values, read straight off the running settings — the default provider, the failover order, the Qwen + embedding gates, the extraction flag and the fairness gate."
        />
        <Card pad={false} className="mt-6 p-5">
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

      {/* §16 — acceptance */}
      <section className="mt-16">
        <SectionHeading
          icon={CircleCheck}
          title="Acceptance"
          sub="Spec 63 §16 — the definition of done, each criterion held to the same honest live/in-progress/planned bar and backed by a contract test."
        />
        <Card pad={false} className="mt-6 p-2 sm:p-5">
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

      {/* §17 — open questions */}
      {data && data.open_questions.length > 0 && (
        <section className="mt-16">
          <SectionHeading
            icon={Sparkles}
            title="Open questions"
            sub="The deliberate calls behind the ML core — spec 63 §17."
          />
          <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {data.open_questions.map(q => (
              <Card pad={false} key={q.q} className="flex h-full flex-col gap-2 p-5">
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
          Qwen computes. Claude communicates.
        </p>
        <p className="mx-auto mt-2 max-w-xl text-muted-foreground">
          The highest-stakes surface — the conversation — carries zero Qwen-migration risk, because
          it never moves off Claude. The ML backend earns its role underneath, one eval-gated phase
          at a time.
        </p>
        <div className="mt-5 flex flex-wrap items-center justify-center gap-3">
          <Link to="/goal">
            <Button size="lg" variant="secondary">
              Back to the build hub
            </Button>
          </Link>
          <Link to="/goal/knowledge">
            <Button size="lg" variant="tertiary">
              See the knowledge engine
            </Button>
          </Link>
        </div>
      </section>
    </GoalShell>
  )
}
