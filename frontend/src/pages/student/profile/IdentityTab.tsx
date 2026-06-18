/**
 * Profile → Identity tab.
 *
 * Three list-of-cards sections (values / worldview / self-awareness). The
 * backend's PUT is partial-merge: omitting a key preserves it; passing `[]`
 * clears it. We follow that contract — every save sends ONLY the section
 * being mutated, never the whole object.
 *
 * First-write privacy disclosure is a one-time banner backed by
 * localStorage so we don't surface it on every visit.
 */
import { useState } from 'react'
import { confirmDialog } from '../../../stores/confirm-store'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Globe, Heart, Lightbulb, type LucideIcon, Pencil, Plus, Sparkles, Trash2 } from 'lucide-react'

import {
  type UpsertIdentityBody,
  getIdentity,
  regenerateIdentitySummary,
  upsertIdentity,
} from '../../../api/identity'
import AIBadge from '../../../components/ui/AIBadge'
import Button from '../../../components/ui/Button'
import Card from '../../../components/ui/Card'
import Modal from '../../../components/ui/Modal'
import QueryError from '../../../components/ui/QueryError'
import { SkeletonCard } from '../../../components/ui/Skeleton'
import { showToast } from '../../../stores/toast-store'
import { relativeShort } from './shared'
import type {
  CoreValue,
  SelfAwarenessItem,
  StudentIdentity,
  WorldviewItem,
} from '../../../types'

type ItemKind = 'core_values' | 'worldview' | 'self_awareness'

type EditingState =
  | { kind: 'core_values'; index: number | null; draft: CoreValue }
  | { kind: 'worldview'; index: number | null; draft: WorldviewItem }
  | { kind: 'self_awareness'; index: number | null; draft: SelfAwarenessItem }
  | null

const EMPTY: Record<ItemKind, CoreValue | WorldviewItem | SelfAwarenessItem> = {
  core_values: { value: '', evidence: '', confidence: null, source_quote: null },
  worldview: { belief: '', context: '', confidence: null, source_quote: null },
  self_awareness: {
    insight: '',
    trigger_event: null,
    confidence: null,
    source_quote: null,
  },
}

interface ItemFormProps {
  state: NonNullable<EditingState>
  onCancel: () => void
  onSave: () => void
  setState: (s: NonNullable<EditingState>) => void
  submitting: boolean
}

