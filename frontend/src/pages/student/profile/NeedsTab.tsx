/**
 * Profile → Needs tab.
 *
 * Renders the Maslow-keyed needs map. Five tiers, severity badges.
 * Discovery / inferred sources show provenance + confidence.
 */
import { useState } from 'react'
import { confirmDialog } from '../../../stores/confirm-store'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Pencil, Plus, Sparkles, Trash2 } from 'lucide-react'

import {
  type CreateNeedBody,
  type UpdateNeedBody,
  createNeed,
  deleteNeed,
  listNeeds,
  updateNeed,
} from '../../../api/needs'
import Badge from '../../../components/ui/Badge'
import Button from '../../../components/ui/Button'
import Card from '../../../components/ui/Card'
import Modal from '../../../components/ui/Modal'
import QueryError from '../../../components/ui/QueryError'
import { SkeletonCard } from '../../../components/ui/Skeleton'
import { showToast } from '../../../stores/toast-store'
import type { MaslowLevel, NeedSeverity, StudentNeed } from '../../../types'

// Maslow's hierarchy — bottom-up. We render top-down (self-actualization
// first) because the page reads top-to-bottom and the higher tiers carry
// the differentiating signal (community, scholarship, mental support).
const MASLOW_TIERS: { key: MaslowLevel; label: string; hint: string }[] = [
  {
    key: 'self_actualization',
    label: 'Self-actualization',
    hint: 'Events, alums, career support, oversea education.',
  },
  {
    key: 'self_esteem',
    label: 'Self-esteem',
    hint: 'Scholarship, peer-stress, environment.',
  },
  {
    key: 'social',
    label: 'Social',
    hint: 'Community, culture, diversity, inclusion.',
  },
  {
    key: 'safety',
    label: 'Safety',
    hint: 'Healthcare, finance, environment, policy.',
  },
  {
    key: 'physiological',
    label: 'Physiological',
    hint: 'Housing, food.',
  },
]

const SEVERITY_VARIANTS: Record<NeedSeverity, 'warning' | 'info' | 'neutral'> = {
  must_have: 'warning',
  strong_preference: 'info',
  nice_to_have: 'neutral',
}

const SEVERITY_LABELS: Record<NeedSeverity, string> = {
  must_have: 'must have',
  strong_preference: 'strong preference',
  nice_to_have: 'nice to have',
}

const EMPTY_FORM: CreateNeedBody = {
  maslow_level: 'safety',
  need_type: '',
  signal: '',
  severity: 'strong_preference',
  source: 'manual',
}

interface NeedFormProps {
  initial: CreateNeedBody | StudentNeed
  onCancel: () => void
  onSubmit: (body: CreateNeedBody | UpdateNeedBody) => void
  submitting: boolean
  isEdit: boolean
}

