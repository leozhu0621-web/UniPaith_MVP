/**
 * Spec 09 — "Your matches" section on /s/explore.
 *
 * Ranked program matches with dual scores, reach/target/safer banding (§6,
 * toggle to a flat ranked list), the "Why this match" popover and probability
 * bands on each card (§4 / §4A), a "Refine priorities" entry (§5.2), and the
 * spec's empty / loading / cached-fallback states (§8).
 */
import { useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Compass, LayoutGrid, ListFilter, Loader2, RefreshCw, SlidersHorizontal } from 'lucide-react'

import { getMatches, refreshMatches } from '../../../api/matching'
import BandBadge from '../../../components/ui/BandBadge'
import Button from '../../../components/ui/Button'
import Coachmark from '../../../components/ui/Coachmark'
import QueryError from '../../../components/ui/QueryError'
import { SkeletonCard } from '../../../components/ui/Skeleton'
import { useCompareStore } from '../../../stores/compare-store'
import { showToast } from '../../../stores/toast-store'
import type { MatchBand, MatchResultDual } from '../../../types'
import MatchCard from './MatchCard'
import { useAppliedPrograms } from '../explore/cards/AppStatusPill'
import PrioritySheet from './PrioritySheet'

const BAND_ORDER: MatchBand[] = ['reach', 'target', 'safer']

interface MatchesSectionProps {
  savedIds: Set<string>
  onToggleSave: (programId: string) => void
  /** Spec 2026-06-12 §6.4 — next upcoming event per institution, for the card event chips. */
  nextEventByInstitution?: Map<string, { event_name: string; start_time: string }>
  onEventClick?: () => void
  /** Discover review 2026-06-14 #5 — k-anon peer-cohort count per program_id. */
  peerCohortByProgram?: Record<string, number>
  onPeersClick?: () => void
  /** True when the student has an active strategy — drives the strategy→matches
   *  bridge line (the matches are banded off the strategy; refine it to update them). */
  strategyActive?: boolean
}

function relativeTime(iso?: string | null): string {
  if (!iso) return 'recently'
  const then = new Date(iso).getTime()
  if (!Number.isFinite(then)) return 'recently'
  const mins = Math.round((Date.now() - then) / 60000)
  if (mins < 1) return 'just now'
  if (mins < 60) return `${mins} min ago`
  const hrs = Math.round(mins / 60)
  if (hrs < 24) return `${hrs}h ago`
  return `${Math.round(hrs / 24)}d ago`
}

