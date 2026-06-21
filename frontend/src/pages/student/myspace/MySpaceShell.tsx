import { useEffect, useState } from 'react'
import { Outlet, NavLink, useLocation } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import {
  Backpack, Bookmark, PenLine, FolderKanban, Calendar, User, Briefcase,
  SlidersHorizontal, ChevronRight, ChevronDown, Upload,
} from 'lucide-react'
import { listMyApplications } from '../../../api/applications'

// My Space shell (Spec 2026-06-10 §3; rail tree 2026-06-15) — one personal
// surface. The desktop rail is an EXPANDABLE TREE: a single Overview link plus
// three groups (Profile · Saved · Workspace) that each expand to a dropdown of
// their sub-items. Profile/Saved children deep-link via ?tab=; Workspace
// children are their own rooms. Messages is no longer here — it graduated to a
// top-level nav tab (a peer of My Space). Mobile keeps a flat pill row.

type Sub = { label: string; to: string; meta: string }
type Item =
  | { kind: 'link'; label: string; to: string; icon: typeof Backpack; meta: string }
  | { kind: 'group'; label: string; to: string; icon: typeof Backpack; meta: string; children: Sub[] }

const OVERVIEW: Item = {
  kind: 'link',
  label: 'Overview',
  to: '/s/space',
  icon: Backpack,
  meta: 'What matters now',
}

// Import — upload a file, Uni reads it, complete the gaps. Sits right after
// Overview so it's the obvious first step to fill a fresh profile.
const IMPORT: Item = {
  kind: 'link',
  label: 'Import',
  to: '/s/import',
  icon: Upload,
  meta: 'Review extracted signals',
}

const PROFILE: Item = {
  kind: 'group', label: 'Profile', to: '/s/profile', icon: User, meta: 'Durable student record',
  children: [
    { label: 'Basic info', to: '/s/profile', meta: 'Contact and core facts' },
    { label: 'Identity', to: '/s/profile?tab=identity', meta: 'Values and story signals' },
    { label: 'Academics', to: '/s/profile?tab=academics', meta: 'Grades, tests, coursework' },
    { label: 'Experience', to: '/s/profile?tab=experience', meta: 'Projects, work, activities' },
    { label: 'Analytics', to: '/s/profile?tab=analytics', meta: 'Completeness and gaps' },
    // Data rights moved to account Settings (Spec 2026-06-15 §2.1). Goals ·
    // Needs · Preferences live in the Planning cluster below.
  ],
}

// Planning cluster (2026-06-15) — where you're headed and what you want.
// Strategy (the living-doc: career → degree → paths + game-plan) leads the
// cluster; Needs and Preferences follow.
const PLANNING: Item = {
  kind: 'group',
  label: 'Planning',
  to: '/s/profile?tab=strategy',
  icon: SlidersHorizontal,
  meta: 'Goals, fit, constraints',
  children: [
    { label: 'Strategy', to: '/s/profile?tab=strategy', meta: 'Living admissions plan' },
    { label: 'Goals', to: '/s/profile?tab=goals', meta: 'Career and degree aims' },
    { label: 'Needs', to: '/s/profile?tab=needs', meta: 'Support and constraints' },
    { label: 'Preferences', to: '/s/profile?tab=preferences', meta: 'Location, budget, format' },
  ],
}

const SAVED: Item = {
  kind: 'group', label: 'Saved', to: '/s/saved', icon: Bookmark, meta: 'Shortlist and search memory',
  children: [
    { label: 'Programs', to: '/s/saved', meta: 'Targets to compare' },
    { label: 'Schools', to: '/s/saved?tab=schools', meta: 'Institutions you follow' },
    { label: 'Searches', to: '/s/saved?tab=searches', meta: 'Reusable filters and alerts' },
  ],
}

