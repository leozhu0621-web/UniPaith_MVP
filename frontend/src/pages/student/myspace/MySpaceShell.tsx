import { useEffect, useMemo, useState } from 'react'
import { NavLink, Outlet, useLocation } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import {
  Backpack,
  Bookmark,
  Briefcase,
  Calendar,
  ChevronDown,
  ChevronRight,
  FolderKanban,
  PenLine,
  SlidersHorizontal,
  Upload,
  User,
} from 'lucide-react'

import { listMyApplications } from '../../../api/applications'
import { listRecommendations } from '../../../api/recommendations'

type Icon = typeof Backpack
type SubItem = { label: string; to: string; defaultTab?: string }
type RailItem =
  | { kind: 'link'; label: string; to: string; icon: Icon; defaultTab?: string }
  | { kind: 'group'; label: string; to: string; icon: Icon; children: SubItem[] }

const OVERVIEW: RailItem = { kind: 'link', label: 'Overview', to: '/s/space', icon: Backpack }
const IMPORT: RailItem = { kind: 'link', label: 'Import', to: '/s/import', icon: Upload }

const PROFILE: RailItem = {
  kind: 'group',
  label: 'Profile',
  to: '/s/profile',
  icon: User,
  children: [
    { label: 'Summary', to: '/s/profile', defaultTab: 'overview' },
    { label: 'Identity', to: '/s/profile?tab=identity' },
    { label: 'Academics', to: '/s/profile?tab=academics' },
    { label: 'Experience', to: '/s/profile?tab=experience' },
  ],
}

const PLANNING: RailItem = {
  kind: 'group',
  label: 'Planning',
  to: '/s/profile?tab=strategy',
  icon: SlidersHorizontal,
  children: [
    { label: 'Strategy', to: '/s/profile?tab=strategy' },
    { label: 'Goals', to: '/s/profile?tab=goals' },
    { label: 'Needs', to: '/s/profile?tab=needs' },
    { label: 'Preferences', to: '/s/profile?tab=preferences' },
    { label: 'Financial', to: '/s/profile?tab=financial' },
  ],
}

const SAVED: RailItem = {
  kind: 'group',
  label: 'Saved',
  to: '/s/saved',
  icon: Bookmark,
  children: [
    { label: 'Programs', to: '/s/saved', defaultTab: 'programs' },
    { label: 'Schools', to: '/s/saved?tab=schools' },
    { label: 'Searches', to: '/s/saved?tab=searches' },
  ],
}

