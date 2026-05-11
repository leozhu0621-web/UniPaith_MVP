/**
 * Stage 1 (Discovery) — student home page.
 *
 * Replaces CounselorHomePage at /s. Three-track journey: Profile / Goals
 * / Needs, each backed by `discovery_sessions` rows on the server. The
 * chat panel auto-creates a session on the first message; the artifact
 * rail live-updates as the LLM extractor writes signals into typed tables.
 *
 * When all three tracks reach the handoff threshold (50% for Phase B), a
 * "Generate strategy" CTA appears that bridges to Stage 2 (Match) — it
 * calls /me/strategy/generate and routes the student to the Strategy tab
 * in their profile.
 */
import { useEffect, useMemo, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { CheckCircle2, ChevronRight, Compass, Sparkles } from 'lucide-react'
import clsx from 'clsx'

import { getCompletionMap, listSessions } from '../../api/discovery'
import { generateStrategy } from '../../api/strategy'
import Button from '../../components/ui/Button'
import Card from '../../components/ui/Card'
import { showToast } from '../../stores/toast-store'
import type {
  CompletionMap,
  DiscoveryLayer,
  DiscoverySession,
  DiscoveryTrack,
} from '../../types'
import ArtifactRail from './discover/ArtifactRail'
import ChatPanel from './discover/ChatPanel'
import TrackSelector from './discover/TrackSelector'

const TRACK_KEYS: DiscoveryTrack[] = ['profile', 'goals', 'needs']
const HANDOFF_THRESHOLD = 0.5

const PROFILE_LAYERS: { key: DiscoveryLayer; label: string }[] = [
  { key: 'basic', label: 'Basic' },
  { key: 'personality', label: 'Personality' },
  { key: 'identity', label: 'Identity' },
]

function LayerProgress({ active }: { active: DiscoveryLayer }) {
  const activeIdx = PROFILE_LAYERS.findIndex(l => l.key === active)
  return (
    <div className="flex items-center gap-1.5 text-xs">
      {PROFILE_LAYERS.map((l, i) => (
        <span key={l.key} className="flex items-center gap-1.5">
          <span
            className={clsx(
              'inline-flex items-center gap-1 px-2 py-0.5 rounded-full',
              i === activeIdx
                ? 'bg-student/10 text-student-ink font-medium'
                : i < activeIdx
                  ? 'text-student-text'
                  : 'text-student-text/60',
            )}
          >
            {i < activeIdx && <CheckCircle2 size={11} className="text-student" />}
            {l.label}
          </span>
          {i < PROFILE_LAYERS.length - 1 && (
            <ChevronRight size={11} className="text-student-text/40" />
          )}
        </span>
      ))}
    </div>
  )
}

interface StrategyHandoffProps {
  completion: CompletionMap | null
}

function StrategyHandoffCTA({ completion }: StrategyHandoffProps) {
  const navigate = useNavigate()
  const qc = useQueryClient()
  const ready =
    completion &&
    Number(completion.profile) >= HANDOFF_THRESHOLD &&
    Number(completion.goals) >= HANDOFF_THRESHOLD &&
    Number(completion.needs) >= HANDOFF_THRESHOLD

  const generateMut = useMutation({
    mutationFn: () => generateStrategy(),
    onSuccess: () => {
      showToast('Draft strategy generated.', 'success')
      qc.invalidateQueries({ queryKey: ['strategy'] })
      navigate('/s/profile?tab=strategy')
    },
    onError: (err: unknown) =>
      showToast((err as Error).message ?? 'Could not generate strategy.', 'error'),
  })

  if (!ready) return null

  return (
    <Card className="bg-student/5 border-student/30 flex items-center justify-between gap-3">
      <div className="flex items-center gap-3">
        <Sparkles size={18} className="text-student" />
        <div>
          <div className="text-sm font-medium text-student-ink">Ready to plan a strategy.</div>
          <div className="text-xs text-student-text">
            All three tracks are far enough along — let's turn what you've shared into a broad
            strategy.
          </div>
        </div>
      </div>
      <Button
        size="sm"
        onClick={() => generateMut.mutate()}
        loading={generateMut.isPending}
      >
        Generate strategy
      </Button>
    </Card>
  )
}

export default function DiscoverHomePage() {
  const [params, setParams] = useSearchParams()
  const trackParam = params.get('track') as DiscoveryTrack | null
  const initialTrack: DiscoveryTrack = TRACK_KEYS.includes(trackParam ?? ('' as DiscoveryTrack))
    ? (trackParam as DiscoveryTrack)
    : 'profile'

  const [track, setTrack] = useState<DiscoveryTrack>(initialTrack)
  // Profile track has 3 sub-layers; default to 'basic' for the Phase B
  // first ship. Plan 2's validator may auto-advance the layer; we'll
  // surface explicit layer controls in a follow-up. Pinned to a const
  // because Phase B doesn't expose a switcher yet.
  const layer: DiscoveryLayer = 'basic'

  // Keep the URL in sync so a refresh / shared link lands on the same track.
  useEffect(() => {
    if (track === 'profile') {
      params.delete('track')
    } else {
      params.set('track', track)
    }
    setParams(params, { replace: true })
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [track])

  const { data: completion } = useQuery<CompletionMap>({
    queryKey: ['discovery', 'completion'],
    queryFn: () => getCompletionMap(),
  })

  const { data: sessions = [] } = useQuery<DiscoverySession[]>({
    queryKey: ['discovery', 'sessions', track],
    queryFn: () => listSessions({ track, status: 'active' }),
  })

  // Most-recent active session for this track, or null (ChatPanel will
  // create one lazily on the first message).
  const activeSession = useMemo<DiscoverySession | null>(() => {
    if (sessions.length === 0) return null
    return [...sessions].sort((a, b) =>
      b.started_at.localeCompare(a.started_at),
    )[0]
  }, [sessions])

  return (
    <div className="p-6 max-w-6xl mx-auto space-y-4">
      <header className="flex items-start justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <Compass size={18} className="text-gold" />
            <h1 className="text-2xl font-semibold text-student-ink">Discover</h1>
          </div>
          <p className="text-sm text-student-text max-w-2xl">
            Stage 1 of three. Talk through who you are, what you want, and what you need —
            I'll build out your profile as we go.
          </p>
        </div>
        {track === 'profile' && <LayerProgress active={layer} />}
      </header>

      <TrackSelector active={track} onChange={setTrack} completion={completion ?? null} />

      <StrategyHandoffCTA completion={completion ?? null} />

      <div className="grid grid-cols-1 lg:grid-cols-[1fr_320px] gap-4">
        <Card>
          <ChatPanel
            track={track}
            layer={layer}
            session={activeSession}
          />
        </Card>
        <ArtifactRail track={track} layer={track === 'profile' ? layer : undefined} />
      </div>
    </div>
  )
}
