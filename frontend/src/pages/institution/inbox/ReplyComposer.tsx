import { useEffect, useRef, useState } from 'react'
import { FileText, Paperclip, Send, Sparkles, X } from 'lucide-react'
import Button from '../../../components/ui/Button'
import type { CommunicationTemplate, InboxAttachment, InstSuggestedReply, ReasonCode } from '../../../types'
import { REASON_OPTIONS, REASON_REQUIRES_DUE } from './reasonCodes'
import InstSuggestedReplyCard from './InstSuggestedReplyCard'

const DOC_CATEGORIES: { value: string; label: string }[] = [
  { value: 'transcripts', label: 'Transcript' },
  { value: 'test_scores', label: 'Test scores' },
  { value: 'recommendation_letters', label: 'Recommendation letter' },
  { value: 'essays', label: 'Essay / statement' },
  { value: 'resume', label: 'Résumé / CV' },
  { value: 'documents', label: 'Other document' },
]

export interface SendPayload {
  body: string
  reason_code: ReasonCode
  attachments: InboxAttachment[]
  due_date: string | null
  request_document: boolean
  requested_item: string | null
  ai_draft_used: boolean
}

export default function ReplyComposer({
  onSend,
  sending,
  templates,
  aiDraft,
  aiDraftLoading,
  aiDraftRequested,
  onRequestAiDraft,
}: {
  onSend: (payload: SendPayload) => void
  sending: boolean
  templates: CommunicationTemplate[]
  aiDraft: InstSuggestedReply | null
  aiDraftLoading: boolean
  aiDraftRequested: boolean
  onRequestAiDraft: () => void
}) {
  const [body, setBody] = useState('')
  const [reason, setReason] = useState<ReasonCode>('general_reply')
  const [dueDate, setDueDate] = useState('')
  const [requestedItem, setRequestedItem] = useState('transcripts')
  const [attachments, setAttachments] = useState<InboxAttachment[]>([])
  const [aiDraftUsed, setAiDraftUsed] = useState(false)
  const [showTemplates, setShowTemplates] = useState(false)
  const [showAttach, setShowAttach] = useState(false)
  const [attachName, setAttachName] = useState('')
  const bodyRef = useRef<HTMLTextAreaElement>(null)

  const isDoc = reason === 'request_document'
  const dueRequired = REASON_REQUIRES_DUE.includes(reason)
  const dueMissing = dueRequired && !dueDate
  const canSend = !!body.trim() && !sending && !dueMissing

  // Close the template menu on outside-ish interactions by toggling only.
  useEffect(() => {
    if (!showTemplates) return
    const close = () => setShowTemplates(false)
    const t = setTimeout(() => document.addEventListener('click', close, { once: true }), 0)
    return () => {
      clearTimeout(t)
      document.removeEventListener('click', close)
    }
  }, [showTemplates])

  const send = () => {
    if (!canSend) return
    onSend({
      body: body.trim(),
      reason_code: reason,
      attachments,
      // Parse YYYY-MM-DD as LOCAL midnight so the due date doesn't display a
      // day early in timezones behind UTC.
      due_date: dueDate ? new Date(`${dueDate}T00:00:00`).toISOString() : null,
      request_document: isDoc,
      requested_item: isDoc ? requestedItem : null,
      ai_draft_used: aiDraftUsed,
    })
    setBody('')
    setAttachments([])
    setAttachName('')
    setShowAttach(false)
    setAiDraftUsed(false)
  }

  const addAttachment = () => {
    const name = attachName.trim()
    if (!name) return
    setAttachments(prev => [...prev, { name, kind: 'document' }])
    setAttachName('')
  }
  const removeAttachment = (name: string) =>
    setAttachments(prev => prev.filter(p => p.name !== name))

  return (
    <div className="border-t border-border bg-card px-4 py-3">
      {/* AI draft (§8) — hidden silently when unavailable */}
      {aiDraftLoading ? (
        <div className="mb-2 flex items-center gap-2 text-[11px] text-muted-foreground">
          <Sparkles size={12} className="animate-pulse text-accent" /> Drafting a reply…
        </div>
      ) : aiDraft ? (
        <div className="mb-2">
          <InstSuggestedReplyCard
            reply={aiDraft}
            onUse={text => {
              setBody(text)
              setAiDraftUsed(true)
              bodyRef.current?.focus()
            }}
          />
        </div>
      ) : aiDraftRequested ? (
        <div className="mb-2 text-[11px] text-muted-foreground">
          AI draft unavailable — type your reply.
        </div>
      ) : null}

      {/* Toolbar */}
      <div className="mb-2 flex flex-wrap items-center gap-1.5">
        <select
          value={reason}
          onChange={e => setReason(e.target.value as ReasonCode)}
          aria-label="Reason code"
          className="h-7 rounded-md border border-border bg-card px-2 text-xs font-medium text-foreground focus:outline-none focus:ring-2 focus:ring-primary"
        >
          {REASON_OPTIONS.map(o => (
            <option key={o.value} value={o.value}>
              {o.label}
            </option>
          ))}
        </select>

        {/* Template insert */}
        <div className="relative">
          <button
            type="button"
            onClick={e => {
              e.stopPropagation()
              setShowTemplates(s => !s)
            }}
            className="inline-flex h-7 items-center gap-1 rounded-md border border-border bg-card px-2 text-xs text-foreground hover:bg-muted"
          >
            <FileText size={12} /> Template
          </button>
          {showTemplates && (
            <div
              onClick={e => e.stopPropagation()}
              className="absolute bottom-9 left-0 z-20 max-h-56 w-64 overflow-y-auto rounded-lg border border-border bg-card p-1 shadow-lg"
            >
              {templates.length === 0 ? (
                <p className="px-2 py-2 text-xs text-muted-foreground">
                  No templates yet. Create them in Templates &amp; AI Drafts.
                </p>
              ) : (
                templates.map(t => (
                  <button
                    key={t.id}
                    onClick={() => {
                      setBody(t.body)
                      setShowTemplates(false)
                      bodyRef.current?.focus()
                    }}
                    className="block w-full truncate rounded px-2 py-1.5 text-left text-xs text-foreground hover:bg-muted"
                  >
                    {t.name}
                  </button>
                ))
              )}
            </div>
          )}
        </div>

        <button
          type="button"
          onClick={onRequestAiDraft}
          disabled={aiDraftLoading}
          className="inline-flex h-7 items-center gap-1 rounded-md border border-accent/40 bg-card px-2 text-xs font-medium text-foreground hover:bg-muted disabled:opacity-50"
        >
          <Sparkles size={12} className="text-accent" /> AI draft
        </button>

        <button
          type="button"
          onClick={() => setShowAttach(s => !s)}
          className={`inline-flex h-7 items-center gap-1 rounded-md border border-border px-2 text-xs hover:bg-muted ${
            showAttach ? 'bg-muted text-foreground' : 'bg-card text-foreground'
          }`}
        >
          <Paperclip size={12} /> Attach
        </button>

        {dueRequired && (
          <input
            type="date"
            value={dueDate}
            onChange={e => setDueDate(e.target.value)}
            aria-label="Due date"
            className={`h-7 rounded-md border bg-card px-2 text-xs text-foreground focus:outline-none focus:ring-2 focus:ring-primary ${
              dueMissing ? 'border-warning' : 'border-border'
            }`}
          />
        )}
      </div>

      {/* Document request item picker */}
      {isDoc && (
        <div className="mb-2 flex items-center gap-2">
          <span className="text-[11px] text-muted-foreground">Requested item</span>
          <select
            value={requestedItem}
            onChange={e => setRequestedItem(e.target.value)}
            className="h-7 rounded-md border border-border bg-card px-2 text-xs text-foreground focus:outline-none focus:ring-2 focus:ring-primary"
          >
            {DOC_CATEGORIES.map(o => (
              <option key={o.value} value={o.value}>
                {o.label}
              </option>
            ))}
          </select>
          <span className="text-[11px] text-muted-foreground">
            Creates a checklist item for the applicant.
          </span>
        </div>
      )}

      {/* Attach input */}
      {showAttach && (
        <div className="mb-2 flex items-center gap-2">
          <input
            value={attachName}
            onChange={e => setAttachName(e.target.value)}
            onKeyDown={e => {
              if (e.key === 'Enter') {
                e.preventDefault()
                addAttachment()
              }
            }}
            placeholder="Attachment name (e.g. Offer letter.pdf)"
            className="h-7 flex-1 rounded-md border border-border bg-card px-2 text-xs text-foreground focus:outline-none focus:ring-2 focus:ring-primary"
          />
          <Button variant="tertiary" size="sm" onClick={addAttachment} disabled={!attachName.trim()}>
            Add
          </Button>
        </div>
      )}

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

      {/* Composer row */}
      <div className="flex items-end gap-2">
        <textarea
          ref={bodyRef}
          value={body}
          onChange={e => {
            setBody(e.target.value)
            if (aiDraftUsed) setAiDraftUsed(false)
          }}
          onKeyDown={e => {
            if (e.key === 'Enter' && !e.shiftKey) {
              e.preventDefault()
              send()
            }
          }}
          rows={1}
          placeholder="Write a reply…"
          className="max-h-32 min-h-[40px] flex-1 resize-none rounded-lg border border-border bg-card px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
        />
        {/* Send is cobalt — no gold (§10): gold celebration belongs to the student. */}
        <Button variant="secondary" size="md" loading={sending} disabled={!canSend} onClick={send}>
          <Send size={15} />
        </Button>
      </div>
      {dueMissing && (
        <p className="mt-1 text-[11px] text-warning">A due date is required for this reason.</p>
      )}
    </div>
  )
}
