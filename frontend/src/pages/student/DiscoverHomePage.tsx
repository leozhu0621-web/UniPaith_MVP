/**
 * Stage 1 (Discovery) — student home page (spec 19).
 *
 * Three-track journey: Profile / Goals / Needs, each backed by
 * `discovery_sessions` rows on the server. The chat panel auto-creates a
 * session on the first message; the artifact rail live-updates as the LLM
 * extractor writes signals into typed tables.
 *
 * Profile has three layers (Basic → Personality → Identity) that auto-advance
 * server-side as each layer's exit conditions are met; the active layer is
 * read off the most-recent active profile session. A manual switcher lets the
 * student jump to a deeper layer once the prior one is underway.
 *
 * When all three tracks reach the handoff threshold (50%), the
 * "Generate strategy" CTA turns gold (the one earned accent moment, spec
 * §11) — it calls /me/strategy/generate and routes to Stage 2
 * (`/s/explore?showStrategy=open`, spec §7).
 */
import { useEffect, useMemo, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { CheckCircle2, ChevronRight, Compass, Lock, Sparkles } from 'lucide-react'
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

/** Layer chips + a manual switcher. A deeper layer unlocks once the layer
 *  before it has been started (spec §15 — "Open Personality" beside the chip). */
function LayerSwitcher({
  active,
  unlockedThrough,
  onChange,
}: {
  active: DiscoveryLayer
  /** Index of the deepest layer the student may switch to. */
  unlockedThrough: number
  onChange: (l: DiscoveryLayer) => void
}) {
  const activeIdx = PROFILE_LAYERS.findIndex(l => l.key === active)
  return (
    <div className="flex items-center gap-1.5 text-xs">
      {PROFILE_LAYERS.map((l, i) => {
        const isActive = i === activeIdx
        const isDone = i < activeIdx
        const isLocked = i > unlockedThrough
        return (
          <span key={l.key} className="flex items-center gap-1.5">
            <button
              type="button"
              disabled={isLocked || isActive}
              onClick={() => onChange(l.key)}
              title={
                isLocked ? 'Unlocks as you complete the earlier layers' : `Switch to ${l.label}`
              }
              className={clsx(
                'inline-flex items-center gap-1 px-2 py-0.5 rounded-full transition-colors',
                isActive
                  ? 'bg-student/10 text-student-ink font-medium'
                  : isDone
                    ? 'text-student-text hover:text-student-ink'
                    : isLocked
                      ? 'text-student-text/40 cursor-not-allowed'
                      : 'text-student-text/70 hover:text-student-ink',
              )}
            >
              {isDone && <CheckCircle2 size={11} className="text-student" />}
              {isLocked && <Lock size={9} />}
              {l.label}
            </button>
            {i < PROFILE_LAYERS.length - 1 && (
              <ChevronRight size={11} className="text-student-text/40" />
            )}
          </span>
        )
      })}
    </div>
  )
}

interface StrategyHandoffProps {
  completion: CompletionMap | null
}

/** Always visible once any progress exists; gold + enabled only when all three
 *  tracks clear the threshold (spec §7/§11). */
function StrategyHandoffCTA({ completion }: StrategyHandoffProps) {
  const navigate = useNavigate()
  const qc = useQueryClient()

  const pct = (k: DiscoveryTrack) => (completion ? Number(completion[k]) : 0)
  const ready =
    !!completion &&
    pct('profile') >= HANDOFF_THRESHOLD &&
    pct('goals') >= HANDOFF_THRESHOLD &&
    pct('needs') >= HANDOFF_THRESHOLD

  const generateMut = useMutation({
    mutationFn: () => generateStrategy(),
    onSuccess: () => {
      showToast('Draft strategy generated.', 'success')
      qc.invalidateQueries({ queryKey: ['strategy'] })
      // Spec §7 — hand off to Stage 2 with the strategy view open.
      navigate('/s/explore?showStrategy=open')
    },
    onError: (err: unknown) =>
      showToast((err as Error).message ?? 'Could not generate strategy.', 'error'),
  })

  const behind = TRACK_KEYS.filter(k => pct(k) < HANDOFF_THRESHOLD)
  const hint = ready
    ? "All three tracks are far enough along — let's turn what you've shared into a broad strategy."
    : `Reach 50% on ${behind
        .map(k => k.charAt(0).toUpperCase() + k.slice(1))
        .join(', ')} to unlock your strategy.`

  return (
    <Card
      className={clsx(
        'flex items-center justify-between gap-3 transition-colors',
        ready ? 'bg-student/5 border-student/30' : 'border-divider',
      )}
    >
      <div className="flex items-center gap-3">
        <Sparkles size={18} className={ready ? 'text-student' : 'text-student-text/50'} />
        <div>
          <div className="text-sm font-medium text-student-ink">
            {ready ? 'Ready to plan a strategy.' : 'Keep going to unlock your strategy.'}
          </div>
          <div className="text-xs text-student-text">{hint}</div>
        </div>
      </div>
      <Button
        size="sm"
        disabled={!ready}
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
  // Manual layer override; null means "follow the active session's layer".
  const [layerOverride, setLayerOverride] = useState<DiscoveryLayer | null>(null)

  // Keep the URL in sync so a refresh / shared link lands on the same track.
  useEffect(() => {
    if (track === 'profile') {
      params.delete('track')
    } else {
      params.set('track', track)
    }
    setParams(params, { replace: true })
    setLayerOverride(null) // reset the layer override when switching tracks
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
    return [...sessions].sort((a, b) => b.started_at.localeCompare(a.started_at))[0]
  }, [sessions])

  // The layer the conversation is actually on: the server's active-session
  // layer wins, falling back to 'basic' for a fresh profile track. A manual
  // override (the switcher) takes precedence until the track changes.
  const sessionLayer: DiscoveryLayer = (activeSession?.layer as DiscoveryLayer | null) ?? 'basic'
  const layer: DiscoveryLayer = track === 'profile' ? (layerOverride ?? sessionLayer) : 'basic'

  // Unlock layers up to and including the active session's layer.
  const unlockedThrough = PROFILE_LAYERS.findIndex(l => l.key === sessionLayer)

  return (
    <div className="p-6 max-w-6xl mx-auto space-y-4">
      <header className="flex items-start justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <Compass size={18} className="text-gold" />
            <h1 className="text-2xl font-semibold text-student-ink">
              Let's figure out what you're looking for
            </h1>
          </div>
          <p className="text-sm text-student-text max-w-2xl">
            Stage 1 of three. Talk through who you are, what you want, and what you need —
            I'll build out your profile as we go.
          </p>
        </div>
        {track === 'profile' && (
          <LayerSwitcher
            active={layer}
            unlockedThrough={unlockedThrough < 0 ? 0 : unlockedThrough}
            onChange={setLayerOverride}
          />
        )}
      </header>

      <TrackSelector active={track} onChange={setTrack} completion={completion ?? null} />

      <StrategyHandoffCTA completion={completion ?? null} />

      <div className="grid grid-cols-1 lg:grid-cols-[1fr_320px] gap-4">
        <Card>
          <ChatPanel track={track} layer={layer} session={activeSession} onSwitchTrack={setTrack} />
        </Card>
        <ArtifactRail track={track} layer={track === 'profile' ? layer : undefined} />
      </div>
    </div>
  )
}
