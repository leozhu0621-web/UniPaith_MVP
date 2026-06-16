/**
 * "Here's what I found" — the review-and-confirm card for an uploaded file.
 *
 * Renders Uni's structured reading of a document as toggleable sections; the
 * student keeps/drops sections, then confirms what lands in My Space. Per the
 * show-&-confirm decision, nothing is written until the student hits Add.
 */
import { useMemo, useState } from 'react'
import { Check, FileText, Plus } from 'lucide-react'

import type { ProposedProfile } from '../../api/materials'
import Badge from '../ui/Badge'
import Button from '../ui/Button'
import Card from '../ui/Card'

type SectionKey = keyof Omit<ProposedProfile, 'summary'>

const SECTIONS: { key: SectionKey; label: string; preview: (item: Record<string, unknown>) => string }[] = [
  { key: 'profile', label: 'Basic info', preview: () => '' },
  { key: 'academic_records', label: 'Education', preview: i => String(i.institution_name ?? i.degree_type ?? '') },
  { key: 'test_scores', label: 'Test scores', preview: i => `${i.test_type ?? ''} ${i.total_score ?? ''}`.trim() },
  { key: 'activities', label: 'Activities', preview: i => String(i.title ?? '') },
  { key: 'work_experiences', label: 'Work experience', preview: i => `${i.role_title ?? ''} · ${i.organization ?? ''}` },
  { key: 'goals', label: 'Goals', preview: i => String(i.specific ?? '') },
  { key: 'needs', label: 'Needs', preview: i => String(i.signal ?? i.need_type ?? '') },
  { key: 'identity', label: 'Values & identity', preview: () => '' },
]

function sectionItems(proposed: ProposedProfile, key: SectionKey): Record<string, unknown>[] {
  if (key === 'profile') {
    const p = proposed.profile ?? {}
    return Object.entries(p)
      .filter(([, v]) => v)
      .map(([k, v]) => ({ k, v }))
  }
  if (key === 'identity') {
    const id = proposed.identity ?? {}
    return [...(id.core_values ?? []), ...(id.worldview ?? []), ...(id.self_awareness ?? [])]
  }
  return (proposed[key] as Record<string, unknown>[] | undefined) ?? []
}

function itemLabel(key: SectionKey, item: Record<string, unknown>): string {
  if (key === 'profile') return `${item.k}: ${item.v}`
  if (key === 'identity') return String(item.value ?? item.belief ?? item.insight ?? '')
  const s = SECTIONS.find(x => x.key === key)
  return s ? s.preview(item) : ''
}

export default function MaterialReviewCard({
  proposed,
  onConfirm,
  onCancel,
  applying = false,
}: {
  proposed: ProposedProfile
  onConfirm: (selection: Partial<ProposedProfile>) => void
  onCancel: () => void
  applying?: boolean
}) {
  const present = useMemo(
    () => SECTIONS.map(s => ({ ...s, items: sectionItems(proposed, s.key) })).filter(s => s.items.length > 0),
    [proposed],
  )
  const [enabled, setEnabled] = useState<Record<string, boolean>>(
    () => Object.fromEntries(present.map(s => [s.key, true])),
  )
  const total = present.reduce((n, s) => n + (enabled[s.key] ? s.items.length : 0), 0)

  const confirm = () => {
    const sel: Partial<ProposedProfile> = {}
    for (const s of present) {
      if (!enabled[s.key]) continue
      if (s.key === 'identity') sel.identity = proposed.identity
      else if (s.key === 'profile') sel.profile = proposed.profile
      else (sel as Record<string, unknown>)[s.key] = proposed[s.key]
    }
    onConfirm(sel)
  }

  if (present.length === 0) {
    return (
      <Card variant="card" pad>
        <p className="text-sm text-muted-foreground">
          I couldn't pull anything structured from this file — you can add the details by hand.
        </p>
        <div className="mt-3 flex justify-end">
          <Button variant="ghost" size="sm" onClick={onCancel}>
            Close
          </Button>
        </div>
      </Card>
    )
  }

  return (
    <Card variant="card-accent" pad>
      <div className="flex items-center gap-2">
        <span className="text-secondary">
          <FileText size={16} />
        </span>
        <span className="text-sm font-semibold text-foreground">Here's what I found</span>
        <Badge>{total} items</Badge>
      </div>
      {proposed.summary && <p className="mt-1.5 text-sm text-muted-foreground">{proposed.summary}</p>}

      <div className="mt-3 divide-y divide-border">
        {present.map(s => {
          const on = enabled[s.key]
          return (
            <button
              key={s.key}
              type="button"
              onClick={() => setEnabled(e => ({ ...e, [s.key]: !e[s.key] }))}
              aria-pressed={on}
              className="flex w-full items-start gap-2.5 py-2 text-left"
            >
              <span
                className={`mt-0.5 flex h-4 w-4 shrink-0 items-center justify-center rounded border ${
                  on ? 'border-secondary bg-secondary text-white' : 'border-border text-transparent'
                }`}
              >
                <Check size={12} />
              </span>
              <span className="flex-1">
                <span className="flex items-center gap-2">
                  <span className="text-sm font-medium text-foreground">{s.label}</span>
                  <span className="text-xs text-muted-foreground">{s.items.length}</span>
                </span>
                <span className="mt-0.5 block text-xs text-muted-foreground line-clamp-1">
                  {s.items.slice(0, 3).map(i => itemLabel(s.key, i)).filter(Boolean).join(' · ')}
                </span>
              </span>
            </button>
          )
        })}
      </div>

      <div className="mt-3 flex items-center justify-end gap-2.5">
        <Button variant="ghost" size="sm" onClick={onCancel} disabled={applying}>
          Cancel
        </Button>
        <Button variant="secondary" size="sm" onClick={confirm} loading={applying} disabled={total === 0}>
          <Plus size={14} className="mr-1" /> Add to My Space
        </Button>
      </div>
    </Card>
  )
}
