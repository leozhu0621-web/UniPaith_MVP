import { useQuery } from '@tanstack/react-query'
import {
  Building2,
  Cable,
  CircleCheck,
  Clock,
  FlaskConical,
  GraduationCap,
  ListChecks,
  Rocket,
  ShieldCheck,
  TableProperties,
} from 'lucide-react'

import { getAcceptance } from '../../api/build'
import type { AcceptanceJourney, AcceptanceLevel, LaunchBlocker, SignoffArea } from '../../types/build'
import Card from '../../components/ui/Card'
import usePageTitle from '../../hooks/usePageTitle'
import {
  CardSkeleton,
  Chip,
  ErrorState,
  GoalShell,
  Hero,
  SectionHeading,
  Stat,
  StatBand,
  StatSkeleton,
} from './goalUi'

// Spec 52 — the MVP acceptance & runbook. The readiness numbers come from
// GET /api/v1/build/acceptance, which reads the running system (routes, agents,
// schema, feature coverage); the launch-blocker statuses are evidence-backed.

const LEVEL_DOT: Record<string, string> = {
  green: 'bg-success dark:bg-success-dark',
  amber: 'bg-warning dark:bg-warning-dark',
  red: 'bg-warning dark:bg-warning-dark',
}

const JOURNEY_ICON: Record<string, typeof GraduationCap> = {
  student: GraduationCap,
  institution: Building2,
}

function LevelCard({ level }: { level: AcceptanceLevel }) {
  return (
    <Card className="flex flex-col gap-2 p-5">
      <div className="flex items-center justify-between">
        <span className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">
          Level {level.order}
        </span>
        <span className="inline-flex items-center gap-1.5 text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">
          <span className={`h-2 w-2 rounded-full ${LEVEL_DOT[level.status] ?? 'bg-muted'}`} aria-hidden />
          {level.status}
        </span>
      </div>
      <h3 className="text-h3 text-foreground">{level.title}</h3>
      <p className="text-sm text-muted-foreground">{level.body}</p>
      <p className="mt-auto pt-2 text-[13px] text-muted-foreground">
        <span className="font-semibold text-foreground">Live: </span>
        {level.evidence}
      </p>
    </Card>
  )
}

function JourneyCard({ journey }: { journey: AcceptanceJourney }) {
  const Icon = JOURNEY_ICON[journey.key] ?? GraduationCap
  return (
    <Card className="p-6">
      <div className="flex items-start justify-between gap-3">
        <h3 className="flex items-center gap-2 text-h3 text-foreground">
          <Icon size={20} className="text-secondary" />
          {journey.title}
        </h3>
        <Chip tone="neutral">Spec {journey.spec}</Chip>
      </div>
      <p className="mt-2 text-sm text-muted-foreground">{journey.blurb}</p>
      <ol className="mt-4 space-y-3">
        {journey.steps.map(s => (
          <li key={s.n} className="flex gap-3">
            <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-secondary/10 text-[12px] font-semibold text-secondary">
              {s.n}
            </span>
            <div className="min-w-0">
              <div className="flex flex-wrap items-center gap-2">
                <span className="text-[14px] font-semibold text-foreground">{s.title}</span>
                <Chip tone="cobalt">Spec {s.spec}</Chip>
              </div>
              <p className="mt-0.5 text-[13px] text-muted-foreground">{s.detail}</p>
            </div>
          </li>
        ))}
      </ol>
    </Card>
  )
}

function BlockerRow({ blocker }: { blocker: LaunchBlocker }) {
  const cleared = blocker.status === 'cleared'
  return (
    <li className="flex items-start gap-3 rounded-lg border border-border bg-card p-3">
      {cleared ? (
        <CircleCheck size={18} className="mt-0.5 shrink-0 text-success dark:text-success-dark" />
      ) : (
        <Clock size={18} className="mt-0.5 shrink-0 text-warning dark:text-warning-dark" />
      )}
      <div className="min-w-0">
        <div className="flex flex-wrap items-center gap-2">
          <span className="text-[14px] font-semibold text-foreground">{blocker.title}</span>
          <Chip tone="neutral">Spec {blocker.spec}</Chip>
          <Chip tone={cleared ? 'success' : 'warning'}>{cleared ? 'Cleared' : 'Deferred'}</Chip>
        </div>
        <p className="mt-1 text-[13px] text-muted-foreground">{blocker.evidence}</p>
      </div>
    </li>
  )
}

