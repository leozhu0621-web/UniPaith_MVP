import { useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import {
  ArrowRight,
  CircleCheck,
  Compass,
  FileCode,
  Gauge,
  Layers,
  Network,
  Sparkles,
} from 'lucide-react'

import { getUxBenchmark } from '../../api/build'
import type { UxSurface } from '../../types/build'
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

// Spec 53 — the UX-benchmark & interaction-standards surface, read from
// GET /api/v1/build/ux-benchmark. Each surface carries its benchmark + build
// contract; the "backed by N live routes" count is resolved from the running
// route table, so the page proves each benchmarked surface is actually wired.
// The page is itself built to the bar it documents: skeletons (never a blank
// flash), motion via the design-system tokens, and keyboard-accessible filters.

// §1 — the experience bar. Static spec text, so the lede never flashes empty.
const THE_BAR =
  'A surface is "market-grade" when a user arriving from LinkedIn or Handshake ' +
  'notices no drop in responsiveness or polish: instant (optimistic) feedback, no ' +
  'blank states, smooth motion, forgiving inputs — the app already knew what they wanted.'

const BENCH_LABELS: Record<string, string> = {
  linkedin: 'LinkedIn',
  handshake: 'Handshake',
  chatgpt: 'ChatGPT',
  ats: 'ATS',
}

function SurfaceCard({ surface }: { surface: UxSurface }) {
  return (
    <Card pad={false} className="flex h-full flex-col gap-3 p-5">
      <div className="flex items-start justify-between gap-3">
        <h3 className="text-h3 leading-snug text-foreground">{surface.name}</h3>
        <span
          className="inline-flex shrink-0 items-center gap-1 rounded-pill bg-secondary/10 px-2 py-0.5 text-[11px] font-semibold text-secondary"
          title="Endpoints backing this surface, counted live from the running route table"
        >
          <Network size={11} />
          {surface.backed_route_count} live routes
        </span>
      </div>

      <div className="flex flex-wrap items-center gap-1.5">
        <Chip tone="cobalt">vs {surface.benchmark}</Chip>
        {surface.specs.map(s => (
          <Chip key={s} tone="neutral">
            Spec {s}
          </Chip>
        ))}
      </div>

      <ul className="space-y-1.5">
        {surface.build_contract.map(item => (
          <li key={item} className="flex gap-2 text-sm text-muted-foreground">
            <span className="mt-2 h-1 w-1 shrink-0 rounded-full bg-secondary" aria-hidden />
            <span>{item}</span>
          </li>
        ))}
      </ul>

      <div className="mt-auto space-y-1 pt-1">
        <p className="flex items-center gap-1.5 text-[12px] text-muted-foreground">
          <FileCode size={13} className="shrink-0 text-secondary" />
          <span className="font-mono">{surface.files.join(' · ')}</span>
        </p>
        {surface.sample_paths[0] && (
          <p className="truncate font-mono text-[11px] text-muted-foreground/80">
            e.g. {surface.sample_paths[0]}
          </p>
        )}
      </div>
    </Card>
  )
}

export default function ExperienceStandardsPage() {
  usePageTitle('Experience standards · Spec 53')
  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ['build-ux-benchmark'],
    queryFn: getUxBenchmark,
    staleTime: 5 * 60_000,
  })

  const [bench, setBench] = useState('all')

  const surfaces = useMemo(() => {
    const list = data?.surfaces ?? []
    return bench === 'all' ? list : list.filter(s => s.benchmark_key === bench)
  }, [data, bench])

  const benchFilters = useMemo(() => {
    const keys = data?.summary.benchmark_keys ?? []
    return [{ key: 'all', label: 'All' }, ...keys.map(k => ({ key: k, label: BENCH_LABELS[k] ?? k }))]
  }, [data])

  return (
    <GoalShell>
      <Hero
        eyebrow="Experience standards · Spec 53"
        title="Built to the LinkedIn / Handshake bar."
        lede={THE_BAR}
      >
        {data && (
          <span className="inline-flex items-center gap-1.5 rounded-pill border border-primary/40 px-3 py-1 text-[13px] font-semibold text-foreground">
            <span className="h-1.5 w-1.5 rounded-full bg-primary" aria-hidden />
            {data.summary.backed_route_total} live routes back these surfaces
          </span>
        )}
        <a
          href="#surfaces"
          className="inline-flex items-center gap-1 text-[13px] font-semibold text-secondary hover:underline"
        >
          Jump to the surfaces <ArrowRight size={14} />
        </a>
      </Hero>

      {/* Headline stats */}
      <StatBand>
        {isLoading || !data ? (
          [0, 1, 2, 3].map(i => <StatSkeleton key={i} />)
        ) : (
          <>
            <Stat value={data.summary.surface_count} label="Benchmarked surfaces" />
            <Stat value={data.summary.standard_count} label="Interaction standards" />
            <Stat
              value={
                <span className="inline-flex items-center gap-1.5">
                  <Network className="text-secondary" size={24} />
                  {data.summary.backed_route_total}
                </span>
              }
              label="Live routes backing them"
            />
            <Stat value={data.summary.acceptance_count} label="Acceptance checks" />
          </>
        )}
      </StatBand>

      {/* §2 — per-surface build contracts */}
      <section id="surfaces" className="mt-16 scroll-mt-20">
        <SectionHeading
          icon={Layers}
          title="Every surface, benchmarked"
          sub="Each surface is held to a named competitor and tied to the real page file it lives in. The route count is read live from the running app — proof the surface is actually wired, not just specced."
        />

        <div className="mt-6">
          <FilterRow options={benchFilters} value={bench} onChange={setBench} />
        </div>

        {isError ? (
          <ErrorState
            onRetry={() => refetch()}
            label="We couldn't load the experience standards just now."
          />
        ) : (
          <>
            {data && (
              <p className="mt-5 text-sm text-muted-foreground">
                Showing {surfaces.length} of {data.summary.surface_count} surfaces
              </p>
            )}
            <div className="mt-3 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {data
                ? surfaces.map(s => <SurfaceCard key={s.key} surface={s} />)
                : [0, 1, 2, 3, 4, 5].map(i => <CardSkeleton key={i} className="h-64" />)}
            </div>
            {data && surfaces.length === 0 && (
              <p className="mt-6 text-center text-muted-foreground">
                No surfaces match this benchmark.
              </p>
            )}
          </>
        )}
      </section>

      {/* §3 — interaction standards */}
      <section className="mt-16">
        <SectionHeading
          icon={Sparkles}
          title="Interaction standards — applied everywhere"
          sub="Each standard maps to a concrete frontend mechanism (specs 54 / 56 / 57) so the bar is enforced in code, not aspiration."
        />
        <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {data
            ? data.standards.map(s => (
                <Card pad={false} key={s.title} className="flex h-full flex-col gap-2 p-5">
                  <h3 className="text-h3 text-foreground">{s.title}</h3>
                  <p className="text-sm text-muted-foreground">{s.body}</p>
                  <div className="mt-auto pt-1">
                    <Chip tone="neutral">{s.mechanism}</Chip>
                  </div>
                </Card>
              ))
            : [0, 1, 2, 3, 4, 5].map(i => <CardSkeleton key={i} className="h-36" />)}
        </div>
      </section>

      {/* §4 — empty / first-run polish */}
      <section className="mt-16">
        <SectionHeading
          icon={Compass}
          title="First-run polish"
          sub="The highest-churn moment. Every surface ships a real empty-state component, not a generic “no data”."
        />
        <Card pad={false} className="mt-6 p-6">
          <p className="text-foreground">{data?.empty_state.rule ?? ''}</p>
          {!data && <div className="h-5 w-3/4 animate-pulse rounded bg-muted" />}
          <div className="mt-5 grid gap-4 sm:grid-cols-2">
            {(data?.empty_state.first_run ?? []).map(fr => (
              <div
                key={fr.side}
                className="rounded-lg border border-border bg-background p-4"
              >
                <Chip tone="cobalt">{fr.side === 'student' ? 'Student' : 'Institution'}</Chip>
                <p className="mt-2 text-sm text-foreground">
                  First run → <span className="font-semibold">{fr.to}</span>
                </p>
                <p className="mt-1 font-mono text-[12px] text-muted-foreground">{fr.file}</p>
              </div>
            ))}
          </div>
        </Card>
      </section>

      {/* §5 — acceptance */}
      <section className="mt-16">
        <SectionHeading
          icon={CircleCheck}
          title="Acceptance"
          sub="A surface ships when it passes a side-by-side click test against its named competitor — no drop the visitor can feel."
        />
        <Card pad={false} className="mt-6 p-6">
          <ul className="space-y-3">
            {(data?.acceptance ?? []).map(item => (
              <li key={item} className="flex gap-3 text-sm text-foreground">
                <CircleCheck
                  size={18}
                  className="mt-0.5 shrink-0 text-success dark:text-success-dark"
                />
                <span>{item}</span>
              </li>
            ))}
            {!data &&
              [0, 1, 2, 3].map(i => (
                <li key={i} className="h-5 w-2/3 animate-pulse rounded bg-muted" />
              ))}
          </ul>
        </Card>
      </section>

      {/* Closing — the page practices what it documents */}
      <section className="mt-16 rounded-xl border border-border bg-card p-8 text-center">
        <p className="inline-flex items-center justify-center gap-2 text-h2 text-foreground">
          <Gauge className="text-secondary" size={24} />
          Built to the bar it documents.
        </p>
        <p className="mx-auto mt-2 max-w-xl text-muted-foreground">
          Skeleton-loaded, never a blank flash; motion on the design-system tokens with
          reduced-motion honored; keyboard-accessible filters. The route counts above are read
          live from the running API.
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
