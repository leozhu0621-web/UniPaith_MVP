import { useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import {
  ArrowRight,
  CircleCheck,
  Compass,
  Database,
  FileCode,
  Gauge,
  Layers,
  ListChecks,
  Network,
  Radio,
  ShieldCheck,
  Sparkles,
} from 'lucide-react'

import { getFrontendStandards } from '../../api/build'
import { qk } from '../../api/queryKeys'
import type { BuildTaskStatus, FrontendBuildTask } from '../../types/build'
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
  type Tone,
} from './goalUi'

// Spec 54 — the frontend-engineering build spec, read from
// GET /build/frontend-standards. The narrative (rules, budgets, build-task
// status) is authored from spec 54; the §5 api-module ↔ router parity counts
// are resolved live from the running route table.
//
// The page's own self-verifying hook — the frontend analog of the backend
// reading its route table: it counts ITS OWN modules at build time via
// import.meta.glob (eager:false → paths only, nothing executed), and confirms
// each fe-verifiable build artifact actually exists in the running bundle. So
// the "in bundle" badges are read from the deployed app, not asserted.

const API_GLOB = import.meta.glob('../../api/*.ts')
const STORE_GLOB = import.meta.glob('../../stores/*.ts')
const HOOK_GLOB = import.meta.glob('../../hooks/*.ts')
const LIB_GLOB = import.meta.glob('../../lib/*.ts')
const TYPE_GLOB = import.meta.glob('../../types/*.ts')

const LIVE = {
  apiModules: Object.keys(API_GLOB).length,
  stores: Object.keys(STORE_GLOB).length,
  hooks: Object.keys(HOOK_GLOB).length,
  lib: Object.keys(LIB_GLOB).length,
}

// Normalize a glob key ('../../api/x.ts' or '/abs/.../src/api/x.ts') to the
// 'src/api/x.ts' shape the backend reports as a build-task artifact.
function toSrcPath(key: string): string {
  if (key.includes('/src/')) return `src/${key.split('/src/')[1]}`
  return `src/${key.replace(/^(\.\.\/)+/, '')}`
}

const PRESENT_FILES = new Set(
  [
    ...Object.keys(API_GLOB),
    ...Object.keys(HOOK_GLOB),
    ...Object.keys(LIB_GLOB),
    ...Object.keys(TYPE_GLOB),
  ].map(toSrcPath),
)

function isVerifiedInBundle(task: FrontendBuildTask): boolean {
  return task.fe_verifiable && task.artifact != null && PRESENT_FILES.has(task.artifact)
}

const STATUS_TONE: Record<BuildTaskStatus, Tone> = {
  done: 'success',
  partial: 'warning',
  planned: 'cobalt',
}
const STATUS_LABEL: Record<BuildTaskStatus, string> = {
  done: 'Done',
  partial: 'In progress',
  planned: 'Planned',
}

function CodeBlock({ children }: { children: string }) {
  return (
    <pre className="overflow-x-auto whitespace-pre rounded-lg border border-border bg-muted/50 p-4 font-mono text-[12px] leading-relaxed text-foreground">
      {children}
    </pre>
  )
}

function TaskCard({ task }: { task: FrontendBuildTask }) {
  const verified = isVerifiedInBundle(task)
  return (
    <Card pad={false} className="flex h-full flex-col gap-2 p-5">
      <div className="flex items-start justify-between gap-3">
        <h3 className="text-h3 leading-snug text-foreground">{task.title}</h3>
        <Chip tone={STATUS_TONE[task.status]}>{STATUS_LABEL[task.status]}</Chip>
      </div>
      <p className="text-sm text-muted-foreground">{task.evidence}</p>
      <div className="mt-auto space-y-1.5 pt-1">
        {task.artifact && (
          <p className="flex items-center gap-1.5 font-mono text-[11px] text-muted-foreground">
            <FileCode size={12} className="shrink-0 text-secondary" />
            {task.artifact}
          </p>
        )}
        {verified && (
          <span
            className="inline-flex items-center gap-1 rounded-pill bg-success-soft px-2 py-0.5 text-[11px] font-semibold text-success dark:bg-success-dark-soft dark:text-success-dark"
            title="Confirmed present in the running bundle via import.meta.glob"
          >
            <CircleCheck size={11} />
            Verified in bundle
          </span>
        )}
      </div>
    </Card>
  )
}

