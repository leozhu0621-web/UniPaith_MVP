import { Link } from 'react-router-dom'
import { Calendar, Sparkles, ChevronRight, Compass } from 'lucide-react'
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
  /** Spec 11 §4 — back to Discovery with this program's attributes pre-applied. */
  discoveryBackHref?: string
}

export default function RelatedSidebar({
  events = [],
  sameSchoolPrograms = [],
  similarPrograms = [],
  onRsvp,
  rsvpedIds = new Set(),
  discoveryBackHref,
}: Props) {
  const upcomingEvents = events
    .filter(e => new Date((e as any).event_datetime || (e as any).starts_at || (e as any).start_time || Date.now()) > new Date())
    .slice(0, 2)

  // "Programs that fit you" — semantically-recommended programs first; fall back
  // to other programs at the same school so the rail is never empty.
  const fitById = new Map<string, ProgramLink>()
  for (const p of [...similarPrograms, ...sameSchoolPrograms]) {
    if (!fitById.has(p.id)) fitById.set(p.id, p)
  }
  const fitPrograms = [...fitById.values()].slice(0, 6)

  return (
    <aside className="space-y-4">
      {/* Upcoming events */}
      {upcomingEvents.length > 0 && (
        <Card className="p-4">
          <div className="flex items-center gap-2 mb-3">
            <Calendar size={14} className="text-secondary" />
            <h3 className="text-sm font-semibold text-foreground">Upcoming Events</h3>
          </div>
          <div className="space-y-2">
            {upcomingEvents.map((ev: any) => (
              <div key={ev.id} className="px-3 py-2.5 rounded-lg border border-border hover:border-secondary/30 transition-colors">
                <p className="text-xs font-semibold text-foreground line-clamp-2">{ev.title}</p>
                <p className="text-[10px] text-foreground mt-0.5">
                  {formatDate(ev.event_datetime || ev.starts_at)}
                </p>
                {onRsvp && (
                  <button
                    onClick={() => onRsvp(ev.id)}
                    className={`mt-2 text-[11px] font-medium px-2 py-1 rounded-md transition-colors ${
                      rsvpedIds.has(ev.id)
                        ? 'bg-success-soft text-success'
                        : 'bg-secondary text-secondary-foreground hover:brightness-95'
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

      {/* Programs that fit you */}
      {fitPrograms.length > 0 && (
        <Card className="p-4">
          <div className="flex items-center gap-2 mb-3">
            <Sparkles size={14} className="text-secondary" />
            <h3 className="text-sm font-semibold text-foreground">Programs that fit you</h3>
          </div>
          <div className="space-y-1">
            {fitPrograms.map(p => (
              <Link
                key={p.id}
                to={`/s/programs/${p.id}`}
                className="flex items-center justify-between gap-2 px-2.5 py-2 rounded-md hover:bg-muted group transition-colors"
              >
                <div className="min-w-0">
                  <p className="text-xs font-medium text-foreground truncate group-hover:text-secondary">{p.program_name}</p>
                  {(p.department || p.degree_type) && (
                    <p className="text-[10px] text-foreground/70 truncate">
                      {p.degree_type ? (DEGREE_LABELS[p.degree_type] || p.degree_type) : ''}
                      {p.department ? ` · ${p.department}` : ''}
                    </p>
                  )}
                </div>
                <ChevronRight size={12} className="text-foreground/40 group-hover:text-secondary flex-shrink-0" />
              </Link>
            ))}
          </div>
        </Card>
      )}

      {/* Back to Discovery with these attributes pre-applied (§4) */}
      {discoveryBackHref && (
        <Link
          to={discoveryBackHref}
          className="flex items-center justify-between gap-2 px-3 py-3 rounded-lg border border-border hover:border-secondary hover:bg-muted transition-colors group"
        >
          <div className="flex items-center gap-2 min-w-0">
            <Compass size={14} className="text-secondary flex-shrink-0" />
            <span className="text-xs font-medium text-foreground">
              Find more like this in Discovery
            </span>
          </div>
          <ChevronRight size={12} className="text-foreground/40 group-hover:text-secondary flex-shrink-0" />
        </Link>
      )}
    </aside>
  )
}
