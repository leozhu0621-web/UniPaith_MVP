import { useState } from 'react'
import QueryError from '../../components/ui/QueryError'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { CalendarDays, Plus, Users, MapPin, Clock, Edit2, XCircle, Video, UserCheck, UserX } from 'lucide-react'
import { getInstitutionEvents, createEvent, updateEvent, cancelEvent, getEventAttendees, markAttendance } from '../../api/events-admin'
import { getInstitutionPrograms } from '../../api/institutions'
import Card from '../../components/ui/Card'
import Badge from '../../components/ui/Badge'
import Button from '../../components/ui/Button'
import Modal from '../../components/ui/Modal'
import Input from '../../components/ui/Input'
import Select from '../../components/ui/Select'
import Textarea from '../../components/ui/Textarea'
import EmptyState from '../../components/ui/EmptyState'
import Skeleton from '../../components/ui/Skeleton'
import InstitutionPageHeader from '../../components/institution/InstitutionPageHeader'
import { showToast } from '../../stores/toast-store'
import { formatDateTime } from '../../utils/format'
import { STATUS_COLORS, EVENT_TYPES } from '../../utils/constants'
import type { EventItem, RSVP, Program } from '../../types'

export default function EventsPage() {
  const queryClient = useQueryClient()
  const [statusFilter, setStatusFilter] = useState('')
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [showAttendeesModal, setShowAttendeesModal] = useState(false)
  const [selectedEventId, setSelectedEventId] = useState<string | null>(null)
  const [editTarget, setEditTarget] = useState<EventItem | null>(null)

  // Create form state
  const [eventName, setEventName] = useState('')
  const [eventType, setEventType] = useState('webinar')
  const [startTime, setStartTime] = useState('')
  const [endTime, setEndTime] = useState('')
  const [description, setDescription] = useState('')
  const [location, setLocation] = useState('')
  const [meetingLink, setMeetingLink] = useState('')
  const [capacity, setCapacity] = useState('')
  const [programId, setProgramId] = useState('')
  const [cancelTarget, setCancelTarget] = useState<EventItem | null>(null)

  const eventsQ = useQuery({
    queryKey: ['institution-events', statusFilter],
    queryFn: () => getInstitutionEvents(statusFilter || undefined),
  })
  const events: EventItem[] = Array.isArray(eventsQ.data) ? eventsQ.data : []

  const programsQ = useQuery({ queryKey: ['institution-programs'], queryFn: getInstitutionPrograms })
  const programs: Program[] = Array.isArray(programsQ.data) ? programsQ.data : []
  const programOptions = [{ value: '', label: 'None' }, ...programs.map(p => ({ value: p.id, label: p.program_name }))]

  const attendeesQ = useQuery({
    queryKey: ['event-attendees', selectedEventId],
    queryFn: () => getEventAttendees(selectedEventId!),
    enabled: !!selectedEventId && showAttendeesModal,
  })
  const attendees: RSVP[] = Array.isArray(attendeesQ.data) ? attendeesQ.data : []

  const createMut = useMutation({
    mutationFn: createEvent,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['institution-events'] })
      showToast('Event created', 'success')
      setShowCreateModal(false)
      resetForm()
    },
    onError: () => showToast('Failed to create event', 'error'),
  })

  const updateMut = useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: any }) => updateEvent(id, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['institution-events'] })
      showToast('Event updated', 'success')
      setShowCreateModal(false)
      resetForm()
    },
    onError: () => showToast('Failed to update event', 'error'),
  })

  const cancelMut = useMutation({
    mutationFn: cancelEvent,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['institution-events'] })
      showToast('Event cancelled — RSVP’d students notified', 'success')
      setCancelTarget(null)
    },
    onError: () => showToast('Failed to cancel event', 'error'),
  })

  const attendanceMut = useMutation({
    mutationFn: ({ rsvpId, status }: { rsvpId: string; status: 'attended' | 'no_show' }) =>
      markAttendance(selectedEventId!, rsvpId, status),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['event-attendees', selectedEventId] })
    },
    onError: () => showToast('Failed to update attendance', 'error'),
  })

  const openEdit = (ev: EventItem) => {
    setEditTarget(ev)
    setEventName(ev.event_name)
    setEventType(ev.event_type)
    setStartTime(ev.start_time.slice(0, 16))
    setEndTime(ev.end_time.slice(0, 16))
    setDescription(ev.description ?? '')
    setLocation(ev.location ?? '')
    setMeetingLink(ev.meeting_link ?? '')
    setCapacity(ev.capacity?.toString() ?? '')
    setProgramId(ev.program_id ?? '')
    setShowCreateModal(true)
  }

  const resetForm = () => {
    setEditTarget(null)
    setEventName('')
    setEventType('webinar')
    setStartTime('')
    setEndTime('')
    setDescription('')
    setLocation('')
    setMeetingLink('')
    setCapacity('')
    setProgramId('')
  }

  const handleCreate = () => {
    if (!eventName || !startTime || !endTime) { showToast('Name, start, and end times are required', 'warning'); return }
    const payload = {
      event_name: eventName,
      event_type: eventType,
      start_time: new Date(startTime).toISOString(),
      end_time: new Date(endTime).toISOString(),
      description: description || undefined,
      location: location || undefined,
      meeting_link: meetingLink || undefined,
      capacity: capacity ? Number(capacity) : undefined,
      program_id: programId || null,
    }
    if (editTarget) {
      updateMut.mutate({ id: editTarget.id, payload })
    } else {
      createMut.mutate(payload)
    }
  }

  const statusOptions = [
    { value: '', label: 'All Statuses' },
    { value: 'open', label: 'Open' },
    { value: 'closed', label: 'Closed' },
    { value: 'cancelled', label: 'Cancelled' },
  ]

  return (
    <div className="p-6 space-y-4">
      <InstitutionPageHeader
        title="Recruitment Events"
        actions={(
          <Button variant="secondary" onClick={() => { resetForm(); setShowCreateModal(true) }} className="flex items-center gap-2">
            <Plus size={16} /> New Event
          </Button>
        )}
      />

      <Card pad={false} className="p-3">
        <p className="text-xs text-muted-foreground">Operational cue</p>
        <p className="text-sm text-foreground">
          Compare event fill rates to identify which event types and programs attract stronger applicant intent.
        </p>
      </Card>

      {events.length > 0 && (
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          <Card pad={false} className="p-3">
            <p className="text-xs text-muted-foreground">Open Events</p>
            <p className="text-xl font-semibold text-foreground">{events.filter(e => e.status === 'open').length}</p>
          </Card>
          <Card pad={false} className="p-3">
            <p className="text-xs text-muted-foreground">Total RSVPs</p>
            <p className="text-xl font-semibold text-foreground">{events.reduce((sum, e) => sum + e.rsvp_count, 0)}</p>
          </Card>
          <Card pad={false} className="p-3">
            <p className="text-xs text-muted-foreground">Average Fill</p>
            <p className="text-xl font-semibold text-foreground">
              {(() => {
                const withCapacity = events.filter(e => (e.capacity ?? 0) > 0)
                if (withCapacity.length === 0) return '-'
                const ratio = withCapacity.reduce((sum, e) => sum + (e.rsvp_count / (e.capacity ?? 1)), 0) / withCapacity.length
                return `${Math.round(ratio * 100)}%`
              })()}
            </p>
          </Card>
        </div>
      )}

      <div className="flex items-center gap-4">
        <Select options={statusOptions} value={statusFilter} onChange={e => setStatusFilter(e.target.value)} className="w-48" />
      </div>

      {eventsQ.isError ? (
        <QueryError detail="Couldn’t load events." onRetry={() => eventsQ.refetch()} />
      ) : eventsQ.isLoading ? (
        <div className="grid grid-cols-2 gap-4">{Array.from({ length: 4 }).map((_, i) => <Skeleton key={i} className="h-40" />)}</div>
      ) : events.length === 0 ? (
        <EmptyState
          icon={<CalendarDays size={40} />}
          title="No events"
          description="Create events to engage with prospective students."
          action={{ label: 'New Event', onClick: () => setShowCreateModal(true) }}
        />
      ) : (
        <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
          {events.map(ev => {
            const prog = programs.find(p => p.id === ev.program_id)
            return (
              <Card pad={false} key={ev.id} className="p-4">
                <div className="flex items-start justify-between mb-2">
                  <h3 className="font-semibold text-foreground">{ev.event_name}</h3>
                  <Badge variant={(STATUS_COLORS[ev.status] as any) ?? 'neutral'}>{ev.status}</Badge>
                </div>
                <Badge variant="info" className="mb-3">{ev.event_type}</Badge>
                <div className="space-y-1.5 text-sm text-muted-foreground">
                  <div className="flex items-center gap-2"><Clock size={14} /> {formatDateTime(ev.start_time)} - {formatDateTime(ev.end_time)}</div>
                  {ev.location && <div className="flex items-center gap-2"><MapPin size={14} /> {ev.location}</div>}
                  <div className="flex items-center gap-2 flex-wrap">
                    <Users size={14} />
                    RSVP&rsquo;d: {ev.confirmed_count ?? ev.rsvp_count}{ev.capacity ? ` / ${ev.capacity}` : ''}
                    {(ev.waitlist_count ?? 0) > 0 && (
                      <span className="text-secondary font-medium">· {ev.waitlist_count} waitlisted</span>
                    )}
                  </div>
                  {ev.meeting_link && <div className="flex items-center gap-2"><Video size={14} /> Online event</div>}
                  {prog && <p className="text-xs text-muted-foreground/70">Program: {prog.program_name}</p>}
                </div>
                <div className="flex gap-2 mt-3">
                  <Button variant="ghost" size="sm" onClick={() => { setSelectedEventId(ev.id); setShowAttendeesModal(true) }}>
                    View Attendees
                  </Button>
                  {ev.status !== 'cancelled' && (
                    <>
                      <Button variant="ghost" size="sm" onClick={() => openEdit(ev)} className="flex items-center gap-1">
                        <Edit2 size={14} /> Edit
                      </Button>
                      <Button variant="ghost" size="sm" onClick={() => setCancelTarget(ev)}
                        className="flex items-center gap-1 text-destructive">
                        <XCircle size={14} /> Cancel
                      </Button>
                    </>
                  )}
                </div>
              </Card>
            )
          })}
        </div>
      )}

      {/* Create Event Modal */}
      <Modal isOpen={showCreateModal} onClose={() => { setShowCreateModal(false); resetForm() }} title={editTarget ? 'Edit Event' : 'New Event'}>
        <div className="space-y-4">
          <Input label="Event Name *" value={eventName} onChange={e => setEventName(e.target.value)} />
          <Select label="Event Type" options={EVENT_TYPES} value={eventType} onChange={e => setEventType(e.target.value)} />
          <div className="grid grid-cols-2 gap-4">
            <Input label="Start *" type="datetime-local" value={startTime} onChange={e => setStartTime(e.target.value)} />
            <Input label="End *" type="datetime-local" value={endTime} onChange={e => setEndTime(e.target.value)} />
          </div>
          <Textarea label="Description" value={description} onChange={e => setDescription(e.target.value)} rows={3} />
          <Input label="Location" value={location} onChange={e => setLocation(e.target.value)} placeholder="Venue or city (in-person)" />
          <Input label="Meeting link" value={meetingLink} onChange={e => setMeetingLink(e.target.value)} placeholder="Zoom / Meet link (online events)" />
          <Input label="Capacity" type="number" value={capacity} onChange={e => setCapacity(e.target.value)} />
          <Select label="Program" options={programOptions} value={programId} onChange={e => setProgramId(e.target.value)} />
          <div className="flex justify-end gap-2">
            <Button variant="ghost" onClick={() => { setShowCreateModal(false); resetForm() }}>Cancel</Button>
            <Button variant="secondary" onClick={handleCreate} disabled={createMut.isPending || updateMut.isPending}>
              {(createMut.isPending || updateMut.isPending) ? 'Saving...' : editTarget ? 'Update Event' : 'Create Event'}
            </Button>
          </div>
        </div>
      </Modal>

      {/* Attendees Modal */}
      <Modal isOpen={showAttendeesModal} onClose={() => setShowAttendeesModal(false)} title="Event Attendees">
        {attendeesQ.isLoading ? (
          <div className="space-y-2">{Array.from({ length: 3 }).map((_, i) => <Skeleton key={i} className="h-10" />)}</div>
        ) : attendees.length === 0 ? (
          <p className="text-sm text-muted-foreground text-center py-4">No attendees yet.</p>
        ) : (
          <div className="space-y-3">
            <p className="text-sm text-muted-foreground">
              Attendees: {attendees.filter(a => a.attendance_status === 'attended' || a.attended_at).length} of{' '}
              {attendees.filter(a => a.rsvp_status !== 'waitlisted').length} RSVPs
              {attendees.some(a => a.rsvp_status === 'waitlisted') &&
                ` · ${attendees.filter(a => a.rsvp_status === 'waitlisted').length} waitlisted`}
            </p>
            <div className="space-y-2 max-h-96 overflow-y-auto">
              {attendees.map(a => {
                const attended = a.attendance_status === 'attended' || !!a.attended_at
                const noShow = a.attendance_status === 'no_show'
                return (
                  <div key={a.id} className="flex items-center justify-between py-2 border-b border-border gap-2">
                    <div className="min-w-0">
                      <p className="text-sm text-foreground truncate">
                        {a.student_name || a.student_email || `${a.student_id.slice(0, 8)}…`}
                      </p>
                      {a.student_name && a.student_email && (
                        <p className="text-xs text-muted-foreground/70 truncate">{a.student_email}</p>
                      )}
                    </div>
                    <div className="flex items-center gap-2 flex-shrink-0">
                      <Badge variant={a.rsvp_status === 'waitlisted' ? 'warning' : 'success'}>
                        {a.rsvp_status === 'waitlisted' ? 'Waitlist' : 'RSVP'}
                      </Badge>
                      <button
                        onClick={() => attendanceMut.mutate({ rsvpId: a.id, status: 'attended' })}
                        className={`p-1 rounded ${attended ? 'bg-success-soft text-success' : 'text-muted-foreground/70 hover:bg-muted'}`}
                        title="Mark attended"
                      ><UserCheck size={16} /></button>
                      <button
                        onClick={() => attendanceMut.mutate({ rsvpId: a.id, status: 'no_show' })}
                        className={`p-1 rounded ${noShow ? 'bg-destructive/10 text-destructive' : 'text-muted-foreground/70 hover:bg-muted'}`}
                        title="Mark no-show"
                      ><UserX size={16} /></button>
                    </div>
                  </div>
                )
              })}
            </div>
          </div>
        )}
      </Modal>

      {/* Cancel Confirmation (Spec 27 §7) */}
      <Modal isOpen={!!cancelTarget} onClose={() => setCancelTarget(null)} title="Cancel Event">
        <p className="text-sm text-muted-foreground mb-4">
          Cancel &ldquo;{cancelTarget?.event_name}&rdquo;? All RSVP&rsquo;d students will be notified and the event
          removed from their calendars. This cannot be undone.
        </p>
        <div className="flex justify-end gap-2">
          <Button variant="ghost" onClick={() => setCancelTarget(null)}>Keep event</Button>
          <Button variant="danger" onClick={() => cancelTarget && cancelMut.mutate(cancelTarget.id)} disabled={cancelMut.isPending}>
            {cancelMut.isPending ? 'Cancelling...' : 'Cancel event'}
          </Button>
        </div>
      </Modal>
    </div>
  )
}
