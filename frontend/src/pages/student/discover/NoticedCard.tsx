/**
 * Inline "Noticed" confirmation card (Task 6 / spec §3.3).
 *
 * After a turn surfaces something real, Uni quietly reflects it back ("✓ Noticed:
 * you want to study marine biology") so the student sees they're being heard —
 * and can correct it on the spot. Items that map to a saved goal / need get an
 * inline ✎ that edits through `updateSignal`; everything else links into the
 * full profile drawer.
 */
import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { Check, Pencil, X } from 'lucide-react'

import { updateSignal } from '../../../api/livingProfile'
import { showToast } from '../../../stores/toast-store'

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

export function EditableChip({ item }: { item: NoticedItem }) {
  const qc = useQueryClient()
  const [editing, setEditing] = useState(false)
  const [value, setValue] = useState(item.label)

  const mut = useMutation({
    mutationFn: (next: string) => updateSignal({ ...item.ref!, value: next }),
    onSuccess: () => {
      setEditing(false)
      qc.invalidateQueries({ queryKey: ['goals'] })
      qc.invalidateQueries({ queryKey: ['needs'] })
      qc.invalidateQueries({ queryKey: ['discovery', 'livingProfile'] })
    },
    onError: (e: unknown) => showToast((e as Error).message ?? 'Could not update.', 'error'),
  })

  const save = () => {
    const next = value.trim()
    if (!next || next === item.label) {
      setEditing(false)
      return
    }
    mut.mutate(next)
  }

  if (editing) {
    return (
      <span className="inline-flex items-center gap-1">
        <input
          autoFocus
          value={value}
          onChange={e => setValue(e.target.value)}
          onKeyDown={e => {
            if (e.key === 'Enter') {
              e.preventDefault()
              save()
            }
            if (e.key === 'Escape') setEditing(false)
          }}
          className="rounded-md border border-secondary bg-background px-2 py-0.5 text-xs focus:outline-none"
          aria-label="Edit what Uni noticed"
        />
        <button type="button" onClick={save} aria-label="Save" disabled={mut.isPending}>
          <Check size={13} className="text-secondary" />
        </button>
        <button type="button" onClick={() => setEditing(false)} aria-label="Cancel">
          <X size={13} className="text-muted-foreground" />
        </button>
      </span>
    )
  }

  return (
    <span className="inline-flex items-center gap-1 rounded-full bg-card border border-border px-2.5 py-0.5 text-xs text-foreground">
      {item.label}
      <button
        type="button"
        onClick={() => {
          setValue(item.label)
          setEditing(true)
        }}
        aria-label={`Tweak: ${item.label}`}
        className="text-muted-foreground hover:text-secondary transition-colors"
      >
        <Pencil size={11} />
      </button>
    </span>
  )
}

export default function NoticedCard({
  items,
  onAdjust,
}: {
  items: NoticedItem[]
  onAdjust?: () => void
}) {
  if (items.length === 0) return null
  return (
    <div className="flex justify-start pl-9" data-testid="noticed-card">
      <div className="rounded-xl bg-muted/40 border border-border/60 px-3 py-2 max-w-[80%]">
        <div className="flex items-center gap-1.5 text-xs text-muted-foreground mb-1.5">
          <Check size={12} className="text-secondary" /> Noticed
        </div>
        <div className="flex flex-wrap gap-1.5">
          {items.map(item =>
            item.ref ? (
              <EditableChip key={`${item.ref.kind}:${item.ref.id}`} item={item} />
            ) : (
              <span
                key={item.label}
                className="rounded-full bg-card border border-border px-2.5 py-0.5 text-xs text-foreground"
              >
                {item.label}
              </span>
            ),
          )}
        </div>
        {onAdjust && (
          <button
            type="button"
            onClick={onAdjust}
            className="mt-1.5 text-xs text-secondary hover:underline"
          >
            Adjust in your profile →
          </button>
        )}
      </div>
    </div>
  )
}
