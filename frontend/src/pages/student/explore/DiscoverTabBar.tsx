// Discover hub top tabs (Spec 2026-06-14 restructure). For you = the Match
// surface; Academic = universities + school updates + events (sub-tabbed);
// Financial + International = the Resources guides, promoted to top tabs. The
// Academic badge counts school updates since the last visit.
import { useRef } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Banknote, Globe2, GraduationCap, Newspaper, Sparkles } from 'lucide-react'
import { getUnseenCount } from '../../../api/connect'
import { getConnectSeenAt } from '../../../utils/connectSeen'

export type DiscoverTab = 'foryou' | 'academic' | 'financial' | 'international'
export const DISCOVER_TABS: readonly DiscoverTab[] = ['foryou', 'academic', 'financial', 'international'] as const

const TABS: { key: DiscoverTab; label: string; icon: typeof Newspaper }[] = [
  { key: 'foryou', label: 'For you', icon: Sparkles },
  { key: 'academic', label: 'Academic', icon: GraduationCap },
  { key: 'financial', label: 'Financial', icon: Banknote },
  { key: 'international', label: 'International', icon: Globe2 },
]

interface Props {
  tab: DiscoverTab
  onChange: (t: DiscoverTab) => void
}

export default function DiscoverTabBar({ tab, onChange }: Props) {
  const tablistRef = useRef<HTMLDivElement>(null)
  const { data: unseen = 0 } = useQuery({
    queryKey: ['connect-unseen'],
    queryFn: () => getUnseenCount(getConnectSeenAt()),
    staleTime: 5 * 60 * 1000,
    retry: false,
  })
  const badges: Partial<Record<DiscoverTab, number>> = { academic: unseen }

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
      onChange(TABS[next].key)
    }
  }

  return (
    <div className="border-b border-border mb-5">
      <div ref={tablistRef} role="tablist" aria-label="Discover sections" className="flex justify-center gap-1 overflow-x-auto no-scrollbar">
        {TABS.map((t, idx) => {
          const badge = badges[t.key] ?? 0
          return (
            <button
              key={t.key}
              id={`discover-tab-${t.key}`}
              role="tab"
              aria-selected={tab === t.key}
              aria-controls={`discover-panel-${t.key}`}
              aria-label={badge > 0 ? `${t.label}, ${badge} new update${badge === 1 ? '' : 's'}` : undefined}
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
    </div>
  )
}
