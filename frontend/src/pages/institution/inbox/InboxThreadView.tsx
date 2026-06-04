import { useEffect, useRef } from 'react'
import { CalendarClock, CheckCircle2, ChevronLeft, FileText, ListChecks, Sparkles } from 'lucide-react'
import Badge from '../../../components/ui/Badge'
import Button from '../../../components/ui/Button'
import { formatRelative } from '../../../utils/format'
import type { CommunicationTemplate, InstSuggestedReply, InstThread, StaffMember } from '../../../types'
import { REASON_CONFIG, STATUS_CONFIG, formatDue, isOverdue } from './reasonCodes'
import AssignMenu from './AssignMenu'
import ReplyComposer, { type SendPayload } from './ReplyComposer'

export default function InboxThreadView({
  thread,
  roster,
  onBack,
  onAssign,
  onClose,
  closing,
  onSend,
  sending,
  templates,
  aiDraft,
  aiDraftLoading,
  aiDraftRequested,
  onRequestAiDraft,
}: {
  thread: InstThread
  roster: StaffMember[]
  onBack: () => void
  onAssign: (staffUserId: string | null) => void
  onClose: () => void
  closing: boolean
  onSend: (payload: SendPayload) => void
  sending: boolean
  templates: CommunicationTemplate[]
  aiDraft: InstSuggestedReply | null
  aiDraftLoading: boolean
  aiDraftRequested: boolean
  onRequestAiDraft: () => void
}) {
  const endRef = useRef<HTMLDivElement>(null)
  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [thread.messages.length, thread.id])

  const reason = thread.reason_label ? REASON_CONFIG[thread.reason_label] : null
  const ReasonIcon = reason?.icon
  const status = STATUS_CONFIG[thread.status]
  const StatusIcon = status?.icon
  const due = formatDue(thread.due_date)
  const overdue = isOverdue(thread)
  const isClosed = thread.status === 'closed'

  return (
    <div className="flex h-full flex-col">
      {/* Header */}
      <div className="flex items-start gap-2 border-b border-border bg-card px-4 py-2.5">
        <button
          onClick={onBack}
          className="-ml-1 shrink-0 rounded-md p-1 text-muted-foreground hover:bg-muted xl:hidden"
          aria-label="Back to inbox"
        >
          <ChevronLeft size={18} />
        </button>
        <div className="min-w-0 flex-1">
          <p className="truncate text-[11px] font-medium uppercase tracking-wide text-secondary">
            {thread.application_id ? 'Application · ' : ''}
            {thread.program_name || 'General inquiry'}
          </p>
          <p className="truncate text-sm font-semibold text-foreground">{thread.student.name}</p>
          <div className="mt-1 flex flex-wrap items-center gap-x-2.5 gap-y-1">
            {reason ? (
              <Badge variant={reason.variant} size="sm">
                {ReasonIcon && <ReasonIcon size={10} />}
                {reason.label}
              </Badge>
            ) : (
              status && (
                <Badge variant={status.variant} size="sm">
                  {StatusIcon && <StatusIcon size={10} />}
                  {status.label}
                </Badge>
              )
            )}
            {due && (
              <span
                className={`inline-flex items-center gap-1 text-[11px] ${
                  overdue ? 'font-semibold text-warning' : 'text-muted-foreground'
                }`}
              >
                <CalendarClock size={11} /> {overdue ? 'Overdue' : 'Due'} {due}
              </span>
            )}
            {thread.context.checklist_total > 0 && (
              <span className="inline-flex items-center gap-1 text-[11px] text-muted-foreground xl:hidden">
                <ListChecks size={11} /> {thread.context.checklist_complete}/
                {thread.context.checklist_total}
              </span>
            )}
          </div>
        </div>
        <div className="flex shrink-0 items-center gap-1.5">
          <AssignMenu thread={thread} roster={roster} onAssign={onAssign} />
          {!isClosed && (
            <Button variant="tertiary" size="sm" loading={closing} onClick={onClose}>
              <CheckCircle2 size={13} className="mr-1.5" /> Close
            </Button>
          )}
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 space-y-3 overflow-y-auto px-4 py-4 sm:px-6">
        {thread.messages.map(m => {
          const own = m.sender === 'institution' || m.sender === 'admissions_officer'
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
                      ? 'rounded-br-md bg-secondary text-secondary-foreground'
                      : 'rounded-bl-md bg-muted text-foreground'
                  }`}
                >
                  {m.body}
                  {m.attachments?.length > 0 && (
                    <div
                      className={`mt-1.5 space-y-1 border-t pt-1.5 ${own ? 'border-secondary-foreground/20' : 'border-border'}`}
                    >
                      {m.attachments.map((a, i) => (
                        <div key={i} className="flex items-center gap-1 text-[11px] opacity-90">
                          <FileText size={10} /> {a.name}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
                <p className={`mt-0.5 text-[10px] text-muted-foreground ${own ? 'text-right' : ''}`}>
                  {m.sender === 'student' ? thread.student.name : 'You'} · {formatRelative(m.sent_at)}
                  {m.ai_draft_used ? ' · AI-assisted' : ''}
                </p>
              </div>
            </div>
          )
        })}
        <div ref={endRef} />
      </div>

      {/* Composer (hidden once closed) */}
      {isClosed ? (
        <div className="border-t border-border bg-card px-4 py-3 text-center text-xs text-muted-foreground">
          This conversation is closed.{' '}
          <button
            onClick={() => onSend({
              body: 'Reopening this conversation.',
              reason_code: 'general_reply',
              attachments: [],
              due_date: null,
              request_document: false,
              requested_item: null,
              ai_draft_used: false,
            })}
            className="font-medium text-secondary hover:underline"
          >
            Reply to reopen
          </button>
        </div>
      ) : (
        <ReplyComposer
          onSend={onSend}
          sending={sending}
          templates={templates}
          aiDraft={aiDraft}
          aiDraftLoading={aiDraftLoading}
          aiDraftRequested={aiDraftRequested}
          onRequestAiDraft={onRequestAiDraft}
        />
      )}
    </div>
  )
}
