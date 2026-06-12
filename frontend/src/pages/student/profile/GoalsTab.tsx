/**
 * Profile → Goals tab.
 *
 * Renders the SMART goal stack grouped by category (academic / social /
 * personal). CRUD against /me/goals. Discovery-sourced goals show a small
 * provenance badge with confidence.
 */
import { useState } from 'react'
import { confirmDialog } from '../../../stores/confirm-store'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Pencil, Plus, Sparkles, Trash2 } from 'lucide-react'

import {
  type CreateGoalBody,
  type UpdateGoalBody,
  createGoal,
  deleteGoal,
  listGoals,
  updateGoal,
} from '../../../api/goals'
import Badge from '../../../components/ui/Badge'
import Button from '../../../components/ui/Button'
import Card from '../../../components/ui/Card'
import Modal from '../../../components/ui/Modal'
import QueryError from '../../../components/ui/QueryError'
import { SkeletonCard } from '../../../components/ui/Skeleton'
import { showToast } from '../../../stores/toast-store'
import { formatDate } from '../../../utils/format'
import { ConfidenceDots } from './shared'
import type { GoalCategory, GoalStatus, StudentGoal } from '../../../types'

const CATEGORIES: { key: GoalCategory; label: string; hint: string }[] = [
  { key: 'academic', label: 'Academic', hint: 'Degree, major, programs.' },
  { key: 'social', label: 'Social', hint: 'Connection, networking, community.' },
  { key: 'personal', label: 'Personal', hint: 'Finance, wellbeing, growth.' },
]

const STATUS_VARIANTS: Record<GoalStatus, 'success' | 'info' | 'warning' | 'neutral'> = {
  active: 'info',
  met: 'success',
  revised: 'warning',
  dropped: 'neutral',
}

const EMPTY_FORM: CreateGoalBody = {
  category: 'academic',
  specific: '',
  measurable: null,
  achievable_notes: null,
  relevant_notes: null,
  time_bound: null,
  status: 'active',
  source: 'manual',
}

interface GoalFormProps {
  initial: CreateGoalBody | StudentGoal
  onCancel: () => void
  onSubmit: (body: CreateGoalBody | UpdateGoalBody) => void
  submitting: boolean
  isEdit: boolean
}

