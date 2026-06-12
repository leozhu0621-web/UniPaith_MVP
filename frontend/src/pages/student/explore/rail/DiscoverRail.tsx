// The Discover live rail (Spec 2026-06-12 §2) — ambient Connect context while
// browsing matches: latest updates, next events, deadline radar, following +
// follow suggestions. Rail rows fire NO engagement tracking by design (§2).
import { useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import { ArrowRight, Bell, CalendarClock, CalendarDays, GraduationCap, Newspaper, UserPlus } from 'lucide-react'
import { getConnectEvents, getConnectFeed } from '../../../../api/connect'
import { getMatches } from '../../../../api/matching'
import { listSaved } from '../../../../api/saved-lists'

function relTime(iso: string): string {
  const days = Math.floor((Date.now() - new Date(iso).getTime()) / 86400000)
  if (days <= 0) return 'today'
  if (days === 1) return 'yesterday'
  if (days < 7) return `${days}d ago`
  return new Date(iso).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
}

function eventDay(iso: string): string {
  return new Date(iso).toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' })
}

interface Props {
  followedIds: Set<string>
  onToggleFollow: (institutionId: string) => void
  onOpenTab: (t: 'updates' | 'events') => void
  onManageFollowing: () => void
}

export default function DiscoverRail({ followedIds, onToggleFollow, onOpenTab, onManageFollowing }: Props) {
  const { data: feed } = useQuery({
    queryKey: ['connect-feed-rail'],
    queryFn: () => getConnectFeed('recent', undefined, { limit: 8 }),
    staleTime: 5 * 60 * 1000,
    retry: false,
  })
  const { data: eventsData } = useQuery({
    queryKey: ['connect-events', 'upcoming'],
    queryFn: () => getConnectEvents('upcoming'),
    staleTime: 5 * 60 * 1000,
    retry: false,
  })
  const { data: deadlines } = useQuery({
    queryKey: ['connect-deadline-radar'],
    queryFn: () => getConnectFeed('recent', undefined, { limit: 12, kinds: 'deadline' }),
    staleTime: 5 * 60 * 1000,
    retry: false,
  })
  const { data: matches = [] } = useQuery({ queryKey: ['matches'], queryFn: () => getMatches(), retry: 1, staleTime: 60_000 })
  const { data: saved } = useQuery({ queryKey: ['saved-programs'], queryFn: listSaved, retry: false })

  const updates = (feed?.items ?? []).filter(it => it.kind === 'post').slice(0, 3)
  const events = (eventsData?.events ?? []).slice(0, 3)
  // Soonest deadlines: items arrive urgency-sorted on the recency axis; sort by days_until to be explicit.
  const radar = [...(deadlines?.items ?? [])]
    .sort((a, b) => (a.days_until ?? 999) - (b.days_until ?? 999))
    .slice(0, 3)

  // Follow suggestions (Spec 2026-06-12 §6.6): institutions from top matches +
  // saved programs the student doesn't follow yet, in match order, top 3.
  const suggestions = useMemo(() => {
    const out: { id: string; name: string }[] = []
    const seen = new Set<string>()
    const push = (id?: string | null, name?: string | null) => {
      if (!id || seen.has(id) || followedIds.has(id)) return
      seen.add(id)
      out.push({ id, name: name || 'Institution' })
    }
    for (const m of matches) push(m.institution_id, m.institution_name)
    for (const s of saved ?? []) push(s.institution_id ?? s.program?.institution_id, s.institution_name ?? s.program?.institution_name)
    return out.slice(0, 3)
  }, [matches, saved, followedIds])

  const followCount = followedIds.size

  return (
    <div className="space-y-4">
      {/* From your schools */}
      <RailCard
        icon={Newspaper}
        title="From your schools"
        action={updates.length > 0 ? { label: 'See all', onClick: () => onOpenTab('updates') } : undefined}
      >
        {updates.length === 0 ? (
          <p className="text-xs text-muted-foreground px-1">
            {followCount === 0 ? 'Follow a school to see its updates here.' : 'No updates yet from schools you follow.'}
          </p>
        ) : (
          updates.map(it => (
            <button
              key={it.id}
              onClick={() => onOpenTab('updates')}
              className="w-full text-left px-1 py-1.5 rounded-md hover:bg-muted transition-colors"
            >
              <p className="text-xs font-semibold text-foreground line-clamp-1">{it.title}</p>
              <p className="text-[10px] text-muted-foreground truncate">
                {it.institution_name} · {relTime(it.date)}
              </p>
            </button>
          ))
        )}
      </RailCard>

      {/* Upcoming events */}
      <RailCard
        icon={CalendarDays}
        title="Upcoming events"
        action={events.length > 0 ? { label: 'See all', onClick: () => onOpenTab('events') } : undefined}
      >
        {events.length === 0 ? (
          <p className="text-xs text-muted-foreground px-1">No upcoming events from schools you follow.</p>
        ) : (
          events.map(ev => (
            <button
              key={ev.id}
              onClick={() => onOpenTab('events')}
              className="w-full text-left px-1 py-1.5 rounded-md hover:bg-muted transition-colors"
            >
              <p className="text-xs font-semibold text-foreground line-clamp-1">{ev.event_name}</p>
              <p className="text-[10px] text-muted-foreground truncate">
                {ev.institution_name} · {eventDay(ev.start_time)}
                {ev.rsvp_state === 'rsvp' && <span className="text-secondary font-semibold"> · Going</span>}
              </p>
            </button>
          ))
        )}
      </RailCard>

      {/* Deadline radar */}
      <RailCard icon={CalendarClock} title="Deadline radar">
        {radar.length === 0 ? (
          <p className="text-xs text-muted-foreground px-1">Save a program to track its deadline here.</p>
        ) : (
          radar.map(it => (
            <button
              key={it.id}
              onClick={() => onOpenTab('updates')}
              className="w-full text-left px-1 py-1.5 rounded-md hover:bg-muted transition-colors"
            >
              <p className="text-xs font-semibold text-foreground line-clamp-1">{it.program_name}</p>
              <p
                className={`text-[10px] truncate ${
                  (it.days_until ?? 99) <= 7
                    ? 'text-error font-semibold'
                    : (it.days_until ?? 99) <= 30
                      ? 'text-warning'
                      : 'text-muted-foreground'
                }`}
              >
                {it.days_until === 0 ? 'Due today' : `${it.days_until} day${it.days_until !== 1 ? 's' : ''} left`} ·{' '}
                {it.institution_name}
              </p>
            </button>
          ))
        )}
      </RailCard>

      {/* Following + suggestions */}
      <RailCard icon={Bell} title={`Following · ${followCount}`} action={{ label: 'Manage', onClick: onManageFollowing }}>
        {suggestions.length === 0 ? (
          <p className="text-xs text-muted-foreground px-1">Updates from schools you follow land in this rail.</p>
        ) : (
          <>
            <p className="text-[10px] uppercase tracking-wide text-muted-foreground px-1 mb-1">Add to your feed</p>
            {suggestions.map(s => (
              <div key={s.id} className="flex items-center gap-2 px-1 py-1.5">
                <div className="w-6 h-6 rounded-md bg-secondary/10 flex items-center justify-center flex-shrink-0">
                  <GraduationCap size={12} className="text-secondary" />
                </div>
                <p className="text-xs font-medium text-foreground truncate flex-1">{s.name}</p>
                <button
                  onClick={() => onToggleFollow(s.id)}
                  className="inline-flex items-center gap-1 text-[11px] font-semibold text-secondary hover:underline flex-shrink-0"
                >
                  <UserPlus size={11} /> Follow
                </button>
              </div>
            ))}
          </>
        )}
      </RailCard>
    </div>
  )
}

function RailCard({
  icon: Icon,
  title,
  action,
  children,
}: {
  icon: typeof Newspaper
  title: string
  action?: { label: string; onClick: () => void }
  children: React.ReactNode
}) {
  return (
    <section className="bg-card rounded-xl border border-border p-3">
      <div className="flex items-center gap-1.5 mb-2 px-1">
        <Icon size={13} className="text-secondary" />
        <h3 className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground flex-1">{title}</h3>
        {action && (
          <button
            onClick={action.onClick}
            className="inline-flex items-center gap-0.5 text-[11px] font-semibold text-secondary hover:underline"
          >
            {action.label} <ArrowRight size={11} />
          </button>
        )}
      </div>
      <div className="space-y-0.5">{children}</div>
    </section>
  )
}
