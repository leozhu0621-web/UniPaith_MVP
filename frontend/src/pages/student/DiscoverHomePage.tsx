/**
 * Stage 1 (Discovery) — student home page (spec 19).
 */
import { useCallback, useEffect, useMemo, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { CheckCircle2, ChevronRight, Lock, Sparkles } from 'lucide-react'
import clsx from 'clsx'

import { getCompletionMap, getHandoffVerdict, listSessions } from '../../api/discovery'
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
import ReadinessRail from './discover/ReadinessRail'
import TrackSelector from './discover/TrackSelector'
import {
  DISCOVERY_TRACKS,
  HANDOFF_THRESHOLD,
  PROFILE_LAYERS,
  confirmDiscardDraft,
} from './discover/discoveryConstants'

const VALID_LAYERS = new Set(PROFILE_LAYERS.map(l => l.key))

function parseLayerParam(raw: string | null): DiscoveryLayer | null {
  if (raw && VALID_LAYERS.has(raw as DiscoveryLayer)) return raw as DiscoveryLayer
  return null
}

function LayerSwitcher({
  active,
  unlockedThrough,
  onChange,
}: {
  active: DiscoveryLayer
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
                  ? 'bg-primary/15 text-foreground font-medium'
                  : isDone
                    ? 'text-muted-foreground hover:text-foreground'
                    : isLocked
                      ? 'text-muted-foreground/50 cursor-not-allowed'
                      : 'text-muted-foreground hover:text-foreground',
              )}
            >
              {isDone && <CheckCircle2 size={11} className="text-accent" />}
              {isLocked && <Lock size={9} />}
              {l.label}
            </button>
            {i < PROFILE_LAYERS.length - 1 && (
              <ChevronRight size={11} className="text-muted-foreground/40" />
            )}
          </span>
        )
      })}
    </div>
  )
}

interface StrategyHandoffProps {
  completion: CompletionMap | null
  judgeReady: boolean
}

