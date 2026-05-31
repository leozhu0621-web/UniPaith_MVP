import { useEffect, useRef, useState } from 'react'
import {
  CalendarClock,
  CheckCircle2,
  ChevronLeft,
  ExternalLink,
  FileText,
  Paperclip,
  Send,
  Sparkles,
  X,
} from 'lucide-react'
import Badge from '../../../components/ui/Badge'
import Button from '../../../components/ui/Button'
import { formatRelative } from '../../../utils/format'
import type { ActionLabel, InboxAttachment, InboxThread, SuggestedReply } from '../../../types'
import { ACTION_CONFIG, formatDue, threadEyebrow, waitingCopy } from './actionLabels'
import AttachmentPicker from './AttachmentPicker'
import SuggestedReplyCard from './SuggestedReplyCard'

const ACTION_COPY: Record<ActionLabel, string> = {
  needs_reply: 'Reply to continue.',
  document_requested: 'Attach a document or reply.',
  clarification_required: 'Answer the question to continue.',
  interview_invite: 'Accept, decline, or propose a new time.',
  status_update_only: 'No action needed — informational.',
  completed: 'This conversation is complete.',
}

export default function ThreadView({
  thread,
  onBack,
  onSend,
  sending,
  onMarkComplete,
  completing,
  suggestion,
  suggestionLoading,
  onNavigate,
}: {
  thread: InboxThread
  onBack: () => void
  onSend: (body: string, attachments: InboxAttachment[], aiDraftUsed: boolean) => void
  sending: boolean
  onMarkComplete: () => void
  completing: boolean
  suggestion: SuggestedReply | null
  suggestionLoading: boolean
  onNavigate: (path: string) => void
}) {
  const [reply, setReply] = useState('')
  const [attachments, setAttachments] = useState<InboxAttachment[]>([])
  const [showAttach, setShowAttach] = useState(false)
  const endRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [thread.messages.length])

  // Reset composer when switching threads.
  useEffect(() => {
    setReply('')
    setAttachments([])
    setShowAttach(false)
  }, [thread.id])

  const action = thread.action_label ? ACTION_CONFIG[thread.action_label] : null
  const ActionIcon = action?.icon
  const due = formatDue(thread.due_date)
  const waiting = waitingCopy(thread)
  const isCompleted = thread.action_label === 'completed'

  const sendManual = () => {
    const body = reply.trim()
    if (!body || sending) return
    onSend(body, attachments, false)
    setReply('')
    setAttachments([])
    setShowAttach(false)
  }

  const addAttachment = (a: InboxAttachment) => setAttachments(prev => [...prev, a])
  const removeAttachment = (name: string) =>
    setAttachments(prev => prev.filter(p => p.name !== name))

  return (
    <div className="flex h-full flex-col">
      {/* Header */}
      <div className="flex items-start gap-2 border-b border-border bg-card px-4 py-2.5">
        <button
          onClick={onBack}
          className="-ml-1 shrink-0 rounded-md p-1 text-muted-foreground hover:bg-muted lg:hidden"
          aria-label="Back to inbox"
        >
          <ChevronLeft size={18} />
        </button>
        <div className="min-w-0 flex-1">
          <p className="truncate text-[11px] font-medium uppercase tracking-wide text-cobalt">
            {thread.application_id ? 'Application · ' : ''}
            {threadEyebrow(thread)}
          </p>
          <p className="truncate text-sm font-semibold text-foreground">
            {thread.subject || 'Conversation'}
          </p>
          <div className="mt-1 flex flex-wrap items-center gap-x-2.5 gap-y-1">
            {action && (
              <Badge variant={action.variant} size="sm">
                {ActionIcon && <ActionIcon size={10} />}
                {action.label}
              </Badge>
            )}
            {waiting && <span className="text-[11px] text-muted-foreground">{waiting}</span>}
            {due && (
              <span className="inline-flex items-center gap-1 text-[11px] text-muted-foreground">
                <CalendarClock size={11} /> Due {due}
              </span>
            )}
            {thread.application_id && (
              <button
                onClick={() => onNavigate(`/s/applications/${thread.application_id}`)}
                className="inline-flex items-center gap-1 text-[11px] text-cobalt hover:underline"
              >
                View application <ExternalLink size={9} />
              </button>
            )}
          </div>
        </div>
        {!isCompleted && (
          <Button variant="tertiary" size="sm" loading={completing} onClick={onMarkComplete}>
            <CheckCircle2 size={13} className="mr-1.5" /> Mark complete
          </Button>
        )}
      </div>

      {/* Messages */}
      <div className="flex-1 space-y-3 overflow-y-auto px-4 py-4 sm:px-6">
        {thread.messages.map(m => {
          const own = m.sender === 'student'
          const system = m.sender === 'system'
          if (system) {
            return (
              <div key={m.id} className="mx-auto max-w-[85%] text-center">
                <div className="inline-flex items-start gap-2 rounded-lg border border-border bg-muted/50 px-3 py-2 text-left text-xs text-muted-foreground">
                  <Sparkles size={12} className="mt-0.5 shrink-0 text-accent" />
                  <span>{m.body}</span>
                </div>
                <p className="mt-0.5 text-[10px] text-muted-foreground">{formatRelative(m.sent_at)}</p>
              </div>
            )
          }
          return (
            <div key={m.id} className={`flex ${own ? 'justify-end' : 'justify-start'}`}>
              <div className={`max-w-[75%] ${own ? 'items-end' : 'items-start'}`}>
                <div
                  className={`whitespace-pre-wrap rounded-2xl px-4 py-2 text-sm ${
                    own
                      ? 'rounded-br-md bg-cobalt text-white'
                      : 'rounded-bl-md bg-muted text-foreground'
                  }`}
                >
                  {m.body}
                  {m.attachments?.length > 0 && (
                    <div className={`mt-1.5 space-y-1 border-t pt-1.5 ${own ? 'border-white/20' : 'border-border'}`}>
                      {m.attachments.map((a, i) => (
                        <div key={i} className="flex items-center gap-1 text-[11px] opacity-90">
                          <FileText size={10} /> {a.name}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
                <p className={`mt-0.5 text-[10px] text-muted-foreground ${own ? 'text-right' : ''}`}>
                  {formatRelative(m.sent_at)}
                </p>
              </div>
            </div>
          )
        })}

        {/* Action banner */}
        {thread.action_label && !isCompleted && (
          <div className="rounded-lg border border-warning/30 bg-warning-soft/50 px-3 py-2 text-sm text-foreground">
            <span className="font-semibold text-warning">★ Action: </span>
            {ACTION_COPY[thread.action_label]}
            {due && <span className="text-muted-foreground"> · Due {due}</span>}
          </div>
        )}
        <div ref={endRef} />
      </div>

      {/* Composer (hidden once completed) */}
      {!isCompleted && (
        <div className="border-t border-border bg-card px-4 py-3">
          {/* AI assist suggested reply (§7) — hidden silently when null */}
          {suggestionLoading ? (
            <div className="mb-2 flex items-center gap-2 text-[11px] text-muted-foreground">
              <Sparkles size={12} className="animate-pulse text-accent" /> Drafting a suggestion…
            </div>
          ) : suggestion ? (
            <div className="mb-2">
              <SuggestedReplyCard
                reply={suggestion}
                sending={sending}
                onSend={text => onSend(text, [], true)}
              />
            </div>
          ) : null}

          {showAttach && <AttachmentPicker selected={attachments} onAdd={addAttachment} />}

          {attachments.length > 0 && (
            <div className="mb-2 flex flex-wrap gap-1.5">
              {attachments.map((a, i) => (
                <span
                  key={i}
                  className="inline-flex items-center gap-1 rounded-pill bg-muted px-2 py-0.5 text-[11px] text-foreground"
                >
                  <FileText size={10} /> {a.name}
                  <button onClick={() => removeAttachment(a.name)} aria-label={`Remove ${a.name}`}>
                    <X size={10} className="text-muted-foreground hover:text-foreground" />
                  </button>
                </span>
              ))}
            </div>
          )}

          <div className="flex items-end gap-2">
            <button
              onClick={() => setShowAttach(s => !s)}
              className={`shrink-0 rounded-lg p-2 transition-colors ${
                showAttach ? 'bg-muted text-foreground' : 'text-muted-foreground hover:text-foreground'
              }`}
              aria-label="Attach a document"
            >
              <Paperclip size={16} />
            </button>
            <textarea
              value={reply}
              onChange={e => setReply(e.target.value)}
              onKeyDown={e => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault()
                  sendManual()
                }
              }}
              rows={1}
              placeholder="Type a reply…"
              className="max-h-32 min-h-[40px] flex-1 resize-none rounded-lg border border-border bg-surface px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
            />
            {/* Send is cobalt — no gold (§10): the school is the celebrant, not you. */}
            <Button variant="secondary" size="md" loading={sending} disabled={!reply.trim()} onClick={sendManual}>
              <Send size={15} />
            </Button>
          </div>
        </div>
      )}
    </div>
  )
}
