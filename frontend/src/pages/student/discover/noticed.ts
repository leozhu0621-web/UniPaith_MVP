/**
 * Pure helpers for the in-thread "Noticed" cards — kept out of the component
 * file so they're importable without a React dependency (and so fast-refresh
 * stays happy).
 */
import type { LivingProfile } from '../../../api/livingProfile'

export interface NoticedItem {
  label: string
  /** Present when the signal was saved as an editable goal / need row. */
  ref?: { kind: 'goal' | 'need'; id: string }
}

/** Pull a readable label out of one extracted-signal entry (string or object). */
function labelOf(entry: unknown): string | null {
  if (typeof entry === 'string') return entry.trim() || null
  if (entry && typeof entry === 'object') {
    const o = entry as Record<string, unknown>
    for (const k of ['specific', 'signal', 'value', 'belief', 'insight', 'goal', 'need', 'text']) {
      const v = o[k]
      if (typeof v === 'string' && v.trim()) return v.trim()
    }
  }
  return null
}

/** Normalize a message's `extracted_signals` JSONB into display items. */
export function noticedItemsFromSignals(signals: Record<string, unknown> | null): NoticedItem[] {
  if (!signals) return []
  const items: NoticedItem[] = []
  for (const key of ['goals', 'needs', 'identity', 'personality']) {
    const list = signals[key]
    if (!Array.isArray(list)) continue
    for (const entry of list) {
      const label = labelOf(entry)
      if (label) items.push({ label })
    }
  }
  // De-dupe by label, keep order.
  const seen = new Set<string>()
  return items.filter(i => (seen.has(i.label) ? false : (seen.add(i.label), true)))
}

/**
 * Attach editable refs to noticed items by matching their label to a saved goal
 * or need in the living profile. Unmatched items stay ref-less (read-only chip +
 * "Adjust in your profile →"). Used to wire the thread's Noticed cards.
 */
export function attachRefs(items: NoticedItem[], profile?: LivingProfile | null): NoticedItem[] {
  if (!profile) return items
  const norm = (s: string) => s.toLowerCase().trim()
  const find = (label: string): NoticedItem['ref'] => {
    const n = norm(label)
    const g = profile.goals.find(x => norm(x.label) === n)
    if (g) return { kind: 'goal', id: g.id }
    const nd = profile.needs.find(x => norm(x.label) === n)
    if (nd) return { kind: 'need', id: nd.id }
    return undefined
  }
  return items.map(i => (i.ref ? i : { ...i, ref: find(i.label) }))
}
