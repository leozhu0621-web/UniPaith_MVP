// Spec 42 §3.20 — one story-bank card. Reusable narrative unit mapped to prompts.
import { Pencil, Star, Trash2, Users } from 'lucide-react'

import Card from '../../../../components/ui/Card'
import type { Story } from '../../../../types/promptLibrary'

import { COMPETENCY_LABELS } from './constants'

export default function StoryCard({
  story,
  onEdit,
  onDelete,
}: {
  story: Story
  onEdit: (s: Story) => void
  onDelete: (s: Story) => void
}) {
  return (
    <Card variant="card-raised" className="flex flex-col gap-2">
      <div className="flex items-start justify-between gap-2">
        <h4 className="text-sm font-semibold leading-snug text-foreground">{story.title}</h4>
        <div className="flex shrink-0 gap-1">
          <button
            type="button"
            onClick={() => onEdit(story)}
            className="rounded p-1 text-muted-foreground transition-colors hover:bg-muted hover:text-secondary"
            aria-label="Edit story"
          >
            <Pencil size={14} />
          </button>
          <button
            type="button"
            onClick={() => onDelete(story)}
            className="rounded p-1 text-muted-foreground transition-colors hover:bg-error-soft hover:text-error"
            aria-label="Delete story"
          >
            <Trash2 size={14} />
          </button>
        </div>
      </div>

      {story.summary && (
        <p className="line-clamp-2 text-xs text-muted-foreground">{story.summary}</p>
      )}

      <div className="mt-auto flex flex-wrap items-center gap-1.5 pt-1">
        {story.primary_competency && (
          <span className="rounded-full bg-secondary/10 px-2 py-0.5 text-xs font-medium text-secondary">
            {COMPETENCY_LABELS[story.primary_competency] ?? story.primary_competency}
          </span>
        )}
        {(story.context_tags ?? []).slice(0, 3).map(t => (
          <span
            key={t}
            className="rounded-full bg-muted px-2 py-0.5 text-xs capitalize text-muted-foreground"
          >
            {t}
          </span>
        ))}
        {story.difficulty_tier != null && (
          <span className="inline-flex items-center gap-0.5 text-xs text-muted-foreground">
            <Star size={11} /> {story.difficulty_tier}/5
          </span>
        )}
        {story.scale_tier != null && (
          <span className="inline-flex items-center gap-0.5 text-xs text-muted-foreground">
            <Users size={11} /> {story.scale_tier}/5
          </span>
        )}
      </div>
    </Card>
  )
}
