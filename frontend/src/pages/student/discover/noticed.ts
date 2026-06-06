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
  /**
   * The original (frozen) extracted-signal label this item was built from. Used
   * as the stable key for reconciling later inline edits — the message's
   * `extracted_signals` never change, but the goal/need text can.
   */
  signalLabel?: string
  /**
   * Which `extracted_signals` bucket this label came from. Only `goals` / `needs`
   * are editable rows; `identity` / `personality` are reflections and must never
   * be wired to a goal/need id even when the wording collides.
   */
  source?: 'goals' | 'needs' | 'identity' | 'personality'
}

/**
 * Remembered inline edits, keyed by the frozen signal label. After an edit the
 * living-profile row is renamed, so it no longer matches the historical signal
 * text by label. We keep the resolved ref (and the new wording) here so the
 * chip stays editable and shows current text on subsequent renders.
 */
const editedSignals = new Map<string, { ref: NonNullable<NoticedItem['ref']>; label: string }>()

const norm = (s: string) => s.toLowerCase().trim()

/** Record an inline edit so the renamed signal stays linked to its row. */
export function rememberSignalEdit(
  signalLabel: string,
  ref: NonNullable<NoticedItem['ref']>,
  label: string,
): void {
  editedSignals.set(norm(signalLabel), { ref, label })
}

/**
 * Drop all remembered inline edits. Must be called on logout / session change so
 * a later user on the same SPA session can't inherit another account's frozen
 * `{ ref, label }` entries (which are keyed only by normalized signal text).
 */
export function clearSignalEdits(): void {
  editedSignals.clear()
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
  for (const key of ['goals', 'needs', 'identity', 'personality'] as const) {
    const list = signals[key]
    if (!Array.isArray(list)) continue
    for (const entry of list) {
      const label = labelOf(entry)
      if (label) items.push({ label, source: key })
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
  // Identity / personality reflections are never editable rows; only match goal
  // labels against goals and need labels against needs so colliding wording can't
  // wire a chip to an unrelated row. (A missing `source` keeps the legacy
  // match-either behavior for callers that build items by hand.)
  const find = (item: NoticedItem): NoticedItem['ref'] => {
    if (!profile) return undefined
    if (item.source === 'identity' || item.source === 'personality') return undefined
    const n = norm(item.label)
    if (item.source !== 'needs') {
      const g = profile.goals.find(x => norm(x.label) === n)
      if (g) return { kind: 'goal', id: g.id }
    }
    if (item.source !== 'goals') {
      const nd = profile.needs.find(x => norm(x.label) === n)
      if (nd) return { kind: 'need', id: nd.id }
    }
    return undefined
  }
  return items.map(i => {
    if (i.ref) return i
    if (i.source === 'identity' || i.source === 'personality') return i
    // A prior inline edit renamed the row, so it no longer matches the frozen
    // signal label — recover the ref (and current wording) from the edit log.
    const edited = editedSignals.get(norm(i.label))
    if (edited) return { ...i, label: edited.label, ref: edited.ref, signalLabel: i.label }
    const ref = find(i)
    return ref ? { ...i, ref, signalLabel: i.label } : i
  })
}
