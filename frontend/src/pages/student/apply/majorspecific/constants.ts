// Spec 43 — Major-Specific readiness display constants. Dark-mode-safe semantic
// tokens throughout (the Spec 42 lesson); gold is reserved for the one earned
// beat — a "high" readiness band. Cobalt (secondary) is the functional accent.
import type { ReadinessBand } from '../../../../types/majorSpecific'

export const BAND_META: Record<ReadinessBand, { label: string; ring: string; text: string }> = {
  high: { label: 'Strong', ring: 'text-gold', text: 'text-gold' },
  medium: { label: 'Developing', ring: 'text-secondary', text: 'text-secondary' },
  low: { label: 'Getting started', ring: 'text-warning', text: 'text-warning' },
}

export const SEVERITY_META: Record<string, { label: string; cls: string }> = {
  none: { label: 'No gaps', cls: 'bg-success-soft text-success' },
  low: { label: 'Minor gaps', cls: 'bg-success-soft text-success' },
  medium: { label: 'Some gaps', cls: 'bg-warning-soft text-warning' },
  high: { label: 'Major gaps', cls: 'bg-warning-soft text-warning' },
}

export const RATING_LABELS = ['', 'None', 'Basic', 'Competent', 'Strong', 'Expert']

// Friendly title-case for a track_key, used as a fallback when no label is
// supplied (the catalog always supplies one, this is defensive).
export function trackLabel(trackKey: string, label?: string): string {
  if (label) return label
  return trackKey
    .split('_')
    .map(w => w.charAt(0).toUpperCase() + w.slice(1))
    .join(' ')
}