const FILTERS: { key: string; label: string }[] = [
  { key: 'all', label: 'All' },
  { key: 'done', label: 'Done' },
  { key: 'partial', label: 'In progress' },
  { key: 'planned', label: 'Planned' },
]

export default function FrontendStandardsPage() {
  usePageTitle('Frontend engineering · Spec 54')
  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: qk.buildFrontendStandards(),
    queryFn: getFrontendStandards,
    staleTime: 5 * 60_000,
  })

  const [filter, setFilter] = useState('all')

  const tasks = useMemo(() => {
    const list = data?.build_tasks ?? []
    return filter === 'all' ? list : list.filter((t) => t.status === filter)
  }, [data, filter])

  const verifiedCount = useMemo(
    () => (data?.build_tasks ?? []).filter(isVerifiedInBundle).length,
    [data],
  )

  return (
    <GoalShell>
      <Hero
        eyebrow="Frontend engineering · Spec 54"
        title="The build spec behind the React app."
        lede={
          data?.the_standard ??
          'A buildable engineering spec for the real frontend: typed api modules one-per-router, server state only in TanStack Query, one query-key factory, one optimistic-mutation shape, every route error-boundaried, and enforced Core-Web-Vitals budgets.'
        }
      >
        <span className="inline-flex items-center gap-1.5 rounded-pill border border-primary/40 px-3 py-1 text-[13px] font-semibold text-foreground">
          <span className="h-1.5 w-1.5 rounded-full bg-primary" aria-hidden />
          {LIVE.apiModules} api modules ↔ {data?.parity.live_router_count ?? '…'} live routers
        </span>
        <a
          href="#tasks"
          className="inline-flex items-center gap-1 text-[13px] font-semibold text-secondary hover:underline"
        >
          Jump to the build tasks <ArrowRight size={14} />
        </a>
      </Hero>

      {/* Headline — frontend self-counts (left) meet the live backend (right) */}
      <StatBand>
        {isLoading || !data ? (
          [0, 1, 2, 3].map((i) => <StatSkeleton key={i} />)
        ) : (
          <>
            <Stat value={LIVE.apiModules} label="Typed api modules (live)" />
            <Stat value={LIVE.stores} label="Zustand stores (live)" />
            <Stat
              value={
                <span className="inline-flex items-center gap-1.5">
                  <Network className="text-secondary" size={24} />
                  {data.parity.live_router_count}
                </span>
              }
              label="Backend routers (live)"
            />
            <Stat
              value={`${data.summary.build_tasks_done}/${data.summary.build_task_count}`}
              label="Build tasks complete"
            />
          </>
        )}
      </StatBand>

      {/* §5 — api-module ↔ router parity, the self-verifying centerpiece */}
      <section id="parity" className="mt-16 scroll-mt-20">
        <SectionHeading
          icon={Network}
          title="One typed module per router"
          sub={data?.parity.statement}
        />
        <Card pad={false} className="mt-6 p-6">
          <div className="grid items-center gap-6 sm:grid-cols-[1fr_auto_1fr]">
            <div className="rounded-lg border border-border bg-background p-5">
              <Chip tone="cobalt">Frontend · this bundle</Chip>
              <dl className="mt-3 space-y-1.5 text-sm">
                <ParityRow label="Typed api modules" value={LIVE.apiModules} />
                <ParityRow label="Zustand stores" value={LIVE.stores} />
                <ParityRow label="Hooks" value={LIVE.hooks} />
                <ParityRow label="lib/ modules" value={LIVE.lib} />
              </dl>
              <p className="mt-3 text-[11px] text-muted-foreground">
                Counted at build time from import.meta.glob.
              </p>
            </div>

            <div className="flex items-center justify-center">
              <span className="text-h1 text-secondary" aria-hidden>
                ↔
              </span>
            </div>

            <div className="rounded-lg border border-border bg-background p-5">
              <Chip tone="cobalt">Backend · running routes</Chip>
              <dl className="mt-3 space-y-1.5 text-sm">
                <ParityRow label="Live routers" value={data?.parity.live_router_count ?? '…'} />
                <ParityRow label="Live routes" value={data?.parity.live_route_count ?? '…'} />
              </dl>
              <p className="mt-3 text-[11px] text-muted-foreground">
                Read live from the running route table (same source as the API-contract page).
              </p>
            </div>
          </div>
          {data && (
            <p className="mt-5 border-t border-border pt-4 text-sm text-muted-foreground">
              Spec 54 was drafted at {data.parity.doc_claimed_api_modules} api modules /{' '}
              {data.parity.doc_claimed_routers} routers; the live tree has grown past that. Both
              sides are counted from the running systems — neither number is asserted in a doc.
            </p>
          )}
        </Card>
      </section>

      {/* §12 — the build-task checklist, filterable + live-verified */}
      <section id="tasks" className="mt-16 scroll-mt-20">
        <SectionHeading
          icon={ListChecks}
          title="The build checklist — honestly scored"
          sub="Each task carries its real status and the artifact it produced. Where the artifact is a source file, the page confirms it's actually in the running bundle — done means done, not asserted."
        />

        <div className="mt-6 flex flex-wrap items-center justify-between gap-3">
          <FilterRow options={FILTERS} value={filter} onChange={setFilter} />
          {data && (
            <span className="text-sm text-muted-foreground">
              {verifiedCount} artifact{verifiedCount === 1 ? '' : 's'} verified in this bundle
            </span>
          )}
        </div>

        {isError ? (
          <ErrorState
            onRetry={() => refetch()}
            label="We couldn't load the frontend standards just now."
          />
        ) : (
          <>
            {data && (
              <p className="mt-5 text-sm text-muted-foreground">
                Showing {tasks.length} of {data.summary.build_task_count} tasks
              </p>
            )}
            <div className="mt-3 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {data
                ? tasks.map((t) => <TaskCard key={t.key} task={t} />)
                : [0, 1, 2, 3, 4, 5].map((i) => <CardSkeleton key={i} className="h-44" />)}
            </div>
            {data && tasks.length === 0 && (
              <p className="mt-6 text-center text-muted-foreground">No tasks in this state.</p>
            )}
          </>
        )}
      </section>

      {/* §2 — state layering */}
      <section className="mt-16">
        <SectionHeading
          icon={Database}
          title="State lives in exactly one place"
          sub={data?.state_build_rule}
        />
        <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {data
            ? data.state_rules.map((r) => (
                <Card pad={false} key={r.kind} className="flex h-full flex-col gap-2 p-5">
                  <h3 className="text-h3 text-foreground">{r.kind}</h3>
                  <Chip tone="cobalt">{r.tool}</Chip>
                  <p className="font-mono text-[11px] text-muted-foreground">{r.where}</p>
                  <p className="mt-auto pt-1 text-sm text-muted-foreground">{r.rule}</p>
                </Card>
              ))
            : [0, 1, 2, 3].map((i) => <CardSkeleton key={i} className="h-44" />)}
        </div>
      </section>

      {/* §3 / §4 — query-key + optimistic-mutation conventions */}
      <section className="mt-16">
        <SectionHeading
          icon={FileCode}
          title="Two conventions, applied everywhere"
          sub="A single key factory keeps caches reconcilable; one optimistic-mutation shape keeps every save instant and rollback-safe."
        />
        <div className="mt-6 grid gap-4 lg:grid-cols-2">
          <Card pad={false} className="flex flex-col gap-3 p-5">
            <h3 className="text-h3 text-foreground">Query keys — one factory</h3>
            <p className="text-sm text-muted-foreground">{data?.query_key.rule}</p>
            {data ? (
              <CodeBlock>{data.query_key.example}</CodeBlock>
            ) : (
              <div className="h-28 animate-pulse rounded-lg bg-muted" />
            )}
            <p className="text-[12px] text-muted-foreground">{data?.query_key.stale_time}</p>
          </Card>
          <Card pad={false} className="flex flex-col gap-3 p-5">
            <h3 className="text-h3 text-foreground">Optimistic mutations — one shape</h3>
            <p className="text-sm text-muted-foreground">{data?.mutation.rule}</p>
            {data ? (
              <CodeBlock>{data.mutation.shape}</CodeBlock>
            ) : (
              <div className="h-28 animate-pulse rounded-lg bg-muted" />
            )}
            <div className="flex flex-wrap gap-1.5">
              {(data?.mutation.surfaces ?? []).map((s) => (
                <Chip key={s} tone="neutral">
                  {s}
                </Chip>
              ))}
            </div>
          </Card>
        </div>
      </section>

      {/* §8 — performance budgets */}
      <section className="mt-16">
        <SectionHeading
          icon={Gauge}
          title="Core Web Vitals — budgeted, not hoped for"
          sub="Enforced via Lighthouse-CI (soft-fail first, then hard-gate)."
        />
        <div className="mt-6 grid gap-4 sm:grid-cols-3">
          {data
            ? data.perf_budgets.map((b) => (
                <Card pad={false} key={b.metric} className="flex h-full flex-col gap-1 p-5">
                  <span className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">
                    {b.metric}
                  </span>
                  <span className="text-h1 leading-none text-foreground">{b.target}</span>
                  <p className="mt-1 text-sm text-muted-foreground">{b.note}</p>
                </Card>
              ))
            : [0, 1, 2].map((i) => <CardSkeleton key={i} className="h-32" />)}
        </div>
        {data && (
          <ul className="mt-4 space-y-1.5">
            {data.perf_tactics.map((t) => (
              <li key={t} className="flex gap-2 text-sm text-muted-foreground">
                <span className="mt-2 h-1 w-1 shrink-0 rounded-full bg-secondary" aria-hidden />
                <span>{t}</span>
              </li>
            ))}
          </ul>
        )}
      </section>

      {/* §9 / §10 — realtime + analytics clients */}
      <section className="mt-16">
        <SectionHeading
          icon={Radio}
          title="Realtime + instrumentation"
          sub="Two net-new clients: a reconnecting realtime transport that patches the cache, and a consent-gated analytics bus."
        />
        <div className="mt-6 grid gap-4 lg:grid-cols-2">
          <Card pad={false} className="flex flex-col gap-2 p-5">
            <h3 className="inline-flex items-center gap-2 text-h3 text-foreground">
              <Radio size={18} className="text-secondary" />
              Realtime (SSE + WebSocket)
            </h3>
            <p className="text-sm text-muted-foreground">{data?.realtime.summary}</p>
            <ul className="space-y-1.5">
              {(data?.realtime.transports ?? []).map((t) => (
                <li key={t} className="flex gap-2 text-sm text-muted-foreground">
                  <span className="mt-2 h-1 w-1 shrink-0 rounded-full bg-secondary" aria-hidden />
                  <span>{t}</span>
                </li>
              ))}
            </ul>
            {data && (
              <p className="mt-auto pt-1 text-[12px] text-muted-foreground">
                {data.realtime.status}
              </p>
            )}
          </Card>
          <Card pad={false} className="flex flex-col gap-2 p-5">
            <h3 className="inline-flex items-center gap-2 text-h3 text-foreground">
              <Sparkles size={18} className="text-secondary" />
              Analytics event bus
            </h3>
            <p className="text-sm text-muted-foreground">{data?.analytics.summary}</p>
            <ul className="space-y-1.5">
              {(data?.analytics.rules ?? []).map((r) => (
                <li key={r} className="flex gap-2 text-sm text-muted-foreground">
                  <span className="mt-2 h-1 w-1 shrink-0 rounded-full bg-secondary" aria-hidden />
                  <span>{r}</span>
                </li>
              ))}
            </ul>
          </Card>
        </div>
      </section>

      {/* §6 / §7 / §11 — how it holds up */}
      <section className="mt-16">
        <SectionHeading
          icon={ShieldCheck}
          title="No white screens, no silent failures"
          sub="Routing guards, error boundaries, AI fallbacks and the testing bar that keeps them honest."
        />
        <div className="mt-6 grid gap-4 lg:grid-cols-3">
          <Card pad={false} className="flex flex-col gap-2 p-5">
            <h3 className="inline-flex items-center gap-2 text-h3 text-foreground">
              <Layers size={18} className="text-secondary" />
              Routing & boundaries
            </h3>
            <ul className="space-y-1.5">
              {(data?.routing ?? []).map((r) => (
                <li key={r} className="flex gap-2 text-sm text-muted-foreground">
                  <span className="mt-2 h-1 w-1 shrink-0 rounded-full bg-secondary" aria-hidden />
                  <span>{r}</span>
                </li>
              ))}
            </ul>
          </Card>
          <Card pad={false} className="flex flex-col gap-2 p-5">
            <h3 className="inline-flex items-center gap-2 text-h3 text-foreground">
              <ShieldCheck size={18} className="text-secondary" />
              Errors & AI fallback
            </h3>
            <p className="text-sm text-muted-foreground">{data?.error_handling.interceptor}</p>
            <p className="text-sm text-muted-foreground">{data?.error_handling.ai_fallback}</p>
          </Card>
          <Card pad={false} className="flex flex-col gap-2 p-5">
            <h3 className="inline-flex items-center gap-2 text-h3 text-foreground">
              <CircleCheck size={18} className="text-secondary" />
              Testing
            </h3>
            <ul className="space-y-1.5">
              {(data?.testing ?? []).map((t) => (
                <li key={t} className="flex gap-2 text-sm text-muted-foreground">
                  <span className="mt-2 h-1 w-1 shrink-0 rounded-full bg-secondary" aria-hidden />
                  <span>{t}</span>
                </li>
              ))}
            </ul>
          </Card>
        </div>
      </section>

      {/* §13 — acceptance */}
      <section className="mt-16">
        <SectionHeading
          icon={CircleCheck}
          title="Acceptance"
          sub="The frontend ships to spec when each of these holds."
        />
        <Card pad={false} className="mt-6 p-6">
          <ul className="space-y-3">
            {(data?.acceptance ?? []).map((item) => (
              <li key={item} className="flex gap-3 text-sm text-foreground">
                <CircleCheck size={18} className="mt-0.5 shrink-0 text-success dark:text-success-dark" />
                <span>{item}</span>
              </li>
            ))}
            {!data &&
              [0, 1, 2, 3].map((i) => (
                <li key={i} className="h-5 w-2/3 animate-pulse rounded bg-muted" />
              ))}
          </ul>
        </Card>
      </section>

      {/* §14 — open questions */}
      {data && data.open_questions.length > 0 && (
        <section className="mt-16">
          <SectionHeading
            icon={Compass}
            title="Open questions"
            sub="Decisions still on the table, with a recommended call."
          />
          <div className="mt-6 grid gap-4 sm:grid-cols-3">
            {data.open_questions.map((q) => (
              <Card pad={false} key={q.question} className="flex h-full flex-col gap-2 p-5">
                <h3 className="text-h3 leading-snug text-foreground">{q.question}</h3>
                <p className="text-sm text-muted-foreground">{q.recommendation}</p>
              </Card>
            ))}
          </div>
        </section>
      )}

      {/* Closing — the page practices what it documents */}
      <section className="mt-16 rounded-xl border border-border bg-card p-8 text-center">
        <p className="inline-flex items-center justify-center gap-2 text-h2 text-foreground">
          <Layers className="text-secondary" size={24} />
          Built to the spec it documents.
        </p>
        <p className="mx-auto mt-2 max-w-xl text-muted-foreground">
          Skeleton-loaded, error-boundaried, keyboard-accessible filters — and the module / router
          counts above are read live from the running frontend bundle and backend route table.
        </p>
        <div className="mt-5 flex flex-wrap items-center justify-center gap-3">
          <Link to="/goal">
            <Button size="lg" variant="secondary">
              Back to the build hub
            </Button>
          </Link>
          <Link to="/goal/experience">
            <Button size="lg" variant="tertiary">
              See the experience standards
            </Button>
          </Link>
        </div>
      </section>
    </GoalShell>
  )
}

function ParityRow({ label, value }: { label: string; value: number | string }) {
  return (
    <div className="flex items-baseline justify-between gap-3">
      <dt className="text-muted-foreground">{label}</dt>
      <dd className="text-h3 leading-none text-foreground">{value}</dd>
    </div>
  )
}