// Flattened (Spec 2026-06-15 §2.2) — every Prep sub-tab and Applications view
// is a direct Workspace rail item, so the on-page tab strips are redundant on
// desktop (hidden there; kept on mobile where the rail collapses to pills).
const WORKSPACE: Item = {
  kind: 'group',
  label: 'Workspace',
  to: '/s/prep',
  icon: Briefcase,
  meta: 'Prep, applications, decisions',
  children: [
    { label: 'Workshops', to: '/s/prep', meta: 'Essay, interview, test feedback' },
    { label: 'Prompts', to: '/s/prep?tab=prompts', meta: 'Prompt library readiness' },
    { label: 'Interviews', to: '/s/prep?tab=interviews', meta: 'Invites and practice' },
    { label: 'Recommenders', to: '/s/prep?tab=recommenders', meta: 'Requests and letter risk' },
    { label: 'Documents', to: '/s/prep?tab=documents', meta: 'Materials and evidence' },
    { label: 'Applications', to: '/s/applications', meta: 'Portfolio execution' },
    { label: 'Offers', to: '/s/applications?tab=offers', meta: 'Admits and responses' },
    { label: 'Costs & aid', to: '/s/applications?tab=costs', meta: 'Net cost and funding' },
    { label: 'Calendar', to: '/s/calendar', meta: 'Deadlines and reminders' },
  ],
}

const ITEMS: Item[] = [OVERVIEW, IMPORT, PROFILE, PLANNING, SAVED, WORKSPACE]

// Mobile pill row — flat top-level rooms (no nesting).
const MOBILE_PILLS: { label: string; to: string; icon: typeof Backpack; meta: string; end?: boolean }[] = [
  { label: 'Overview', to: '/s/space', icon: Backpack, meta: 'What matters now', end: true },
  { label: 'Import', to: '/s/import', icon: Upload, meta: 'Review extracted signals' },
  { label: 'Profile', to: '/s/profile', icon: User, meta: 'Durable student record' },
  { label: 'Saved', to: '/s/saved', icon: Bookmark, meta: 'Shortlist and search memory' },
  { label: 'Prep', to: '/s/prep', icon: PenLine, meta: 'Prompt, document, and interview readiness' },
  { label: 'Applications', to: '/s/applications', icon: FolderKanban, meta: 'Portfolio execution' },
  { label: 'Calendar', to: '/s/calendar', icon: Calendar, meta: 'Deadlines and reminders' },
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
                  aria-label={`${item.label}: ${item.meta}`}
                  className={`flex items-start gap-2 rounded-md px-2 py-1.5 text-sm transition-colors ${
                    active
                      ? 'bg-muted font-medium text-foreground'
                      : 'text-muted-foreground hover:bg-muted/50 hover:text-foreground'
                  }`}
                >
                  <item.icon size={15} strokeWidth={1.75} className="mt-0.5 shrink-0" />
                  <span className="min-w-0">
                    <span className="block truncate">{item.label}</span>
                    <span className="block truncate text-[11px] font-normal text-muted-foreground">
                      {item.meta}
                    </span>
                  </span>
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
                <div
                  className={`flex items-center rounded-md text-sm transition-colors ${
                    owns ? 'font-medium text-foreground' : 'text-muted-foreground hover:bg-muted/50 hover:text-foreground'
                  }`}
                >
                  <NavLink
                    to={item.to}
                    onClick={() => { setOpen(prev => new Set(prev).add(item.label)) }}
                    aria-label={`${item.label}: ${item.meta}`}
                    className="flex min-w-0 flex-1 items-start gap-2 px-2 py-1.5"
                    aria-current={owns ? 'page' : undefined}
                  >
                    <item.icon size={15} strokeWidth={1.75} className="mt-0.5 shrink-0" />
                    <span className="min-w-0">
                      <span className="block truncate">
                        {item.label}
                        {badge}
                      </span>
                      <span className="block truncate text-[11px] font-normal text-muted-foreground">
                        {item.meta}
                      </span>
                    </span>
                  </NavLink>
                  <button
                    type="button"
                    aria-expanded={isOpen}
                    aria-label={isOpen ? `Collapse ${item.label}` : `Expand ${item.label}`}
                    onClick={() => toggle(item.label)}
                    className="mr-1 inline-flex h-7 w-7 items-center justify-center rounded text-muted-foreground hover:bg-background hover:text-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2"
                  >
                    {isOpen ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
                  </button>
                </div>
                {isOpen && (
                  <div className="mt-0.5 ml-[18px] border-l border-border pl-2">
                    {item.children.map(sub => {
                      const active = subActive(sub.to, pathname, search)
                      return (
                        <NavLink
                          key={sub.to}
                          to={sub.to}
                          title={sub.meta}
                          aria-label={`${sub.label}: ${sub.meta}`}
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
                aria-label={`${pill.label}: ${pill.meta}`}
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
