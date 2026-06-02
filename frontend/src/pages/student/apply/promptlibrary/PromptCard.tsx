// Spec 42 §3.19 — a single prompt in the catalog. Shows channel/format/limit,
// the student's draft status, and STAR completeness (server flags) at a glance.
import { Clock, FileText, Link2, PenLine } from 'lucide-react'

import Badge from '../../../../components/ui/Badge'
import Card from '../../../../components/ui/Card'
import type { BehavioralPrompt, BehavioralResponse } from '../../../../types/promptLibrary'

import { CHANNEL_LABELS, DRAFT_META } from './constants'
import StarChips from './StarChips'

function limitLabel(p: BehavioralPrompt): string | null {
  if (p.time_limit_seconds) {
    const s = p.time_limit_seconds
    return s >= 60 ? `${Math.round(s / 60)} min` : `${s}s`
  }
  if (p.word_limit) return `${p.word_limit} words`
  return null
}

export default function PromptCard({
  prompt,
  response,
  onEdit,
}: {
  prompt: BehavioralPrompt
  response?: BehavioralResponse
  onEdit: (p: BehavioralPrompt) => void
}) {
  const draft = response ? DRAFT_META[response.draft_status] : DRAFT_META.none
  const limit = limitLabel(prompt)
  const starFlags = response
    ? {
        situation: response.star_situation_present,
        task: response.star_task_present,
        action: response.star_action_present,
        result: response.star_result_present,
        reflection: response.star_reflection_present,
      }
    : null

  return (
    <Card
      interactive
      variant="card-raised"
      onClick={() => onEdit(prompt)}
      className="flex flex-col gap-2.5"
    >
      <div className="flex items-start justify-between gap-2">
        <h4 className="text-sm font-semibold leading-snug text-foreground">{prompt.title}</h4>
        <Badge variant={draft.variant} size="sm">
          {draft.label}
        </Badge>
      </div>

      <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-muted-foreground">
        <span className="inline-flex items-center gap-1">
          <FileText size={12} /> {CHANNEL_LABELS[prompt.target_channel]}
        </span>
        {limit && (
          <span className="inline-flex items-center gap-1">
            <Clock size={12} /> {limit}
          </span>
        )}
        {prompt.format_required !== 'freeform' && (
          <span className="font-medium text-secondary">{prompt.format_required}</span>
        )}
        {response?.linked_story_id && (
          <span className="inline-flex items-center gap-1 text-secondary">
            <Link2 size={12} /> Story linked
          </span>
        )}
      </div>

      <div className="mt-auto flex items-center justify-between pt-1">
        {starFlags ? (
          <StarChips flags={starFlags} size="sm" />
        ) : (
          <span className="inline-flex items-center gap-1 text-xs text-muted-foreground">
            <PenLine size={12} /> Not started
          </span>
        )}
        <span className="text-xs font-medium text-secondary">{response ? 'Edit' : 'Answer'}</span>
      </div>
    </Card>
  )
}
