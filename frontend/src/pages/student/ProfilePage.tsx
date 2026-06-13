/**
 * Universal Profile — the student's durable record (Spec/08-universal-profile.md).
 *
 * Brand shell: density PageHeader ("Your record" + gold completion ring) + the
 * 11-tab strip (active tab = the one gold underline). Each tab is a lazy
 * module under `profile/`. Preparation and Financial left for My Space
 * (Spec 2026-06-10 §5) — their legacy tab params redirect out via
 * PROFILE_TAB_ALIASES; the completion ring still counts those clusters.
 */
import { lazy, Suspense, useEffect, useRef } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'

import { PageContainer, PageHeader } from '../../components/student/density'
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
const PreferencesTab = lazy(() => import('./profile/PreferencesTab'))
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
  { key: 'preferences', label: 'Preferences' },
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

  // Legacy tab aliases — tabs that left the profile (Spec 2026-06-10 §5)
  // redirect to their new homes in My Space. ?tab=preparation keeps its
  // section deep link (recommenders) across the move.
  useEffect(() => {
    if (!rawTab) return
    if (rawTab === 'preparation' && searchParams.get('section') === 'recommenders') {
      navigate('/s/prep?tab=recommenders', { replace: true })
      return
    }
    const alias = PROFILE_TAB_ALIASES[rawTab]
    if (alias) navigate(alias, { replace: true })
  }, [rawTab, navigate, searchParams])

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
    <PageContainer>
      {/* Room header — density PageHeader (eyebrow = surface) + completion ring. */}
      <PageHeader
        eyebrow="My Space"
        title="Your record"
        sub={lastUpdatedLabel(lastUpdated)}
        actions={
          // Finding 3: don't show 0% during load — render the ring dimmed
          <div className={isLoading ? 'opacity-30' : undefined}>
            <CompletionRing value={overall} size={48} />
          </div>
        }
      />

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
        // stagger-list: the active tab's root (and the Suspense fallback) is the
        // single direct child → one fade/rise on tab switch instead of a hard swap.
        className="stagger-list focus-visible:outline-none"
      >
        <Suspense fallback={<div className="space-y-3"><SkeletonCard /><SkeletonCard /></div>}>
          {activeTab === 'overview' && <OverviewTab onOpenTab={setTab} />}
          {activeTab === 'identity' && <IdentityTab />}
          {activeTab === 'academics' && <AcademicsTab />}
          {activeTab === 'experience' && <ExperienceTab />}
          {activeTab === 'goals' && <GoalsTab />}
          {activeTab === 'needs' && <NeedsTab />}
          {activeTab === 'strategy' && <StrategyTab />}
          {activeTab === 'preferences' && <PreferencesTab />}
          {activeTab === 'timeline' && <TimelineTab />}
          {activeTab === 'analytics' && <AnalyticsTab />}
          {activeTab === 'data' && <DataTab />}
        </Suspense>
      </div>
    </PageContainer>
  )
}
