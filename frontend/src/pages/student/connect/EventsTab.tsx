// Connect → Events (Spec 20 §5). Upcoming | Past | My RSVPs; RSVP / waitlist;
// add-to-calendar; detail sheet with meeting-link reveal near start.
// Brand: cobalt CTAs; GOLD reserved for the RSVP-confirmed state (§10).
import { useMemo, useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  CalendarPlus, Check, Clock, ExternalLink, MapPin, Sparkles, Users, Video,
} from 'lucide-react'
import { getConnectEvents, type ConnectEvent } from '../../../api/connect'
import { rsvpEvent, cancelRsvp, addEventToCalendar } from '../../../api/events'
import Sheet from '../../../components/ui/Sheet'
import QueryError from '../../../components/ui/QueryError'
import Skeleton from '../../../components/ui/Skeleton'
import { showToast } from '../../../stores/toast-store'

type Scope = 'upcoming' | 'past' | 'mine'

const SCOPES: { key: Scope; label: string }[] = [
  { key: 'upcoming', label: 'Upcoming' },
  { key: 'past', label: 'Past' },
  { key: 'mine', label: 'My RSVPs' },
]

const EVENT_TYPE_LABELS: Record<string, string> = {
  info_session: 'Info session',
  webinar: 'Webinar',
  qa: 'Q&A',
  q_and_a: 'Q&A',
  portfolio_review: 'Portfolio review',
  campus_visit: 'Campus visit',
  fair: 'Fair',
}

function fmtDate(iso: string) {
  return new Date(iso).toLocaleString('en-US', {
    weekday: 'short', month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit',
  })
}

export default function EventsTab() {
  const qc = useQueryClient()
  const [scope, setScope] = useState<Scope>('upcoming')
  const [detail, setDetail] = useState<ConnectEvent | null>(null)

  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ['connect-events', scope],
    queryFn: () => getConnectEvents(scope),
    retry: false,
  })

  // Optimistic RSVP (Ship D §4): flip the visible card instantly, roll back +
  // toast if the call fails, then reconcile with the server either way.
  const rsvpMut = useMutation({
    mutationFn: ({ id, going }: { id: string; going: boolean }) =>
      going ? cancelRsvp(id) : rsvpEvent(id),
    onMutate: async ({ id, going }) => {
      const mutationScope = scope
      await qc.cancelQueries({ queryKey: ['connect-events', mutationScope] })
      const previous = qc.getQueryData<{ events: ConnectEvent[] }>(['connect-events', mutationScope])
      qc.setQueryData<{ events: ConnectEvent[] }>(['connect-events', mutationScope], old => {
        if (!old?.events) return old
        return {
          ...old,
          events: old.events.map(ev => {
            if (ev.id !== id) return ev
            if (going) {
              // Cancelling — leave the going count alone unless we held a seat.
              return {
                ...ev,
                rsvp_state: 'none' as const,
                going_count: ev.rsvp_state === 'rsvp' ? Math.max(0, ev.going_count - 1) : ev.going_count,
              }
            }
            const waitlisted = ev.at_capacity
            return {
              ...ev,
              rsvp_state: waitlisted ? ('waitlist' as const) : ('rsvp' as const),
              going_count: waitlisted ? ev.going_count : ev.going_count + 1,
            }
          }),
        }
      })
      return { previous, mutationScope }
    },
    onError: (_err, vars, ctx) => {
      if (ctx?.previous !== undefined) qc.setQueryData(['connect-events', ctx.mutationScope], ctx.previous)
      showToast(
        vars.going
          ? "We couldn't cancel your RSVP. Please try again."
          : "We couldn't RSVP you for this event. Please try again.",
        'error',
      )
    },
    onSettled: () => {
      qc.invalidateQueries({ queryKey: ['connect-events'] })
      qc.invalidateQueries({ queryKey: ['my-rsvps'] })
    },
  })

  // Discover review 2026-06-14 — float events recommended for the student's
  // saved/applied programs to the top of the Upcoming scope (stable within each
  // group; the backend already keeps start-time order). Past/mine stay as-is.
  const events = useMemo(() => {
    const list = data?.events ?? []
    if (scope !== 'upcoming') return list
    return [...list].sort((a, b) => Number(b.recommended) - Number(a.recommended))
  }, [data, scope])

  return (
    <div className="space-y-4">
      <div className="flex gap-1">
        {SCOPES.map(s => (
          <button
            key={s.key}
            onClick={() => setScope(s.key)}
            className={`px-3 py-1.5 text-xs font-medium rounded-full transition-colors ${
              scope === s.key
                ? 'bg-secondary text-secondary-foreground'
                : 'bg-muted text-muted-foreground hover:text-foreground'
            }`}
          >
            {s.label}
          </button>
        ))}
      </div>

      {isLoading ? (
        <div className="space-y-3">
          {[1, 2, 3].map(i => <Skeleton key={i} className="h-24 rounded-xl" />)}
        </div>
      ) : isError ? (
        <QueryError onRetry={() => refetch()} />
      ) : events.length === 0 ? (
        <div className="text-center py-12">
          <p className="text-sm text-muted-foreground">
            {scope === 'mine' ? 'Events you RSVP to will show up here.'
              : scope === 'past' ? 'No past events.'
              : 'No upcoming events from the institutions you follow.'}
          </p>
        </div>
      ) : (
        <div className="stagger-list space-y-4">
          {events.map(ev => (
            <EventListCard
              key={ev.id}
              event={ev}
              busy={rsvpMut.isPending}
              onOpen={() => setDetail(ev)}
              onRsvp={() => rsvpMut.mutate({ id: ev.id, going: ev.rsvp_state === 'rsvp' || ev.rsvp_state === 'waitlist' })}
              onAddCalendar={() => addEventToCalendar(ev.id, ev.event_name)}
            />
          ))}
        </div>
      )}

      {/* Detail sheet — right on desktop, bottom on mobile */}
      {detail && (
        <Sheet
          isOpen
          onClose={() => setDetail(null)}
          title={detail.event_name}
          side="right"
          footer={
            <div className="flex items-center gap-2">
              <RsvpButton
                event={detail}
                onRsvp={() => rsvpMut.mutate({ id: detail.id, going: detail.rsvp_state === 'rsvp' || detail.rsvp_state === 'waitlist' })}
              />
              <button
                onClick={() => addEventToCalendar(detail.id, detail.event_name)}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-lg text-secondary hover:bg-secondary/5"
              >
                <CalendarPlus size={13} /> Add to calendar
              </button>
            </div>
          }
        >
          <EventDetailBody event={detail} />
        </Sheet>
      )}
    </div>
  )
}

