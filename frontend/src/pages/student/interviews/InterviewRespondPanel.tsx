import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { CalendarClock, ExternalLink, Video } from 'lucide-react'
import Badge from '../../../components/ui/Badge'
import Button from '../../../components/ui/Button'
import {
  confirmInterview,
  declineInterview,
  requestInterviewReschedule,
} from '../../../api/interviews'
import { showToast } from '../../../stores/toast-store'
import { formatDateTime } from '../../../utils/format'
import {
  ASYNC_INTERVIEW_TYPES,
  INTERVIEW_TYPE_LABELS,
  STATUS_COLORS,
} from '../../../utils/constants'
import type { Interview } from '../../../types'

type BadgeVariant = 'neutral' | 'info' | 'success' | 'warning' | 'danger'

const STATUS_LABELS: Record<string, string> = {
  proposed: 'Awaiting student',
  confirmed: 'Confirmed',
  completed: 'Completed',
  cancelled: 'Cancelled',
  no_show: 'No show',
}

interface Props {
  interview: Interview
  compact?: boolean
  onUpdated?: () => void
}

export default function InterviewRespondPanel({ interview, compact = false, onUpdated }: Props) {
  const [selectedSlot, setSelectedSlot] = useState('')
  const qc = useQueryClient()
  const isAsync = ASYNC_INTERVIEW_TYPES.includes(interview.interview_type)
  const isProposed = interview.status === 'proposed'
  const isConfirmed = interview.status === 'confirmed'
  const canRespond = isProposed && !interview.async_expired

  const invalidate = () => {
    qc.invalidateQueries({ queryKey: ['interviews'] })
    qc.invalidateQueries({ queryKey: ['calendar'] })
    onUpdated?.()
  }

  const confirmMut = useMutation({
    mutationFn: () =>
      confirmInterview(
        interview.id,
        isAsync ? null : selectedSlot || interview.proposed_times?.[0] || null,
      ),
    onSuccess: () => {
      invalidate()
      showToast('Interview confirmed', 'success')
    },
    onError: () => showToast('Could not confirm — pick a proposed time and try again', 'error'),
  })

  const declineMut = useMutation({
    mutationFn: () => declineInterview(interview.id),
    onSuccess: () => {
      invalidate()
      showToast('Interview declined', 'success')
    },
    onError: () => showToast('Could not decline interview', 'error'),
  })

  const rescheduleMut = useMutation({
    mutationFn: () => requestInterviewReschedule(interview.id),
    onSuccess: () => {
      invalidate()
      showToast('Reschedule request sent to admissions', 'success')
    },
    onError: () => showToast('Could not request reschedule', 'error'),
  })

  const busy = confirmMut.isPending || declineMut.isPending || rescheduleMut.isPending

  const statusBadge = () => {
    if (interview.async_expired) {
      return <Badge variant="danger">No submission received</Badge>
    }
    if (interview.status === 'proposed') {
      return <Badge variant="warning">Awaiting student</Badge>
    }
    const variant = (STATUS_COLORS[interview.status] as BadgeVariant) ?? 'neutral'
    return (
      <Badge variant={variant}>
        {STATUS_LABELS[interview.status] || interview.status.replace(/_/g, ' ')}
      </Badge>
    )
  }

  const scheduledLabel = () => {
    const at = interview.scheduled_at ?? interview.confirmed_time
    if (at) return formatDateTime(at)
    if (interview.async_window_end) return `Submit by ${formatDateTime(interview.async_window_end)}`
    if (interview.proposed_times?.length) return `${interview.proposed_times.length} times proposed`
    return 'Not yet scheduled'
  }

  const meetingLink = interview.meeting_link || (
    interview.location_or_link?.startsWith('http') ? interview.location_or_link : null
  )
  const location = interview.location || (
    interview.location_or_link && !interview.location_or_link.startsWith('http')
      ? interview.location_or_link
      : null
  )

  return (
    <div className={compact ? 'space-y-3' : 'rounded-lg border border-border p-4 space-y-3'}>
      <div className="flex flex-wrap items-start justify-between gap-2">
        <div className="flex items-start gap-3 min-w-0">
          {!compact && (
            <div className="w-10 h-10 rounded-full bg-student-mist flex items-center justify-center shrink-0">
              <CalendarClock size={18} className="text-cobalt" />
            </div>
          )}
          <div className="min-w-0">
            <p className="text-sm font-medium text-student-ink">
              {INTERVIEW_TYPE_LABELS[interview.interview_type] ||
                (interview.interview_type || 'Interview').replace(/_/g, ' ')}
            </p>
            <p className="text-xs text-student-text mt-0.5">{scheduledLabel()}</p>
          </div>
        </div>
        {statusBadge()}
      </div>

      {interview.notes_to_student && (
        <p className="text-sm text-student-text whitespace-pre-wrap">{interview.notes_to_student}</p>
      )}

      {(meetingLink || location) && (isConfirmed || interview.status === 'completed') && (
        <div className="text-sm space-y-1">
          {location && (
            <p className="text-student-text">
              <span className="font-medium text-student-ink">Location: </span>
              {location}
            </p>
          )}
          {meetingLink && (
            <a
              href={meetingLink}
              target="_blank"
              rel="noreferrer"
              className="inline-flex items-center gap-1 text-cobalt hover:underline"
            >
              <Video size={14} /> Join meeting <ExternalLink size={12} />
            </a>
          )}
        </div>
      )}

      {canRespond && (
        <div className="rounded-lg border border-warning/30 bg-warning-soft/40 p-3 space-y-3">
          <p className="text-sm text-foreground">
            {isAsync
              ? 'Accept this interview window, or decline if you cannot participate.'
              : 'Pick one of the proposed times, or request a reschedule.'}
          </p>

          {!isAsync && interview.proposed_times?.length > 0 && (
            <div className="flex flex-wrap gap-2">
              {interview.proposed_times.map(slot => {
                const on = selectedSlot === slot
                return (
                  <button
                    key={slot}
                    type="button"
                    disabled={busy}
                    onClick={() => setSelectedSlot(slot)}
                    className={`rounded-pill border px-3 py-1.5 text-xs font-medium transition-colors ${
                      on
                        ? 'border-cobalt bg-cobalt text-white'
                        : 'border-border bg-card text-foreground hover:bg-muted'
                    }`}
                  >
                    {formatDateTime(slot)}
                  </button>
                )
              })}
            </div>
          )}

          <div className="flex flex-wrap gap-2">
            <Button
              size="sm"
              variant="secondary"
              loading={confirmMut.isPending}
              disabled={busy || (!isAsync && !selectedSlot && !interview.proposed_times?.[0])}
              onClick={() => confirmMut.mutate()}
            >
              Confirm
            </Button>
            <Button
              size="sm"
              variant="tertiary"
              loading={rescheduleMut.isPending}
              disabled={busy}
              onClick={() => rescheduleMut.mutate()}
            >
              Reschedule
            </Button>
            <Button
              size="sm"
              variant="ghost"
              className="text-error"
              loading={declineMut.isPending}
              disabled={busy}
              onClick={() => declineMut.mutate()}
            >
              Decline
            </Button>
          </div>
        </div>
      )}

      {isConfirmed && !compact && (
        <div className="rounded-lg bg-student-mist p-3">
          <p className="text-xs font-medium text-student-ink mb-1">Prep checklist</p>
          <ul className="text-xs text-student-text space-y-1">
            <li>Research the program and recent news</li>
            <li>Prepare key talking points and questions</li>
            <li>
              {isAsync || interview.interview_type === 'live'
                ? 'Test your camera, mic, and recording setup if needed'
                : 'Plan arrival or platform access ahead of time'}
            </li>
          </ul>
        </div>
      )}
    </div>
  )
}
