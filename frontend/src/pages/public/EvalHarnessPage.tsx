import { useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import {
  Activity,
  ArrowRight,
  Bot,
  CircleCheck,
  Database,
  FlaskConical,
  Gauge,
  Gavel,
  Layers,
  ListChecks,
  Network,
  RefreshCw,
  Ruler,
  Scale,
  ShieldAlert,
  ShieldCheck,
  Sparkles,
  Target,
} from 'lucide-react'

import { getEvalHarness } from '../../api/build'
import { qk } from '../../api/queryKeys'
import type {
  EvalHarnessConsumer,
  EvalHarnessMode,
  EvalHarnessStatusItem,
  EvalHarnessSuite,
  EvalHarnessTable,
} from '../../types/buildEvalHarness'
import type { ReadinessStatus } from '../../types/build'
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

// Spec 62 — the shared evaluation harness, read from GET /api/v1/build/eval-harness.
// The consumers (chatbot + extraction, plugged in via thin adapters), their golden
// case counts, scored dimensions, the calibrated + independent judge, the four eval
// modes and the two added tables are all read from the running system — the page
// can't claim a harness the deployed app doesn't run. Built to the bar it documents:
// skeletons (never a blank flash), motion on the design tokens, keyboard-accessible
// filters, dark-safe semantic tokens, at most one Sunlit-Gold beat.

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

const CONSUMER_ICONS: Record<string, typeof Bot> = {
  chatbot: Bot,
  extraction: Database,
  match_rationale: Target,
}

const MODE_ICONS: Record<string, typeof ShieldCheck> = {
  ci_gate: ShieldCheck,
  ab: Scale,
  sampling: Activity,
  drift: RefreshCw,
}

function StatusChip({ status }: { status: ReadinessStatus }) {
  return <Chip tone={STATUS_TONE[status]}>{STATUS_LABEL[status]}</Chip>
}

function HardFloorChip() {
  return (
    <Chip tone="warning" icon={ShieldAlert}>
      Hard floor
    </Chip>
  )
}

function ConsumerCard({ consumer }: { consumer: EvalHarnessConsumer }) {
  const Icon = CONSUMER_ICONS[consumer.key] ?? Layers
  return (
    <Card pad={false} className="flex h-full flex-col gap-3 p-5">
      <div className="flex items-start justify-between gap-3">
        <CardTitle icon={Icon} className="leading-snug">
          {consumer.title}
        </CardTitle>
        <StatusChip status={consumer.status} />
      </div>
      <div className="flex flex-wrap items-center gap-1.5">
        <Chip tone="neutral">Spec {consumer.spec}</Chip>
        {consumer.status !== 'planned' && (
          <Chip tone="cobalt">
            {consumer.golden_case_count} cases · {consumer.golden_version}
          </Chip>
        )}
        {consumer.judge?.independent && <Chip tone="success">Independent judge</Chip>}
      </div>

      {/* The three hooks (§3) */}
      <dl className="space-y-1.5 text-sm">
        <div>
          <dt className="inline font-mono text-[11px] text-secondary">produce</dt>
          <dd className="inline text-muted-foreground"> — {consumer.hooks.produce}</dd>
        </div>
        <div>
          <dt className="inline font-mono text-[11px] text-secondary">rubric</dt>
          <dd className="inline text-muted-foreground"> — {consumer.hooks.rubric}</dd>
        </div>
        <div>
          <dt className="inline font-mono text-[11px] text-secondary">materialize</dt>
          <dd className="inline text-muted-foreground"> — {consumer.hooks.materialize}</dd>
        </div>
      </dl>

      {/* Scored dimensions */}
      {consumer.dimensions.length > 0 && (
        <div className="mt-auto">
          <p className="mb-1.5 text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">
            Scored dimensions
          </p>
          <div className="flex flex-wrap gap-1.5">
            {consumer.dimensions.map(d =>
              d.hard_floor ? (
                <Chip key={d.key} tone="warning" icon={ShieldAlert}>
                  {d.label}
                </Chip>
              ) : (
                <Chip key={d.key} tone={d.kind === 'deterministic' ? 'cobalt' : 'neutral'}>
                  {d.label}
                </Chip>
              ),
            )}
          </div>
        </div>
      )}
      {consumer.file && (
        <p className="pt-1 font-mono text-[11px] text-muted-foreground">{consumer.file}</p>
      )}
    </Card>
  )
}

function ModeCard({ mode }: { mode: EvalHarnessMode }) {
  const Icon = MODE_ICONS[mode.key] ?? Gauge
  return (
    <Card pad={false} className="flex h-full flex-col gap-2 p-4">
      <div className="flex items-center justify-between gap-2">
        <span className="inline-flex items-center gap-2 text-sm font-semibold text-foreground">
          <Icon size={16} className="shrink-0 text-secondary" />
          {mode.title}
        </span>
        <StatusChip status={mode.status} />
      </div>
      <p className="text-[12px] text-muted-foreground">{mode.blurb}</p>
      <p className="mt-auto inline-flex items-center gap-1 pt-1 font-mono text-[11px] text-muted-foreground">
        {mode.backing_table_present ? (
          <CircleCheck size={12} className="text-success dark:text-success-dark" />
        ) : null}
        {mode.backing_table}
      </p>
    </Card>
  )
}

function SuiteRow({ suite }: { suite: EvalHarnessSuite }) {
  const thr = Object.entries(suite.threshold)[0]
  return (
    <li className="flex flex-col gap-1 py-3 sm:flex-row sm:items-start sm:gap-3">
      <div className="flex shrink-0 items-center gap-2 sm:w-36">
        {suite.in_runner ? <Chip tone="success">In runner</Chip> : <Chip tone="neutral">—</Chip>}
        {suite.hard_floor && <HardFloorChip />}
      </div>
      <div className="min-w-0 flex-1">
        <div className="flex flex-wrap items-center gap-2">
          <span className="font-mono text-[13px] text-foreground">{suite.key}</span>
          {thr && (
            <Chip tone="cobalt">
              {thr[0]} ≥ {thr[1]}
            </Chip>
          )}
        </div>
        <p className="mt-0.5 text-[12px] text-muted-foreground">{suite.blurb}</p>
      </div>
    </li>
  )
}

function TableRow({ table, isNew }: { table: EvalHarnessTable; isNew?: boolean }) {
  return (
    <li className="flex items-start gap-3 py-2.5">
      <CircleCheck
        size={15}
        className={
          table.present
            ? 'mt-0.5 shrink-0 text-success dark:text-success-dark'
            : 'mt-0.5 shrink-0 text-muted-foreground'
        }
      />
      <div className="min-w-0 flex-1">
        <div className="flex flex-wrap items-center gap-2">
          <code className="font-mono text-[13px] text-foreground">{table.name}</code>
          {isNew && <Chip tone="gold">New</Chip>}
          <span className="text-[11px] text-muted-foreground">{table.column_count} cols</span>
        </div>
        <p className="mt-0.5 text-[12px] text-muted-foreground">{table.blurb}</p>
      </div>
    </li>
  )
}

function StatusList({ items }: { items: EvalHarnessStatusItem[] }) {
  return (
    <ul className="space-y-2.5">
      {items.map(i => (
        <li key={i.text} className="flex items-start gap-2.5">
          <StatusChip status={i.status} />
          <span className="text-sm text-foreground">{i.text}</span>
        </li>
      ))}
    </ul>
  )
}

export default function EvalHarnessPage() {
  usePageTitle('Evaluation harness · Spec 62')
  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: qk.buildEvalHarness(),
    queryFn: getEvalHarness,
    staleTime: 5 * 60_000,
  })

  const [consumerFilter, setConsumerFilter] = useState<string>('all')
  const consumers = useMemo(() => {
    const list = data?.consumers ?? []
    if (consumerFilter === 'live') return list.filter(c => c.status === 'live')
    return list
  }, [data, consumerFilter])

  const judges = useMemo(
    () => (data?.consumers ?? []).filter(c => c.judge !== null),
    [data],
  )

  return (
    <GoalShell>
      <Hero
        eyebrow="Evaluation harness · Spec 62"
        title="One harness. Every AI surface, measured."
        lede={data?.the_bar.statement ?? THE_BAR_FALLBACK}
      >
        {data && (
          <span className="inline-flex items-center gap-1.5 rounded-pill border border-primary/40 px-3 py-1 text-[13px] font-semibold text-foreground">
            <span className="h-1.5 w-1.5 rounded-full bg-primary" aria-hidden />
            {data.summary.consumers_live} consumers · one harness · no duplicated eval code
          </span>
        )}
        <a
          href="#consumers"
          className="inline-flex items-center gap-1 text-[13px] font-semibold text-secondary hover:underline"
        >
          Jump to the consumers <ArrowRight size={14} />
        </a>
      </Hero>

      {/* Headline stats — read live from the running backend */}
      <StatBand isError={isError}>
        {isLoading || !data ? (
          [0, 1, 2, 3].map(i => <StatSkeleton key={i} />)
        ) : (
          <>
            <Stat
              value={
                <span className="inline-flex items-center gap-1.5">
                  <Layers className="text-secondary" size={24} />
                  {data.summary.consumers_live}
                </span>
              }
              label="Consumers live (chatbot + extraction)"
            />
            <Stat value={data.summary.golden_case_total} label="Golden cases (live from disk)" />
            <Stat
              value={
                <span className="inline-flex items-center gap-1.5">
                  <ShieldAlert className="text-secondary" size={22} />
                  {data.summary.hard_floor_dimension_count}
                </span>
              }
              label="Hard-floor dimensions"
            />
            <Stat
              value={`${data.summary.modes_live}/${data.summary.eval_mode_count}`}
              label="Eval modes live"
            />
          </>
        )}
      </StatBand>

      {/* §3/§5 — the consumers, read live from the registry */}
      <section id="consumers" className="mt-16 scroll-mt-20">
        <SectionHeading
          icon={Layers}
          title="Pluggable consumers — one adapter each"
          sub="Adding a consumer is one adapter (produce / rubric / materialize) + a golden set; it inherits the runner, gate, A/B, drift and metrics. The chatbot and the crawler extraction run through the same harness — read live from the registry, not asserted."
        />
        <div className="mt-5">
          <FilterRow
            options={[
              { key: 'all', label: 'All consumers' },
              { key: 'live', label: 'Live only' },
            ]}
            value={consumerFilter}
            onChange={setConsumerFilter}
          />
        </div>
        {isError ? (
          <ErrorState
            onRetry={() => refetch()}
            label="We couldn't load the eval-harness surface just now."
          />
        ) : (
          <div className="mt-5 grid gap-4 lg:grid-cols-3">
            {data
              ? consumers.map(c => <ConsumerCard key={c.key} consumer={c} />)
              : [0, 1, 2].map(i => <CardSkeleton key={i} className="h-72" />)}
          </div>
        )}
      </section>

      {/* §3 — the three hooks */}
      <section className="mt-16">
        <SectionHeading
          icon={Sparkles}
          title="The adapter contract — three hooks"
          sub="Everything else (runner, gate, A/B, drift, metrics) is shared. A consumer implements exactly these."
        />
        <div className="mt-6 grid gap-4 sm:grid-cols-3">
          {(data?.adapter_hooks ?? []).map(h => (
            <Card pad={false} key={h.hook} className="flex flex-col gap-2 p-5">
              <code className="font-mono text-sm text-secondary">{h.hook}</code>
              <p className="text-sm text-muted-foreground">{h.blurb}</p>
            </Card>
          ))}
          {!data && [0, 1, 2].map(i => <CardSkeleton key={i} className="h-28" />)}
        </div>
      </section>

      {/* §4 — the judge & calibration */}
      <section className="mt-16">
        <SectionHeading
          icon={Gavel}
          title="The judge — calibrated, and independent of what it grades"
          sub="The judge scores each subjective dimension 0–1 with a required justification, and runs only after the deterministic checks. It is a different model family from the system under test — for the Qwen extraction, Claude judges. The agreement number is recorded honestly: the deterministic floor is live; a live ≥85% human-agreement pass is an expert-hours item."
        />
        <div className="mt-6 grid gap-4 lg:grid-cols-2">
          {judges.map(c => (
            <Card pad={false} key={c.key} className="flex flex-col gap-2 p-5">
              <div className="flex items-start justify-between gap-3">
                <CardTitle icon={Scale}>{c.title}</CardTitle>
                {c.judge?.independent ? (
                  <Chip tone="success">Independent</Chip>
                ) : (
                  <Chip tone="neutral">Distinct slot</Chip>
                )}
              </div>
              <div className="flex flex-wrap items-center gap-1.5">
                <Chip tone="cobalt">judge: {c.judge?.model}</Chip>
                <Chip tone="neutral">target ≥ {c.judge?.target_agreement}</Chip>
                <Chip tone="neutral">
                  agreement: {c.judge?.agreement ?? 'not yet measured'}
                </Chip>
              </div>
              <p className="text-[12px] text-muted-foreground">
                Grades <span className="text-foreground">{c.judge?.system_under_test}</span>.{' '}
                {c.judge?.note}
              </p>
            </Card>
          ))}
          {!data && [0, 1].map(i => <CardSkeleton key={i} className="h-40" />)}
        </div>
      </section>

      {/* §4 — deterministic checks first */}
      <section className="mt-16">
        <SectionHeading
          icon={Ruler}
          title="Deterministic checks gate first"
          sub="Cheap, exact, token-free — schema validity, grounding, PII, refusal, no-generation. They catch the failures you never want to pay a judge to notice, so the extraction consumer gates in CI with no API key at all."
        />
        <div className="mt-6 grid gap-4 lg:grid-cols-2">
          {(data?.consumers ?? [])
            .filter(c => c.deterministic_checks.length > 0)
            .map(c => (
              <Card pad={false} key={c.key} className="flex flex-col gap-3 p-5">
                <h3 className="inline-flex items-center gap-2 text-h3 text-foreground">
                  <Ruler size={18} className="text-secondary" />
                  {c.title}
                </h3>
                <ul className="space-y-2">
                  {c.deterministic_checks.map(chk => (
                    <li key={chk.name} className="flex gap-2 text-sm text-foreground">
                      <CircleCheck
                        size={15}
                        className="mt-0.5 shrink-0 text-success dark:text-success-dark"
                      />
                      <span>
                        <code className="font-mono text-[12px] text-secondary">{chk.name}</code> —{' '}
                        {chk.blurb}
                      </span>
                    </li>
                  ))}
                </ul>
              </Card>
            ))}
          {!data && [0, 1].map(i => <CardSkeleton key={i} className="h-40" />)}
        </div>
      </section>

      {/* §6 — eval modes */}
      <section className="mt-16">
        <SectionHeading
          icon={Gauge}
          title="Four modes, one run loop"
          sub="The CI gate, pre-promote A/B, production sampling and scheduled drift all reuse the same run loop — only the trigger and what's compared differ. Each backing table is confirmed present in the running schema; the traffic-dependent modes are named in-progress, not hidden."
        />
        <div className="mt-6 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          {data
            ? data.eval_modes.map(m => <ModeCard key={m.key} mode={m} />)
            : [0, 1, 2, 3].map(i => <CardSkeleton key={i} className="h-32" />)}
        </div>
      </section>

      {/* §6.1 — CI suites */}
      <section className="mt-16">
        <SectionHeading
          icon={ShieldCheck}
          title="The CI gate — deterministic, blocks with no key"
          sub="The extraction consumer's suites run through the shared harness and are confirmed present in the live runner. The no-fabrication suite is a hard floor; a single ungrounded field blocks the release."
        />
        <Card pad={false} className="mt-6 p-2 sm:p-5">
          <ul className="divide-y divide-border">
            {(data?.suites ?? []).map(s => (
              <SuiteRow key={s.key} suite={s} />
            ))}
            {!data &&
              [0, 1].map(i => (
                <li key={i} className="py-3">
                  <div className="h-5 w-3/4 animate-pulse rounded bg-muted" />
                </li>
              ))}
          </ul>
        </Card>
      </section>

      {/* §8 — data model additions */}
      <section className="mt-16">
        <SectionHeading
          icon={Database}
          title="Two tables added, four reused"
          sub="The harness reuses the ml_loop tables and the ai_turns ledger; it adds exactly two. Presence + column counts are introspected from the running SQLAlchemy metadata — the page can't claim a table the app doesn't have."
        />
        <div className="mt-6 grid gap-4 lg:grid-cols-2">
          <Card pad={false} className="p-5">
            <h3 className="mb-2 inline-flex items-center gap-2 text-h3 text-foreground">
              <Database size={18} className="text-secondary" />
              Added (§8)
            </h3>
            <ul className="divide-y divide-border">
              {(data?.data_model.new_tables ?? []).map(t => (
                <TableRow key={t.name} table={t} isNew />
              ))}
              {!data && [0, 1].map(i => <li key={i} className="h-10 animate-pulse" />)}
            </ul>
          </Card>
          <Card pad={false} className="p-5">
            <h3 className="mb-2 inline-flex items-center gap-2 text-h3 text-foreground">
              <RefreshCw size={18} className="text-secondary" />
              Reused
            </h3>
            <ul className="divide-y divide-border">
              {(data?.data_model.reused_tables ?? []).map(t => (
                <TableRow key={t.name} table={t} />
              ))}
              {!data && [0, 1].map(i => <li key={i} className="h-10 animate-pulse" />)}
            </ul>
          </Card>
        </div>
      </section>

      {/* §7 — synthetic + red-team */}
      <section className="mt-16">
        <SectionHeading
          icon={ShieldAlert}
          title="Synthetic + red-team"
          sub="Spec 62 §7 — generated edge cases per consumer and a red-team battery every release; any pass blocks."
        />
        <div className="mt-6 grid gap-4 sm:grid-cols-3">
          {(data?.synthetic_redteam ?? []).map(s => (
            <Card pad={false} key={s.key} className="flex h-full flex-col gap-2 p-5">
              <div className="flex items-start justify-between gap-2">
                <h3 className="text-h3 text-foreground">{s.title}</h3>
                <StatusChip status={s.status} />
              </div>
              <p className="text-sm text-muted-foreground">{s.blurb}</p>
            </Card>
          ))}
          {!data && [0, 1, 2].map(i => <CardSkeleton key={i} className="h-32" />)}
        </div>
      </section>

      {/* §9/§10 — SLOs + cost controls */}
      <section className="mt-16 grid gap-4 lg:grid-cols-2">
        <Card pad={false} className="p-5">
          <h3 className="mb-3 inline-flex items-center gap-2 text-h3 text-foreground">
            <Target size={18} className="text-secondary" />
            SLOs (§9)
          </h3>
          {data ? (
            <StatusList items={data.slos} />
          ) : (
            <div className="h-32 animate-pulse rounded bg-muted" />
          )}
        </Card>
        <Card pad={false} className="p-5">
          <h3 className="mb-3 inline-flex items-center gap-2 text-h3 text-foreground">
            <Gauge size={18} className="text-secondary" />
            Cost control (§10)
          </h3>
          {data ? (
            <StatusList items={data.cost_controls} />
          ) : (
            <div className="h-32 animate-pulse rounded bg-muted" />
          )}
        </Card>
      </section>

      {/* §11 — phasing */}
      <section className="mt-16">
        <SectionHeading
          icon={FlaskConical}
          title="Phasing"
          sub="Spec 62 §11 — primitives + chatbot, then the extraction adapter, then the traffic-dependent modes, then more consumers."
        />
        <div className="mt-6 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          {(data?.phases ?? []).map(p => (
            <Card pad={false} key={p.key} className="flex h-full flex-col gap-2 p-4">
              <div className="flex items-center justify-between gap-2">
                <span className="inline-flex h-6 w-6 items-center justify-center rounded-full bg-secondary/10 text-[12px] font-semibold text-secondary">
                  {p.key}
                </span>
                <StatusChip status={p.status} />
              </div>
              <h3 className="text-sm font-semibold text-foreground">{p.title}</h3>
              <p className="text-[12px] text-muted-foreground">{p.blurb}</p>
            </Card>
          ))}
          {!data && [0, 1, 2, 3].map(i => <CardSkeleton key={i} className="h-32" />)}
        </div>
      </section>

      {/* §12 — acceptance */}
      <section className="mt-16">
        <SectionHeading
          icon={ListChecks}
          title="Acceptance"
          sub="Spec 62 §12 — the definition of done, held to the same honest live / in-progress / planned bar."
        />
        <Card pad={false} className="mt-6 p-5">
          {data ? (
            <StatusList items={data.acceptance} />
          ) : (
            <div className="h-40 animate-pulse rounded bg-muted" />
          )}
        </Card>
      </section>

      {/* Backing routes */}
      <section className="mt-16">
        <SectionHeading
          icon={Network}
          title="Backed by live routes"
          sub="The AI surfaces the harness governs — resolved straight from the running route table."
        />
        <div className="mt-6 grid gap-4 lg:grid-cols-2">
          <Card pad={false} className="flex flex-col gap-3 p-5">
            <h3 className="inline-flex items-center gap-2 text-h3 text-foreground">
              <Bot size={18} className="text-secondary" />
              Chatbot (Discovery)
              {data && <Chip tone="cobalt">{data.routes.chatbot.length}</Chip>}
            </h3>
            <ul className="space-y-1.5">
              {(data?.routes.chatbot ?? []).slice(0, 6).map(p => (
                <li
                  key={p}
                  className="flex items-start gap-2 font-mono text-[12px] text-foreground"
                >
                  <CircleCheck
                    size={13}
                    className="mt-0.5 shrink-0 text-success dark:text-success-dark"
                  />
                  <span className="break-all">{p}</span>
                </li>
              ))}
            </ul>
          </Card>
          <Card pad={false} className="flex flex-col gap-3 p-5">
            <h3 className="inline-flex items-center gap-2 text-h3 text-foreground">
              <Database size={18} className="text-secondary" />
              Extraction (Reference)
              {data && <Chip tone="cobalt">{data.routes.extraction.length}</Chip>}
            </h3>
            <ul className="space-y-1.5">
              {(data?.routes.extraction ?? []).slice(0, 6).map(p => (
                <li
                  key={p}
                  className="flex items-start gap-2 font-mono text-[12px] text-foreground"
                >
                  <CircleCheck
                    size={13}
                    className="mt-0.5 shrink-0 text-success dark:text-success-dark"
                  />
                  <span className="break-all">{p}</span>
                </li>
              ))}
            </ul>
          </Card>
        </div>
      </section>

      {/* §13 — open questions */}
      {data && data.open_questions.length > 0 && (
        <section className="mt-16">
          <SectionHeading
            icon={Sparkles}
            title="Open questions"
            sub="The deliberate calls still open — spec 62 §13."
          />
          <div className="mt-6 grid gap-4 sm:grid-cols-2">
            {data.open_questions.map(q => (
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
          <FlaskConical className="text-secondary" size={24} />
          Built once, shared by every AI surface.
        </p>
        <p className="mx-auto mt-2 max-w-xl text-muted-foreground">
          The consumers, golden-case counts, dimensions, suites and tables above are read straight
          from the running backend — the registry, the fixtures on disk, the live runner and schema.
          The deterministic floor and red-team battery are hard floors; the A/B, drift and sampling
          modes are named as what's next.
        </p>
        <div className="mt-5 flex flex-wrap items-center justify-center gap-3">
          <Link to="/goal">
            <Button size="lg" variant="secondary">
              Back to the build hub
            </Button>
          </Link>
          <Link to="/goal/chatbot-eval">
            <Button size="lg" variant="tertiary">
              See the chatbot eval loop
            </Button>
          </Link>
        </div>
      </section>
    </GoalShell>
  )
}

const THE_BAR_FALLBACK =
  'An AI surface is good when it is good measurably — a golden set it must pass, a judge ' +
  'calibrated to humans, a gate that blocks any regression or safety / no-fabrication breach ' +
  'before it ships. One harness proves it for every surface; only the cases and the rubric differ.'
