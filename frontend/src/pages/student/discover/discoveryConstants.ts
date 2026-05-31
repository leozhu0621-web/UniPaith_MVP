import type { DiscoveryLayer, DiscoveryTrack } from '../../../types'

export const DISCOVERY_TRACKS: DiscoveryTrack[] = ['profile', 'goals', 'needs']

export const PROFILE_LAYERS: { key: DiscoveryLayer; label: string }[] = [
  { key: 'basic', label: 'Basic' },
  { key: 'personality', label: 'Personality' },
  { key: 'identity', label: 'Identity' },
]

export const HANDOFF_THRESHOLD = 0.5

/** Spec §3 — basic-layer empty-state chip seeds. */
export const PROFILE_BASIC_CHIP_PROMPTS = [
  'I love board games',
  'I like to fix things',
  'Word puzzles I guess',
] as const

export function confirmDiscardDraft(draft: string, action = 'leave this view'): boolean {
  if (!draft.trim()) return true
  return window.confirm(`Discard your message and ${action}?`)
}

export function layerDotIndex(layer: DiscoveryLayer): number {
  return PROFILE_LAYERS.findIndex(l => l.key === layer)
}
