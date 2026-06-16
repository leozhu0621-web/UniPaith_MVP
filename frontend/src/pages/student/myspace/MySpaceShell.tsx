import { useEffect, useState } from 'react'
import { Outlet, NavLink, useLocation, useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import {
  Backpack, Bookmark, PenLine, FolderKanban, Calendar, User, Briefcase,
  SlidersHorizontal, ChevronRight, ChevronDown,
} from 'lucide-react'
import { listMyApplications } from '../../../api/applications'
import Coachmark from '../../../components/ui/Coachmark'

// My Space shell (Spec 2026-06-10 §3; rail tree 2026-06-15) — one personal
// surface. The desktop rail is an EXPANDABLE TREE: a single Overview link plus
// three groups (Profile · Saved · Workspace) that each expand to a dropdown of
// their sub-items. Profile/Saved children deep-link via ?tab=; Workspace
// children are their own rooms. Messages is no longer here — it graduated to a
// top-level nav tab (a peer of My Space). Mobile keeps a flat pill row.

type Sub = { label: string; to: string }
type Item =
  | { kind: 'link'; label: string; to: string; icon: typeof Backpack }
  | { kind: 'group'; label: string; to: string; icon: typeof Backpack; children: Sub[] }

const OVERVIEW: Item = { kind: 'link', label: 'Overview', to: '/s/space', icon: Backpack }

const PROFILE: Item = {
  kind: 'group', label: 'Profile', to: '/s/profile', icon: User,
  children: [
    { label: 'Personal', to: '/s/profile' },
    { label: 'Identity', to: '/s/profile?tab=identity' },
    { label: 'Academics', to: '/s/profile?tab=academics' },
    { label: 'Experience', to: '/s/profile?tab=experience' },
    { label: 'Goals', to: '/s/profile?tab=goals' },
    { label: 'Analytics', to: '/s/profile?tab=analytics' },
    // Data rights moved to account Settings (Spec 2026-06-15 §2.1). Needs ·
    // Timeline · Preferences moved to the Planning cluster below.
  ],
}

// Planning cluster (2026-06-15) — where you're headed and what you want.
// Strategy (the living-doc: career → degree → paths + game-plan) leads the
// cluster; Needs and Preferences follow.
const PLANNING: Item = {
  kind: 'group', label: 'Planning', to: '/s/profile?tab=strategy', icon: SlidersHorizontal,
  children: [
    { label: 'Strategy', to: '/s/profile?tab=strategy' },
    { label: 'Needs', to: '/s/profile?tab=needs' },
    { label: 'Preferences', to: '/s/profile?tab=preferences' },
  ],
}

const SAVED: Item = {
  kind: 'group', label: 'Saved', to: '/s/saved', icon: Bookmark,
  children: [
    { label: 'Programs', to: '/s/saved' },
    { label: 'Schools', to: '/s/saved?tab=schools' },
    { label: 'Searches', to: '/s/saved?tab=searches' },
  ],
}

// Flattened (Spec 2026-06-15 §2.2) — every Prep sub-tab and Applications view
// is a direct Workspace rail item, so the on-page tab strips are redundant on
// desktop (hidden there; kept on mobile where the rail collapses to pills).
const WORKSPACE: Item = {
  kind: 'group', label: 'Workspace', to: '/s/prep', icon: Briefcase,
  children: [
    { label: 'Workshops', to: '/s/prep' },
    { label: 'Prompts', to: '/s/prep?tab=prompts' },
    { label: 'Interviews', to: '/s/prep?tab=interviews' },
    { label: 'Recommenders', to: '/s/prep?tab=recommenders' },
    { label: 'Documents', to: '/s/prep?tab=documents' },
    { label: 'Applications', to: '/s/applications' },
    { label: 'Offers', to: '/s/applications?tab=offers' },
    { label: 'Costs & aid', to: '/s/applications?tab=costs' },
    { label: 'Calendar', to: '/s/calendar' },
  ],
}

const ITEMS: Item[] = [OVERVIEW, PROFILE, PLANNING, SAVED, WORKSPACE]

// Flat list of room landing routes — drives the top-nav My Space active state.
// Messages is intentionally absent (it is its own nav tab now).
export const MY_SPACE_ROUTES = ['/s/space', '/s/profile', '/s/saved', '/s/prep', '/s/applications', '/s/calendar']

// Mobile pill row — flat top-level rooms (no nesting).
const MOBILE_PILLS: { label: string; to: string; icon: typeof Backpack; end?: boolean }[] = [
  { label: 'Overview', to: '/s/space', icon: Backpack, end: true },
  { label: 'Profile', to: '/s/profile', icon: User },
  { label: 'Saved', to: '/s/saved', icon: Bookmark },
  { label: 'Prep', to: '/s/prep', icon: PenLine },
  { label: 'Applications', to: '/s/applications', icon: FolderKanban },
  { label: 'Calendar', to: '/s/calendar', icon: Calendar },
]

/** A group "owns" the current route when one of its children is the active
 *  sub-item. ?tab-aware (via subActive) — required now that Profile and Planning
 *  share the /s/profile path but split its tabs between them. */
function groupOwns(group: Extract<Item, { kind: 'group' }>, pathname: string, search: string): boolean {
  return group.children.some(c => subActive(c.to, pathname, search))
}

/** Sub-item active = same pathname AND same ?tab (landing item = no/absent tab). */
function subActive(to: string, pathname: string, search: string): boolean {
  const [path, query = ''] = to.split('?')
  if (pathname !== path) return false
  const toTab = new URLSearchParams(query).get('tab')
  const curTab = new URLSearchParams(search).get('tab')
  // A landing item (no ?tab) matches the bare route or the page's default tab key.
  if (!toTab) return !curTab || curTab === 'overview' || curTab === 'programs' || curTab === 'workshops'
  return curTab === toTab
}

export default function MySpaceShell() {
  const location = useLocation()
  const navigate = useNavigate()
  const { pathname, search } = location

  // Application count badge on the Workspace group (cache shared with the home
  // pipeline tiles + ApplicationsPage — reused, not refetched).
  const { data: apps } = useQuery({ queryKey: ['my-applications'], queryFn: listMyApplications, staleTime: 60_000 })
  const appCount = Array.isArray(apps) ? apps.length : 0

  // Expanded groups — seed with whichever group owns the current route; keep the
  // active group open as the route changes (others stay as the user left them).
  const [open, setOpen] = useState<Set<string>>(() => {
    const s = new Set<string>()
    for (const it of ITEMS) if (it.kind === 'group' && groupOwns(it, pathname, search)) s.add(it.label)
    return s
  })
  useEffect(() => {
    for (const it of ITEMS) {
      if (it.kind === 'group' && groupOwns(it, pathname, search)) {
        setOpen(prev => (prev.has(it.label) ? prev : new Set(prev).add(it.label)))
      }
    }
  }, [pathname, search])

  const toggle = (label: string) =>
    setOpen(prev => {
      const next = new Set(prev)
      if (next.has(label)) next.delete(label)
      else next.add(label)
      return next
    })

  const roomSegment = pathname.split('/')[2] ?? 'space'

  return (
    <div className="flex min-h-0 flex-1">
      {/* Desktop rail (lg+) — expandable tree. */}
      <aside className="hidden lg:block w-48 flex-shrink-0 border-r border-border" aria-label="My Space">
        <div className="sticky top-0">
        <Coachmark id="myspace-rail-tree" title="Everything, one click away" body="Overview pulls it all together. Profile, Saved, and Workspace each open to reveal what's inside." placement="right" minViewport="lg">
        <nav className="max-h-[calc(100dvh-4rem)] overflow-y-auto px-3 py-4">
          {ITEMS.map(item => {
            if (item.kind === 'link') {
              // ?tab-aware active (Strategy → ?tab=timeline); NavLink alone
              // would match by pathname and over-highlight on profile routes.
              const active = subActive(item.to, pathname, search)
              return (
                <NavLink
                  key={item.to}
                  to={item.to}
                  className={`flex items-center gap-2 rounded-md px-2 py-1.5 text-sm transition-colors ${
                    active
                      ? 'bg-muted font-medium text-foreground'
                      : 'text-muted-foreground hover:bg-muted/50 hover:text-foreground'
                  }`}
                >
                  <item.icon size={15} strokeWidth={1.75} />
                  {item.label}
                </NavLink>
              )
            }
            const isOpen = open.has(item.label)
            const owns = groupOwns(item, pathname, search)
            const badge =
              item.label === 'Workspace' && appCount > 0
                ? <span className="ml-1 text-xs text-muted-foreground">{appCount}</span>
                : null
            return (
              <div key={item.label} className="mt-1">
                {/* Group header: navigates to the landing view AND opens the group. */}
                <button
                  type="button"
                  aria-expanded={isOpen}
                  onClick={() => { setOpen(prev => new Set(prev).add(item.label)); navigate(item.to) }}
                  className={`flex w-full items-center gap-2 rounded-md px-2 py-1.5 text-sm transition-colors ${
                    owns ? 'font-medium text-foreground' : 'text-muted-foreground hover:bg-muted/50 hover:text-foreground'
                  }`}
                >
                  <item.icon size={15} strokeWidth={1.75} />
                  {item.label}
                  {badge}
                  <span
                    role="button"
                    tabIndex={0}
                    aria-label={isOpen ? `Collapse ${item.label}` : `Expand ${item.label}`}
                    onClick={e => { e.stopPropagation(); toggle(item.label) }}
                    onKeyDown={e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); e.stopPropagation(); toggle(item.label) } }}
                    className="ml-auto -mr-1 inline-flex h-5 w-5 items-center justify-center rounded text-muted-foreground hover:text-foreground"
                  >
                    {isOpen ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
                  </span>
                </button>
                {isOpen && (
                  <div className="mt-0.5 ml-[18px] border-l border-border pl-2">
                    {item.children.map(sub => {
                      const active = subActive(sub.to, pathname, search)
                      return (
                        <NavLink
                          key={sub.to}
                          to={sub.to}
                          className={`block rounded-md px-2 py-1 text-[13px] transition-colors ${
                            active ? 'bg-muted font-medium text-foreground' : 'text-muted-foreground hover:bg-muted/50 hover:text-foreground'
                          }`}
                        >
                          {sub.label}
                        </NavLink>
                      )
                    })}
                  </div>
                )}
              </div>
            )
          })}
        </nav>
        </Coachmark>
        </div>
      </aside>

      {/* Content column — mobile gets the flat room pills above the page. */}
      <div className="flex min-w-0 flex-1 flex-col">
        <div className="lg:hidden sticky top-0 z-20 flex-shrink-0 overflow-x-auto border-b border-border bg-background px-3 py-2 no-scrollbar">
          <div className="flex items-center gap-1.5 w-max">
            {MOBILE_PILLS.map(pill => (
              <NavLink
                key={pill.to}
                to={pill.to}
                end={pill.end}
                className={({ isActive }) =>
                  `flex items-center gap-1.5 whitespace-nowrap rounded-full border px-3 py-1 text-xs font-medium transition-colors ${
                    isActive
                      ? 'border-secondary bg-secondary/10 text-secondary'
                      : 'border-border text-muted-foreground hover:text-foreground'
                  }`
                }
              >
                <pill.icon size={13} strokeWidth={1.75} />
                {pill.label}
              </NavLink>
            ))}
          </div>
        </div>

        {/* Rooms animate via their own PageContainer. */}
        <div key={roomSegment} className="min-h-0 flex-1">
          <Outlet />
        </div>
      </div>
    </div>
  )
}
