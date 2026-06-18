/**
 * AI Structure (Spec 1) — the "enrich your profile" widget.
 *
 * A droppable card (sibling to a program card) that surfaces the next
 * Prompt-Library signal to fill and renders the right input by its ask_kind
 * (reusing the conversation's AnswerChoices for the 0–5 importance slider).
 * On submit it stores the value and advances to the next signal. Render it
 * anywhere — the chat thread, the profile page, the My Space home.
 */
import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import AnswerChoices from '../../pages/student/discover/AnswerChoices'
import Button from '../ui/Button'
import { getEnrichNext, setEnrichValue, type EnrichItem } from '../../api/enrichment'
import { ACTION_PROMPT, humanizeField } from './enrichHelpers'

const QK = ['enrichment', 'next'] as const

/** The typed input for one signal. Keyed by field so state resets per signal. */
function SignalInput({
  item,
  onSubmit,
  disabled,
}: {
  item: EnrichItem
  onSubmit: (value: unknown) => void
  disabled?: boolean
}) {
  const [text, setText] = useState('')
  const [min, setMin] = useState('')
  const [max, setMax] = useState('')

  if (item.ask_kind === 'scale') {
    // 0–5 importance slider (reuses the conversation widget).
    return <AnswerChoices kind="scale" options={[]} onPick={onSubmit} disabled={disabled} />
  }

  if (item.ask_kind === 'range') {
    return (
      <div className="flex items-end gap-2">
        <label className="flex-1 text-sm">
          <span className="text-muted-foreground">Min</span>
          <input
            type="number"
            value={min}
            onChange={(e) => setMin(e.target.value)}
            className="mt-1 w-full rounded-md border border-border bg-card px-2 py-1.5 text-sm"
          />
        </label>
        <label className="flex-1 text-sm">
          <span className="text-muted-foreground">Max</span>
          <input
            type="number"
            value={max}
            onChange={(e) => setMax(e.target.value)}
            className="mt-1 w-full rounded-md border border-border bg-card px-2 py-1.5 text-sm"
          />
        </label>
        <Button
          variant="secondary"
          size="sm"
          disabled={disabled || (!min && !max)}
          onClick={() => onSubmit({ min: min ? Number(min) : null, max: max ? Number(max) : null })}
        >
          Set
        </Button>
      </div>
    )
  }

  const inputType = item.ask_kind === 'number' ? 'number' : item.ask_kind === 'date' ? 'date' : 'text'
  return (
    <div className="flex items-end gap-2">
      <input
        type={inputType}
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder={`Your ${humanizeField(item.field).toLowerCase()}`}
        className="flex-1 rounded-md border border-border bg-card px-2.5 py-1.5 text-sm"
      />
      <Button
        variant="secondary"
        size="sm"
        disabled={disabled || !text}
        onClick={() => onSubmit(inputType === 'number' ? Number(text) : text)}
      >
        {item.action === 'confirm' ? 'Confirm' : 'Save'}
      </Button>
    </div>
  )
}

export default function EnrichWidget() {
  const qc = useQueryClient()
  const { data, isLoading } = useQuery({ queryKey: QK, queryFn: () => getEnrichNext(1) })
  const mutation = useMutation({
    mutationFn: ({ field, value }: { field: string; value: unknown }) => setEnrichValue(field, value),
    onSuccess: () => qc.invalidateQueries({ queryKey: QK }),
  })

  if (isLoading) return null
  const item = data?.items?.[0]
  if (!item) return null // nothing left to enrich

  return (
    <div className="rounded-lg border border-border bg-card p-4">
      <div className="mb-1 flex items-center justify-between gap-2">
        <span className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
          Enrich your profile
        </span>
        {item.tier === 'essential' && (
          <span className="rounded-full bg-secondary/10 px-2 py-0.5 text-[10px] font-medium text-secondary">
            needed to match
          </span>
        )}
      </div>
      <p className="mb-3 text-sm text-foreground">
        <span className="font-medium">{humanizeField(item.field)}</span>
        <span className="text-muted-foreground"> · {ACTION_PROMPT[item.action]}</span>
      </p>
      <SignalInput
        key={item.field}
        item={item}
        disabled={mutation.isPending}
        onSubmit={(value) => mutation.mutate({ field: item.field, value })}
      />
    </div>
  )
}
