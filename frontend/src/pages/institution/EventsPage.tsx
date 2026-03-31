import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { CalendarDays, Plus, Users, MapPin, Clock } from 'lucide-react'
import { getInstitutionEvents, createEvent, getEventAttendees } from '../../api/events-admin'
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
import { showToast } from '../../stores/toast-store'
import { formatDateTime } from '../../utils/format'
import { EVENT_TYPES, toBadgeVariant } from '../../utils/constants'
import type { EventItem, RSVP, Program } from '../../types'

export default function EventsPage() {
  const queryClient = useQueryClient()
  const [statusFilter, setStatusFilter] = useState('')
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [showAttendeesModal, setShowAttendeesModal] = useState(false)
  const [selectedEventId, setSelectedEventId] = useState<string | null>(null)

  // Create form state
  const [eventName, setEventName] = useState('')
  const [eventType, setEventType] = useState('webinar')
  const [startTime, setStartTime] = useState('')
  const [endTime, setEndTime] = useState('')
  const [description, setDescription] = useState('')
  const [location, setLocation] = useState('')
  const [capacity, setCapacity] = useState('')
  const [programId, setProgramId] = useState('')

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

  const resetForm = () => {
    setEventName('')
    setEventType('webinar')
    setStartTime('')
    setEndTime('')
    setDescription('')
    setLocation('')
    setCapacity('')
    setProgramId('')
  }

  const handleCreate = () => {
    if (!eventName || !startTime || !endTime) { showToast('Name, start, and end times are required', 'warning'); return }
    createMut.mutate({
      event_name: eventName,
      event_type: eventType,
      start_time: new Date(startTime).toISOString(),
      end_time: new Date(endTime).toISOString(),
      description: description || undefined,
      location: location || undefined,
      capacity: capacity ? Number(capacity) : undefined,
      program_id: programId || null,
    })
  }

  const statusOptions = [
    { value: '', label: 'All Statuses' },
    { value: 'open', label: 'Open' },
    { value: 'closed', label: 'Closed' },
    { value: 'cancelled', label: 'Cancelled' },
  ]

  return (
    <div className="p-6 space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Events</h1>
        <Button onClick={() => setShowCreateModal(true)} className="flex items-center gap-2">
          <Plus size={16} /> New Event
        </Button>
      </div>

      <div className="flex items-center gap-4">
        <Select options={statusOptions} value={statusFilter} onChange={e => setStatusFilter(e.target.value)} className="w-48" />
      </div>

      {eventsQ.isLoading ? (
        <div className="grid grid-cols-2 gap-4">{Array.from({ length: 4 }).map((_, i) => <Skeleton key={i} className="h-40" />)}</div>
      ) : events.length === 0 ? (
        <EmptyState
          icon={<CalendarDays size={40} />}
          title="No events"
          description="Create events to engage with prospective students."
          action={{ label: 'New Event', onClick: () => setShowCreateModal(true) }}
        />
      ) : (
        <div className="grid grid-cols-2 gap-4">
          {events.map(ev => {
            const prog = programs.find(p => p.id === ev.program_id)
            return (
              <Card key={ev.id} className="p-4">
                <div className="flex items-start justify-between mb-2">
                  <h3 className="font-semibold text-gray-900">{ev.event_name}</h3>
                  <Badge variant={toBadgeVariant(ev.status)}>{ev.status}</Badge>
                </div>
                <Badge variant="info" className="mb-3">{ev.event_type}</Badge>
                <div className="space-y-1.5 text-sm text-gray-600">
                  <div className="flex items-center gap-2"><Clock size={14} /> {formatDateTime(ev.start_time)} - {formatDateTime(ev.end_time)}</div>
                  {ev.location && <div className="flex items-center gap-2"><MapPin size={14} /> {ev.location}</div>}
                  <div className="flex items-center gap-2">
                    <Users size={14} />
                    {ev.rsvp_count} RSVPs{ev.capacity ? ` / ${ev.capacity} capacity` : ''}
                  </div>
                  {prog && <p className="text-xs text-gray-400">Program: {prog.program_name}</p>}
                </div>
                <div className="mt-3">
                  <Button variant="ghost" size="sm" onClick={() => { setSelectedEventId(ev.id); setShowAttendeesModal(true) }}>
                    View Attendees
                  </Button>
                </div>
              </Card>
            )
          })}
        </div>
      )}

      {/* Create Event Modal */}
      <Modal isOpen={showCreateModal} onClose={() => setShowCreateModal(false)} title="New Event">
        <div className="space-y-4">
          <Input label="Event Name *" value={eventName} onChange={e => setEventName(e.target.value)} />
          <Select label="Event Type" options={EVENT_TYPES} value={eventType} onChange={e => setEventType(e.target.value)} />
          <div className="grid grid-cols-2 gap-4">
            <Input label="Start *" type="datetime-local" value={startTime} onChange={e => setStartTime(e.target.value)} />
            <Input label="End *" type="datetime-local" value={endTime} onChange={e => setEndTime(e.target.value)} />
          </div>
          <Textarea label="Description" value={description} onChange={e => setDescription(e.target.value)} rows={3} />
          <Input label="Location" value={location} onChange={e => setLocation(e.target.value)} />
          <Input label="Capacity" type="number" value={capacity} onChange={e => setCapacity(e.target.value)} />
          <Select label="Program" options={programOptions} value={programId} onChange={e => setProgramId(e.target.value)} />
          <div className="flex justify-end gap-2">
            <Button variant="ghost" onClick={() => setShowCreateModal(false)}>Cancel</Button>
            <Button onClick={handleCreate} disabled={createMut.isPending}>
              {createMut.isPending ? 'Creating...' : 'Create Event'}
            </Button>
          </div>
        </div>
      </Modal>

      {/* Attendees Modal */}
      <Modal isOpen={showAttendeesModal} onClose={() => setShowAttendeesModal(false)} title="Event Attendees">
        {attendeesQ.isLoading ? (
          <div className="space-y-2">{Array.from({ length: 3 }).map((_, i) => <Skeleton key={i} className="h-10" />)}</div>
        ) : attendees.length === 0 ? (
          <p className="text-sm text-gray-500 text-center py-4">No attendees yet.</p>
        ) : (
          <div className="space-y-2">
            {attendees.map(a => (
              <div key={a.id} className="flex items-center justify-between py-2 border-b border-gray-100">
                <span className="text-sm text-gray-700">{a.student_id.slice(0, 12)}...</span>
                <div className="flex items-center gap-2">
                  <Badge variant={a.rsvp_status === 'registered' ? 'success' : 'neutral'}>{a.rsvp_status}</Badge>
                  {a.attended_at && <Badge variant="info">Attended</Badge>}
                </div>
              </div>
            ))}
          </div>
        )}
      </Modal>
    </div>
  )
}
