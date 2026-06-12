import { useMemo, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { CircleCheck, Clock, GraduationCap, ListChecks, Sparkles, Building2 } from 'lucide-react'

import { getFeatureCatalog } from '../../api/build'
import type { FeatureItem } from '../../types/build'
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

// Spec 49 — the Feature-List V1 coverage map, read from GET /api/v1/build/features.
// Two axes: `klass` (the MVP plan — core/extend/defer) and `delivered` (live now).
// Where they differ, the build shipped ahead of the plan.

const STATUS_TONE = { covered: 'neutral', written: 'cobalt', net_new: 'warning' } as const

function FeatureCard({ feature }: { feature: FeatureItem }) {
  const aheadOfPlan = feature.klass === 'defer' && feature.delivered
  return (
    <Card pad={false} className="flex h-full flex-col gap-2 p-4">
      <div className="flex items-start justify-between gap-2">
        <h3 className="text-[15px] font-semibold leading-snug text-foreground">{feature.name}</h3>
        {feature.delivered ? (
          <span
            className="inline-flex shrink-0 items-center gap-1 text-[11px] font-semibold text-success dark:text-success-dark"
            title="In the live build"
          >
            <CircleCheck size={14} /> Live
          </span>
        ) : (
          <span className="inline-flex shrink-0 items-center gap-1 text-[11px] font-semibold text-muted-foreground">
            <Clock size={14} /> Planned
          </span>
        )}
      </div>

      <div className="mt-auto flex flex-wrap items-center gap-1.5 pt-1">
        <Chip tone={feature.klass === 'core' ? 'cobalt' : 'neutral'}>{feature.klass_label}</Chip>
        <Chip tone={STATUS_TONE[feature.status]}>{feature.status_label}</Chip>
        <Chip tone="neutral">Spec {feature.spec}</Chip>
        {aheadOfPlan && (
          <Chip tone="gold" icon={Sparkles}>
            Ahead of plan
          </Chip>
        )}
      </div>

      {feature.note && <p className="text-[12px] text-muted-foreground">{feature.note}</p>}
    </Card>
  )
}

const SIDE_FILTERS = [
  { key: 'all', label: 'All' },
  { key: 'student', label: 'Student' },
  { key: 'institution', label: 'Institution' },
]
const KLASS_FILTERS = [
  { key: 'all', label: 'All tiers' },
  { key: 'core', label: 'Core' },
  { key: 'extend', label: 'Extend' },
  { key: 'defer', label: 'Defer' },
]

export default function FeatureBacklogPage() {
  usePageTitle('Feature coverage · Spec 49')
  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ['build-features'],
    queryFn: getFeatureCatalog,
    staleTime: 5 * 60_000,
  })

  const [side, setSide] = useState('all')
  const [klass, setKlass] = useState('all')

  const features = useMemo(() => {
    const list = data?.features ?? []
    return list.filter(
      f => (side === 'all' || f.side === side) && (klass === 'all' || f.klass === klass),
    )
  }, [data, side, klass])

  return (
    <GoalShell>
      <Hero
        eyebrow="Feature coverage · Spec 49"
        title="Every feature on the founder's list — mapped, nothing dropped."
        lede="Each feature is tied to the spec that covers it (or flagged net-new) and classified core, extend or defer for the MVP cut. A second axis shows what's actually live today — which, for a few up-market items, is ahead of the plan."
      >
        {data && data.summary.ahead_of_plan > 0 && (
          <span className="inline-flex items-center gap-1.5 rounded-pill border border-primary/40 px-3 py-1 text-[13px] font-semibold text-foreground">
            <span className="h-1.5 w-1.5 rounded-full bg-primary" aria-hidden />
            {data.summary.ahead_of_plan} shipped ahead of plan
          </span>
        )}
      </Hero>

      <StatBand>
        {isLoading || !data ? (
          [0, 1, 2, 3].map(i => <StatSkeleton key={i} />)
        ) : (
          <>
            <Stat value={data.summary.feature_count} label="Features mapped" />
            <Stat
              value={
                <span className="inline-flex items-center gap-1.5">
                  <CircleCheck className="text-success dark:text-success-dark" size={26} />
                  {data.summary.mvp_delivered}/{data.summary.mvp_scope_count}
                </span>
              }
              label="MVP features delivered"
            />
            <Stat value={data.summary.delivered} label="Total features live" />
            <Stat value={data.summary.klass_counts.core ?? 0} label="Core features" />
          </>
        )}
      </StatBand>

      <section className="mt-16">
        <SectionHeading
          icon={ListChecks}
          title="The coverage map"
          sub="Core + extend make up the MVP cut; defer is real product scope held for later. Use the filters to slice by side and tier."
        />

        <div className="mt-6 flex flex-col gap-3">
          <FilterRow options={SIDE_FILTERS} value={side} onChange={setSide} />
          <FilterRow options={KLASS_FILTERS} value={klass} onChange={setKlass} />
        </div>

        {isError ? (
          <ErrorState onRetry={() => refetch()} label="We couldn't load the feature map just now." />
        ) : (
          <>
            {data && (
              <p className="mt-5 flex items-center gap-2 text-sm text-muted-foreground">
                {side === 'institution' ? (
                  <Building2 size={15} className="text-secondary" />
                ) : side === 'student' ? (
                  <GraduationCap size={15} className="text-secondary" />
                ) : null}
                Showing {features.length} of {data.summary.feature_count} features
              </p>
            )}
            <div className="mt-3 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
              {data
                ? features.map(f => <FeatureCard key={`${f.side}-${f.name}`} feature={f} />)
                : [0, 1, 2, 3, 4, 5].map(i => <CardSkeleton key={i} className="h-28" />)}
            </div>
            {data && features.length === 0 && (
              <p className="mt-6 text-center text-muted-foreground">No features match this filter.</p>
            )}
          </>
        )}
      </section>
    </GoalShell>
  )
}
