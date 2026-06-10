import { Outlet, NavLink, useLocation } from 'react-router-dom'
import {
  Backpack, Bookmark, PenLine, FolderKanban, Calendar, MessageSquare, User,
} from 'lucide-react'

// My Space shell (Spec 2026-06-10 §3) — one personal surface, rooms ordered by
// the journey sequence: Home on top, then Plan → Prepare → Apply & decide →
// Anytime → Record. Desktop gets a slim left rail; mobile a scrollable pill
// row under the top bar. Rooms keep flat URLs — unification comes from this
// shared layout route, not nested paths.

type Room = { to: string; label: string; icon: typeof Backpack; end?: boolean }

const HOME: Room = { to: '/s/space', label: 'Home', icon: Backpack, end: true }

const GROUPS: { label: string | null; rooms: Room[] }[] = [
  { label: null, rooms: [HOME] },
  { label: 'Plan', rooms: [{ to: '/s/saved', label: 'Saved', icon: Bookmark }] },
  { label: 'Prepare', rooms: [{ to: '/s/prep', label: 'Prep', icon: PenLine }] },
  { label: 'Apply & decide', rooms: [{ to: '/s/applications', label: 'Applications', icon: FolderKanban }] },
  {
    label: 'Anytime',
    rooms: [
      { to: '/s/calendar', label: 'Calendar', icon: Calendar },
      { to: '/s/messages', label: 'Messages', icon: MessageSquare },
    ],
  },
  { label: 'Record', rooms: [{ to: '/s/profile', label: 'Profile', icon: User }] },
]

const ALL_ROOMS = GROUPS.flatMap(g => g.rooms)

/** Route prefixes owned by My Space — used by StudentLayout for nav active state. */
export const MY_SPACE_ROUTES = ALL_ROOMS.map(r => r.to)

export default function MySpaceShell() {
  const location = useLocation()
  // Messages is a fixed two-pane surface (Spec 17 §2) — it manages its own
  // height; every other room scrolls in the layout's <main>.
  const isMessages = location.pathname.startsWith('/s/messages')

  return (
    <div className="flex min-h-0 flex-1">
      {/* Desktop rail (lg+) — journey-grouped rooms. */}
      <aside className="hidden lg:block w-44 flex-shrink-0 border-r border-border" aria-label="My Space">
        <nav className="sticky top-0 max-h-[calc(100dvh-4rem)] overflow-y-auto px-3 py-4">
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
                </NavLink>
              ))}
            </div>
          ))}
        </nav>
      </aside>

      {/* Content column — mobile gets the room pills above the page. */}
      <div className="flex min-w-0 flex-1 flex-col">
        <div className="lg:hidden flex-shrink-0 overflow-x-auto border-b border-border bg-background px-3 py-2 scrollbar-none">
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
              </NavLink>
            ))}
          </div>
        </div>

        <div className={`min-h-0 flex-1 ${isMessages ? 'overflow-hidden' : ''}`}>
          <Outlet />
        </div>
      </div>
    </div>
  )
}