function ItemForm({ state, onCancel, onSave, setState, submitting }: ItemFormProps) {
  // Render-by-kind to keep each form's required fields clear.
  if (state.kind === 'core_values') {
    const draft = state.draft
    return (
      <form
        onSubmit={e => {
          e.preventDefault()
          if (!draft.value.trim() || !draft.evidence.trim()) {
            showToast('Value and evidence are required.', 'error')
            return
          }
          onSave()
        }}
        className="space-y-3"
      >
        <div>
          <label htmlFor="identity-value" className="block text-sm font-medium text-foreground mb-1">
            Value <span className="text-error">*</span>
          </label>
          <input
            id="identity-value"
            className="w-full rounded-md border border-border bg-card px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring focus:border-secondary"
            maxLength={200}
            value={draft.value}
            onChange={e => setState({ ...state, draft: { ...draft, value: e.target.value } })}
            placeholder="e.g., Curiosity, Honesty, Service"
          />
        </div>
        <div>
          <label htmlFor="identity-evidence" className="block text-sm font-medium text-foreground mb-1">
            Evidence <span className="text-error">*</span>
          </label>
          <textarea
            id="identity-evidence"
            className="w-full rounded-md border border-border bg-card px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring focus:border-secondary"
            rows={3}
            maxLength={4000}
            value={draft.evidence}
            onChange={e =>
              setState({ ...state, draft: { ...draft, evidence: e.target.value } })
            }
            placeholder="A specific moment or pattern that shows this."
          />
        </div>
        <ItemFooter onCancel={onCancel} submitting={submitting} />
      </form>
    )
  }

  if (state.kind === 'worldview') {
    const draft = state.draft
    return (
      <form
        onSubmit={e => {
          e.preventDefault()
          if (!draft.belief.trim() || !draft.context.trim()) {
            showToast('Belief and context are required.', 'error')
            return
          }
          onSave()
        }}
        className="space-y-3"
      >
        <div>
          <label htmlFor="identity-belief" className="block text-sm font-medium text-foreground mb-1">
            Belief <span className="text-error">*</span>
          </label>
          <input
            id="identity-belief"
            className="w-full rounded-md border border-border bg-card px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring focus:border-secondary"
            maxLength={400}
            value={draft.belief}
            onChange={e => setState({ ...state, draft: { ...draft, belief: e.target.value } })}
            placeholder="A view you hold about how the world works."
          />
        </div>
        <div>
          <label htmlFor="identity-context" className="block text-sm font-medium text-foreground mb-1">
            Context <span className="text-error">*</span>
          </label>
          <textarea
            id="identity-context"
            className="w-full rounded-md border border-border bg-card px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring focus:border-secondary"
            rows={3}
            maxLength={4000}
            value={draft.context}
            onChange={e =>
              setState({ ...state, draft: { ...draft, context: e.target.value } })
            }
            placeholder="Where does this belief come from?"
          />
        </div>
        <ItemFooter onCancel={onCancel} submitting={submitting} />
      </form>
    )
  }

  // self_awareness
  const draft = state.draft
  return (
    <form
      onSubmit={e => {
        e.preventDefault()
        if (!draft.insight.trim()) {
          showToast('Insight is required.', 'error')
          return
        }
        onSave()
      }}
      className="space-y-3"
    >
      <div>
        <label htmlFor="identity-insight" className="block text-sm font-medium text-foreground mb-1">
          Insight <span className="text-error">*</span>
        </label>
        <input
          id="identity-insight"
          className="w-full rounded-md border border-border bg-card px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring focus:border-secondary"
          maxLength={400}
          value={draft.insight}
          onChange={e => setState({ ...state, draft: { ...draft, insight: e.target.value } })}
          placeholder="A pattern you've noticed about yourself."
        />
      </div>
      <div>
        <label htmlFor="identity-trigger" className="block text-sm font-medium text-foreground mb-1">Trigger event</label>
        <textarea
          id="identity-trigger"
          className="w-full rounded-md border border-border bg-card px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring focus:border-secondary"
          rows={3}
          maxLength={4000}
          value={draft.trigger_event ?? ''}
          onChange={e =>
            setState({
              ...state,
              draft: { ...draft, trigger_event: e.target.value || null },
            })
          }
          placeholder="The moment or situation that revealed it."
        />
      </div>
      <ItemFooter onCancel={onCancel} submitting={submitting} />
    </form>
  )
}

function ItemFooter({ onCancel, submitting }: { onCancel: () => void; submitting: boolean }) {
  return (
    <div className="flex justify-end gap-2 pt-2">
      <Button type="button" variant="ghost" onClick={onCancel}>
        Cancel
      </Button>
      <Button type="submit" loading={submitting}>
        Save
      </Button>
    </div>
  )
}