function NeedForm({ initial, onCancel, onSubmit, submitting, isEdit }: NeedFormProps) {
  const [form, setForm] = useState({
    maslow_level: initial.maslow_level as MaslowLevel,
    need_type: initial.need_type ?? '',
    signal: initial.signal ?? '',
    severity: initial.severity as NeedSeverity,
    source_quote: ('source_quote' in initial ? initial.source_quote : null) ?? '',
  })

  const handle = (e: React.FormEvent) => {
    e.preventDefault()
    if (!form.need_type.trim()) {
      showToast('Need type is required.', 'error')
      return
    }
    if (!form.signal.trim()) {
      showToast('Signal is required.', 'error')
      return
    }
    onSubmit({
      maslow_level: form.maslow_level,
      need_type: form.need_type.trim(),
      signal: form.signal.trim(),
      severity: form.severity,
      source_quote: form.source_quote.trim() || null,
    })
  }

  return (
    <form onSubmit={handle} className="space-y-4">
      <div className="grid grid-cols-2 gap-3">
        <div>
          <label htmlFor="need-maslow-level" className="block text-sm font-medium text-foreground mb-1">Maslow tier</label>
          <select
            id="need-maslow-level"
            className="w-full rounded border border-border bg-card focus:outline-none focus:ring-2 focus:ring-ring focus:border-secondary px-3 py-2 text-sm"
            value={form.maslow_level}
            onChange={e => setForm(f => ({ ...f, maslow_level: e.target.value as MaslowLevel }))}
          >
            {MASLOW_TIERS.map(t => (
              <option key={t.key} value={t.key}>
                {t.label}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label htmlFor="need-severity" className="block text-sm font-medium text-foreground mb-1">Severity</label>
          <select
            id="need-severity"
            className="w-full rounded border border-border bg-card focus:outline-none focus:ring-2 focus:ring-ring focus:border-secondary px-3 py-2 text-sm"
            value={form.severity}
            onChange={e => setForm(f => ({ ...f, severity: e.target.value as NeedSeverity }))}
          >
            <option value="must_have">Must have</option>
            <option value="strong_preference">Strong preference</option>
            <option value="nice_to_have">Nice to have</option>
          </select>
        </div>
      </div>

      <div>
        <label htmlFor="need-type" className="block text-sm font-medium text-foreground mb-1">
          Need type <span className="text-error">*</span>
        </label>
        <input
          id="need-type"
          className="w-full rounded border border-border bg-card focus:outline-none focus:ring-2 focus:ring-ring focus:border-secondary px-3 py-2 text-sm"
          maxLength={120}
          value={form.need_type}
          onChange={e => setForm(f => ({ ...f, need_type: e.target.value }))}
          placeholder="e.g., on-campus housing, scholarships for first-gen, mental health support"
          required
        />
      </div>

      <div>
        <label htmlFor="need-signal" className="block text-sm font-medium text-foreground mb-1">
          Signal <span className="text-error">*</span>
        </label>
        <textarea
          id="need-signal"
          className="w-full rounded border border-border bg-card focus:outline-none focus:ring-2 focus:ring-ring focus:border-secondary px-3 py-2 text-sm"
          rows={2}
          maxLength={4000}
          value={form.signal}
          onChange={e => setForm(f => ({ ...f, signal: e.target.value }))}
          placeholder="What did you say or notice that points to this need?"
          required
        />
      </div>

      <div>
        <label htmlFor="need-source-quote" className="block text-sm font-medium text-foreground mb-1">Source quote</label>
        <input
          id="need-source-quote"
          className="w-full rounded border border-border bg-card focus:outline-none focus:ring-2 focus:ring-ring focus:border-secondary px-3 py-2 text-sm"
          value={form.source_quote}
          onChange={e => setForm(f => ({ ...f, source_quote: e.target.value }))}
          placeholder="Optional — direct quote from a conversation or note."
        />
      </div>

      <div className="flex justify-end gap-2 pt-2">
        <Button type="button" variant="ghost" onClick={onCancel}>
          Cancel
        </Button>
        <Button type="submit" loading={submitting}>
          {isEdit ? 'Save' : 'Add need'}
        </Button>
      </div>
    </form>
  )
}

export default function NeedsTab() {
  const qc = useQueryClient()
  const { data: needs = [], isLoading, isError, refetch } = useQuery<StudentNeed[]>({
    queryKey: ['needs'],
    queryFn: () => listNeeds(),
  })

  const [creating, setCreating] = useState(false)
  const [editing, setEditing] = useState<StudentNeed | null>(null)

  const onSettled = () => qc.invalidateQueries({ queryKey: ['needs'] })

  const createMut = useMutation({
    mutationFn: (body: CreateNeedBody) => createNeed(body),
    onSuccess: () => {
      showToast('Need added.', 'success')
      setCreating(false)
    },
    onError: (err: unknown) => showToast((err as Error).message ?? 'Could not add need.', 'error'),
    onSettled,
  })
  const updateMut = useMutation({
    mutationFn: ({ id, body }: { id: string; body: UpdateNeedBody }) => updateNeed(id, body),
    onSuccess: () => {
      showToast('Need updated.', 'success')
      setEditing(null)
    },
    onError: (err: unknown) =>
      showToast((err as Error).message ?? 'Could not update need.', 'error'),
    onSettled,
  })
  const deleteMut = useMutation({
    mutationFn: (id: string) => deleteNeed(id),
    onSuccess: () => showToast('Need removed.', 'success'),
    onError: (err: unknown) =>
      showToast((err as Error).message ?? 'Could not delete need.', 'error'),
    onSettled,
  })

  const grouped: Record<MaslowLevel, StudentNeed[]> = {
    physiological: [],
    safety: [],
    social: [],
    self_esteem: [],
    self_actualization: [],
  }
  for (const n of needs) if (grouped[n.maslow_level]) grouped[n.maslow_level].push(n)

  if (isError) return <QueryError onRetry={() => refetch()} />

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold text-foreground">Needs map</h2>
          <p className="text-sm text-muted-foreground mt-1">
            What you need from a program and campus — ranked by how much it matters to you.
            Discovery infers; you can edit anything.
          </p>
        </div>
        <Button onClick={() => setCreating(true)}>
          <Plus size={16} className="mr-1" /> Add need
        </Button>
      </div>

      {isLoading && (
        <div className="space-y-3">
          <SkeletonCard />
          <SkeletonCard />
          <SkeletonCard />
        </div>
      )}

      {!isLoading &&
        MASLOW_TIERS.map(tier => (
          <div key={tier.key}>
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-sm font-semibold text-foreground">{tier.label}</h3>
              <span className="text-xs text-muted-foreground">{tier.hint}</span>
            </div>
            {grouped[tier.key].length === 0 ? (
              <Card pad={false} className="p-4 text-sm text-muted-foreground">
                No {tier.label.toLowerCase()} signals yet — add one above.
              </Card>
            ) : (
              <div className="space-y-2">
                {grouped[tier.key].map(n => (
                  <Card pad={false} key={n.id} className="p-4 space-y-2">
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <div className="text-sm font-medium text-foreground">{n.need_type}</div>
                        <div className="text-xs text-muted-foreground mt-0.5">{n.signal}</div>
                        {n.source_quote && (
                          <div className="text-xs text-muted-foreground mt-1 italic border-l-2 border-border pl-2">
                            "{n.source_quote}"
                          </div>
                        )}
                      </div>
                      <div className="flex gap-1 shrink-0">
                        <button
                          aria-label="Edit need"
                          className="p-1 text-muted-foreground hover:text-foreground"
                          onClick={() => setEditing(n)}
                        >
                          <Pencil size={14} />
                        </button>
                        <button
                          aria-label="Delete need"
                          className="p-1 text-error hover:opacity-80"
                          onClick={async () => {
                            if (await confirmDialog({ title: 'Remove this need?', body: 'You can add it again later.', confirmLabel: 'Remove', destructive: true })) deleteMut.mutate(n.id)
                          }}
                        >
                          <Trash2 size={14} />
                        </button>
                      </div>
                    </div>
                    <div className="flex items-center gap-2 flex-wrap">
                      <Badge variant={SEVERITY_VARIANTS[n.severity]} size="sm">
                        {SEVERITY_LABELS[n.severity]}
                      </Badge>
                      {(n.source === 'discovery' || n.source === 'inferred') && (
                        <Badge variant="info" size="sm" className="inline-flex items-center gap-1">
                          <Sparkles size={10} />
                          {n.source}
                          {n.confidence ? ` · ${Math.round(Number(n.confidence) * 100)}%` : ''}
                        </Badge>
                      )}
                    </div>
                  </Card>
                ))}
              </div>
            )}
          </div>
        ))}

      {creating && (
        <Modal isOpen onClose={() => setCreating(false)} title="Add need">
          <NeedForm
            initial={EMPTY_FORM}
            onCancel={() => setCreating(false)}
            onSubmit={body => createMut.mutate(body as CreateNeedBody)}
            submitting={createMut.isPending}
            isEdit={false}
          />
        </Modal>
      )}

      {editing && (
        <Modal isOpen onClose={() => setEditing(null)} title="Edit need">
          <NeedForm
            initial={editing}
            onCancel={() => setEditing(null)}
            onSubmit={body => updateMut.mutate({ id: editing.id, body: body as UpdateNeedBody })}
            submitting={updateMut.isPending}
            isEdit
          />
        </Modal>
      )}
    </div>
  )
}