function SignoffCell({ ok, klass }: { ok: boolean; klass: string }) {
  if (klass !== 'core') return <span className="text-muted-foreground">—</span>
  return ok ? (
    <CircleCheck size={16} className="text-success dark:text-success-dark" aria-label="green" />
  ) : (
    <Clock size={16} className="text-warning dark:text-warning-dark" aria-label="not yet" />
  )
}

function SignoffMatrix({ rows }: { rows: SignoffArea[] }) {
  const KLASS_TONE = { core: 'cobalt', extend: 'neutral', excluded: 'neutral' } as const
  return (
    <div className="mt-4 overflow-hidden rounded-lg border border-border">
      <table className="w-full text-left text-sm">
        <thead className="bg-muted text-[11px] uppercase tracking-wider text-muted-foreground">
          <tr>
            <th className="px-3 py-2 font-semibold">Area</th>
            <th className="px-3 py-2 font-semibold">Class</th>
            <th className="px-3 py-2 text-center font-semibold">Boots</th>
            <th className="px-3 py-2 text-center font-semibold">Path</th>
            <th className="px-3 py-2 text-center font-semibold">DoD</th>
          </tr>
        </thead>
        <tbody>
          {rows.map(r => (
            <tr key={r.area} className="border-t border-border">
              <td className="px-3 py-2 text-muted-foreground">
                {r.area}
                {r.path_ref !== '—' && (
                  <span className="ml-1 text-[11px] text-muted-foreground">({r.path_ref})</span>
                )}
              </td>
              <td className="px-3 py-2">
                <Chip tone={KLASS_TONE[r.klass]}>{r.klass}</Chip>
              </td>
              <td className="px-3 py-2 text-center">
                <span className="inline-flex justify-center">
                  <SignoffCell ok={r.boots} klass={r.klass} />
                </span>
              </td>
              <td className="px-3 py-2 text-center">
                <span className="inline-flex justify-center">
                  <SignoffCell ok={r.critical_path} klass={r.klass} />
                </span>
              </td>
              <td className="px-3 py-2 text-center">
                <span className="inline-flex justify-center">
                  <SignoffCell ok={r.dod} klass={r.klass} />
                </span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

export default function AcceptancePage() {
  usePageTitle('Acceptance & runbook · Spec 52')
  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ['build-acceptance'],
    queryFn: getAcceptance,
    staleTime: 5 * 60_000,
  })

  return (
    <GoalShell>
      <Hero
        eyebrow="Acceptance & runbook · Spec 52"
        title="The definition of done — checked against the running system."
        lede="Three readiness levels, two end-to-end journeys, the launch-blocker checklist and the sign-off matrix. The readiness numbers are read live from the deployed app, so this is a scorecard, not a promise."
      >
        {data?.summary.launch_ready && (
          <span className="inline-flex items-center gap-1.5 rounded-pill border border-primary/40 px-3 py-1 text-[13px] font-semibold text-foreground">
            <span className="h-1.5 w-1.5 rounded-full bg-primary" aria-hidden />
            MVP-ready — all gates clear
          </span>
        )}
      </Hero>

      <StatBand>
        {isLoading || !data ? (
          [0, 1, 2, 3].map(i => <StatSkeleton key={i} />)
        ) : (
          <>
            <Stat
              value={
                <span className="inline-flex items-center gap-1.5">
                  <Rocket className="text-secondary" size={24} />
                  {data.summary.launch_blockers_cleared}/{data.summary.launch_blockers_total}
                </span>
              }
              label="Launch blockers cleared"
            />
            <Stat
              value={`${data.summary.core_areas_green}/${data.summary.core_areas_total}`}
              label="Core areas signed off"
            />
            <Stat
              value={`${data.summary.mvp_delivered}/${data.summary.mvp_scope_count}`}
              label="MVP features delivered"
            />
            <Stat value={data.summary.ai_endpoint_count} label="AI endpoints (never 5xx)" />
          </>
        )}
      </StatBand>

      {isError && (
        <ErrorState onRetry={() => refetch()} label="We couldn't load the acceptance runbook just now." />
      )}

      {/* §1 — the three readiness levels */}
      <section className="mt-16">
        <SectionHeading
          icon={Rocket}
          title="What 'ready to use' means"
          sub="Three levels, in order — don't move up until the lower is green."
        />
        <div className="mt-6 grid gap-4 lg:grid-cols-3">
          {data
            ? data.levels.map(l => <LevelCard key={l.key} level={l} />)
            : [0, 1, 2].map(i => <CardSkeleton key={i} className="h-44" />)}
        </div>
      </section>

      {/* §2 — the two critical-path journeys */}
      <section className="mt-16">
        <SectionHeading
          icon={GraduationCap}
          title="The critical paths"
          sub="A path is green only if every step works front and back — UI action → API call → DB write → UI reflects it — against the real backend."
        />
        <div className="mt-6 grid gap-4 lg:grid-cols-2">
          {data
            ? data.journeys.map(j => <JourneyCard key={j.key} journey={j} />)
            : [0, 1].map(i => <CardSkeleton key={i} className="h-96" />)}
        </div>
        {data && (
          <Card variant="card-flush" className="mt-4 flex items-start gap-3 p-4">
            <ShieldCheck size={18} className="mt-0.5 shrink-0 text-secondary" />
            <p className="text-sm text-muted-foreground">
              <span className="font-semibold text-foreground">Acceptance bar: </span>
              {data.acceptance_bar}
            </p>
          </Card>
        )}
      </section>

      {/* §5 — launch-blocker checklist */}
      <section className="mt-16">
        <SectionHeading
          icon={ShieldCheck}
          title="Launch-blocker checklist"
          sub="Hard gates — any one open means not launch-ready. Each names what, in the shipped build, demonstrates it."
        />
        <ul className="mt-6 grid gap-2 lg:grid-cols-2">
          {data
            ? data.launch_blockers.map(b => <BlockerRow key={b.title} blocker={b} />)
            : [0, 1, 2, 3, 4, 5].map(i => <CardSkeleton key={i} className="h-16" />)}
        </ul>
      </section>

      {/* §3 DoD + §4 integration gates */}
      <section className="mt-16 grid gap-8 lg:grid-cols-2">
        <div>
          <SectionHeading
            icon={ListChecks}
            title="Per-surface definition of done"
            sub="A surface is 'done' only when all of these hold — not just the happy path."
          />
          <ul className="mt-4 space-y-2">
            {(data?.dod ?? []).map(d => (
              <li key={d.text} className="flex items-start gap-2 rounded-lg border border-border bg-card p-3">
                <CircleCheck size={16} className="mt-0.5 shrink-0 text-secondary" />
                <span className="text-[13px] text-muted-foreground">
                  {d.text} <span className="text-[11px] text-muted-foreground">· {d.spec}</span>
                </span>
              </li>
            ))}
            {!data && [0, 1, 2, 3].map(i => <CardSkeleton key={i} className="h-12" />)}
          </ul>
        </div>

        <div>
          <SectionHeading
            icon={Cable}
            title="Front ↔ back integration gates"
            sub="Built individually, verified together."
          />
          <ul className="mt-4 space-y-2">
            {(data?.integration_gates ?? []).map(g => (
              <li key={g.title} className="rounded-lg border border-border bg-card p-3">
                <div className="flex flex-wrap items-center gap-2">
                  <span className="text-[14px] font-semibold text-foreground">{g.title}</span>
                  <Chip tone="cobalt">Spec {g.spec}</Chip>
                </div>
                <p className="mt-1 text-[13px] text-muted-foreground">{g.body}</p>
              </li>
            ))}
            {!data && [0, 1, 2, 3].map(i => <CardSkeleton key={i} className="h-16" />)}
          </ul>
        </div>
      </section>

      {/* §8 sign-off matrix */}
      <section className="mt-16">
        <SectionHeading
          icon={TableProperties}
          title="Sign-off matrix"
          sub="'MVP ready' = all core rows green. Extend and excluded rows are outside this gate."
        />
        {data ? <SignoffMatrix rows={data.signoff} /> : <CardSkeleton className="mt-4 h-64" />}
      </section>

      {/* §6 seed / demo data */}
      {data && (
        <section className="mt-16">
          <SectionHeading
            icon={FlaskConical}
            title="Seed / demo data"
            sub={data.seed.intro}
          />
          <div className="mt-6 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {data.seed.items.map(item => (
              <Card key={item.label} className="p-4">
                <h3 className="text-[14px] font-semibold text-foreground">{item.label}</h3>
                <p className="mt-1 text-[13px] text-muted-foreground">{item.detail}</p>
              </Card>
            ))}
          </div>
        </section>
      )}
    </GoalShell>
  )
}