export default function IdentityTab() {
  const qc = useQueryClient()
  const { data: identity, isLoading, isError, refetch } = useQuery<StudentIdentity>({
    queryKey: ['identity'],
    queryFn: () => getIdentity(),
  })
  const [editing, setEditing] = useState<EditingState>(null)

  const onSettled = () => qc.invalidateQueries({ queryKey: ['identity'] })

  const upsertMut = useMutation({
    mutationFn: (body: UpsertIdentityBody) => upsertIdentity(body),
    onSuccess: () => {
      showToast('Identity updated.', 'success')
      setEditing(null)
    },
    onError: (err: unknown) =>
      showToast((err as Error).message ?? 'Could not save changes.', 'error'),
    onSettled,
  })

  const regenMut = useMutation({
    mutationFn: () => regenerateIdentitySummary(),
    onSuccess: () => showToast('Summary regenerated.', 'success'),
    onError: (err: unknown) =>
      showToast((err as Error).message ?? 'Could not regenerate.', 'error'),
    onSettled,
  })

  // Per the partial-merge contract — only send the list being mutated.
  const saveCurrentEdit = () => {
    if (!editing || !identity) return
    if (editing.kind === 'core_values') {
      const list = [...(identity.core_values ?? [])]
      if (editing.index === null) list.push(editing.draft as CoreValue)
      else list[editing.index] = editing.draft as CoreValue
      upsertMut.mutate({ core_values: list })
    } else if (editing.kind === 'worldview') {
      const list = [...(identity.worldview ?? [])]
      if (editing.index === null) list.push(editing.draft as WorldviewItem)
      else list[editing.index] = editing.draft as WorldviewItem
      upsertMut.mutate({ worldview: list })
    } else {
      const list = [...(identity.self_awareness ?? [])]
      if (editing.index === null) list.push(editing.draft as SelfAwarenessItem)
      else list[editing.index] = editing.draft as SelfAwarenessItem
      upsertMut.mutate({ self_awareness: list })
    }
  }

  const removeItem = async (kind: ItemKind, index: number) => {
    if (!identity) return
    if (!(await confirmDialog({ title: 'Remove this entry?', confirmLabel: 'Remove', destructive: true }))) return
    if (kind === 'core_values') {
      const list = (identity.core_values ?? []).filter((_, i) => i !== index)
      upsertMut.mutate({ core_values: list })
    } else if (kind === 'worldview') {
      const list = (identity.worldview ?? []).filter((_, i) => i !== index)
      upsertMut.mutate({ worldview: list })
    } else {
      const list = (identity.self_awareness ?? []).filter((_, i) => i !== index)
      upsertMut.mutate({ self_awareness: list })
    }
  }

  if (isError) return <QueryError onRetry={() => refetch()} />
  if (isLoading || !identity) {
    return (
      <div className="space-y-3">
        <SkeletonCard />
        <SkeletonCard />
        <SkeletonCard />
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {/* Who you are — the synthesized portrait leads (§5, IdentitySummaryAgent). */}
      <Card pad={false} className="bg-muted/40 p-5">
        <div className="mb-2 flex items-center gap-2">
          <span className="text-eyebrow uppercase text-muted-foreground">Who you are</span>
          <AIBadge />
          <button
            type="button"
            onClick={() => regenMut.mutate()}
            disabled={regenMut.isPending}
            aria-label="Regenerate summary"
            className="ml-auto inline-flex items-center gap-1 text-xs text-secondary hover:underline disabled:opacity-50"
          >
            <Sparkles size={13} /> Regenerate
          </button>
        </div>
        {identity.identity_summary ? (
          <p className="whitespace-pre-line text-sm leading-relaxed text-foreground">{identity.identity_summary}</p>
        ) : (
          <p className="text-sm text-muted-foreground">Nothing yet</p>
        )}
        {regenMut.isError && (
          <p className="mt-2 text-xs text-warning">We couldn't reach the AI service. Showing your last summary.</p>
        )}
        {identity.identity_summary && identity.updated_at && (
          <p className="mt-3 text-xs text-muted-foreground">Updated {relativeShort(identity.updated_at) ?? 'recently'}</p>
        )}
      </Card>

      {/* The three layers — compact cards (Self-awareness spans the row). */}
      <div className="grid grid-cols-1 gap-3 lg:grid-cols-2">
        <Section title="Core values" icon={Heart}
          onAdd={() => setEditing({ kind: 'core_values', index: null, draft: { ...(EMPTY.core_values as CoreValue) } })}
        >
          {identity.core_values.length === 0 ? (
            <EmptyHint onAdd={() => setEditing({ kind: 'core_values', index: null, draft: { ...(EMPTY.core_values as CoreValue) } })} />
          ) : (
            identity.core_values.map((v, i) => (
              <Row key={i} title={v.value} sub={v.evidence} quote={v.source_quote}
                onEdit={() => setEditing({ kind: 'core_values', index: i, draft: { ...v } })}
                onRemove={() => removeItem('core_values', i)} />
            ))
          )}
        </Section>

        <Section title="Worldview" icon={Globe}
          onAdd={() => setEditing({ kind: 'worldview', index: null, draft: { ...(EMPTY.worldview as WorldviewItem) } })}
        >
          {identity.worldview.length === 0 ? (
            <EmptyHint onAdd={() => setEditing({ kind: 'worldview', index: null, draft: { ...(EMPTY.worldview as WorldviewItem) } })} />
          ) : (
            identity.worldview.map((w, i) => (
              <Row key={i} title={w.belief} sub={w.context}
                onEdit={() => setEditing({ kind: 'worldview', index: i, draft: { ...w } })}
                onRemove={() => removeItem('worldview', i)} />
            ))
          )}
        </Section>

        <Section title="Self-awareness" icon={Lightbulb} className="lg:col-span-2"
          onAdd={() => setEditing({ kind: 'self_awareness', index: null, draft: { ...(EMPTY.self_awareness as SelfAwarenessItem) } })}
        >
          {identity.self_awareness.length === 0 ? (
            <EmptyHint onAdd={() => setEditing({ kind: 'self_awareness', index: null, draft: { ...(EMPTY.self_awareness as SelfAwarenessItem) } })} />
          ) : (
            <div className="grid grid-cols-1 gap-x-5 gap-y-2.5 sm:grid-cols-2">
              {identity.self_awareness.map((s, i) => (
                <Row key={i} title={s.insight} sub={s.trigger_event}
                  onEdit={() => setEditing({ kind: 'self_awareness', index: i, draft: { ...s } })}
                  onRemove={() => removeItem('self_awareness', i)} />
              ))}
            </div>
          )}
        </Section>
      </div>

      {editing && (
        <Modal
          isOpen
          onClose={() => setEditing(null)}
          title={editing.index === null ? 'Add entry' : 'Edit entry'}
        >
          <ItemForm
            state={editing}
            onCancel={() => setEditing(null)}
            onSave={saveCurrentEdit}
            setState={setEditing}
            submitting={upsertMut.isPending}
          />
        </Modal>
      )}
    </div>
  )
}

interface SectionProps {
  title: string
  icon: LucideIcon
  onAdd: () => void
  className?: string
  children: React.ReactNode
}

/** A bordered layer card: icon + title + a small "+ Add", items stacked below. */
function Section({ title, icon: Icon, onAdd, className = '', children }: SectionProps) {
  return (
    <div className={`rounded-lg border border-border p-4 ${className}`}>
      <div className="mb-3 flex items-center gap-2">
        <Icon size={15} strokeWidth={1.75} className="text-muted-foreground" />
        <h3 className="text-sm font-semibold text-foreground">{title}</h3>
        <button
          type="button"
          onClick={onAdd}
          className="ml-auto inline-flex items-center gap-1 text-xs text-secondary hover:underline"
        >
          <Plus size={13} /> Add
        </button>
      </div>
      <div className="space-y-2.5">{children}</div>
    </div>
  )
}

/** One item — a light border-left row: title + muted sub + optional quote. */
function Row({
  title,
  sub,
  quote,
  onEdit,
  onRemove,
}: {
  title: string
  sub?: string | null
  quote?: string | null
  onEdit: () => void
  onRemove: () => void
}) {
  return (
    <div className="border-l-2 border-border pl-3">
      <div className="flex items-start justify-between gap-2">
        <p className="text-sm font-medium text-foreground">{title}</p>
        <ItemActions onEdit={onEdit} onRemove={onRemove} />
      </div>
      {sub && <p className="text-xs text-muted-foreground">{sub}</p>}
      {quote && <p className="mt-1 text-xs italic text-muted-foreground">"{quote}"</p>}
    </div>
  )
}

/** Empty layer — a single clickable line instead of a big centered state. */
function EmptyHint({ onAdd }: { onAdd: () => void }) {
  return (
    <button
      type="button"
      onClick={onAdd}
      className="w-full rounded-md border border-dashed border-border px-3 py-2.5 text-left text-xs text-muted-foreground transition-colors hover:border-secondary/50 hover:text-foreground"
    >
      Nothing yet
    </button>
  )
}

function ItemActions({ onEdit, onRemove }: { onEdit: () => void; onRemove: () => void }) {
  return (
    <div className="flex gap-1 shrink-0">
      <button
        aria-label="Edit"
        className="p-1 text-muted-foreground hover:text-foreground"
        onClick={onEdit}
      >
        <Pencil size={14} />
      </button>
      <button
        aria-label="Delete"
        className="p-1 text-error hover:opacity-80"
        onClick={onRemove}
      >
        <Trash2 size={14} />
      </button>
    </div>
  )
}
