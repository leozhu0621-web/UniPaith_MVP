// Spec 42 §3.20 — story-bank create/edit (right sheet).
import { useEffect, useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'

import { createStory, updateStory } from '../../../../api/prompt-library'
import Button from '../../../../components/ui/Button'
import Sheet from '../../../../components/ui/Sheet'
import { showToast } from '../../../../stores/toast-store'
import type { Story, StoryInput } from '../../../../types/promptLibrary'

import {
  COMPETENCIES,
  COMPETENCY_LABELS,
  CONTEXT_TAGS,
  ROLE_TYPES,
  STAKEHOLDER_TYPES,
} from './constants'

const EMPTY: StoryInput = {
  title: '',
  summary: '',
  primary_competency: null,
  secondary_competency: null,
  competency_tags: [],
  context_tags: [],
  role_type: null,
  difficulty_tier: null,
  scale_tier: null,
  duration: '',
  evidence_link: '',
  referenceable_contact_flag: false,
}

const field =
  'w-full rounded-md border border-border bg-background px-3 py-2 text-sm text-foreground focus:border-secondary focus:outline-none'

export default function StoryEditor({
  story,
  isOpen,
  onClose,
}: {
  story: Story | null
  isOpen: boolean
  onClose: () => void
}) {
  const qc = useQueryClient()
  const [form, setForm] = useState<StoryInput>(EMPTY)

  useEffect(() => {
    if (!isOpen) return
    setForm(
      story
        ? {
            title: story.title,
            summary: story.summary ?? '',
            primary_competency: story.primary_competency,
            secondary_competency: story.secondary_competency,
            competency_tags: story.competency_tags ?? [],
            context_tags: story.context_tags ?? [],
            role_type: story.role_type,
            difficulty_tier: story.difficulty_tier,
            scale_tier: story.scale_tier,
            duration: story.duration ?? '',
            evidence_link: story.evidence_link ?? '',
            referenceable_contact_flag: story.referenceable_contact_flag,
          }
        : EMPTY,
    )
  }, [isOpen, story])

  const set = <K extends keyof StoryInput>(k: K, v: StoryInput[K]) =>
    setForm(f => ({ ...f, [k]: v }))

  const toggleArr = (k: 'competency_tags' | 'context_tags', v: string) =>
    setForm(f => {
      const cur = new Set(f[k] ?? [])
      if (cur.has(v)) cur.delete(v)
      else cur.add(v)
      return { ...f, [k]: [...cur] }
    })

  const save = useMutation({
    mutationFn: () => (story ? updateStory(story.id, form) : createStory(form)),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['prompt-library'] })
      showToast(story ? 'Story updated.' : 'Story added.', 'success')
      onClose()
    },
    onError: (e: unknown) => showToast((e as Error).message ?? 'Could not save.', 'error'),
  })

  return (
    <Sheet
      isOpen={isOpen}
      onClose={onClose}
      title={story ? 'Edit story' : 'New story'}
      footer={
        <div className="flex justify-end gap-2">
          <Button variant="tertiary" size="sm" onClick={onClose}>
            Cancel
          </Button>
          <Button
            variant="secondary"
            size="sm"
            loading={save.isPending}
            disabled={!form.title.trim()}
            onClick={() => save.mutate()}
          >
            {story ? 'Save changes' : 'Add story'}
          </Button>
        </div>
      }
    >
      <div className="space-y-4">
        <div>
          <label className="mb-1 block text-sm font-medium text-foreground">
            Title <span className="text-error">*</span>
          </label>
          <input
            className={field}
            value={form.title}
            maxLength={255}
            onChange={e => set('title', e.target.value)}
            placeholder="e.g., Rebuilt a failing robotics team"
          />
        </div>

        <div>
          <label className="mb-1 block text-sm font-medium text-foreground">Summary</label>
          <textarea
            className={`${field} min-h-[90px] resize-y`}
            value={form.summary ?? ''}
            maxLength={8000}
            onChange={e => set('summary', e.target.value)}
            placeholder="A few sentences capturing the situation, your role, and the outcome."
          />
        </div>

        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="mb-1 block text-sm font-medium text-foreground">
              Primary competency
            </label>
            <select
              className={field}
              value={form.primary_competency ?? ''}
              onChange={e => set('primary_competency', e.target.value || null)}
            >
              <option value="">—</option>
              {COMPETENCIES.map(c => (
                <option key={c} value={c}>
                  {COMPETENCY_LABELS[c]}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium text-foreground">Role</label>
            <select
              className={field}
              value={form.role_type ?? ''}
              onChange={e => set('role_type', e.target.value || null)}
            >
              <option value="">—</option>
              {ROLE_TYPES.map(r => (
                <option key={r} value={r} className="capitalize">
                  {r}
                </option>
              ))}
            </select>
          </div>
        </div>

        <div>
          <label className="mb-1 block text-sm font-medium text-foreground">
            Competency tags
          </label>
          <div className="flex flex-wrap gap-1.5">
            {COMPETENCIES.map(c => {
              const on = (form.competency_tags ?? []).includes(c)
              return (
                <button
                  key={c}
                  type="button"
                  onClick={() => toggleArr('competency_tags', c)}
                  className={`rounded-full px-2.5 py-1 text-xs font-medium transition-colors ${
                    on ? 'bg-secondary text-secondary-foreground' : 'bg-muted text-muted-foreground hover:bg-muted'
                  }`}
                >
                  {COMPETENCY_LABELS[c]}
                </button>
              )
            })}
          </div>
        </div>

        <div>
          <label className="mb-1 block text-sm font-medium text-foreground">Context</label>
          <div className="flex flex-wrap gap-1.5">
            {CONTEXT_TAGS.map(c => {
              const on = (form.context_tags ?? []).includes(c)
              return (
                <button
                  key={c}
                  type="button"
                  onClick={() => toggleArr('context_tags', c)}
                  className={`rounded-full px-2.5 py-1 text-xs font-medium capitalize transition-colors ${
                    on ? 'bg-secondary text-secondary-foreground' : 'bg-muted text-muted-foreground hover:bg-muted'
                  }`}
                >
                  {c}
                </button>
              )
            })}
          </div>
        </div>

        <div className="grid grid-cols-2 gap-3">
          <TierSelect
            label="Difficulty"
            value={form.difficulty_tier}
            onChange={v => set('difficulty_tier', v)}
          />
          <TierSelect label="Scale" value={form.scale_tier} onChange={v => set('scale_tier', v)} />
        </div>

        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="mb-1 block text-sm font-medium text-foreground">Stakeholder</label>
            <select
              className={field}
              value={form.stakeholder_type ?? ''}
              onChange={e => set('stakeholder_type', e.target.value || null)}
            >
              <option value="">—</option>
              {STAKEHOLDER_TYPES.map(s => (
                <option key={s} value={s} className="capitalize">
                  {s}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium text-foreground">Duration</label>
            <input
              className={field}
              value={form.duration ?? ''}
              maxLength={80}
              onChange={e => set('duration', e.target.value)}
              placeholder="e.g., 6 months"
            />
          </div>
        </div>

        <div>
          <label className="mb-1 block text-sm font-medium text-foreground">
            Evidence link (optional)
          </label>
          <input
            className={field}
            value={form.evidence_link ?? ''}
            maxLength={500}
            onChange={e => set('evidence_link', e.target.value)}
            placeholder="https://…"
          />
        </div>

        <label className="flex items-center gap-2 text-sm text-foreground">
          <input
            type="checkbox"
            checked={!!form.referenceable_contact_flag}
            onChange={e => set('referenceable_contact_flag', e.target.checked)}
            className="h-4 w-4 rounded border-border text-secondary focus:ring-cobalt"
          />
          Someone can vouch for this story
        </label>
      </div>
    </Sheet>
  )
}

function TierSelect({
  label,
  value,
  onChange,
}: {
  label: string
  value: number | null | undefined
  onChange: (v: number | null) => void
}) {
  return (
    <div>
      <label className="mb-1 block text-sm font-medium text-foreground">{label} (1–5)</label>
      <select
        className={field}
        value={value ?? ''}
        onChange={e => onChange(e.target.value ? Number(e.target.value) : null)}
      >
        <option value="">—</option>
        {[1, 2, 3, 4, 5].map(n => (
          <option key={n} value={n}>
            {n}
          </option>
        ))}
      </select>
    </div>
  )
}
