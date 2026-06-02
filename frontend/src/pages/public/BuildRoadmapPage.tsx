import { useMemo, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { CircleCheck, Clock, Layers, Map as MapIcon } from 'lucide-react'

import { getRoadmap } from '../../api/build'
import type { RoadmapPhase } from '../../types/build'
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

// Spec 48 — the phased build roadmap, read from GET /api/v1/build/roadmap.
// Phases 1–13 are the MVP; phase 14 is the explicitly-deferred bucket.

function statusChip(status: string) {
  return status === 'shipped' ? (
    <Chip tone="success" icon={CircleCheck}>
      Shipped
    </Chip>
  ) : (
    <Chip tone="neutral" icon={Clock}>
      Deferred
    </Chip>
  )
}

function PhaseCard({ phase }: { phase: RoadmapPhase }) {
  const shipped = phase.status === 'shipped'
  return (
    <Card
      variant={shipped ? 'card' : 'card-flush'}
      className="flex flex-col gap-3 p-5 sm:flex-row sm:gap-5"
    >
      {/* Number badge */}
      <div className="shrink-0">
        <div
          className={
            'flex h-10 w-10 items-center justify-center rounded-full text-h3 font-semibold ' +
            (shipped
              ? 'bg-success-soft text-success dark:bg-success-dark-soft dark:text-success-dark'
              : 'bg-muted text-muted-foreground')
          }
        >
          {phase.number}
        </div>
      </div>

      <div className="min-w-0 flex-1">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <h3 className="text-h3 text-foreground">{phase.title}</h3>
          <div className="flex items-center gap-1.5">
            {statusChip(phase.status)}
            <Chip tone="cobalt" icon={Layers}>
              {phase.workstream}
            </Chip>
          </div>
        </div>

        <p className="mt-2 text-sm text-muted-foreground">{phase.goal}</p>

        <p className="mt-3 flex items-start gap-1.5 text-sm text-foreground">
          <CircleCheck
            size={15}
            className={
              'mt-0.5 shrink-0 ' +
              (shipped ? 'text-success dark:text-success-dark' : 'text-muted-foreground')
            }
          />
          <span className="text-muted-foreground">
            <span className="font-semibold text-foreground">
              {shipped ? 'Evidence: ' : 'Plan: '}
            </span>
            {phase.evidence}
          </span>
        </p>

        <div className="mt-3 flex flex-wrap items-center gap-1.5">
          {phase.specs.map(s => (
            <Chip key={s} tone="neutral">
              Spec {s}
            </Chip>
          ))}
          {phase.gap_items.map(g => (
            <Chip key={g} tone="cobalt">
              {g}
            </Chip>
          ))}
          <span className="text-[11px] text-muted-foreground">· {phase.effort}</span>
        </div>
      </div>
    </Card>
  )
}

const WORKSTREAM_FILTERS = [
  { key: 'all', label: 'All workstreams' },
  { key: 'Frontend', label: 'Frontend' },
  { key: 'Backend', label: 'Backend' },
  { key: 'Data', label: 'Data' },
  { key: 'Cross-cutting', label: 'Cross-cutting' },
]
const STATUS_FILTERS = [
  { key: 'all', label: 'All' },
  { key: 'shipped', label: 'Shipped' },
  { key: 'deferred', label: 'Deferred' },
]

export default function BuildRoadmapPage() {
  usePageTitle('Build roadmap · Spec 48')
  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ['build-roadmap'],
    queryFn: getRoadmap,
    staleTime: 5 * 60_000,
  })

  const [workstream, setWorkstream] = useState('all')
  const [status, setStatus] = useState('all')

  const phases = useMemo(() => {
    const list = data?.phases ?? []
    return list.filter(
      p =>
        (workstream === 'all' || p.workstream === workstream) &&
        (status === 'all' || p.status === status),
    )
  }, [data, workstream, status])

  return (
    <GoalShell>
      <Hero
        eyebrow="The build roadmap · Spec 48"
        title="From MVP to the master-paper spec, in 14 phases."
        lede="Each phase is one focused session — brand, the Claude migration, the data spine, dual-score matching, fairness, Connect and more. Phases 1–13 are the MVP; phase 14 is the explicitly-deferred up-market bucket."
      />

      <StatBand>
        {isLoading || !data ? (
          [0, 1, 2, 3].map(i => <StatSkeleton key={i} />)
        ) : (
          <>
            <Stat value={data.summary.phase_count} label="Phases planned" />
            <Stat
              value={
                <span className="inline-flex items-center gap-1.5">
                  <CircleCheck className="text-success dark:text-success-dark" size={26} />
                  {data.summary.shipped}
                </span>
              }
              label="Phases shipped"
            />
            <Stat value={data.summary.deferred} label="Deferred (post-MVP)" />
            <Stat value={data.summary.mvp_complete ? 'Yes' : 'No'} label="MVP (1–13) complete" />
          </>
        )}
      </StatBand>

      <section className="mt-16">
        <SectionHeading
          icon={MapIcon}
          title="The phases, in order"
          sub="The critical path runs top to bottom; some workstreams ran in parallel. Each card shows what, in the live build, demonstrates its status."
        />

        <div className="mt-6 flex flex-col gap-3">
          <FilterRow options={WORKSTREAM_FILTERS} value={workstream} onChange={setWorkstream} />
          <FilterRow options={STATUS_FILTERS} value={status} onChange={setStatus} />
        </div>

        {isError ? (
          <ErrorState onRetry={() => refetch()} label="We couldn't load the roadmap just now." />
        ) : (
          <>
            {data && (
              <p className="mt-5 text-sm text-muted-foreground">
                Showing {phases.length} of {data.summary.phase_count} phases
              </p>
            )}
            <div className="mt-3 flex flex-col gap-3">
              {data
                ? phases.map(p => <PhaseCard key={p.number} phase={p} />)
                : [0, 1, 2, 3, 5].map(i => <CardSkeleton key={i} className="h-32" />)}
            </div>
            {data && phases.length === 0 && (
              <p className="mt-6 text-center text-muted-foreground">No phases match this filter.</p>
            )}
          </>
        )}
      </section>
    </GoalShell>
  )
}
