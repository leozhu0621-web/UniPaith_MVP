import type { DiscoveryLayer, DiscoveryTrack } from '../../../types'
import { confirmDialog } from '../../../stores/confirm-store'

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

export async function confirmDiscardDraft(draft: string, action = 'leave this view'): Promise<boolean> {
  if (!draft.trim()) return true
  return confirmDialog({
    title: 'Discard your message?',
    body: `Your draft will be cleared so you can ${action}.`,
    confirmLabel: 'Discard',
    destructive: true,
  })
}

export function layerDotIndex(layer: DiscoveryLayer): number {
  return PROFILE_LAYERS.findIndex(l => l.key === layer)
}