function GoalForm({ initial, onCancel, onSubmit, submitting, isEdit }: GoalFormProps) {
  const [form, setForm] = useState({
    category: initial.category as GoalCategory,
    specific: initial.specific ?? '',
    measurable: initial.measurable ?? '',
    achievable_notes: initial.achievable_notes ?? '',
    relevant_notes: initial.relevant_notes ?? '',
    time_bound: initial.time_bound ?? '',
    status: (initial.status ?? 'active') as GoalStatus,
  })

  const handle = (e: React.FormEvent) => {
    e.preventDefault()
    if (!form.specific.trim()) {
      showToast('Specific is required.', 'error')
      return
    }
    const payload: CreateGoalBody | UpdateGoalBody = {
      category: form.category,
      specific: form.specific.trim(),
      measurable: form.measurable.trim() || null,
      achievable_notes: form.achievable_notes.trim() || null,
      relevant_notes: form.relevant_notes.trim() || null,
      time_bound: form.time_bound || null,
      status: form.status,
    }
    onSubmit(payload)
  }

  return (
    <form onSubmit={handle} className="space-y-4">
      <div>
        <label htmlFor="goal-category" className="block text-sm font-medium text-foreground mb-1">Category</label>
        <select
          id="goal-category"
          className="w-full rounded border border-border bg-card focus:outline-none focus:ring-2 focus:ring-ring focus:border-secondary px-3 py-2 text-sm"
          value={form.category}
          onChange={e => setForm(f => ({ ...f, category: e.target.value as GoalCategory }))}
        >
          {CATEGORIES.map(c => (
            <option key={c.key} value={c.key}>
              {c.label}
            </option>
          ))}
        </select>
      </div>

      <div>
        <label htmlFor="goal-specific" className="block text-sm font-medium text-foreground mb-1">
          Specific <span className="text-error">*</span>
        </label>
        <textarea
          id="goal-specific"
          className="w-full rounded border border-border bg-card focus:outline-none focus:ring-2 focus:ring-ring focus:border-secondary px-3 py-2 text-sm"
          rows={2}
          maxLength={2000}
          value={form.specific}
          onChange={e => setForm(f => ({ ...f, specific: e.target.value }))}
          placeholder="e.g., Become a family medicine physician practicing in underserved areas."
          required
        />
      </div>

      <div>
        <label htmlFor="goal-measurable" className="block text-sm font-medium text-foreground mb-1">Measurable</label>
        <input
          id="goal-measurable"
          className="w-full rounded border border-border bg-card focus:outline-none focus:ring-2 focus:ring-ring focus:border-secondary px-3 py-2 text-sm"
          maxLength={2000}
          value={form.measurable}
          onChange={e => setForm(f => ({ ...f, measurable: e.target.value }))}
          placeholder="What does success look like in concrete terms?"
        />
      </div>

      <div>
        <label htmlFor="goal-achievable" className="block text-sm font-medium text-foreground mb-1">Achievable notes</label>
        <input
          id="goal-achievable"
          className="w-full rounded border border-border bg-card focus:outline-none focus:ring-2 focus:ring-ring focus:border-secondary px-3 py-2 text-sm"
          value={form.achievable_notes}
          onChange={e => setForm(f => ({ ...f, achievable_notes: e.target.value }))}
          placeholder="What gets in the way?"
        />
      </div>

      <div>
        <label htmlFor="goal-relevant" className="block text-sm font-medium text-foreground mb-1">Relevance</label>
        <input
          id="goal-relevant"
          className="w-full rounded border border-border bg-card focus:outline-none focus:ring-2 focus:ring-ring focus:border-secondary px-3 py-2 text-sm"
          value={form.relevant_notes}
          onChange={e => setForm(f => ({ ...f, relevant_notes: e.target.value }))}
          placeholder="Why does this matter to you?"
        />
      </div>

      <div className="grid grid-cols-2 gap-3">
        <div>
          <label htmlFor="goal-time-bound" className="block text-sm font-medium text-foreground mb-1">Target date</label>
          <input
            id="goal-time-bound"
            type="date"
            className="w-full rounded border border-border bg-card focus:outline-none focus:ring-2 focus:ring-ring focus:border-secondary px-3 py-2 text-sm"
            value={form.time_bound}
            onChange={e => setForm(f => ({ ...f, time_bound: e.target.value }))}
          />
        </div>
        {isEdit && (
          <div>
            <label htmlFor="goal-status" className="block text-sm font-medium text-foreground mb-1">Status</label>
            <select
              id="goal-status"
              className="w-full rounded border border-border bg-card focus:outline-none focus:ring-2 focus:ring-ring focus:border-secondary px-3 py-2 text-sm"
              value={form.status}
              onChange={e => setForm(f => ({ ...f, status: e.target.value as GoalStatus }))}
            >
              <option value="active">Active</option>
              <option value="met">Met</option>
              <option value="revised">Revised</option>
              <option value="dropped">Dropped</option>
            </select>
          </div>
        )}
      </div>

      <div className="flex justify-end gap-2 pt-2">
        <Button type="button" variant="ghost" onClick={onCancel}>
          Cancel
        </Button>
        <Button type="submit" loading={submitting}>
          {isEdit ? 'Save' : 'Add goal'}
        </Button>
      </div>
    </form>
  )
}

