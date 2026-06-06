import { Calendar, Clock, MapPin, Users } from 'lucide-react'

interface Props {
  event: any
  isRsvped: boolean
  onRsvp: () => void
}

export default function EventCard({ event, isRsvped, onRsvp }: Props) {
  const d = new Date(event.start_time)
  const validDate = !Number.isNaN(d.getTime())
  const month = validDate ? d.toLocaleString('en-US', { month: 'short' }) : '—'
  const day = validDate ? String(d.getDate()) : '—'
  const time = validDate ? d.toLocaleString('en-US', { hour: 'numeric', minute: '2-digit', hour12: true }) : null
  const spotsLeft = event.capacity ? Math.max(0, event.capacity - (event.rsvp_count || 0)) : null

  return (
    <div className="bg-card rounded-xl border border-border hover:elev-raised transition-shadow overflow-hidden">
      <div className="flex items-center gap-2 px-4 pt-3 pb-1">
        <Calendar size={12} className="text-secondary" />
        <span className="text-[10px] font-semibold text-secondary uppercase tracking-wider">Event</span>
        {event.event_type && (
          <span className="px-2 py-0.5 text-[10px] rounded-full bg-secondary/10 text-secondary capitalize">
            {event.event_type.replace(/_/g, ' ')}
          </span>
        )}
      </div>
      <div className="flex gap-4 px-4 pb-4">
        <div className="w-14 h-16 bg-muted border border-border/50 rounded-lg flex flex-col items-center justify-center flex-shrink-0">
          <span className="text-[10px] font-semibold text-secondary uppercase">{month}</span>
          <span className="text-xl font-bold text-foreground">{day}</span>
        </div>
        <div className="flex-1 min-w-0">
          <h3 className="text-sm font-semibold text-foreground mb-0.5">{event.event_name || event.title}</h3>
          <p className="text-xs text-foreground mb-1">{event.institution_name || 'School Event'}</p>
          <div className="flex items-center gap-3 text-[10px] text-foreground">
            {time && <span className="flex items-center gap-0.5"><Clock size={9} /> {time}</span>}
            {event.location && <span className="flex items-center gap-0.5 truncate"><MapPin size={9} /> {event.location}</span>}
            {spotsLeft !== null && <span className="flex items-center gap-0.5"><Users size={9} /> {spotsLeft > 0 ? `${spotsLeft} spots` : 'Full'}</span>}
          </div>
        </div>
        <button
          onClick={onRsvp}
          className={`self-center px-4 py-1.5 text-xs font-medium rounded-lg transition-colors flex-shrink-0 ${
            isRsvped
              ? 'bg-primary text-primary-foreground border border-primary'
              : 'bg-secondary text-secondary-foreground hover:brightness-95'
          }`}
        >
          {isRsvped ? '\u2713 Going' : 'RSVP'}
        </button>
      </div>
    </div>
  )
}
