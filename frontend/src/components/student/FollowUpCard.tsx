/**
 * "Uni has a few questions" — the post-import follow-up loop.
 *
 * Walks the student through Uni's targeted questions one at a time. Each is
 * answerable by tap-chips (when the question offers options) and/or a free-text
 * box, and is individually skippable. Calls `onAnswer` per answered question and
 * `onDone` when the student finishes or skips them all.
 */
import { useState } from 'react'
import { MessageCircleQuestion } from 'lucide-react'

import type { FollowupQuestion } from '../../api/materials'
import Button from '../ui/Button'
import Card from '../ui/Card'

export default function FollowUpCard({
  questions,
  onAnswer,
  onDone,
}: {
  questions: FollowupQuestion[]
  onAnswer: (q: FollowupQuestion, answer: string) => void | Promise<void>
  onDone: () => void
}) {
  const [idx, setIdx] = useState(0)
  const [draft, setDraft] = useState('')
  const [busy, setBusy] = useState(false)

  if (questions.length === 0) return null
  const q = questions[idx]
  const last = idx >= questions.length - 1

  const advance = () => {
    setDraft('')
    if (last) onDone()
    else setIdx(i => i + 1)
  }

  const submit = async (value: string) => {
    const v = value.trim()
    if (!v) return
    setBusy(true)
    try {
      await onAnswer(q, v)
    } finally {
      setBusy(false)
    }
    advance()
  }

  return (
    <Card variant="card-accent" pad>
      <div className="flex items-center gap-2">
        <span className="text-secondary">
          <MessageCircleQuestion size={16} />
        </span>
        <span className="text-sm font-semibold text-foreground">Uni has a few questions</span>
        <span className="text-xs text-muted-foreground">
          {idx + 1} of {questions.length}
        </span>
      </div>

      {q.section && (
        <p className="mt-2 text-eyebrow uppercase tracking-wide text-muted-foreground">
          {q.section}
        </p>
      )}
      <p className="mt-1 text-sm text-foreground">{q.prompt}</p>

      {q.kind === 'choice' && q.options && q.options.length > 0 && (
        <div className="mt-2 flex flex-wrap gap-1.5">
          {q.options.map(opt => (
            <button
              key={opt}
              type="button"
              disabled={busy}
              onClick={() => void submit(opt)}
              className="rounded-full border border-border bg-card px-3 py-1 text-sm text-foreground transition-colors hover:border-secondary/50 hover:bg-secondary/5 disabled:opacity-50"
            >
              {opt}
            </button>
          ))}
        </div>
      )}

      <form
        className="mt-2 flex items-end gap-2"
        onSubmit={e => {
          e.preventDefault()
          void submit(draft)
        }}
      >
        <input
          type="text"
          value={draft}
          disabled={busy}
          onChange={e => setDraft(e.target.value)}
          placeholder="Type your answer…"
          className="flex-1 rounded-lg border border-border bg-background px-3 py-2 text-sm focus:border-secondary focus:outline-none"
          aria-label={q.prompt}
        />
        <Button type="submit" variant="secondary" size="sm" loading={busy} disabled={!draft.trim()}>
          Add
        </Button>
      </form>

      <div className="mt-2 flex items-center justify-end gap-2.5">
        <Button variant="ghost" size="sm" onClick={advance} disabled={busy}>
          {last ? 'Done' : 'Skip'}
        </Button>
      </div>
    </Card>
  )
}
