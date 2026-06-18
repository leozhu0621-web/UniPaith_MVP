// Discover hub sub-tabs (Spec 2026-06-12 §2). For you = the Match surface;
// Updates / Events / Peers are the absorbed Connect tabs. Badges: Updates =
// posts since last visit (server count); Events = recommended upcoming events.
import { useRef } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Calendar, ChevronDown, LibraryBig, Newspaper, Sparkles, Users } from 'lucide-react'
import { getConnectEvents, getFollowing, getUnseenCount } from '../../../api/connect'
import { getConnectSeenAt } from '../../../utils/connectSeen'

export type DiscoverTab = 'foryou' | 'resources' | 'updates' | 'events' | 'peers'
export const DISCOVER_TABS: readonly DiscoverTab[] = ['foryou', 'resources', 'updates', 'events', 'peers'] as const

const TABS: { key: DiscoverTab; label: string; icon: typeof Newspaper }[] = [
  { key: 'foryou', label: 'For you', icon: Sparkles },
  { key: 'resources', label: 'Resources', icon: LibraryBig },
  { key: 'updates', label: 'Updates', icon: Newspaper },
  { key: 'events', label: 'Events', icon: Calendar },
  { key: 'peers', label: 'Peers', icon: Users },
]

interface Props {
  tab: DiscoverTab
  onChange: (t: DiscoverTab) => void
  onManageFollowing: () => void
  /** Hide the Peers tab when its flag is off so it never dead-ends (Discover review 2026-06-14). */
  peersEnabled?: boolean
}

export default function DiscoverTabBar({ tab, onChange, onManageFollowing, peersEnabled = true }: Props) {
  const tablistRef = useRef<HTMLDivElement>(null)
  const visibleTabs = TABS.filter(t => t.key !== 'peers' || peersEnabled)
  const { data: follows } = useQuery({ queryKey: ['connect-follows'], queryFn: getFollowing, retry: false })
  const { data: unseen = 0 } = useQuery({
    queryKey: ['connect-unseen'],
    queryFn: () => getUnseenCount(getConnectSeenAt()),
    staleTime: 5 * 60 * 1000,
    retry: false,
  })
  const { data: eventsData } = useQuery({
    queryKey: ['connect-events', 'upcoming'],
    queryFn: () => getConnectEvents('upcoming'),
    staleTime: 5 * 60 * 1000,
    retry: false,
  })
  const recommended = (eventsData?.events ?? []).filter(e => e.recommended).length
  const badges: Partial<Record<DiscoverTab, number>> = { updates: unseen, events: recommended }
  const followCount = follows?.length ?? 0

  // Arrow-key / Home / End keyboard navigation on the tablist (ARIA tabs pattern).
  const handleTabKeyDown = (e: React.KeyboardEvent<HTMLButtonElement>, idx: number) => {
    const buttons = tablistRef.current?.querySelectorAll<HTMLButtonElement>('[role="tab"]')
    if (!buttons) return
    let next = -1
    if (e.key === 'ArrowRight') next = (idx + 1) % buttons.length
    else if (e.key === 'ArrowLeft') next = (idx - 1 + buttons.length) % buttons.length
    else if (e.key === 'Home') next = 0
    else if (e.key === 'End') next = buttons.length - 1
    if (next >= 0) {
      e.preventDefault()
      buttons[next].focus()
      onChange(visibleTabs[next].key)
    }
  }

  return (
    <div className="flex items-end justify-between border-b border-border mb-5">
      <div ref={tablistRef} role="tablist" aria-label="Discover sections" className="flex gap-1 overflow-x-auto no-scrollbar">
        {visibleTabs.map((t, idx) => {
          const badge = badges[t.key] ?? 0
          return (
            <button
              key={t.key}
              id={`discover-tab-${t.key}`}
              role="tab"
              aria-selected={tab === t.key}
              aria-controls={`discover-panel-${t.key}`}
              tabIndex={tab === t.key ? 0 : -1}
              onClick={() => onChange(t.key)}
              onKeyDown={e => handleTabKeyDown(e, idx)}
              className={`flex items-center gap-1.5 px-4 py-2 text-sm font-medium border-b-2 -mb-px whitespace-nowrap transition-colors ${
                tab === t.key
                  ? 'border-secondary text-secondary'
                  : 'border-transparent text-muted-foreground hover:text-foreground'
              }`}
            >
              <t.icon size={14} />
              {t.label}
              {badge > 0 && (
                <span className="min-w-[16px] h-4 px-1 inline-flex items-center justify-center rounded-full bg-secondary text-secondary-foreground text-[9px] font-bold leading-none">
                  {badge > 9 ? '9+' : badge}
                </span>
              )}
            </button>
          )
        })}
      </div>
      <button
        onClick={onManageFollowing}
        className="hidden sm:inline-flex items-center gap-1 px-3 py-1.5 mb-1 text-xs font-medium text-muted-foreground hover:text-foreground rounded-lg hover:bg-muted transition-colors flex-shrink-0"
      >
        Manage following ({followCount}) <ChevronDown size={13} />
      </button>
      <button
        onClick={onManageFollowing}
        className="inline-flex sm:hidden items-center gap-1 px-3 py-1.5 mb-1 text-xs font-medium text-muted-foreground hover:text-foreground rounded-lg hover:bg-muted transition-colors flex-shrink-0"
      >
        Following ({followCount}) <ChevronDown size={13} />
      </button>
    </div>
  )
}
