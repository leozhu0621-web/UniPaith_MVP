import { Link } from 'react-router-dom'
import { Calendar, GraduationCap, Sparkles, ChevronRight } from 'lucide-react'
import Card from '../../../components/ui/Card'
import { formatDate } from '../../../utils/format'
import { DEGREE_LABELS } from '../../../utils/constants'
import type { EventItem } from '../../../types'

interface ProgramLink {
  id: string
  program_name: string
  department?: string | null
  degree_type?: string
}

interface Props {
  events?: EventItem[]
  sameSchoolPrograms?: ProgramLink[]
  similarPrograms?: ProgramLink[]
  onRsvp?: (eventId: string) => void
  rsvpedIds?: Set<string>
}

export default function RelatedSidebar({
  events = [],
  sameSchoolPrograms = [],
  similarPrograms = [],
  onRsvp,
  rsvpedIds = new Set(),
}: Props) {
  const upcomingEvents = events
    .filter(e => new Date(e.start_time || Date.now()) > new Date())
    .slice(0, 2)

  return (
    <aside className="space-y-4">
      {/* Upcoming events */}
      {upcomingEvents.length > 0 && (
        <Card className="p-4">
          <div className="flex items-center gap-2 mb-3">
            <Calendar size={14} className="text-student" />
            <h3 className="text-sm font-semibold text-student-ink">Upcoming Events</h3>
          </div>
          <div className="space-y-2">
            {upcomingEvents.map((ev: any) => (
              <div key={ev.id} className="px-3 py-2.5 rounded-lg border border-divider hover:border-student/30 transition-colors">
                <p className="text-xs font-semibold text-student-ink line-clamp-2">{ev.event_name}</p>
                <p className="text-[10px] text-student-text mt-0.5">
                  {formatDate(ev.start_time)}
                </p>
                {onRsvp && (
                  <button
                    onClick={() => onRsvp(ev.id)}
                    className={`mt-2 text-[11px] font-medium px-2 py-1 rounded-md transition-colors ${
                      rsvpedIds.has(ev.id)
                        ? 'bg-emerald-50 text-emerald-700'
                        : 'bg-student text-white hover:bg-student-hover'
                    }`}
                  >
                    {rsvpedIds.has(ev.id) ? '✓ Going' : 'RSVP'}
                  </button>
                )}
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* Same school */}
      {sameSchoolPrograms.length > 0 && (
        <Card className="p-4">
          <div className="flex items-center gap-2 mb-3">
            <GraduationCap size={14} className="text-student" />
            <h3 className="text-sm font-semibold text-student-ink">Other at this school</h3>
          </div>
          <div className="space-y-1">
            {sameSchoolPrograms.slice(0, 5).map(p => (
              <Link
                key={p.id}
                to={`/s/programs/${p.id}`}
                className="flex items-center justify-between gap-2 px-2.5 py-2 rounded-md hover:bg-student-mist group transition-colors"
              >
                <div className="min-w-0">
                  <p className="text-xs font-medium text-student-ink truncate group-hover:text-student">{p.program_name}</p>
                  {(p.department || p.degree_type) && (
                    <p className="text-[10px] text-student-text/70 truncate">
                      {p.degree_type ? (DEGREE_LABELS[p.degree_type] || p.degree_type) : ''}
                      {p.department ? ` · ${p.department}` : ''}
                    </p>
                  )}
                </div>
                <ChevronRight size={12} className="text-student-text/40 group-hover:text-student flex-shrink-0" />
              </Link>
            ))}
          </div>
        </Card>
      )}

      {/* Similar programs elsewhere */}
      {similarPrograms.length > 0 && (
        <Card className="p-4">
          <div className="flex items-center gap-2 mb-3">
            <Sparkles size={14} className="text-gold" />
            <h3 className="text-sm font-semibold text-student-ink">Similar programs</h3>
          </div>
          <div className="space-y-1">
            {similarPrograms.slice(0, 5).map(p => (
              <Link
                key={p.id}
                to={`/s/programs/${p.id}`}
                className="flex items-center justify-between gap-2 px-2.5 py-2 rounded-md hover:bg-student-mist group transition-colors"
              >
                <div className="min-w-0">
                  <p className="text-xs font-medium text-student-ink truncate group-hover:text-student">{p.program_name}</p>
                  {p.degree_type && (
                    <p className="text-[10px] text-student-text/70 truncate">{DEGREE_LABELS[p.degree_type] || p.degree_type}</p>
                  )}
                </div>
                <ChevronRight size={12} className="text-student-text/40 group-hover:text-student flex-shrink-0" />
              </Link>
            ))}
          </div>
        </Card>
      )}
    </aside>
  )
}
