import { useState } from 'react'
import { Plus, Trash2 } from 'lucide-react'
import { rescheduleInterview } from '../../../api/interviews-admin'
import type { Interview } from '../../../types'
import Modal from '../../../components/ui/Modal'
import Button from '../../../components/ui/Button'
import Input from '../../../components/ui/Input'
import { showToast } from '../../../stores/toast-store'
import { ASYNC_INTERVIEW_TYPES } from '../../../utils/constants'

interface Props {
  isOpen: boolean
  onClose: () => void
  onRescheduled: () => void
  interview: Interview | null
}

export default function RescheduleInterviewModal({ isOpen, onClose, onRescheduled, interview }: Props) {
  const [slots, setSlots] = useState<string[]>(['', '', ''])
  const [windowEnd, setWindowEnd] = useState('')
  const [location, setLocation] = useState('')
  const [submitting, setSubmitting] = useState(false)

  const isAsync = interview ? ASYNC_INTERVIEW_TYPES.includes(interview.interview_type) : false
  const toIso = (local: string) => (local ? new Date(local).toISOString() : '')

  const addSlot = () => setSlots([...slots, ''])
  const removeSlot = (i: number) => setSlots(slots.filter((_, idx) => idx !== i))
  const updateSlot = (i: number, v: string) => setSlots(slots.map((t, idx) => (idx === i ? v : t)))

  const handleSubmit = async () => {
    if (!interview) return
    const validSlots = slots.filter(Boolean).map(toIso)
    if (!isAsync && validSlots.length < 3) {
      showToast('Add at least three proposed times for live interviews', 'warning')
      return
    }
    if (isAsync && !windowEnd) {
      showToast('Set a new submission window deadline', 'warning')
      return
    }
    setSubmitting(true)
    try {
      await rescheduleInterview(interview.id, {
        proposed_times: isAsync ? [] : validSlots,
        async_window_end: isAsync ? toIso(windowEnd) : null,
        location_or_link: location || null,
      })
      showToast('Interview rescheduled — the applicant has been re-invited', 'success')
      onRescheduled()
      onClose()
    } catch {
      showToast('Failed to reschedule', 'error')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Reschedule interview">
      <div className="space-y-4">
        {interview && (
          <p className="text-sm text-muted-foreground">
            {interview.applicant?.name} · {interview.program?.name}
          </p>
        )}
        {isAsync ? (
          <Input
            label="New submission window deadline"
            type="datetime-local"
            value={windowEnd}
            onChange={e => setWindowEnd(e.target.value)}
          />
        ) : (
          <div>
            <label className="block text-sm font-medium text-foreground mb-1">New proposed times</label>
            {slots.map((t, i) => (
              <div key={i} className="flex items-center gap-2 mb-2">
                <Input
                  type="datetime-local"
                  value={t}
                  onChange={e => updateSlot(i, e.target.value)}
                  className="flex-1"
                />
                {slots.length > 1 && (
                  <button
                    type="button"
                    onClick={() => removeSlot(i)}
                    className="p-1 text-muted-foreground hover:text-error transition-colors"
                    aria-label="Remove time"
                  >
                    <Trash2 size={16} />
                  </button>
                )}
              </div>
            ))}
            <Button variant="ghost" size="sm" onClick={addSlot} className="flex items-center gap-1">
              <Plus size={14} /> Add time
            </Button>
          </div>
        )}
        <Input
          label="Location or meeting link (optional)"
          value={location}
          onChange={e => setLocation(e.target.value)}
          placeholder="Update if it changed"
        />
        <div className="flex justify-end gap-2 pt-1">
          <Button variant="tertiary" onClick={onClose}>
            Cancel
          </Button>
          <Button variant="secondary" onClick={handleSubmit} loading={submitting}>
            Reschedule
          </Button>
        </div>
      </div>
    </Modal>
  )
}