function StrategyHandoffCTA({ completion, judgeReady }: StrategyHandoffProps) {
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
      navigate('/s/explore?showStrategy=open')
    },
    onError: (err: unknown) =>
      showToast((err as Error).message ?? 'Could not generate strategy.', 'error'),
  })

  const behind = DISCOVERY_TRACKS.filter(k => pct(k) < HANDOFF_THRESHOLD)
  const hint = ready
    ? "All three tracks are far enough along — let's turn what you've shared into a broad strategy."
    : `Reach 50% on ${behind
        .map(k => k.charAt(0).toUpperCase() + k.slice(1))
        .join(', ')} to unlock your strategy.`

  return (
    <Card
      className={clsx(
        'flex items-center justify-between gap-3 transition-colors',
        ready ? 'border-primary/40 bg-primary/5' : 'border-border',
      )}
    >
      <div className="flex items-center gap-3">
        <Sparkles size={18} className={ready ? 'text-primary' : 'text-muted-foreground'} />
        <div>
          <div className="text-sm font-medium text-foreground">
            {ready ? 'Ready to plan a strategy.' : 'Keep going to unlock your strategy.'}
          </div>
          <div className="text-xs text-muted-foreground">{hint}</div>
          {judgeReady && !ready && (
            <div className="text-xs text-accent mt-0.5">
              You're making strong progress — keep going on all three tracks.
            </div>
          )}
        </div>
      </div>
      <Button
        size="sm"
        variant={ready ? 'primary' : 'tertiary'}
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
  const initialTrack: DiscoveryTrack = DISCOVERY_TRACKS.includes(trackParam ?? ('' as DiscoveryTrack))
    ? (trackParam as DiscoveryTrack)
    : 'profile'

  const [track, setTrack] = useState<DiscoveryTrack>(initialTrack)
  const [layerOverride, setLayerOverride] = useState<DiscoveryLayer | null>(
    () => parseLayerParam(params.get('layer')),
  )
  const [draft, setDraft] = useState('')
  const [handoffBanner, setHandoffBanner] = useState(false)

  const { data: completion } = useQuery<CompletionMap>({
    queryKey: ['discovery', 'completion'],
    queryFn: () => getCompletionMap(),
  })

  const { data: sessions = [] } = useQuery<DiscoverySession[]>({
    queryKey: ['discovery', 'sessions', track],
    queryFn: () => listSessions({ track, status: 'active' }),
  })

  const activeSession = useMemo<DiscoverySession | null>(() => {
    if (sessions.length === 0) return null
    return [...sessions].sort((a, b) => b.started_at.localeCompare(a.started_at))[0]
  }, [sessions])

  const sessionLayer: DiscoveryLayer = (activeSession?.layer as DiscoveryLayer | null) ?? 'basic'
  const layer: DiscoveryLayer = track === 'profile' ? (layerOverride ?? sessionLayer) : 'basic'
  const unlockedThrough = PROFILE_LAYERS.findIndex(l => l.key === sessionLayer)

  const guardedSetTrack = useCallback(
    (next: DiscoveryTrack) => {
      if (next === track) return
      if (!confirmDiscardDraft(draft, 'switch track')) return
      setDraft('')
      setLayerOverride(null)
      setTrack(next)
    },
    [draft, track],
  )

  const guardedSetLayer = useCallback(
    (next: DiscoveryLayer) => {
      if (next === layer) return
      if (!confirmDiscardDraft(draft, 'switch layer')) return
      setDraft('')
      setLayerOverride(next)
    },
    [draft, layer],
  )

  useEffect(() => {
    const next = new URLSearchParams(params)
    if (track === 'profile') {
      next.delete('track')
    } else {
      next.set('track', track)
    }
    if (track === 'profile') {
      next.set('layer', layer)
    } else {
      next.delete('layer')
    }
    setParams(next, { replace: true })
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [track, layer])

  const refreshHandoff = useCallback(() => {
    getHandoffVerdict()
      .then(v => setHandoffBanner(v.should_handoff))
      .catch(() => setHandoffBanner(false))
  }, [])

  useEffect(() => {
    refreshHandoff()
  }, [completion, refreshHandoff])

  return (
    <div className="p-6 max-w-6xl mx-auto space-y-4">
      <header className="flex items-start justify-between gap-4">
        <div>
          <p className="text-eyebrow text-accent mb-1">Discover</p>
          <h1 className="text-2xl font-semibold text-foreground">
            Let's figure out what you're looking for
          </h1>
          <p className="text-sm text-muted-foreground max-w-2xl mt-1">
            Talk through who you are, what you want, and what you need — I'll build your profile as
            we go.
          </p>
        </div>
        {track === 'profile' && (
          <LayerSwitcher
            active={layer}
            unlockedThrough={unlockedThrough < 0 ? 0 : unlockedThrough}
            onChange={guardedSetLayer}
          />
        )}
      </header>

      {handoffBanner && (
        <div className="rounded-lg border border-accent/30 bg-accent/5 px-3 py-2 text-xs text-foreground">
          Your discovery progress looks strong. Generate a strategy when all three tracks reach 50%.
        </div>
      )}

      <TrackSelector
        active={track}
        onChange={guardedSetTrack}
        completion={completion ?? null}
        profileLayer={track === 'profile' ? layer : sessionLayer}
      />

      <StrategyHandoffCTA completion={completion ?? null} judgeReady={handoffBanner} />

      <div className="grid grid-cols-1 lg:grid-cols-[1fr_320px] gap-4">
        <Card className="p-4">
          <ChatPanel
            track={track}
            layer={layer}
            session={activeSession}
            draft={draft}
            onDraftChange={setDraft}
            onSwitchTrack={guardedSetTrack}
            onTurnComplete={refreshHandoff}
            onSessionCreated={() => {
              refreshHandoff()
            }}
          />
        </Card>
        <div className="space-y-4">
          <ReadinessRail />
          <ArtifactRail track={track} layer={track === 'profile' ? layer : undefined} />
        </div>
      </div>
    </div>
  )
}