function TypeBadge({ type }: { type: string | null }) {
  if (!type) return null
  return (
    <span className="px-2 py-0.5 text-[10px] rounded-full bg-secondary/10 text-secondary">
      {EVENT_TYPE_LABELS[type] || type.replace(/_/g, ' ')}
    </span>
  )
}

function RsvpButton({ event, onRsvp, busy }: { event: ConnectEvent; onRsvp: () => void; busy?: boolean }) {
  if (event.status === 'cancelled') {
    return <span className="px-4 py-1.5 text-xs font-medium rounded-lg bg-muted text-muted-foreground">Cancelled</span>
  }
  const st = event.rsvp_state
  if (st === 'rsvp') {
    // Gold = the earned RSVP-confirmed state (Spec 20 §10).
    return (
      <button onClick={onRsvp} disabled={busy} className="px-4 py-1.5 text-xs font-semibold rounded-lg bg-primary text-primary-foreground border border-primary hover:brightness-95 transition-colors disabled:opacity-60 inline-flex items-center gap-1">
        <Check size={13} /> RSVP'd
      </button>
    )
  }
  if (st === 'waitlist') {
    return (
      <button onClick={onRsvp} disabled={busy} className="px-4 py-1.5 text-xs font-medium rounded-lg border border-secondary text-secondary hover:bg-secondary/5 transition-colors disabled:opacity-60">
        On waitlist · Leave
      </button>
    )
  }
  if (st === 'attended') {
    return <span className="px-4 py-1.5 text-xs font-medium rounded-lg bg-muted text-muted-foreground">Attended</span>
  }
  if (event.at_capacity) {
    return (
      <button onClick={onRsvp} disabled={busy} className="px-4 py-1.5 text-xs font-medium rounded-lg border border-secondary text-secondary hover:bg-secondary/5 transition-colors disabled:opacity-60">
        Join waitlist
      </button>
    )
  }
  return (
    <button onClick={onRsvp} disabled={busy} className="px-4 py-1.5 text-xs font-medium rounded-lg bg-secondary text-secondary-foreground hover:brightness-95 transition-colors disabled:opacity-60">
      RSVP
    </button>
  )
}

interface CardProps {
  event: ConnectEvent
  busy?: boolean
  onOpen: () => void
  onRsvp: () => void
  onAddCalendar: () => void
}