const WORKSPACE: RailItem = {
  kind: 'group',
  label: 'Workspace',
  to: '/s/prep',
  icon: Briefcase,
  children: [
    { label: 'Workshops', to: '/s/prep', defaultTab: 'workshops' },
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

const RAIL_ITEMS: RailItem[] = [OVERVIEW, IMPORT, PROFILE, PLANNING, SAVED, WORKSPACE]

const MOBILE_ROOMS: { label: string; to: string; icon: Icon; end?: boolean }[] = [
  { label: 'Overview', to: '/s/space', icon: Backpack, end: true },
  { label: 'Import', to: '/s/import', icon: Upload },
  { label: 'Profile', to: '/s/profile', icon: User },
  { label: 'Saved', to: '/s/saved', icon: Bookmark },
  { label: 'Prep', to: '/s/prep', icon: PenLine },
  { label: 'Applications', to: '/s/applications', icon: FolderKanban },
  { label: 'Calendar', to: '/s/calendar', icon: Calendar },
]

function subActive(to: string, pathname: string, search: string, defaultTab?: string) {
  const [path, query = ''] = to.split('?')
  if (pathname !== path) return false
  const targetTab = new URLSearchParams(query).get('tab')
  const currentTab = new URLSearchParams(search).get('tab')
  if (!targetTab) return !currentTab || currentTab === defaultTab
  return currentTab === targetTab
}

function groupOwns(group: Extract<RailItem, { kind: 'group' }>, pathname: string, search: string) {
  return group.children.some(child => subActive(child.to, pathname, search, child.defaultTab))
}

export default function MySpaceShell() {
  const location = useLocation()
  const { pathname, search } = location
  const { data: apps } = useQuery({ queryKey: ['my-applications'], queryFn: listMyApplications, staleTime: 60_000 })
  const { data: recs } = useQuery({ queryKey: ['recommendations'], queryFn: listRecommendations, staleTime: 60_000 })

  const childMeta = useMemo(() => {
    const meta = new Map<string, string>()
    if (Array.isArray(apps)) {
      meta.set('/s/applications', String(apps.length))
      const pendingOffers = apps.filter(app => app.offer && !app.offer.student_response && app.student_decision == null)
      if (pendingOffers.length > 0) meta.set('/s/applications?tab=offers', String(pendingOffers.length))
    }
    if (Array.isArray(recs)) {
      const tracked = recs.filter(rec => ['requested', 'submitted', 'received'].includes(rec.status ?? ''))
      const received = tracked.filter(rec => rec.status === 'received')
      if (tracked.length > 0) meta.set('/s/prep?tab=recommenders', `${received.length}/${tracked.length}`)
    }
    return meta
  }, [apps, recs])

  const [openGroups, setOpenGroups] = useState<Set<string>>(() => {
    const seed = new Set<string>()
    for (const item of RAIL_ITEMS) {
      if (item.kind === 'group' && groupOwns(item, pathname, search)) seed.add(item.label)
    }
    return seed
  })

  useEffect(() => {
    for (const item of RAIL_ITEMS) {
      if (item.kind === 'group' && groupOwns(item, pathname, search)) {
        setOpenGroups(prev => (prev.has(item.label) ? prev : new Set(prev).add(item.label)))
      }
    }
  }, [pathname, search])

  const toggleGroup = (label: string) => {
    setOpenGroups(prev => {
      const next = new Set(prev)
      if (next.has(label)) next.delete(label)
      else next.add(label)
      return next
    })
  }

  return (
    <div className="flex min-h-0 flex-1 bg-background">
      <aside className="hidden w-52 shrink-0 border-r border-border bg-card/60 lg:block" aria-label="My Space">
        <nav className="sticky top-0 max-h-[calc(100dvh-4rem)] overflow-y-auto px-3 py-4">
          {RAIL_ITEMS.map(item => {
            if (item.kind === 'link') {
              const active = subActive(item.to, pathname, search, item.defaultTab)
              return (
                <NavLink
                  key={item.to}
                  to={item.to}
                  className={`mb-1 flex min-h-9 items-center gap-2 rounded-md px-2.5 py-1.5 text-sm transition-colors ${
                    active
                      ? 'bg-muted font-semibold text-foreground'
                      : 'text-muted-foreground hover:bg-muted/70 hover:text-foreground'
                  }`}
                  aria-current={active ? 'page' : undefined}
                >
                  <item.icon size={15} strokeWidth={1.8} />
                  {item.label}
                </NavLink>
              )
            }

            const owns = groupOwns(item, pathname, search)
            const isOpen = openGroups.has(item.label)
            return (
              <div key={item.label} className="mb-1">
                <div
                  className={`flex min-h-9 items-center rounded-md transition-colors ${
                    owns
                      ? 'font-semibold text-foreground'
                      : 'text-muted-foreground hover:bg-muted/70 hover:text-foreground'
                  }`}
                >
                  <NavLink
                    to={item.to}
                    onClick={() => {
                      if (!isOpen) toggleGroup(item.label)
                    }}
                    className="flex min-w-0 flex-1 items-center gap-2 px-2.5 py-1.5 text-sm"
                    aria-current={owns ? 'page' : undefined}
                  >
                    <item.icon size={15} strokeWidth={1.8} />
                    <span className="truncate">{item.label}</span>
                  </NavLink>
                  <button
                    type="button"
                    className="mr-1 inline-flex h-7 w-7 shrink-0 items-center justify-center rounded text-muted-foreground hover:bg-background hover:text-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2"
                    aria-label={isOpen ? `Collapse ${item.label}` : `Expand ${item.label}`}
                    aria-expanded={isOpen}
                    onClick={() => toggleGroup(item.label)}
                  >
                    {isOpen ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
                  </button>
                </div>
                {isOpen && (
                  <div className="ml-[18px] mt-0.5 border-l border-border pl-2">
                    {item.children.map(child => {
                      const active = subActive(child.to, pathname, search, child.defaultTab)
                      const meta = childMeta.get(child.to)
                      return (
                        <NavLink
                          key={child.to}
                          to={child.to}
                          className={`flex min-h-8 items-center gap-2 rounded-md px-2 py-1 text-[13px] transition-colors ${
                            active
                              ? 'bg-muted font-semibold text-foreground'
                              : 'text-muted-foreground hover:bg-muted/70 hover:text-foreground'
                          }`}
                          aria-current={active ? 'page' : undefined}
                        >
                          <span className="min-w-0 flex-1 truncate">{child.label}</span>
                          {meta && <span className="text-xs tabular-nums text-muted-foreground">{meta}</span>}
                        </NavLink>
                      )
                    })}
                  </div>
                )}
              </div>
            )
          })}
        </nav>
      </aside>

      <div className="flex min-w-0 flex-1 flex-col">
        <nav className="sticky top-0 z-20 shrink-0 overflow-x-auto border-b border-border bg-background px-3 py-2 no-scrollbar lg:hidden" aria-label="My Space rooms">
          <div className="flex w-max items-center gap-1.5">
            {MOBILE_ROOMS.map(room => (
              <NavLink
                key={room.to}
                to={room.to}
                end={room.end}
                className={({ isActive }) =>
                  `inline-flex min-h-9 items-center gap-1.5 whitespace-nowrap rounded-full border px-3 text-xs font-semibold transition-colors ${
                    isActive
                      ? 'border-secondary bg-secondary/10 text-secondary'
                      : 'border-border text-muted-foreground hover:text-foreground'
                  }`
                }
              >
                <room.icon size={13} strokeWidth={1.8} />
                {room.label}
              </NavLink>
            ))}
          </div>
        </nav>
        <div className="min-h-0 flex-1">
          <Outlet />
        </div>
      </div>
    </div>
  )
}
