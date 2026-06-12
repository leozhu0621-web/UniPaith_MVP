/**
 * Apply → Prompts → "Major-specific readiness" view (Spec 43 §3.18 / §4.18).
 *
 * The per-discipline readiness layer: a student picks the track(s) that match
 * their major (inferred from their academic record, or chosen manually), rates
 * their readiness across that field's areas, and gets a fit score, coverage map,
 * and suggested artifacts back from the deterministic MajorTrackCoach. Companion
 * to the behavioral Prompt Library (Spec 42). Feedback-only: we score and surface
 * gaps; we never fill the field in for the student.
 */
import { useMemo, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Compass } from 'lucide-react'

import { getCatalog, getSummary, getTracks, upsertTrack } from '../../../../api/major-specific'
import Card from '../../../../components/ui/Card'
import { showToast } from '../../../../stores/toast-store'
import type { TrackSignals } from '../../../../types/majorSpecific'

import TrackForm from './TrackForm'
import TrackReadinessHeader from './TrackReadinessHeader'
import TrackSelector from './TrackSelector'

export default function MajorSpecificPanel() {
  const qc = useQueryClient()
  const catalog = useQuery({ queryKey: ['major-specific', 'catalog'], queryFn: getCatalog })
  const tracks = useQuery({ queryKey: ['major-specific', 'tracks'], queryFn: getTracks })
  const summary = useQuery({ queryKey: ['major-specific', 'summary'], queryFn: getSummary })

  const [selected, setSelected] = useState<string | null>(null)

  const rowsByKey = useMemo(
    () => new Map((tracks.data?.tracks ?? []).map(t => [t.track_key, t])),
    [tracks.data],
  )
  const fitScores = useMemo(() => {
    const m: Record<string, number> = {}
    for (const t of tracks.data?.tracks ?? []) {
      if (t.coach) m[t.track_key] = t.coach.major_track_fit_score
    }
    return m
  }, [tracks.data])

  const save = useMutation({
    mutationFn: (vars: { trackKey: string; signals: TrackSignals }) =>
      upsertTrack(vars.trackKey, vars.signals),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['major-specific', 'tracks'] })
      qc.invalidateQueries({ queryKey: ['major-specific', 'summary'] })
    },
    onError: (e: unknown) =>
      showToast((e as Error)?.message ?? 'Could not save your readiness.', 'error'),
  })

  if (catalog.isLoading || tracks.isLoading) return <LoadingSkeleton />
  if (catalog.isError || !catalog.data) {
    return (
      <Card className="text-sm text-foreground">
        We couldn&apos;t load the major-specific catalog just now. Please refresh in a moment.
      </Card>
    )
  }

  const activeKeys = tracks.data?.active_tracks ?? []
  const suggestedKeys = tracks.data?.suggested_tracks ?? catalog.data.suggested_tracks ?? []
  // Default selection: the strongest started track, else first started, else
  // first suggested, else the first catalog track.
  const fallback =
    summary.data?.primary_track ??
    activeKeys[0] ??
    suggestedKeys[0] ??
    catalog.data.tracks[0]?.track_key
  const sel = selected ?? fallback
  const schema = catalog.data.tracks.find(t => t.track_key === sel)
  const row = sel ? rowsByKey.get(sel) : undefined

  return (
    <div className="space-y-5">
      <header>
        <h3 className="flex items-center gap-2 text-h3 text-foreground">
          <Compass size={18} /> Major-specific readiness
        </h3>
        <p className="mt-1 text-sm text-muted-foreground">
          Rate your readiness in the field you&apos;re targeting. We score your fit, map your
          coverage, and suggest what evidence to add — we never fill it in for you.
        </p>
      </header>

      <TrackSelector
        catalog={catalog.data.tracks}
        activeKeys={activeKeys}
        suggestedKeys={suggestedKeys}
        fitScores={fitScores}
        selected={sel ?? ''}
        onSelect={setSelected}
      />

      {schema ? (
        <>
          {row?.coach && <TrackReadinessHeader coach={row.coach} />}
          <TrackForm
            key={`${sel}:${row?.record_version ?? 0}`}
            schema={schema}
            initialSignals={row?.signals ?? {}}
            saving={save.isPending}
            onSave={signals => save.mutate({ trackKey: schema.track_key, signals })}
          />
        </>
      ) : (
        <Card pad={false} variant="card-flush" className="px-4 py-10 text-center text-sm text-muted-foreground">
          Pick a track above to start rating your readiness.
        </Card>
      )}
    </div>
  )
}

function LoadingSkeleton() {
  return (
    <div className="space-y-4">
      <div className="h-8 w-64 animate-pulse rounded bg-muted" />
      <div className="flex gap-2">
        {Array.from({ length: 4 }).map((_, i) => (
          <div key={i} className="h-9 w-32 animate-pulse rounded-full bg-muted" />
        ))}
      </div>
      <div className="h-28 animate-pulse rounded-xl bg-muted" />
      <div className="h-64 animate-pulse rounded-xl bg-muted" />
    </div>
  )
}
