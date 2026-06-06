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
import { useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Pencil, Plus, ShieldCheck, Sparkles, Trash2 } from 'lucide-react'

import {
  type UpsertIdentityBody,
  getIdentity,
  regenerateIdentitySummary,
  upsertIdentity,
} from '../../../api/identity'
import AIBadge from '../../../components/ui/AIBadge'
import Button from '../../../components/ui/Button'
import Card from '../../../components/ui/Card'
import EmptyState from '../../../components/ui/EmptyState'
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

const PRIVACY_DISCLOSURE_KEY = 'unipaith.identity-privacy-ack'

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
  const navigate = useNavigate()
  const { data: identity, isLoading, isError, refetch } = useQuery<StudentIdentity>({
    queryKey: ['identity'],
    queryFn: () => getIdentity(),
  })
  const [editing, setEditing] = useState<EditingState>(null)
  const [showPrivacy, setShowPrivacy] = useState(
    () => typeof window !== 'undefined' && !window.localStorage.getItem(PRIVACY_DISCLOSURE_KEY),
  )

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
    <div className="space-y-6">
      {showPrivacy && (
        <Card className="p-4 flex items-start gap-3 bg-muted">
          <ShieldCheck size={18} className="text-secondary shrink-0 mt-0.5" />
          <div className="text-sm text-foreground">
            Identity is the deepest layer of your profile. We use this to personalize matches and
            rationales — nothing here goes to institutions until you choose to share it. Manage in{' '}
            <button
              onClick={() => navigate('/s/profile?tab=data')}
              className="font-semibold text-secondary hover:underline"
            >
              Data Rights →
            </button>
            <button
              className="ml-2 font-semibold text-secondary hover:underline"
              onClick={() => {
                window.localStorage.setItem(PRIVACY_DISCLOSURE_KEY, '1')
                setShowPrivacy(false)
              }}
            >
              Got it
            </button>
          </div>
        </Card>
      )}

      <div>
        <h2 className="text-h3 text-foreground">Identity</h2>
        <p className="text-sm text-muted-foreground mt-1">
          The deepest layer of who you are — values, worldview, and self-awareness. Discovery surfaces
          these from your conversations; edit anything.
        </p>
      </div>

      <Section
        title="Core values"
        hint="What you most consistently care about, with evidence."
        addLabel="Add value"
        onAdd={() =>
          setEditing({
            kind: 'core_values',
            index: null,
            draft: { ...(EMPTY.core_values as CoreValue) },
          })
        }
      >
        {identity.core_values.length === 0 ? (
          <Empty kind="value" addLabel="Add value" onAdd={() => setEditing({ kind: 'core_values', index: null, draft: { ...(EMPTY.core_values as CoreValue) } })} />
        ) : (
          identity.core_values.map((v, i) => (
            <Card key={i} className="p-4 space-y-1">
              <div className="flex items-start justify-between gap-2">
                <div className="text-sm font-medium text-foreground">{v.value}</div>
                <ItemActions
                  onEdit={() =>
                    setEditing({
                      kind: 'core_values',
                      index: i,
                      draft: { ...v },
                    })
                  }
                  onRemove={() => removeItem('core_values', i)}
                />
              </div>
              <div className="text-xs text-muted-foreground">{v.evidence}</div>
              {v.source_quote && (
                <div className="text-xs italic text-muted-foreground border-l-2 border-border pl-2">
                  "{v.source_quote}"
                </div>
              )}
            </Card>
          ))
        )}
      </Section>

      <Section
        title="Worldview"
        hint="Beliefs about how the world works, with the context that shaped them."
        addLabel="Add belief"
        onAdd={() =>
          setEditing({
            kind: 'worldview',
            index: null,
            draft: { ...(EMPTY.worldview as WorldviewItem) },
          })
        }
      >
        {identity.worldview.length === 0 ? (
          <Empty kind="belief" addLabel="Add belief" onAdd={() => setEditing({ kind: 'worldview', index: null, draft: { ...(EMPTY.worldview as WorldviewItem) } })} />
        ) : (
          identity.worldview.map((w, i) => (
            <Card key={i} className="p-4 space-y-1">
              <div className="flex items-start justify-between gap-2">
                <div className="text-sm font-medium text-foreground">{w.belief}</div>
                <ItemActions
                  onEdit={() =>
                    setEditing({
                      kind: 'worldview',
                      index: i,
                      draft: { ...w },
                    })
                  }
                  onRemove={() => removeItem('worldview', i)}
                />
              </div>
              <div className="text-xs text-muted-foreground">{w.context}</div>
            </Card>
          ))
        )}
      </Section>

      <Section
        title="Self-awareness"
        hint="Patterns about yourself you've noticed and the moments that revealed them."
        addLabel="Add insight"
        onAdd={() =>
          setEditing({
            kind: 'self_awareness',
            index: null,
            draft: { ...(EMPTY.self_awareness as SelfAwarenessItem) },
          })
        }
      >
        {identity.self_awareness.length === 0 ? (
          <Empty kind="insight" addLabel="Add insight" onAdd={() => setEditing({ kind: 'self_awareness', index: null, draft: { ...(EMPTY.self_awareness as SelfAwarenessItem) } })} />
        ) : (
          identity.self_awareness.map((s, i) => (
            <Card key={i} className="p-4 space-y-1">
              <div className="flex items-start justify-between gap-2">
                <div className="text-sm font-medium text-foreground">{s.insight}</div>
                <ItemActions
                  onEdit={() =>
                    setEditing({
                      kind: 'self_awareness',
                      index: i,
                      draft: { ...s },
                    })
                  }
                  onRemove={() => removeItem('self_awareness', i)}
                />
              </div>
              {s.trigger_event && <div className="text-xs text-muted-foreground">{s.trigger_event}</div>}
            </Card>
          ))
        )}
      </Section>

      {/* AI summary (§5) — generated by IdentitySummaryAgent. */}
      <Card className="p-5">
        <div className="flex items-center justify-between gap-2 mb-2">
          <div className="flex items-center gap-2">
            <h3 className="text-h3 text-foreground">AI summary</h3>
            <AIBadge />
          </div>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => regenMut.mutate()}
            loading={regenMut.isPending}
            aria-label="Regenerate summary"
          >
            <Sparkles size={14} /> Regenerate
          </Button>
        </div>
        {identity.identity_summary ? (
          <p className="text-sm text-foreground whitespace-pre-line">{identity.identity_summary}</p>
        ) : (
          <p className="text-sm text-muted-foreground">
            Once you've added a few values and beliefs, we'll synthesize a short summary of who you are.
          </p>
        )}
        {regenMut.isError && (
          <p className="text-xs text-warning mt-2">
            We couldn't reach the AI service. Showing your last summary.
          </p>
        )}
        {identity.updated_at && (
          <p className="text-xs text-muted-foreground mt-3">Updated {relativeShort(identity.updated_at) ?? 'recently'}</p>
        )}
      </Card>

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
  hint: string
  addLabel: string
  onAdd: () => void
  children: React.ReactNode
}

function Section({ title, hint, addLabel, onAdd, children }: SectionProps) {
  return (
    <div>
      <div className="flex items-center justify-between mb-2">
        <div>
          <h3 className="text-sm font-semibold text-foreground">{title}</h3>
          <span className="text-xs text-muted-foreground">{hint}</span>
        </div>
        <Button size="sm" variant="ghost" onClick={onAdd}>
          <Plus size={14} className="mr-1" /> {addLabel}
        </Button>
      </div>
      <div className="space-y-2">{children}</div>
    </div>
  )
}

function Empty({ kind, addLabel, onAdd }: { kind: string; addLabel: string; onAdd: () => void }) {
  return (
    <EmptyState
      title={`No ${kind}s added yet`}
      description={`Add your first ${kind} to start building this layer of your profile.`}
      action={{ label: addLabel, onClick: onAdd }}
    />
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
