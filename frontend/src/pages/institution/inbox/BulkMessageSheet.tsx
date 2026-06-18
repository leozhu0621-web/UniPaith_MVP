import { useMemo, useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { Users } from 'lucide-react'
import Sheet from '../../../components/ui/Sheet'
import Button from '../../../components/ui/Button'
import { showToast } from '../../../stores/toast-store'
import { bulkMessage } from '../../../api/institution-inbox'
import type { CommunicationTemplate, ReasonCode, Segment } from '../../../types'
import { REASON_OPTIONS, REASON_REQUIRES_DUE } from './reasonCodes'

// Spec 29 §6 — operational (non-campaign) bulk send to a segment. One thread
// per recipient; marketing-class reasons respect consent.outreach, transactional
// reasons tied to an active application are not suppressed.
export default function BulkMessageSheet({
  isOpen,
  onClose,
  segments,
  templates,
}: {
  isOpen: boolean
  onClose: () => void
  segments: Segment[]
  templates: CommunicationTemplate[]
}) {
  const qc = useQueryClient()
  const [segmentId, setSegmentId] = useState('')
  const [reason, setReason] = useState<ReasonCode>('status_update')
  const [body, setBody] = useState('')
  const [dueDate, setDueDate] = useState('')

  const dueRequired = REASON_REQUIRES_DUE.includes(reason)
  const segment = useMemo(() => segments.find(s => s.id === segmentId), [segments, segmentId])
  const previewCount = segment?.preview_audience_count ?? null

  const reset = () => {
    setSegmentId('')
    setReason('status_update')
    setBody('')
    setDueDate('')
  }

  const mut = useMutation({
    mutationFn: () =>
      bulkMessage({
        segment_id: segmentId,
        body,
        reason_code: reason,
        due_date: dueDate ? new Date(`${dueDate}T00:00:00`).toISOString() : null,
      }),
    onSuccess: res => {
      qc.invalidateQueries({ queryKey: ['inst-inbox-threads'] })
      showToast(
        `Sent to ${res.sent_count} recipient${res.sent_count === 1 ? '' : 's'}` +
          (res.suppressed_count ? ` · ${res.suppressed_count} suppressed (opted out)` : ''),
        'success',
      )
      reset()
      onClose()
    },
    onError: () => showToast('Bulk message failed', 'error'),
  })

  const canSend = !!segmentId && !!body.trim() && !(dueRequired && !dueDate) && !mut.isPending

  return (
    <Sheet
      isOpen={isOpen}
      onClose={onClose}
      title="Message a segment"
      footer={
        <>
          <Button variant="tertiary" onClick={onClose}>
            Cancel
          </Button>
          <Button variant="secondary" loading={mut.isPending} disabled={!canSend} onClick={() => mut.mutate()}>
            <Users size={15} className="mr-1.5" />
            Message {previewCount != null ? `${previewCount} ` : ''}applicants
          </Button>
        </>
      }
    >
      <div className="space-y-4">
        <label className="block">
          <span className="text-xs font-medium text-foreground">Segment</span>
          <select
            value={segmentId}
            onChange={e => setSegmentId(e.target.value)}
            className="mt-1 h-9 w-full rounded-lg border border-border bg-card px-2 text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-primary"
          >
            <option value="">Select a segment…</option>
            {segments.map(s => (
              <option key={s.id} value={s.id}>
                {s.segment_name}
                {s.preview_audience_count != null ? ` (${s.preview_audience_count})` : ''}
              </option>
            ))}
          </select>
        </label>

        <label className="block">
          <span className="text-xs font-medium text-foreground">Reason</span>
          <select
            value={reason}
            onChange={e => setReason(e.target.value as ReasonCode)}
            className="mt-1 h-9 w-full rounded-lg border border-border bg-card px-2 text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-primary"
          >
            {REASON_OPTIONS.map(o => (
              <option key={o.value} value={o.value}>
                {o.label}
              </option>
            ))}
          </select>
        </label>

        {dueRequired && (
          <label className="block">
            <span className="text-xs font-medium text-foreground">Due date</span>
            <input
              type="date"
              value={dueDate}
              onChange={e => setDueDate(e.target.value)}
              className="mt-1 h-9 w-full rounded-lg border border-border bg-card px-2 text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-primary"
            />
          </label>
        )}

        {templates.length > 0 && (
          <label className="block">
            <span className="text-xs font-medium text-foreground">Insert template</span>
            <select
              defaultValue=""
              onChange={e => {
                const t = templates.find(x => x.id === e.target.value)
                if (t) setBody(t.body)
              }}
              className="mt-1 h-9 w-full rounded-lg border border-border bg-card px-2 text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-primary"
            >
              <option value="">Choose a template…</option>
              {templates.map(t => (
                <option key={t.id} value={t.id}>
                  {t.name}
                </option>
              ))}
            </select>
          </label>
        )}

        <label className="block">
          <span className="text-xs font-medium text-foreground">Message</span>
          <textarea
            value={body}
            onChange={e => setBody(e.target.value)}
            rows={6}
            placeholder="Write once — personalized per recipient…"
            className="mt-1 w-full resize-y rounded-lg border border-border bg-card px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
          />
          <span className="mt-1 block text-[11px] text-muted-foreground">
            Variables: {'{{student_name}}'}, {'{{program}}'}, {'{{deadline}}'}, {'{{missing_items}}'}
          </span>
        </label>
      </div>
    </Sheet>
  )
}
