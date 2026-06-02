// Spec 42 §3.19 — response editor (right sheet). The STAR chips light up live as
// the student writes (client preview); the server re-derives the authoritative
// flags on save. Feedback-only ethos: we coach structure, never ghost-write.
import { useEffect, useMemo, useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { Clock, FileText } from 'lucide-react'

import { upsertResponse } from '../../../../api/prompt-library'
import Button from '../../../../components/ui/Button'
import Sheet from '../../../../components/ui/Sheet'
import { showToast } from '../../../../stores/toast-store'
import type {
  BehavioralPrompt,
  BehavioralResponse,
  DraftStatus,
  Story,
} from '../../../../types/promptLibrary'

import { CHANNEL_LABELS, previewStar, STAR_ELEMENTS, starCount, wordCount } from './constants'
import StarChips from './StarChips'

const STATUS_OPTIONS: DraftStatus[] = ['draft', 'revised', 'final']

export default function ResponseEditor({
  prompt,
  response,
  stories,
  isOpen,
  onClose,
}: {
  prompt: BehavioralPrompt | null
  response?: BehavioralResponse
  stories: Story[]
  isOpen: boolean
  onClose: () => void
}) {
  const qc = useQueryClient()
  const [text, setText] = useState('')
  const [status, setStatus] = useState<DraftStatus>('draft')
  const [confidence, setConfidence] = useState<number | null>(null)
  const [storyId, setStoryId] = useState<string>('')

  useEffect(() => {
    if (!isOpen) return
    setText(response?.response_text ?? '')
    setStatus(response && response.draft_status !== 'none' ? response.draft_status : 'draft')
    setConfidence(response?.confidence_self_rating ?? null)
    setStoryId(response?.linked_story_id ?? '')
  }, [isOpen, response])

  const star = useMemo(() => previewStar(text), [text])
  const wc = wordCount(text)
  const overLimit = prompt?.word_limit ? wc > Math.round(prompt.word_limit * 1.15) : false

  const save = useMutation({
    mutationFn: () =>
      upsertResponse(prompt!.prompt_key, {
        response_text: text,
        draft_status: status,
        confidence_self_rating: confidence,
        linked_story_id: storyId || null,
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['prompt-library'] })
      showToast('Saved.', 'success')
      onClose()
    },
    onError: (e: unknown) => showToast((e as Error).message ?? 'Could not save.', 'error'),
  })

  if (!prompt) return null
  const missing = STAR_ELEMENTS.filter(el => !star[el.key]).map(el => el.label)
  const limit = prompt.time_limit_seconds
    ? prompt.time_limit_seconds >= 60
      ? `${Math.round(prompt.time_limit_seconds / 60)} min`
      : `${prompt.time_limit_seconds}s`
    : prompt.word_limit
      ? `${prompt.word_limit} words`
      : null

  return (
    <Sheet
      isOpen={isOpen}
      onClose={onClose}
      title="Practice response"
      widthClass="sm:max-w-[560px]"
      footer={
        <div className="flex items-center justify-between gap-3">
          <span className="text-xs text-student-text">
            {wc} word{wc === 1 ? '' : 's'}
            {prompt.word_limit ? ` · target ${prompt.word_limit}` : ''}
          </span>
          <div className="flex gap-2">
            <Button variant="tertiary" size="sm" onClick={onClose}>
              Cancel
            </Button>
            <Button
              variant="secondary"
              size="sm"
              loading={save.isPending}
              disabled={!text.trim()}
              onClick={() => save.mutate()}
            >
              Save response
            </Button>
          </div>
        </div>
      }
    >
      <div className="space-y-4">
        <div>
          <h3 className="text-base font-semibold text-student-ink">{prompt.title}</h3>
          <div className="mt-1 flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-student-text">
            <span className="inline-flex items-center gap-1">
              <FileText size={12} /> {CHANNEL_LABELS[prompt.target_channel]}
            </span>
            {limit && (
              <span className="inline-flex items-center gap-1">
                <Clock size={12} /> {limit}
              </span>
            )}
            {prompt.format_required !== 'freeform' && (
              <span className="font-medium text-cobalt">{prompt.format_required} format</span>
            )}
          </div>
        </div>

        {/* Live STAR coverage */}
        <div className="rounded-lg border border-divider bg-student-moss/60 px-3 py-2.5">
          <div className="mb-1.5 flex items-center justify-between">
            <span className="text-eyebrow uppercase text-student-text">STAR coverage</span>
            <span className="text-xs font-medium text-student-ink">{starCount(star)}/5</span>
          </div>
          <StarChips flags={star} />
          {missing.length > 0 && text.trim() && (
            <p className="mt-1.5 text-xs text-student-text">Add: {missing.join(', ')}</p>
          )}
        </div>

        <textarea
          className="min-h-[220px] w-full resize-y rounded-md border border-divider bg-paper px-3 py-2 text-sm leading-relaxed text-student-ink focus:border-cobalt focus:outline-none"
          value={text}
          maxLength={20000}
          onChange={e => setText(e.target.value)}
          placeholder="Tell the story in your own words — Situation, Task, Action, Result, and what you learned."
        />
        {overLimit && (
          <p className="-mt-2 text-xs text-warning">
            Over the {prompt.word_limit}-word target — trim for the real submission.
          </p>
        )}

        {/* Confidence self-rating */}
        <div>
          <label className="mb-1 block text-sm font-medium text-student-ink">
            How confident are you in this answer?
          </label>
          <div className="flex gap-1.5">
            {[1, 2, 3, 4, 5].map(n => (
              <button
                key={n}
                type="button"
                onClick={() => setConfidence(confidence === n ? null : n)}
                className={`h-8 w-8 rounded-full text-sm font-semibold transition-colors ${
                  confidence != null && n <= confidence
                    ? 'bg-cobalt text-white'
                    : 'bg-student-mist text-student-text hover:bg-divider'
                }`}
                aria-label={`Confidence ${n}`}
              >
                {n}
              </button>
            ))}
          </div>
        </div>

        {/* Draft status */}
        <div>
          <label className="mb-1 block text-sm font-medium text-student-ink">Status</label>
          <div className="inline-flex overflow-hidden rounded-md border border-divider">
            {STATUS_OPTIONS.map(s => (
              <button
                key={s}
                type="button"
                onClick={() => setStatus(s)}
                className={`px-3 py-1.5 text-sm font-medium capitalize transition-colors ${
                  status === s
                    ? s === 'final'
                      ? 'bg-gold text-student-ink'
                      : 'bg-cobalt text-white'
                    : 'bg-paper text-student-text hover:bg-student-mist'
                }`}
              >
                {s}
              </button>
            ))}
          </div>
        </div>

        {/* Link a story */}
        {stories.length > 0 && (
          <div>
            <label className="mb-1 block text-sm font-medium text-student-ink">
              Draw from a story (optional)
            </label>
            <select
              className="w-full rounded-md border border-divider bg-paper px-3 py-2 text-sm text-student-ink focus:border-cobalt focus:outline-none"
              value={storyId}
              onChange={e => setStoryId(e.target.value)}
            >
              <option value="">— None —</option>
              {stories.map(s => (
                <option key={s.id} value={s.id}>
                  {s.title}
                </option>
              ))}
            </select>
          </div>
        )}
      </div>
    </Sheet>
  )
}