export default function MatchesSection({ savedIds, onToggleSave, nextEventByInstitution, onEventClick, peerCohortByProgram, onPeersClick, strategyActive }: MatchesSectionProps) {
  const navigate = useNavigate()
  const qc = useQueryClient()
  const compareStore = useCompareStore()
  const [grouped, setGrouped] = useState(true)
  const [prioritiesOpen, setPrioritiesOpen] = useState(false)

  const {
    data: matches = [],
    isLoading,
    isError,
    dataUpdatedAt,
  } = useQuery({
    queryKey: ['matches'],
    queryFn: () => getMatches(),
    retry: 1,
    staleTime: 60_000,
  })

  const refreshMut = useMutation({
    mutationFn: refreshMatches,
    onSuccess: data => {
      qc.setQueryData(['matches'], data)
      showToast(
        data.length ? 'Matches refreshed.' : 'No matches yet — add more with Uni.',
        data.length ? 'success' : 'info',
      )
    },
    onError: (err: unknown) =>
      showToast((err as Error).message ?? 'Could not refresh matches.', 'error'),
  })

  const groups = useMemo(() => {
    const by: Record<MatchBand, MatchResultDual[]> = { reach: [], target: [], safer: [] }
    for (const m of matches) {
      const band = (m.band_label ?? 'target') as MatchBand
      ;(by[band] ?? by.target).push(m)
    }
    return by
  }, [matches])

  const firstId = matches[0]?.program_id
  const appliedMap = useAppliedPrograms()
  const renderCard = (m: MatchResultDual) => {
    const card = (
      <MatchCard
        match={m}
        saved={savedIds.has(m.program_id)}
        comparing={compareStore.has(m.program_id)}
        onSave={() => onToggleSave(m.program_id)}
        onCompare={() =>
          compareStore.has(m.program_id)
            ? compareStore.remove(m.program_id)
            : compareStore.add({
                program_id: m.program_id,
                program_name: m.program_name ?? 'Program',
                institution_name: m.institution_name ?? '',
                degree_type: m.degree_type ?? '',
              })
        }
        onView={() => navigate(`/s/programs/${m.program_id}`)}
        nextEvent={m.institution_id ? nextEventByInstitution?.get(m.institution_id) ?? null : null}
        onEventClick={onEventClick}
        peerCount={peerCohortByProgram?.[m.program_id]}
        onPeersClick={onPeersClick}
        appStatus={appliedMap.get(m.program_id)}
      />
    )
    // First-run coachmark on the top match's dual ring (Spec 81 §3.3).
    if (m.program_id === firstId) {
      return (
        <Coachmark
          key={m.program_id}
          id="dualring"
          title="Two scores, not one"
          body="The outer ring is fitness; the inner ring is confidence."
          placement="bottom"
        >
          {card}
        </Coachmark>
      )
    }
    return <div key={m.program_id}>{card}</div>
  }

  // ── Loading ──
  if (isLoading) {
    return (
      <section className="mb-6">
        <SectionHeader count={null} />
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 2xl:grid-cols-4 gap-4 [&>*]:min-w-0">
          {[0, 1, 2, 3, 4, 5].map(i => (
            <SkeletonCard key={i} />
          ))}
        </div>
      </section>
    )
  }

  // ── Error with no cached data → show QueryError (distinct from sparse-profile empty state) ──
  if (isError && matches.length === 0) {
    return (
      <section className="mb-6">
        <SectionHeader count={null} />
        <QueryError
          title="Couldn't reach the matching service"
          onRetry={() => refreshMut.mutate()}
        />
      </section>
    )
  }

  // ── Empty (no matches → profile too sparse / Discovery incomplete) ──
  if (matches.length === 0) {
    return (
      <section className="mb-6">
        <div className="rounded-xl border border-border bg-card p-6 text-center">
          <Compass size={28} className="mx-auto text-foreground/50 mb-3" />
          <p className="text-sm font-semibold text-foreground mb-4">No matches yet</p>
          <div className="flex items-center justify-center gap-2">
            <Button size="sm" onClick={() => navigate('/s')}>
              <Compass size={14} className="mr-1.5" /> Talk to Uni
            </Button>
            <Button
              size="sm"
              variant="tertiary"
              onClick={() => refreshMut.mutate()}
              loading={refreshMut.isPending}
            >
              <RefreshCw size={13} className="mr-1.5" /> Refresh matches
            </Button>
          </div>
        </div>
      </section>
    )
  }

  return (
    <section className="mb-6">
      <SectionHeader
        count={matches.length}
        grouped={grouped}
        onToggleGrouped={() => setGrouped(v => !v)}
        onRefresh={() => refreshMut.mutate()}
        refreshing={refreshMut.isPending}
        onRefinePriorities={() => setPrioritiesOpen(true)}
      />

      {/* Strategy → matches bridge. Only with an active strategy + matches present:
          names the honest relationship (matches are banded off the strategy, not
          ranked in this view) and puts Refine priorities right at the seam. */}
      {strategyActive && (
        <p className="-mt-1 mb-3 text-xs text-muted-foreground">
          These matches reflect your strategy.{' '}
          <button
            onClick={() => setPrioritiesOpen(true)}
            className="font-medium text-secondary hover:underline"
          >
            Refine priorities
          </button>{' '}
          to update them.
        </p>
      )}

      {/* AI-down cached fallback banner (§8). */}
      {isError && (
        <div className="mb-3 rounded-lg border border-warning/30 bg-warning-soft px-3 py-2 text-xs text-foreground">
          We couldn&apos;t reach the matching service. Showing cached matches from{' '}
          {relativeTime(dataUpdatedAt ? new Date(dataUpdatedAt).toISOString() : null)}.
        </div>
      )}

      {grouped ? (
        <div className="space-y-6">
          {BAND_ORDER.filter(b => groups[b].length > 0).map(band => (
            <div key={band}>
              <div className="flex items-center gap-2 mb-2.5">
                {/* One earned-gold beat as the band reveals (Ship B §2 milestone moment). */}
                <BandBadge band={band} className="animate-beat" />
                <span className="ml-auto text-[11px] text-muted-foreground">{groups[band].length}</span>
              </div>
              <div className="stagger-list grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 2xl:grid-cols-4 gap-4 [&>*]:min-w-0">
                {groups[band].map(renderCard)}
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="stagger-list grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 2xl:grid-cols-4 gap-4 [&>*]:min-w-0">
          {matches.map(renderCard)}
        </div>
      )}

      <PrioritySheet
        isOpen={prioritiesOpen}
        onClose={() => setPrioritiesOpen(false)}
        onSaved={() => refreshMut.mutate()}
      />
    </section>
  )
}

function SectionHeader({
  count,
  grouped,
  onToggleGrouped,
  onRefresh,
  refreshing,
  onRefinePriorities,
}: {
  count: number | null
  grouped?: boolean
  onToggleGrouped?: () => void
  onRefresh?: () => void
  refreshing?: boolean
  onRefinePriorities?: () => void
}) {
  return (
    <div className="flex items-center justify-between gap-3 mb-3 flex-wrap">
      <h2 className="text-base font-bold text-foreground">
        Your matches{count != null && <span className="text-muted-foreground font-normal"> · {count}</span>}
      </h2>
      <div className="flex items-center gap-1.5">
        {onRefinePriorities && (
          <button
            onClick={onRefinePriorities}
            className="inline-flex items-center gap-1.5 px-2.5 py-1.5 text-xs font-medium text-secondary hover:bg-secondary/5 rounded-lg transition-colors"
          >
            <SlidersHorizontal size={13} /> Refine priorities
          </button>
        )}
        {onToggleGrouped && (
          <button
            onClick={onToggleGrouped}
            className="inline-flex items-center gap-1.5 px-2.5 py-1.5 text-xs font-medium text-muted-foreground hover:bg-muted rounded-lg transition-colors"
            title={grouped ? 'Show as a flat ranked list' : 'Group by reach / target / safer'}
          >
            {grouped ? <ListFilter size={13} /> : <LayoutGrid size={13} />}
            {grouped ? 'Flat list' : 'Bands'}
          </button>
        )}
        {onRefresh && (
          <button
            onClick={onRefresh}
            disabled={refreshing}
            className="inline-flex items-center gap-1.5 px-2.5 py-1.5 text-xs font-medium text-muted-foreground hover:bg-muted rounded-lg transition-colors disabled:opacity-50"
          >
            {refreshing ? <Loader2 size={13} className="animate-spin" /> : <RefreshCw size={13} />}
            Refresh
          </button>
        )}
      </div>
    </div>
  )
}
