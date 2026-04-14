import { Calendar, Clock, MapPin, Users } from 'lucide-react'

interface Props {
  event: any
  isRsvped: boolean
  onRsvp: () => void
}

export default function EventCard({ event, isRsvped, onRsvp }: Props) {
  const d = new Date(event.start_time)
  const month = d.toLocaleString('en-US', { month: 'short' })
  const day = d.getDate()
  const time = d.toLocaleString('en-US', { hour: 'numeric', minute: '2-digit', hour12: true })
  const spotsLeft = event.capacity ? Math.max(0, event.capacity - (event.rsvp_count || 0)) : null

  return (
    <div className="bg-white rounded-xl border border-divider hover:shadow-md transition-shadow overflow-hidden">
      <div className="flex items-center gap-2 px-4 pt-3 pb-1">
        <Calendar size={12} className="text-student" />
        <span className="text-[10px] font-semibold text-student uppercase tracking-wider">Event</span>
        {event.event_type && (
          <span className="px-2 py-0.5 text-[10px] rounded-full bg-gold-soft text-gold">
            {event.event_type.replace(/_/g, ' ')}
          </span>
        )}
      </div>
      <div className="flex gap-4 px-4 pb-4">
        <div className="w-14 h-16 bg-student-mist rounded-lg flex flex-col items-center justify-center flex-shrink-0">
          <span className="text-[10px] font-semibold text-student uppercase">{month}</span>
          <span className="text-xl font-bold text-student-ink">{day}</span>
        </div>
        <div className="flex-1 min-w-0">
          <h3 className="text-sm font-semibold text-student-ink mb-0.5">{event.event_name || event.title}</h3>
          <p className="text-xs text-student-text mb-1">{event.institution_name || 'School Event'}</p>
          <div className="flex items-center gap-3 text-[10px] text-student-text">
            <span className="flex items-center gap-0.5"><Clock size={9} /> {time}</span>
            {event.location && <span className="flex items-center gap-0.5 truncate"><MapPin size={9} /> {event.location}</span>}
            {spotsLeft !== null && <span className="flex items-center gap-0.5"><Users size={9} /> {spotsLeft > 0 ? `${spotsLeft} spots` : 'Full'}</span>}
          </div>
        </div>
        <button
          onClick={onRsvp}
          className={`self-center px-4 py-1.5 text-xs font-medium rounded-lg transition-colors flex-shrink-0 ${
            isRsvped
              ? 'bg-student-mist text-student border border-student'
              : 'bg-student text-white hover:bg-student-hover'
          }`}
        >
          {isRsvped ? 'Going' : 'RSVP'}
        </button>
      </div>
    </div>
  )
}
