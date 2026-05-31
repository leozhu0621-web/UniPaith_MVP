// Connect feed cards — Spec 20 §4.1 / §10.
// Brand: cobalt + neutral. GOLD is reserved for the pinned-institution marker
// and the RSVP-confirmed state only (Spec 20 §10). No decorative imagery.
import { useState } from 'react'
import {
  AlertTriangle, BellOff, CalendarClock, CalendarPlus, ChevronDown, ChevronUp,
  GraduationCap, Megaphone, Pin,
} from 'lucide-react'
import type { ConnectFeedItem } from '../../../api/connect'

function relativeTime(iso: string): string {
  const then = new Date(iso).getTime()
  const diff = Date.now() - then
  const days = Math.floor(diff / 86400000)
  if (days <= 0) {
    const hours = Math.floor(diff / 3600000)
    if (hours <= 0) return 'just now'
    return `${hours}h ago`
  }
  if (days === 1) return 'yesterday'
  if (days < 7) return `${days} days ago`
  return new Date(iso).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
}

interface Props {
  item: ConnectFeedItem
  onViewProgram: (programId: string) => void
  onAddToCalendar: (item: ConnectFeedItem) => void
  onMute?: (institutionId: string) => void
}

export default function FeedItemCard(props: Props) {
  if (props.item.kind === 'deadline') return <DeadlineCard {...props} />
  if (props.item.kind === 'program_change') return <ProgramChangeCard {...props} />
  return <PostCardLarge {...props} />
}

function CardShell({ children, accent }: { children: React.ReactNode; accent?: string }) {
  return (
    <div className={`bg-white rounded-xl border ${accent || 'border-divider'} hover:shadow-sm transition-shadow`}>
      {children}
    </div>
  )
}

function InstitutionRow({ item }: { item: ConnectFeedItem }) {
  return (
    <div className="flex items-center gap-2 min-w-0">
      <div className="w-7 h-7 rounded-md bg-cobalt/10 flex items-center justify-center flex-shrink-0">
        <GraduationCap size={14} className="text-cobalt" />
      </div>
      <div className="min-w-0">
        <p className="text-xs font-semibold text-student-ink truncate">{item.institution_name}</p>
        {item.program_name && (
          <p className="text-[10px] text-student-text truncate">{item.program_name}</p>
        )}
      </div>
    </div>
  )
}

function CtaRow({ item, onViewProgram, onAddToCalendar }: Props) {
  if (!item.program_id) return null
  // "Add to calendar" only when the item carries a real deadline date (Spec 20
  // §4.1) — avoids meaningless reminders on generic posts.
  const hasDeadline = Boolean(item.deadline)
  return (
    <div className="flex flex-wrap items-center gap-2 mt-3">
      <button
        onClick={() => onViewProgram(item.program_id!)}
        className="px-3 py-1.5 text-xs font-medium rounded-lg border border-cobalt text-cobalt hover:bg-cobalt/5 transition-colors"
      >
        View program
      </button>
      {hasDeadline && (
        <button
          onClick={() => onAddToCalendar(item)}
          className="inline-flex items-center gap-1 px-3 py-1.5 text-xs font-medium rounded-lg text-cobalt hover:bg-cobalt/5 transition-colors"
        >
          <CalendarPlus size={13} /> Add deadline to calendar
        </button>
      )}
    </div>
  )
}

