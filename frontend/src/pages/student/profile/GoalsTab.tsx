/**
 * Profile → Goals tab.
 *
 * Renders the SMART goal stack grouped by category (academic / social /
 * personal). CRUD against /me/goals. Discovery-sourced goals show a small
 * provenance badge with confidence.
 */
import { useState } from 'react'
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
import { showToast } from '../../../stores/toast-store'
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
        <label className="block text-sm font-medium text-student-ink mb-1">Category</label>
        <select
          className="w-full rounded border border-divider px-3 py-2 text-sm"
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
        <label className="block text-sm font-medium text-student-ink mb-1">
          Specific <span className="text-red-600">*</span>
        </label>
        <textarea
          className="w-full rounded border border-divider px-3 py-2 text-sm"
          rows={2}
          maxLength={2000}
          value={form.specific}
          onChange={e => setForm(f => ({ ...f, specific: e.target.value }))}
          placeholder="e.g., Become a family medicine physician practicing in underserved areas."
          required
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-student-ink mb-1">Measurable</label>
        <input
          className="w-full rounded border border-divider px-3 py-2 text-sm"
          maxLength={2000}
          value={form.measurable}
          onChange={e => setForm(f => ({ ...f, measurable: e.target.value }))}
          placeholder="What does success look like in concrete terms?"
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-student-ink mb-1">Achievable notes</label>
        <input
          className="w-full rounded border border-divider px-3 py-2 text-sm"
          value={form.achievable_notes}
          onChange={e => setForm(f => ({ ...f, achievable_notes: e.target.value }))}
          placeholder="What gets in the way?"
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-student-ink mb-1">Relevance</label>
        <input
          className="w-full rounded border border-divider px-3 py-2 text-sm"
          value={form.relevant_notes}
          onChange={e => setForm(f => ({ ...f, relevant_notes: e.target.value }))}
          placeholder="Why does this matter to you?"
        />
      </div>

      <div className="grid grid-cols-2 gap-3">
        <div>
          <label className="block text-sm font-medium text-student-ink mb-1">Target date</label>
          <input
            type="date"
            className="w-full rounded border border-divider px-3 py-2 text-sm"
            value={form.time_bound}
            onChange={e => setForm(f => ({ ...f, time_bound: e.target.value }))}
          />
        </div>
        {isEdit && (
          <div>
            <label className="block text-sm font-medium text-student-ink mb-1">Status</label>
            <select
              className="w-full rounded border border-divider px-3 py-2 text-sm"
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
  const { data: goals = [], isLoading } = useQuery<StudentGoal[]>({
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
  for (const g of goals) grouped[g.category].push(g)

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold text-student-ink">SMART goals</h2>
          <p className="text-sm text-student-text mt-1">
            Specific, measurable, achievable, relevant, time-bound. Discovery-sourced goals show a
            confidence badge; you can edit anything.
          </p>
        </div>
        <Button onClick={() => setCreating(true)}>
          <Plus size={16} className="mr-1" /> Add goal
        </Button>
      </div>

      {isLoading && <div className="text-sm text-student-text">Loading…</div>}

      {!isLoading &&
        CATEGORIES.map(cat => (
          <div key={cat.key}>
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-sm font-semibold text-student-ink">{cat.label}</h3>
              <span className="text-xs text-student-text">{cat.hint}</span>
            </div>
            {grouped[cat.key].length === 0 ? (
              <Card className="text-sm text-student-text italic">
                No {cat.label.toLowerCase()} goals yet.
              </Card>
            ) : (
              <div className="space-y-2">
                {grouped[cat.key].map(g => (
                  <Card key={g.id} className="space-y-2">
                    <div className="flex items-start justify-between gap-3">
                      <div className="text-sm font-medium text-student-ink">{g.specific}</div>
                      <div className="flex gap-1 shrink-0">
                        <button
                          aria-label="Edit goal"
                          className="p-1 text-student-text hover:text-student-ink"
                          onClick={() => setEditing(g)}
                        >
                          <Pencil size={14} />
                        </button>
                        <button
                          aria-label="Delete goal"
                          className="p-1 text-red-600 hover:text-red-700"
                          onClick={() => {
                            if (confirm('Remove this goal?')) deleteMut.mutate(g.id)
                          }}
                        >
                          <Trash2 size={14} />
                        </button>
                      </div>
                    </div>
                    {(g.measurable || g.achievable_notes || g.relevant_notes) && (
                      <div className="text-xs text-student-text space-y-0.5">
                        {g.measurable && <div>📏 {g.measurable}</div>}
                        {g.achievable_notes && <div>🛠️ {g.achievable_notes}</div>}
                        {g.relevant_notes && <div>🎯 {g.relevant_notes}</div>}
                      </div>
                    )}
                    <div className="flex items-center gap-2 flex-wrap">
                      <Badge variant={STATUS_VARIANTS[g.status]} size="sm">
                        {g.status}
                      </Badge>
                      {g.time_bound && (
                        <Badge variant="neutral" size="sm">
                          by {g.time_bound}
                        </Badge>
                      )}
                      {g.source === 'discovery' && (
                        <Badge variant="info" size="sm" className="inline-flex items-center gap-1">
                          <Sparkles size={10} />
                          discovery
                          {g.confidence ? ` · ${Math.round(Number(g.confidence) * 100)}%` : ''}
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
