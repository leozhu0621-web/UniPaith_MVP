import { useEffect, useState } from 'react'
import { Send } from 'lucide-react'
import Button from '../../../components/ui/Button'
import { AIBadge } from '../../../components/ui/AIRationalePopover'
import type { SuggestedReply } from '../../../types'

// Spec 17 §7 — AI-assist suggested reply. Student edits before sending; never
// auto-sends. Up to 2 alternate-tone drafts. "AI suggestion" badge per 02 §15.
export default function SuggestedReplyCard({
  reply,
  sending,
  onSend,
}: {
  reply: SuggestedReply
  sending: boolean
  onSend: (text: string) => void
}) {
  const drafts = [reply.draft, ...(reply.alternate_drafts || [])].slice(0, 3)
  const [activeIdx, setActiveIdx] = useState(0)
  const [text, setText] = useState(reply.draft)
  const [edited, setEdited] = useState(false)

  // Reset when a fresh suggestion arrives.
  useEffect(() => {
    setActiveIdx(0)
    setText(reply.draft)
    setEdited(false)
  }, [reply])

  const toneLabel = (i: number) =>
    i === 0 ? reply.tone || 'Suggested' : `Alt ${i}`

  const pick = (i: number) => {
    setActiveIdx(i)
    setText(drafts[i])
    setEdited(false)
  }

  return (
    <div className="rounded-xl border border-accent/40 bg-card p-3 shadow-sm">
      <div className="flex items-center justify-between gap-2 mb-2">
        <AIBadge label="AI suggestion" />
        {drafts.length > 1 && (
          <div className="flex gap-1">
            {drafts.map((_, i) => (
              <button
                key={i}
                onClick={() => pick(i)}
                className={`rounded-pill px-2 py-0.5 text-[11px] font-medium capitalize transition-colors ${
                  activeIdx === i
                    ? 'bg-secondary text-secondary-foreground'
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
        onChange={e => {
          setText(e.target.value)
          setEdited(true)
        }}
        rows={4}
        className="w-full resize-y rounded-lg border border-border bg-card px-3 py-2 text-sm leading-relaxed focus:outline-none focus:ring-2 focus:ring-primary"
        aria-label="Suggested reply draft"
      />

      <div className="mt-2 flex items-center justify-between">
        <p className="text-[11px] text-muted-foreground">
          {edited ? 'Edited — review before sending.' : 'Edit before sending. Never sent automatically.'}
        </p>
        <Button
          variant="secondary"
          size="sm"
          loading={sending}
          disabled={!text.trim()}
          onClick={() => onSend(text.trim())}
        >
          <Send size={13} className="mr-1.5" /> Edit &amp; send
        </Button>
      </div>
    </div>
  )
}
