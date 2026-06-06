/**
 * Universal Profile — the student's durable record (Spec/08-universal-profile.md).
 *
 * Brand shell: eyebrow + H1 "Your record" + 64px gold completion ring + the
 * 13-tab strip (active tab = the one gold underline). Each tab is a lazy
 * module under `profile/`. The 19 spec sections cluster into these 13 tabs.
 */
import { lazy, Suspense, useEffect, useRef } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'

import { SkeletonCard } from '../../components/ui/Skeleton'
import usePageTitle from '../../hooks/usePageTitle'
import { PROFILE_TAB_ALIASES, normalizeProfileTab, type ProfileTabSpec } from '../../utils/information-architecture'
import { CompletionRing, lastUpdatedLabel } from './profile/shared'
import { useCompletion } from './profile/useCompletion'

const OverviewTab = lazy(() => import('./profile/OverviewTab'))
const IdentityTab = lazy(() => import('./profile/IdentityTab'))
const AcademicsTab = lazy(() => import('./profile/AcademicsTab'))
const ExperienceTab = lazy(() => import('./profile/ExperienceTab'))
const GoalsTab = lazy(() => import('./profile/GoalsTab'))
const NeedsTab = lazy(() => import('./profile/NeedsTab'))
const StrategyTab = lazy(() => import('./profile/StrategyTab'))
const PreparationTab = lazy(() => import('./profile/PreparationTab'))
const PreferencesTab = lazy(() => import('./profile/PreferencesTab'))
const FinancialTab = lazy(() => import('./profile/FinancialTab'))
const TimelineTab = lazy(() => import('./profile/TimelineTab'))
const AnalyticsTab = lazy(() => import('./profile/AnalyticsTab'))
const DataTab = lazy(() => import('./profile/DataTab'))

const TABS: { key: ProfileTabSpec; label: string }[] = [
  { key: 'overview', label: 'Overview' },
  { key: 'identity', label: 'Identity' },
  { key: 'academics', label: 'Academics' },
  { key: 'experience', label: 'Experience' },
  { key: 'goals', label: 'Goals' },
  { key: 'needs', label: 'Needs' },
  { key: 'strategy', label: 'Strategy' },
  { key: 'preparation', label: 'Preparation' },
  { key: 'preferences', label: 'Preferences' },
  { key: 'financial', label: 'Financial' },
  { key: 'timeline', label: 'Timeline' },
  { key: 'analytics', label: 'Analytics' },
  { key: 'data', label: 'Data' },
]

export default function ProfilePage() {
  const navigate = useNavigate()
  const [searchParams, setSearchParams] = useSearchParams()
  const rawTab = searchParams.get('tab')
  const activeTab = normalizeProfileTab(rawTab)
  usePageTitle('Profile')
  const { overall, lastUpdated, isLoading } = useCompletion()
  const tablistRef = useRef<HTMLDivElement>(null)

  // Legacy tab aliases (e.g. ?tab=essays → workshops).
  useEffect(() => {
    if (!rawTab) return
    const alias = PROFILE_TAB_ALIASES[rawTab]
    if (alias) navigate(alias, { replace: true })
  }, [rawTab, navigate])

  const setTab = (tab: string) => {
    const next = new URLSearchParams(searchParams)
    if (tab === 'overview') next.delete('tab')
    else next.set('tab', tab)
    next.delete('section')
    setSearchParams(next, { replace: true })
  }

  // Arrow-key / Home / End keyboard navigation on the tablist (ARIA §3.22).
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
      setTab(TABS[next].key)
    }
  }

  const panelId = `profile-panel-${activeTab}`

  return (
    <div className="max-w-5xl w-full mx-auto p-4 sm:p-6 lg:p-8">
      {/* Header — eyebrow + H1 + completion ring */}
      <div className="flex items-center gap-4 mb-6">
        {/* Finding 3: don't show 0% during load — render the ring dimmed */}
        <div className={isLoading ? 'opacity-30' : undefined}>
          <CompletionRing value={isLoading ? overall : overall} size={64} />
        </div>
        <div>
          <p className="up-eyebrow">Profile</p>
          {/* Finding 5: use semantic heading token */}
          <h1 className="text-h2 text-foreground">Your record</h1>
          <p className="text-xs text-muted-foreground mt-0.5">{lastUpdatedLabel(lastUpdated)}</p>
        </div>
      </div>

      {/* Tab strip — finding 8: proper ARIA tablist attributes */}
      <div
        ref={tablistRef}
        className="flex gap-1 border-b border-border overflow-x-auto no-scrollbar mb-8 -mx-1 px-1 [mask-image:linear-gradient(to_right,#000_92%,transparent)] [-webkit-mask-image:linear-gradient(to_right,#000_92%,transparent)]"
        role="tablist"
        aria-label="Profile sections"
      >
        {TABS.map((tab, idx) => {
          const isActive = activeTab === tab.key
          const tabId = `profile-tab-${tab.key}`
          return (
            <button
              key={tab.key}
              id={tabId}
              role="tab"
              aria-selected={isActive}
              aria-controls={`profile-panel-${tab.key}`}
              tabIndex={isActive ? 0 : -1}
              onClick={() => setTab(tab.key)}
              onKeyDown={e => handleTabKeyDown(e, idx)}
              className={`relative px-3 py-2.5 text-sm whitespace-nowrap transition-colors ${
                isActive ? 'text-foreground font-semibold' : 'text-muted-foreground hover:text-foreground'
              }`}
            >
              {tab.label}
              {isActive && <span className="absolute bottom-0 left-2 right-2 h-0.5 rounded-full bg-primary" />}
            </button>
          )
        })}
      </div>

      {/* Tab content — finding 8: tabpanel role + labelled-by */}
      <div
        id={panelId}
        role="tabpanel"
        aria-labelledby={`profile-tab-${activeTab}`}
        tabIndex={0}
        className="focus-visible:outline-none"
      >
        <Suspense fallback={<div className="space-y-3"><SkeletonCard /><SkeletonCard /></div>}>
          {activeTab === 'overview' && <OverviewTab onOpenTab={setTab} />}
          {activeTab === 'identity' && <IdentityTab />}
          {activeTab === 'academics' && <AcademicsTab />}
          {activeTab === 'experience' && <ExperienceTab />}
          {activeTab === 'goals' && <GoalsTab />}
          {activeTab === 'needs' && <NeedsTab />}
          {activeTab === 'strategy' && <StrategyTab />}
          {activeTab === 'preparation' && <PreparationTab />}
          {activeTab === 'preferences' && <PreferencesTab />}
          {activeTab === 'financial' && <FinancialTab />}
          {activeTab === 'timeline' && <TimelineTab />}
          {activeTab === 'analytics' && <AnalyticsTab />}
          {activeTab === 'data' && <DataTab />}
        </Suspense>
      </div>
    </div>
  )
}
