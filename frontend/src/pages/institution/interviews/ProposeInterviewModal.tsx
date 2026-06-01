import { useMemo, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Plus, Trash2, Sparkles, Search } from 'lucide-react'
import { getReviewPriorityQueue } from '../../../api/reviews'
import { proposeInterview, draftInterviewInvite } from '../../../api/interviews-admin'
import type { Program } from '../../../types'
import Modal from '../../../components/ui/Modal'
import Button from '../../../components/ui/Button'
import Input from '../../../components/ui/Input'
import Select from '../../../components/ui/Select'
import Textarea from '../../../components/ui/Textarea'
import Skeleton from '../../../components/ui/Skeleton'
import { showToast } from '../../../stores/toast-store'
import { INTERVIEW_TYPES, ASYNC_INTERVIEW_TYPES } from '../../../utils/constants'

interface Props {
  isOpen: boolean
  onClose: () => void
  onProposed: () => void
  programs: Program[]
}

export default function ProposeInterviewModal({ isOpen, onClose, onProposed, programs }: Props) {
  const [programId, setProgramId] = useState('')
  const [selected, setSelected] = useState<Set<string>>(new Set())
  const [search, setSearch] = useState('')
  const [type, setType] = useState('live')
  const [slots, setSlots] = useState<string[]>(['', '', ''])
  const [windowEnd, setWindowEnd] = useState('')
  const [duration, setDuration] = useState('30')
  const [location, setLocation] = useState('')
  const [notes, setNotes] = useState('')
  const [aiUsed, setAiUsed] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [drafting, setDrafting] = useState(false)

  const isAsync = ASYNC_INTERVIEW_TYPES.includes(type)

  const applicantsQ = useQuery({
    queryKey: ['review-priority-queue', programId || 'all'],
    queryFn: () => getReviewPriorityQueue(programId || undefined),
    enabled: isOpen,
  })
  const applicants = useMemo(() => {
    const list = Array.isArray(applicantsQ.data) ? applicantsQ.data : []
    if (!search.trim()) return list
    const q = search.toLowerCase()
    return list.filter(
      a => (a.student_name || '').toLowerCase().includes(q) || a.application_id.includes(q),
    )
  }, [applicantsQ.data, search])

  const reset = () => {
    setProgramId('')
    setSelected(new Set())
    setSearch('')
    setType('live')
    setSlots(['', '', ''])
    setWindowEnd('')
    setDuration('30')
    setLocation('')
    setNotes('')
    setAiUsed(false)
  }

  const close = () => {
    reset()
    onClose()
  }

  const toggle = (id: string) => {
    setSelected(prev => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }

  const addSlot = () => setSlots([...slots, ''])
  const removeSlot = (i: number) => setSlots(slots.filter((_, idx) => idx !== i))
  const updateSlot = (i: number, v: string) => setSlots(slots.map((t, idx) => (idx === i ? v : t)))

  const toIso = (local: string) => (local ? new Date(local).toISOString() : '')

  const handleDraft = async () => {
    const firstId = Array.from(selected)[0]
    if (!firstId) {
      showToast('Select an applicant first to draft an invite', 'warning')
      return
    }
    setDrafting(true)
    try {
      const res = await draftInterviewInvite({
        application_id: firstId,
        interview_type: type,
        proposed_times: slots.filter(Boolean).map(toIso),
        async_window_end: isAsync ? toIso(windowEnd) : null,
        duration_minutes: Number(duration) || 30,
        location_or_link: location || null,
      })
      if (res.available && res.draft) {
        setNotes(res.draft)
        setAiUsed(true)
        showToast('AI draft added — review and edit before sending', 'success')
      } else {
        showToast('AI draft unavailable right now — write the note manually', 'info')
      }
    } catch {
      showToast('AI draft unavailable right now — write the note manually', 'info')
    } finally {
      setDrafting(false)
    }
  }

  const handleSubmit = async () => {
    if (selected.size === 0) {
      showToast('Select at least one applicant', 'warning')
      return
    }
    const validSlots = slots.filter(Boolean).map(toIso)
    if (!isAsync && validSlots.length === 0) {
      showToast('Add at least one proposed time', 'warning')
      return
    }
    if (isAsync && !windowEnd) {
      showToast('Set a submission window deadline', 'warning')
      return
    }
    setSubmitting(true)
    try {
      await proposeInterview({
        application_ids: Array.from(selected),
        interview_type: type,
        proposed_times: isAsync ? [] : validSlots,
        async_window_end: isAsync ? toIso(windowEnd) : null,
        duration_minutes: Number(duration) || 30,
        location_or_link: location || null,
        notes_to_student: notes || null,
        ai_draft_used: aiUsed,
      })
      showToast(
        `Interview proposed to ${selected.size} applicant${selected.size > 1 ? 's' : ''}`,
        'success',
      )
      onProposed()
      close()
    } catch {
      showToast('Failed to propose interview', 'error')
    } finally {
      setSubmitting(false)
    }
  }

  const programOptions = [
    { value: '', label: 'All programs' },
    ...programs.map(p => ({ value: p.id, label: p.program_name })),
  ]

  return (
    <Modal isOpen={isOpen} onClose={close} title="Propose interview" size="lg">
      <div className="space-y-4">
        {/* Applicants */}
        <div>
          <div className="flex items-end gap-2 mb-2">
            <Select
              label="Program"
              options={programOptions}
              value={programId}
              onChange={e => {
                setProgramId(e.target.value)
                setSelected(new Set())
              }}
              className="flex-1"
            />
          </div>
          <label className="block text-sm font-medium text-foreground mb-1">
            Applicants{selected.size > 0 ? ` · ${selected.size} selected` : ''}
          </label>
          <div className="relative mb-2">
            <Search
              size={14}
              className="absolute left-2.5 top-1/2 -translate-y-1/2 text-muted-foreground"
            />
            <input
              value={search}
              onChange={e => setSearch(e.target.value)}
              placeholder="Search applicants…"
              className="w-full pl-8 pr-3 py-2 text-sm rounded-md border border-border bg-background text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
            />
          </div>
          <div className="max-h-44 overflow-y-auto rounded-md border border-border divide-y divide-border">
            {applicantsQ.isLoading ? (
              <div className="p-2 space-y-2">
                {Array.from({ length: 3 }).map((_, i) => (
                  <Skeleton key={i} className="h-9" />
                ))}
              </div>
            ) : applicants.length === 0 ? (
              <p className="p-3 text-sm text-muted-foreground">
                No applicants found. Applicants appear here once they've applied to a program.
              </p>
            ) : (
              applicants.map(a => {
                const on = selected.has(a.application_id)
                return (
                  <button
                    key={a.application_id}
                    type="button"
                    onClick={() => toggle(a.application_id)}
                    className={`w-full flex items-center gap-3 px-3 py-2 text-left transition-colors ${
                      on ? 'bg-cobalt/10' : 'hover:bg-muted'
                    }`}
                  >
                    <span
                      className={`w-4 h-4 rounded border flex items-center justify-center shrink-0 ${
                        on ? 'bg-cobalt border-cobalt text-white' : 'border-border'
                      }`}
                    >
                      {on && <span className="text-[10px] leading-none">✓</span>}
                    </span>
                    <span className="flex-1 min-w-0">
                      <span className="block text-sm text-foreground truncate">
                        {a.student_name || 'Applicant'}
                      </span>
                      <span className="block text-xs text-muted-foreground truncate">
                        {a.program_name} · {a.status}
                      </span>
                    </span>
                  </button>
                )
              })
            )}
          </div>
        </div>

        {/* Type */}
        <Select
          label="Interview type"
          options={INTERVIEW_TYPES}
          value={type}
          onChange={e => setType(e.target.value)}
        />

        {/* Live: proposed slots + duration. Async: submission window. */}
        {isAsync ? (
          <Input
            label="Submission window deadline"
            type="datetime-local"
            value={windowEnd}
            onChange={e => setWindowEnd(e.target.value)}
            helperText="Applicants submit their responses by this date."
          />
        ) : (
          <>
            <div>
              <label className="block text-sm font-medium text-foreground mb-1">
                Proposed times
              </label>
              <p className="text-xs text-muted-foreground mb-2">
                Offer at least three options so applicants can choose.
              </p>
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
            <Input
              label="Duration (minutes)"
              type="number"
              value={duration}
              onChange={e => setDuration(e.target.value)}
            />
          </>
        )}

        <Input
          label="Location or meeting link"
          value={location}
          onChange={e => setLocation(e.target.value)}
          placeholder="Zoom link, platform URL, or campus address"
        />

        {/* Notes + AI draft */}
        <div>
          <div className="flex items-center justify-between mb-1">
            <label className="block text-sm font-medium text-foreground">Notes for the student</label>
            <Button
              variant="ghost"
              size="sm"
              onClick={handleDraft}
              loading={drafting}
              className="flex items-center gap-1 text-cobalt"
            >
              <Sparkles size={14} /> AI draft
            </Button>
          </div>
          <Textarea
            value={notes}
            onChange={e => {
              setNotes(e.target.value)
              setAiUsed(false)
            }}
            rows={4}
            placeholder="Add a personal note, or generate a starting draft with AI…"
          />
        </div>

        <div className="flex justify-end gap-2 pt-1">
          <Button variant="tertiary" onClick={close}>
            Cancel
          </Button>
          <Button variant="secondary" onClick={handleSubmit} loading={submitting}>
            Propose interview
          </Button>
        </div>
      </div>
    </Modal>
  )
}
