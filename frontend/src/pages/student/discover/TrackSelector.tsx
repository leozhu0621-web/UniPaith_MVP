/**
 * Discover → 3-track segmented control (spec 19 §3, §11).
 */
import clsx from 'clsx'
import { Compass, Heart, Target } from 'lucide-react'

import type { CompletionMap, DiscoveryLayer, DiscoveryTrack } from '../../../types'
import { PROFILE_LAYERS, layerDotIndex } from './discoveryConstants'

const TRACKS: { key: DiscoveryTrack; label: string; hint: string; Icon: typeof Compass }[] = [
  {
    key: 'profile',
    label: 'Profile',
    hint: 'Basic → Personality → Identity',
    Icon: Compass,
  },
  {
    key: 'goals',
    label: 'Goals',
    hint: 'Academic, social, personal — SMART.',
    Icon: Target,
  },
  {
    key: 'needs',
    label: 'Needs',
    hint: "Maslow-keyed — what you can't do without.",
    Icon: Heart,
  },
]

function LayerDots({ layer }: { layer: DiscoveryLayer }) {
  const activeIdx = layerDotIndex(layer)
  return (
    <span className="inline-flex items-center gap-0.5 text-[10px] text-muted-foreground">
      <span className="mr-1">Layer: {PROFILE_LAYERS[activeIdx]?.label ?? 'Basic'}</span>
      {PROFILE_LAYERS.map((l, i) => (
        <span
          key={l.key}
          className={clsx(
            'h-1.5 w-1.5 rounded-full',
            i <= activeIdx ? 'bg-accent' : 'bg-border',
          )}
          aria-hidden
        />
      ))}
    </span>
  )
}

export interface TrackSelectorProps {
  active: DiscoveryTrack
  onChange: (t: DiscoveryTrack) => void
  completion?: CompletionMap | null
  profileLayer?: DiscoveryLayer | null
}

export default function TrackSelector({
  active,
  onChange,
  completion,
  profileLayer,
}: TrackSelectorProps) {
  return (
    <div className="grid grid-cols-3 gap-2">
      {TRACKS.map(({ key, label, hint, Icon }) => {
        const pct = completion ? Math.round(Number(completion[key]) * 100) : 0
        const isActive = active === key
        return (
          <button
            key={key}
            type="button"
            onClick={() => onChange(key)}
            aria-pressed={isActive}
            className={clsx(
              'text-left rounded-lg border px-3 py-2.5 transition-colors bg-card',
              isActive
                ? 'border-accent ring-1 ring-accent/25'
                : 'border-border hover:border-accent/40',
            )}
          >
            <div className="flex items-center gap-2 mb-1">
              <Icon size={14} className={isActive ? 'text-accent' : 'text-muted-foreground'} />
              <span className="text-sm font-semibold text-foreground">{label}</span>
              <span className="ml-auto text-xs text-muted-foreground">{pct}%</span>
            </div>
            <div className="text-xs text-muted-foreground mb-1.5 truncate">{hint}</div>
            {key === 'profile' && profileLayer && (
              <div className="mb-1.5">
                <LayerDots layer={profileLayer} />
              </div>
            )}
            <div className="h-1 rounded-full bg-muted overflow-hidden">
              <div
                className={clsx(
                  'h-full transition-all duration-300',
                  isActive ? 'bg-accent' : 'bg-muted-foreground/40',
                )}
                style={{ width: `${pct}%` }}
              />
            </div>
          </button>
        )
      })}
    </div>
  )
}