function PostCardLarge({ item, onViewProgram, onAddToCalendar, onMute }: Props) {
  const [expanded, setExpanded] = useState(false)
  const body = item.body || ''
  const isLong = body.length > 220
  const shown = expanded || !isLong ? body : body.slice(0, 220).trimEnd() + '…'
  return (
    <CardShell accent={item.pinned ? 'border-gold' : undefined}>
      <div className="p-4">
        <div className="flex items-start gap-2">
          <InstitutionRow item={item} />
          <div className="ml-auto flex items-center gap-2 flex-shrink-0">
            {item.pinned && (
              // Gold pin marker — one of the two earned gold accents (§10).
              <span className="inline-flex items-center gap-1 text-[10px] font-semibold text-gold-hover">
                <Pin size={11} className="fill-gold text-gold" /> Pinned
              </span>
            )}
            <span className="text-[10px] text-student-text">{relativeTime(item.date)}</span>
            {onMute && (
              <button
                onClick={() => onMute(item.institution_id)}
                title="Mute this institution"
                className="text-student-text hover:text-student-ink p-0.5 rounded"
              >
                <BellOff size={13} />
              </button>
            )}
          </div>
        </div>

        <div className="flex items-center gap-1.5 mt-3 mb-1">
          <Megaphone size={12} className="text-cobalt" />
          <span className="text-[10px] font-semibold text-cobalt uppercase tracking-wider">Update</span>
        </div>
        <h3 className="text-sm font-semibold text-student-ink">{item.title}</h3>
        <p className="text-xs text-student-text leading-relaxed mt-1 whitespace-pre-line">{shown}</p>
        {isLong && (
          <button
            onClick={() => setExpanded(e => !e)}
            className="inline-flex items-center gap-0.5 text-[11px] font-medium text-cobalt mt-1"
          >
            {expanded ? <>Show less <ChevronUp size={12} /></> : <>Read more <ChevronDown size={12} /></>}
          </button>
        )}
        {item.media_urls && item.media_urls.length > 0 && (
          <div className="mt-2 flex gap-2 overflow-x-auto">
            {item.media_urls.slice(0, 3).map((m: string | { url?: string }, i: number) => (
              <div key={i} className="w-28 h-20 rounded-lg bg-student-mist overflow-hidden flex-shrink-0">
                <img
                  src={typeof m === 'string' ? m : m.url}
                  alt=""
                  className="w-full h-full object-cover"
                  onError={e => (e.currentTarget.style.display = 'none')}
                />
              </div>
            ))}
          </div>
        )}
        <CtaRow item={item} onViewProgram={onViewProgram} onAddToCalendar={onAddToCalendar} />
      </div>
    </CardShell>
  )
}

function DeadlineCard({ item, onViewProgram, onAddToCalendar }: Props) {
  const days = item.days_until ?? 0
  const urgent = days <= 14
  return (
    <CardShell>
      <div className="p-4">
        <div className="flex items-start gap-2">
          <InstitutionRow item={item} />
          <span className="ml-auto text-[10px] text-student-text flex-shrink-0">
            {item.deadline ? new Date(item.deadline).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }) : ''}
          </span>
        </div>
        <div className="flex items-center gap-1.5 mt-3 mb-1">
          <CalendarClock size={12} className={urgent ? 'text-error' : 'text-cobalt'} />
          <span className={`text-[10px] font-semibold uppercase tracking-wider ${urgent ? 'text-error' : 'text-cobalt'}`}>
            Application deadline
          </span>
        </div>
        <h3 className="text-sm font-semibold text-student-ink">
          {item.program_name} — {days === 0 ? 'due today' : days < 0 ? 'closed' : `in ${days} day${days !== 1 ? 's' : ''}`}
        </h3>
        <CtaRow item={item} onViewProgram={onViewProgram} onAddToCalendar={onAddToCalendar} />
      </div>
    </CardShell>
  )
}

function ProgramChangeCard({ item, onViewProgram }: Props) {
  return (
    <CardShell accent="border-warning/40">
      <div className="p-4">
        <div className="flex items-start gap-2">
          <InstitutionRow item={item} />
          <span className="ml-auto text-[10px] text-student-text flex-shrink-0">{relativeTime(item.date)}</span>
        </div>
        <div className="flex items-center gap-1.5 mt-3 mb-1">
          <AlertTriangle size={12} className="text-warning" />
          <span className="text-[10px] font-semibold text-warning uppercase tracking-wider">Program change</span>
          {item.muted && <span className="text-[9px] text-student-text">(shown despite mute)</span>}
        </div>
        <h3 className="text-sm font-semibold text-student-ink">{item.change_summary || 'This program changed a requirement'}</h3>
        <p className="text-xs text-student-text mt-0.5">{item.program_name}</p>
        {item.program_id && (
          <button
            onClick={() => onViewProgram(item.program_id!)}
            className="mt-3 px-3 py-1.5 text-xs font-medium rounded-lg border border-cobalt text-cobalt hover:bg-cobalt/5 transition-colors"
          >
            Review changes
          </button>
        )}
      </div>
    </CardShell>
  )
}
