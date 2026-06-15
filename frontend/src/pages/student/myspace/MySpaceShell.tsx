import { Outlet, NavLink, useLocation } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import {
  Backpack, Bookmark, PenLine, FolderKanban, Calendar, MessageSquare, User,
} from 'lucide-react'
import { getThreads } from '../../../api/inbox'
import { listMyApplications } from '../../../api/applications'
import Coachmark from '../../../components/ui/Coachmark'

// My Space shell (Spec 2026-06-10 §3; restructured 2026-06-14) — one personal
// surface, rooms grouped by CONTENT TYPE rather than application-journey phase:
// Home on top, then Record → Collections → Workspace. The taxonomy reads
// identity → tracked objects → where you act, with no phase words. Desktop gets
// a slim left rail; mobile a scrollable pill row under the top bar. Rooms keep
// flat URLs — unification comes from this shared layout route, not nested paths.

type Room = { to: string; label: string; icon: typeof Backpack; end?: boolean }

const HOME: Room = { to: '/s/space', label: 'Home', icon: Backpack, end: true }

const GROUPS: { label: string | null; rooms: Room[] }[] = [
  { label: null, rooms: [HOME] },
  // Record — your durable reference data.
  { label: 'Record', rooms: [{ to: '/s/profile', label: 'Profile', icon: User }] },
  // Collections — sets of items you're tracking.
  {
    label: 'Collections',
    rooms: [
      { to: '/s/saved', label: 'Saved', icon: Bookmark },
      { to: '/s/applications', label: 'Applications', icon: FolderKanban },
    ],
  },
  // Workspace — where you do the work.
  {
    label: 'Workspace',
    rooms: [
      { to: '/s/prep', label: 'Prep', icon: PenLine },
      { to: '/s/calendar', label: 'Calendar', icon: Calendar },
      { to: '/s/messages', label: 'Messages', icon: MessageSquare },
    ],
  },
]

const ALL_ROOMS = GROUPS.flatMap(g => g.rooms)

/** Route prefixes owned by My Space — used by StudentLayout for nav active state. */
export const MY_SPACE_ROUTES = ALL_ROOMS.map(r => r.to)

export default function MySpaceShell() {
  const location = useLocation()
  // Messages is a fixed two-pane surface (Spec 17 §2) — it manages its own
  // height; every other room scrolls in the layout's <main>.
  const isMessages = location.pathname.startsWith('/s/messages')
  // Room path segment (saved / prep / applications / …) — keys the content
  // column so switching rooms replays the entrance animation while the rail
  // and pill row persist (UX overhaul Ship A, 2026-06-12 spec §1).
  const roomSegment = location.pathname.split('/')[2] ?? 'space'

  // Live rail badges — both queries share their keys with existing consumers
  // (MessagesNavButton / ApplicationsPage), so the cache is reused, not refetched.
  const { data: threads } = useQuery({
    queryKey: ['inbox-threads-unread'],
    queryFn: () => getThreads(),
    staleTime: 30_000,
    refetchInterval: 60_000,
  })
  const { data: apps } = useQuery({ queryKey: ['my-applications'], queryFn: listMyApplications, staleTime: 60_000 })
  const unread = Array.isArray(threads) ? threads.filter((t: { unread?: boolean }) => t.unread).length : 0
  const appCount = Array.isArray(apps) ? apps.length : 0

  const badgeFor = (to: string) => {
    if (to === '/s/messages' && unread > 0)
      return (
        <span className="ml-auto rounded-full bg-secondary px-1.5 py-0.5 text-[10px] font-semibold leading-none text-secondary-foreground">
          {unread}
        </span>
      )
    if (to === '/s/applications' && appCount > 0)
      return <span className="ml-auto text-xs text-muted-foreground">{appCount}</span>
    return null
  }

  return (
    <div className="flex min-h-0 flex-1">
      {/* Desktop rail (lg+) — journey-grouped rooms. The sticky wrapper sits outside
          the first-visit coachmark so the bubble escapes the nav's overflow clip;
          minViewport keeps the CSS-hidden rail from blocking the mark queue below lg. */}
      <aside className="hidden lg:block w-44 flex-shrink-0 border-r border-border" aria-label="My Space">
        <div className="sticky top-0">
        <Coachmark id="myspace-rooms" title="Your rooms, organized" body="Grouped by what's inside — your record, your collections, and your workspace. Home pulls it all together." placement="right" minViewport="lg">
        <nav className="max-h-[calc(100dvh-4rem)] overflow-y-auto px-3 py-4">
          {GROUPS.map((group, gi) => (
            <div key={group.label ?? 'home'} className={gi === 0 ? '' : 'mt-4'}>
              {group.label && (
                <p className="px-2 mb-1 text-eyebrow uppercase text-muted-foreground">{group.label}</p>
              )}
              {group.rooms.map(room => (
                <NavLink
                  key={room.to}
                  to={room.to}
                  end={room.end}
                  className={({ isActive }) =>
                    `flex items-center gap-2 rounded-md px-2 py-1.5 text-sm transition-colors ${
                      isActive
                        ? 'bg-muted font-medium text-foreground'
                        : 'text-muted-foreground hover:bg-muted/50 hover:text-foreground'
                    }`
                  }
                >
                  <room.icon size={15} strokeWidth={1.75} />
                  {room.label}
                  {badgeFor(room.to)}
                </NavLink>
              ))}
            </div>
          ))}
        </nav>
        </Coachmark>
        </div>
      </aside>

      {/* Content column — mobile gets the room pills above the page. */}
      <div className="flex min-w-0 flex-1 flex-col">
        <div className="lg:hidden sticky top-0 z-20 flex-shrink-0 overflow-x-auto border-b border-border bg-background px-3 py-2 no-scrollbar">
          <div className="flex items-center gap-1.5 w-max">
            {ALL_ROOMS.map(room => (
              <NavLink
                key={room.to}
                to={room.to}
                end={room.end}
                className={({ isActive }) =>
                  `flex items-center gap-1.5 whitespace-nowrap rounded-full border px-3 py-1 text-xs font-medium transition-colors ${
                    isActive
                      ? 'border-secondary bg-secondary/10 text-secondary'
                      : 'border-border text-muted-foreground hover:text-foreground'
                  }`
                }
              >
                <room.icon size={13} strokeWidth={1.75} />
                {room.label}
                {room.to === '/s/messages' && unread > 0 && (
                  <span className="h-1.5 w-1.5 rounded-full bg-secondary" aria-label={`${unread} unread`} />
                )}
              </NavLink>
            ))}
          </div>
        </div>

        {/* Rooms animate via their own PageContainer; Messages (no PageContainer — full-height split pane) animates here. */}
        <div key={roomSegment} className={`min-h-0 flex-1 ${isMessages ? 'animate-page-in overflow-hidden' : ''}`}>
          <Outlet />
        </div>
      </div>
    </div>
  )
}
