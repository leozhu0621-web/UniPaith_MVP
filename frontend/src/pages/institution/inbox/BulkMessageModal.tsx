import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import Modal from '../../../components/ui/Modal'
import Button from '../../../components/ui/Button'
import Select from '../../../components/ui/Select'
import { getSegments, getTemplates } from '../../../api/institutions'
import { REASON_OPTIONS } from './reasonCodes'
import type { InstReasonCode } from '../../../types'

export default function BulkMessageModal({
  open,
  onClose,
  onSend,
  sending,
}: {
  open: boolean
  onClose: () => void
  onSend: (payload: {
    segment_id: string
    template_id?: string
    body?: string
    reason_code: InstReasonCode
  }) => void
  sending: boolean
}) {
  const [segmentId, setSegmentId] = useState('')
  const [templateId, setTemplateId] = useState('')
  const [body, setBody] = useState('')
  const [reason, setReason] = useState<InstReasonCode>('status_update')

  const segmentsQ = useQuery({ queryKey: ['segments'], queryFn: getSegments, enabled: open })
  const templatesQ = useQuery({
    queryKey: ['templates-inbox'],
    queryFn: () => getTemplates(),
    enabled: open,
  })

  const segments = Array.isArray(segmentsQ.data) ? segmentsQ.data : []
  const templates = Array.isArray(templatesQ.data) ? templatesQ.data : []

  const handleSend = () => {
    if (!segmentId) return
    onSend({
      segment_id: segmentId,
      template_id: templateId || undefined,
      body: body.trim() || undefined,
      reason_code: reason,
    })
  }

  return (
    <Modal isOpen={open} onClose={onClose} title="Message segment">
      <p className="text-sm text-muted-foreground mb-4">
        Each recipient gets an individual thread. Preview per recipient in Templates before sending.
      </p>
      <div className="space-y-3">
        <Select
          label="Segment"
          value={segmentId}
          onChange={e => setSegmentId(e.target.value)}
          options={segments.map(s => ({ value: s.id, label: s.segment_name }))}
          placeholder="Select segment"
        />
        <Select
          label="Template (optional)"
          value={templateId}
          onChange={e => setTemplateId(e.target.value)}
          options={templates.map(t => ({ value: t.id, label: t.name }))}
          placeholder="None — use custom body"
        />
        <Select
          label="Reason"
          value={reason}
          onChange={e => setReason(e.target.value as InstReasonCode)}
          options={REASON_OPTIONS.map(o => ({ value: o.value, label: o.label }))}
        />
        <div>
          <label className="text-sm font-medium text-foreground">Message body</label>
          <textarea
            value={body}
            onChange={e => setBody(e.target.value)}
            rows={4}
            className="mt-1 w-full rounded-md border border-border px-3 py-2 text-sm"
            placeholder="Or rely on template body with {{variables}}"
          />
        </div>
      </div>
      <div className="mt-4 flex justify-end gap-2">
        <Button variant="ghost" onClick={onClose}>
          Cancel
        </Button>
        <Button onClick={handleSend} disabled={!segmentId || sending} className="bg-cobalt hover:bg-cobalt/90">
          {sending ? 'Sending…' : 'Message applicants'}
        </Button>
      </div>
    </Modal>
  )
}