export default function GoalsTab() {
  const qc = useQueryClient()
  const { data: goals = [], isLoading, isError, refetch } = useQuery<StudentGoal[]>({
    queryKey: ['goals'],
    queryFn: () => listGoals(),
  })

  const [creating, setCreating] = useState(false)
  const [editing, setEditing] = useState<StudentGoal | null>(null)

  const onSettled = () => qc.invalidateQueries({ queryKey: ['goals'] })

  const createMut = useMutation({
    mutationFn: (body: CreateGoalBody) => createGoal(body),
    onSuccess: () => {
      showToast('Goal added.', 'success')
      setCreating(false)
    },
    onError: (err: unknown) => showToast((err as Error).message ?? 'Could not add goal.', 'error'),
    onSettled,
  })

  const updateMut = useMutation({
    mutationFn: ({ id, body }: { id: string; body: UpdateGoalBody }) => updateGoal(id, body),
    onSuccess: () => {
      showToast('Goal updated.', 'success')
      setEditing(null)
    },
    onError: (err: unknown) =>
      showToast((err as Error).message ?? 'Could not update goal.', 'error'),
    onSettled,
  })

  const deleteMut = useMutation({
    mutationFn: (id: string) => deleteGoal(id),
    onSuccess: () => showToast('Goal removed.', 'success'),
    onError: (err: unknown) =>
      showToast((err as Error).message ?? 'Could not delete goal.', 'error'),
    onSettled,
  })

  const grouped: Record<GoalCategory, StudentGoal[]> = {
    academic: [],
    social: [],
    personal: [],
  }
  for (const g of goals) if (grouped[g.category]) grouped[g.category].push(g)

  if (isError) return <QueryError onRetry={() => refetch()} />

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold text-foreground">Your goals</h2>
          <p className="text-sm text-muted-foreground mt-1">
            Specific, measurable, achievable, relevant, time-bound. Discovery-sourced goals show a
            confidence badge; you can edit anything.
          </p>
        </div>
        <Button onClick={() => setCreating(true)}>
          <Plus size={16} className="mr-1" /> Add goal
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
        CATEGORIES.map(cat => (
          <div key={cat.key}>
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-sm font-semibold text-foreground">{cat.label}</h3>
              <span className="text-xs text-muted-foreground">{cat.hint}</span>
            </div>
            {grouped[cat.key].length === 0 ? (
              <Card pad={false} className="p-4 text-sm text-muted-foreground">
                No {cat.label.toLowerCase()} goals yet — add one above.
              </Card>
            ) : (
              <div className="space-y-2">
                {grouped[cat.key].map(g => (
                  <Card pad={false} key={g.id} className="p-4 space-y-2">
                    <div className="flex items-start justify-between gap-3">
                      <div className="text-sm font-medium text-foreground">{g.specific}</div>
                      <div className="flex gap-1 shrink-0">
                        <button
                          aria-label="Edit goal"
                          className="p-1 text-muted-foreground hover:text-foreground"
                          onClick={() => setEditing(g)}
                        >
                          <Pencil size={14} />
                        </button>
                        <button
                          aria-label="Delete goal"
                          className="p-1 text-error hover:opacity-80"
                          onClick={async () => {
                            if (await confirmDialog({ title: 'Remove this goal?', body: 'You can add it again later.', confirmLabel: 'Remove', destructive: true })) deleteMut.mutate(g.id)
                          }}
                        >
                          <Trash2 size={14} />
                        </button>
                      </div>
                    </div>
                    {(g.measurable || g.achievable_notes || g.relevant_notes) && (
                      <dl className="text-xs text-muted-foreground space-y-1">
                        {g.measurable && (
                          <div className="flex gap-1.5"><dt className="font-semibold text-foreground shrink-0">Measurable</dt><dd>{g.measurable}</dd></div>
                        )}
                        {g.achievable_notes && (
                          <div className="flex gap-1.5"><dt className="font-semibold text-foreground shrink-0">Achievable</dt><dd>{g.achievable_notes}</dd></div>
                        )}
                        {g.relevant_notes && (
                          <div className="flex gap-1.5"><dt className="font-semibold text-foreground shrink-0">Relevant</dt><dd>{g.relevant_notes}</dd></div>
                        )}
                      </dl>
                    )}
                    <div className="flex items-center gap-2 flex-wrap">
                      <Badge variant={STATUS_VARIANTS[g.status]} size="sm">
                        {g.status}
                      </Badge>
                      {g.time_bound && (
                        <Badge variant="neutral" size="sm">
                          by {formatDate(g.time_bound)}
                        </Badge>
                      )}
                      {g.source === 'discovery' && (
                        <span className="inline-flex items-center gap-1.5">
                          <Badge variant="info" size="sm" className="inline-flex items-center gap-1">
                            <Sparkles size={10} /> discovery
                          </Badge>
                          {g.confidence != null && (
                            <ConfidenceDots filled={Math.round(Number(g.confidence) * 5)} showLabel={false} />
                          )}
                        </span>
                      )}
                    </div>
                  </Card>
                ))}
              </div>
            )}
          </div>
        ))}

      {creating && (
        <Modal isOpen onClose={() => setCreating(false)} title="Add goal">
          <GoalForm
            initial={EMPTY_FORM}
            onCancel={() => setCreating(false)}
            onSubmit={body => createMut.mutate(body as CreateGoalBody)}
            submitting={createMut.isPending}
            isEdit={false}
          />
        </Modal>
      )}

      {editing && (
        <Modal isOpen onClose={() => setEditing(null)} title="Edit goal">
          <GoalForm
            initial={editing}
            onCancel={() => setEditing(null)}
            onSubmit={body => updateMut.mutate({ id: editing.id, body: body as UpdateGoalBody })}
            submitting={updateMut.isPending}
            isEdit
          />
        </Modal>
      )}
    </div>
  )
}