function EventListCard({ event, busy, onOpen, onRsvp, onAddCalendar }: CardProps) {
  const d = new Date(event.start_time)
  const capacityLabel = event.capacity ? ` of ${event.capacity}` : ''
  const waitlistLabel = event.waitlist_count > 0 ? ` · ${event.waitlist_count} waitlisted` : ''
  return (
    <div className="bg-card rounded-xl border border-border elev-subtle hover-lift hover:elev-raised">
      <div className="flex items-center gap-2 px-4 pt-3">
        <TypeBadge type={event.event_type} />
        {event.status === 'cancelled' && (
          <span className="px-2 py-0.5 text-[10px] rounded-full bg-error/10 text-error font-medium">
            Cancelled
          </span>
        )}
        {event.recommended && (
          <span className="inline-flex items-center gap-1 text-[10px] font-semibold text-secondary">
            <Sparkles size={11} /> Recommended
          </span>
        )}
        <span className="ml-auto text-[10px] text-muted-foreground">{fmtDate(event.start_time)}</span>
      </div>
      <div className="flex gap-4 px-4 py-3">
        <div className="w-12 h-14 bg-muted border border-border rounded-lg flex flex-col items-center justify-center flex-shrink-0">
          <span className="text-[10px] font-semibold text-secondary uppercase">{d.toLocaleString('en-US', { month: 'short' })}</span>
          <span className="text-lg font-bold text-foreground">{d.getDate()}</span>
        </div>
        <button onClick={onOpen} className="flex-1 min-w-0 text-left">
          <h3 className="text-sm font-semibold text-foreground truncate hover:text-secondary transition-colors">{event.event_name}</h3>
          <p className="text-xs text-foreground">{event.institution_name}</p>
          <div className="flex items-center gap-3 text-[10px] text-muted-foreground mt-1">
            <span className="flex items-center gap-0.5"><Clock size={9} /> {d.toLocaleString('en-US', { hour: 'numeric', minute: '2-digit' })}</span>
            <span className="flex items-center gap-0.5">
              {event.location ? <><MapPin size={9} /> {event.location}</> : <><Video size={9} /> Online</>}
            </span>
            <span className="flex items-center gap-0.5">
              <Users size={9} /> {event.going_count}{capacityLabel} going{waitlistLabel}
            </span>
          </div>
        </button>
        <div className="flex flex-col items-end justify-center gap-1.5 flex-shrink-0">
          <RsvpButton event={event} onRsvp={onRsvp} busy={busy} />
          <button onClick={onAddCalendar} className="inline-flex items-center gap-1 text-[10px] text-secondary hover:underline">
            <CalendarPlus size={11} /> Add to calendar
          </button>
        </div>
      </div>
    </div>
  )
}

function EventDetailBody({ event }: { event: ConnectEvent }) {
  const rsvped = event.rsvp_state === 'rsvp' || event.rsvp_state === 'attended'
  const capacityLabel = event.capacity ? ` of ${event.capacity}` : ''
  const waitlistLabel = event.waitlist_count > 0 ? ` · ${event.waitlist_count} waitlisted` : ''
  return (
    <div className="space-y-3">
      <p className="text-sm text-foreground">{event.institution_name}</p>
      <div className="flex items-center gap-2 text-sm text-muted-foreground">
        <Clock size={14} className="text-secondary" /> {fmtDate(event.start_time)}
      </div>
      <div className="flex items-center gap-2 text-sm text-muted-foreground">
        {event.location ? <><MapPin size={14} className="text-secondary" /> {event.location}</> : <><Video size={14} className="text-secondary" /> Online event</>}
      </div>
      <div className="flex items-center gap-2 text-sm text-muted-foreground">
        <Users size={14} /> {event.going_count}{capacityLabel} going{waitlistLabel}
      </div>
      {event.description && <p className="text-sm text-foreground leading-relaxed whitespace-pre-line">{event.description}</p>}
      {rsvped && event.meeting_link && (
        <a href={event.meeting_link} target="_blank" rel="noreferrer"
           className="inline-flex items-center gap-1.5 text-sm font-medium text-secondary hover:underline">
          <ExternalLink size={14} /> Join meeting
        </a>
      )}
      {rsvped && !event.meeting_link && event.meeting_link_reveals_at && (
        <p className="text-xs text-muted-foreground">
          Your meeting link will appear here closer to the start time.
        </p>
      )}
    </div>
  )
}
