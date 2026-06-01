import { useEffect, useRef, useState } from 'react'
import { ChevronDown, Paperclip, Send, Sparkles } from 'lucide-react'
import Badge from '../../../components/ui/Badge'
import Button from '../../../components/ui/Button'
import { formatRelative } from '../../../utils/format'
import type { InstInboxThread, InstReasonCode, InstSuggestedReply } from '../../../types'
import { ACTION_CONFIG } from '../../student/inbox/actionLabels'
import { REASON_CONFIG, REASON_OPTIONS, statusLabel } from './reasonCodes'

export default function InstThreadView({
  thread,
  onSend,
  sending,
  onAssignToMe,
  assigning,
  onClose,
  closing,
  suggestion,
  suggestionLoading,
  onRequestAiDraft,
  onInsertTemplate,
}: {
  thread: InstInboxThread
  onSend: (body: string, reason: InstReasonCode, dueDate: string | null, aiUsed: boolean) => void
  sending: boolean
  onAssignToMe: () => void
  assigning: boolean
  onClose: () => void
  closing: boolean
  suggestion: InstSuggestedReply | null
  suggestionLoading: boolean
  onRequestAiDraft: () => void
  onInsertTemplate: () => void
}) {
  const [reply, setReply] = useState('')
  const [reason, setReason] = useState<InstReasonCode>(thread.reason_label || 'general_reply')
  const [dueDate, setDueDate] = useState('')
  const [aiUsed, setAiUsed] = useState(false)
  const endRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [thread.messages.length])

  useEffect(() => {
    setReply('')
    setReason(thread.reason_label || 'general_reply')
    setDueDate(thread.due_date ? thread.due_date.slice(0, 10) : '')
    setAiUsed(false)
  }, [thread.id, thread.reason_label, thread.due_date])

  useEffect(() => {
    if (suggestion?.draft) setReply(suggestion.draft)
    if (suggestion?.suggested_reason_code) setReason(suggestion.suggested_reason_code)
  }, [suggestion])

  const action = thread.action_label ? ACTION_CONFIG[thread.action_label] : null
  const reasonCfg = REASON_CONFIG[reason]
  const requiresDue = Boolean(reasonCfg.requiresDue)
  const isClosed = thread.status === 'closed'

  const send = () => {
    const body = reply.trim()
    if (!body || sending || isClosed) return
    if (requiresDue && !dueDate) return
    onSend(body, reason, requiresDue ? new Date(dueDate).toISOString() : null, aiUsed)
    setReply('')
    setAiUsed(false)
  }

  return (
    <div className="flex min-w-0 flex-1 flex-col bg-background">
      <div className="border-b border-border bg-card px-4 py-3">
        <div className="flex flex-wrap items-start justify-between gap-2">
          <div>
            <p className="text-sm font-semibold text-foreground">
              {thread.student_ref.name}
              {thread.program_ref?.name && (
                <span className="font-normal text-muted-foreground"> · {thread.program_ref.name}</span>
              )}
            </p>
            <p className="text-xs text-muted-foreground">{thread.subject || 'Conversation'}</p>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            {action && <Badge variant={action.variant} size="sm">{action.label}</Badge>}
            <span className="text-xs text-muted-foreground">{statusLabel(thread.status)}</span>
            {!thread.assigned_to && thread.status === 'awaiting_us' && (
              <Button size="sm" variant="outline" onClick={onAssignToMe} disabled={assigning}>
                Assign to me
              </Button>
            )}
            {!isClosed && (
              <Button size="sm" variant="ghost" onClick={onClose} disabled={closing}>
                Close
              </Button>
            )}
          </div>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {thread.messages.length === 0 ? (
          <p className="text-center text-sm text-muted-foreground py-8">No messages yet.</p>
        ) : (
          thread.messages.map(msg => (
            <div
              key={msg.id}
              className={`flex ${msg.sender === 'student' ? 'justify-start' : 'justify-end'}`}
            >
              <div
                className={`max-w-[75%] rounded-lg px-3 py-2 text-sm ${
                  msg.sender === 'student'
                    ? 'border border-border bg-card text-foreground'
                    : 'bg-cobalt text-white'
                }`}
              >
                <p className="whitespace-pre-wrap">{msg.body}</p>
                <p
                  className={`mt-1 text-[10px] ${
                    msg.sender === 'student' ? 'text-muted-foreground' : 'text-white/70'
                  }`}
                >
                  {formatRelative(msg.sent_at)}
                </p>
              </div>
            </div>
          ))
        )}
        <div ref={endRef} />
      </div>

      {!isClosed && (
        <div className="border-t border-border bg-card p-3">
          {suggestion && (
            <div className="mb-2 rounded-md border border-cobalt/30 bg-cobalt/5 p-2 text-xs">
              <p className="font-medium text-cobalt">AI draft — edit before sending</p>
              <p className="mt-1 text-muted-foreground line-clamp-3">{suggestion.draft}</p>
            </div>
          )}
          <div className="mb-2 flex flex-wrap gap-2">
            <Button size="sm" variant="outline" type="button" onClick={onInsertTemplate}>
              Insert template
            </Button>
            <Button
              size="sm"
              variant="outline"
              type="button"
              onClick={() => {
                onRequestAiDraft()
                setAiUsed(true)
              }}
              disabled={suggestionLoading}
            >
              <Sparkles size={14} className="mr-1" />
              {suggestionLoading ? 'Drafting…' : 'AI draft'}
            </Button>
          </div>
          <textarea
            value={reply}
            onChange={e => setReply(e.target.value)}
            rows={3}
            placeholder="Write your reply…"
            className="w-full resize-none rounded-md border border-border bg-background px-3 py-2 text-sm focus:border-cobalt focus:outline-none focus:ring-1 focus:ring-cobalt"
          />
          <div className="mt-2 flex flex-wrap items-end gap-2">
            <div className="relative">
              <select
                value={reason}
                onChange={e => setReason(e.target.value as InstReasonCode)}
                className="h-9 appearance-none rounded-md border border-border bg-card pl-2 pr-7 text-xs"
                aria-label="Reason code"
              >
                {REASON_OPTIONS.map(o => (
                  <option key={o.value} value={o.value}>
                    {o.label}
                  </option>
                ))}
              </select>
              <ChevronDown size={12} className="pointer-events-none absolute right-2 top-1/2 -translate-y-1/2" />
            </div>
            {requiresDue && (
              <input
                type="date"
                value={dueDate}
                onChange={e => setDueDate(e.target.value)}
                className="h-9 rounded-md border border-border bg-card px-2 text-xs"
                aria-label="Due date"
              />
            )}
            <button type="button" className="rounded-md p-2 text-muted-foreground hover:bg-muted" aria-label="Attach">
              <Paperclip size={16} />
            </button>
            <Button
              onClick={send}
              disabled={!reply.trim() || sending || (requiresDue && !dueDate)}
              className="ml-auto bg-cobalt hover:bg-cobalt/90"
            >
              <Send size={16} className="mr-1" />
              Send
            </Button>
          </div>
        </div>
      )}
    </div>
  )
}
