import { useEffect, useState } from 'react'
import { ArrowDownToLine } from 'lucide-react'
import Button from '../../../components/ui/Button'
import { AIBadge } from '../../../components/ui/AIRationalePopover'
import type { InstSuggestedReply } from '../../../types'

// Spec 29 §8 — InstitutionReplyDrafter assist. Staff edits before sending; the
// draft is inserted into the composer (which carries the required reason code),
// never auto-sent. "AI suggestion" badge per 02 §15.
export default function InstSuggestedReplyCard({
  reply,
  onUse,
}: {
  reply: InstSuggestedReply
  onUse: (text: string) => void
}) {
  const drafts = [reply.draft, ...(reply.alternate_drafts || [])].slice(0, 3)
  const [activeIdx, setActiveIdx] = useState(0)
  const [text, setText] = useState(reply.draft)

  useEffect(() => {
    setActiveIdx(0)
    setText(reply.draft)
  }, [reply])

  const toneLabel = (i: number) => (i === 0 ? reply.tone || 'Suggested' : `Alt ${i}`)

  const pick = (i: number) => {
    setActiveIdx(i)
    setText(drafts[i])
  }

  return (
    <div className="rounded-xl border border-accent/40 bg-card p-3 shadow-sm">
      <div className="mb-2 flex items-center justify-between gap-2">
        <AIBadge label="AI draft" />
        {drafts.length > 1 && (
          <div className="flex gap-1">
            {drafts.map((_, i) => (
              <button
                key={i}
                onClick={() => pick(i)}
                className={`rounded-pill px-2 py-0.5 text-[11px] font-medium capitalize transition-colors ${
                  activeIdx === i
                    ? 'bg-cobalt text-white'
                    : 'bg-muted text-muted-foreground hover:brightness-95'
                }`}
              >
                {toneLabel(i)}
              </button>
            ))}
          </div>
        )}
      </div>

      <textarea
        value={text}
        onChange={e => setText(e.target.value)}
        rows={4}
        className="w-full resize-y rounded-lg border border-border bg-surface px-3 py-2 text-sm leading-relaxed focus:outline-none focus:ring-2 focus:ring-primary"
        aria-label="AI-drafted reply"
      />

      <div className="mt-2 flex items-center justify-between">
        <p className="text-[11px] text-muted-foreground">Edit, then add a reason and send.</p>
        <Button variant="secondary" size="sm" disabled={!text.trim()} onClick={() => onUse(text.trim())}>
          <ArrowDownToLine size={13} className="mr-1.5" /> Use draft
        </Button>
      </div>
    </div>
  )
}
