/**
 * Discover → 3-track segmented control.
 *
 * Profile / Goals / Needs. Each pill shows the per-track completion bar so
 * progress is visible without leaving the page.
 */
import clsx from 'clsx'
import { Compass, Heart, Target } from 'lucide-react'

import type { CompletionMap, DiscoveryTrack } from '../../../types'

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

export interface TrackSelectorProps {
  active: DiscoveryTrack
  onChange: (t: DiscoveryTrack) => void
  completion?: CompletionMap | null
}

export default function TrackSelector({ active, onChange, completion }: TrackSelectorProps) {
  return (
    <div className="grid grid-cols-3 gap-2">
      {TRACKS.map(({ key, label, hint, Icon }) => {
        const pct = completion ? Math.round(Number(completion[key]) * 100) : 0
        const isActive = active === key
        return (
          <button
            key={key}
            onClick={() => onChange(key)}
            aria-pressed={isActive}
            className={clsx(
              'text-left rounded-lg border px-3 py-2.5 transition-colors',
              isActive
                ? 'border-student bg-student/5'
                : 'border-divider hover:border-student-text',
            )}
          >
            <div className="flex items-center gap-2 mb-1">
              <Icon size={14} className={isActive ? 'text-student' : 'text-student-text'} />
              <span
                className={clsx(
                  'text-sm font-semibold',
                  isActive ? 'text-student-ink' : 'text-student-ink',
                )}
              >
                {label}
              </span>
              <span className="ml-auto text-xs text-student-text">{pct}%</span>
            </div>
            <div className="text-xs text-student-text mb-1.5 truncate">{hint}</div>
            <div className="h-1 rounded-full bg-divider overflow-hidden">
              <div
                className={clsx(
                  'h-full transition-all duration-300',
                  isActive ? 'bg-student' : 'bg-student-text',
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
