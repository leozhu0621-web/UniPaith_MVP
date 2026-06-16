/**
 * Universal Profile — the student's durable record (Spec/08-universal-profile.md).
 *
 * Tabs only (2026-06-16): the "Your record" header + completion ring were
 * dropped — the My Space rail names the active section and the top nav shows
 * "My Space", so the header was redundant. Each tab is a lazy module under
 * `profile/`. Preparation and Financial left for My Space (Spec 2026-06-10 §5);
 * their legacy tab params redirect out via PROFILE_TAB_ALIASES.
 */
import { lazy, Suspense, useEffect, useRef } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'

import { useQueryClient } from '@tanstack/react-query'

import MaterialUpload from '../../components/student/MaterialUpload'
import { PageContainer } from '../../components/student/density'
import Card from '../../components/ui/Card'
import { SkeletonCard } from '../../components/ui/Skeleton'
import { showToast } from '../../stores/toast-store'
import usePageTitle from '../../hooks/usePageTitle'
import { PROFILE_TAB_ALIASES, normalizeProfileTab, type ProfileTabSpec } from '../../utils/information-architecture'

const OverviewTab = lazy(() => import('./profile/OverviewTab'))
const IdentityTab = lazy(() => import('./profile/IdentityTab'))
const AcademicsTab = lazy(() => import('./profile/AcademicsTab'))
const ExperienceTab = lazy(() => import('./profile/ExperienceTab'))
const GoalsTab = lazy(() => import('./profile/GoalsTab'))
const NeedsTab = lazy(() => import('./profile/NeedsTab'))
// Strategy lives in the Planning rail cluster (2026-06-15); ?tab=timeline (the
// retired chronological view) redirects to ?tab=strategy.
const StrategyTab = lazy(() => import('./profile/StrategyTab'))
const PreferencesTab = lazy(() => import('./profile/PreferencesTab'))
const AnalyticsTab = lazy(() => import('./profile/AnalyticsTab'))

const TABS: { key: ProfileTabSpec; label: string }[] = [
  { key: 'overview', label: 'Basic info' },
  { key: 'identity', label: 'Identity' },
  { key: 'academics', label: 'Academics' },
  { key: 'experience', label: 'Experience' },
  { key: 'goals', label: 'Goals' },
  { key: 'needs', label: 'Needs' },
  { key: 'preferences', label: 'Preferences' },
  { key: 'strategy', label: 'Strategy' },
  { key: 'analytics', label: 'Analytics' },
]

export default function ProfilePage() {
  const navigate = useNavigate()
  const qc = useQueryClient()
  const [searchParams, setSearchParams] = useSearchParams()
  const rawTab = searchParams.get('tab')
  const activeTab = normalizeProfileTab(rawTab)
  usePageTitle('Profile')
  const tablistRef = useRef<HTMLDivElement>(null)

  // Legacy tab aliases — tabs that left the profile (Spec 2026-06-10 §5)
  // redirect to their new homes in My Space. ?tab=preparation keeps its
  // section deep link (recommenders) across the move.
  useEffect(() => {
    if (!rawTab) return
    // Strategy lives in the Planning cluster (2026-06-15). The interim ?tab=timeline
    // alias redirects to the canonical ?tab=strategy.
    if (rawTab === 'timeline') {
      navigate('/s/profile?tab=strategy', { replace: true })
      return
    }
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
      {/* Import-from-a-file — upload a resume/transcript and Uni fills your
          profile (the My Space half of the material-ingest feature). */}
      <Card variant="card" pad className="mb-6">
        <div className="flex items-center justify-between gap-3 flex-wrap">
          <div>
            <p className="text-sm font-semibold text-foreground">Import from a file</p>
            <p className="text-xs text-muted-foreground">
              Upload a resume, transcript, or CV — Uni reads it and fills your profile. You
              review everything before it's saved.
            </p>
          </div>
          <MaterialUpload
            onApplied={result => {
              const n = Object.values(result.counts || {}).reduce((a, b) => a + b, 0)
              void qc.invalidateQueries({ queryKey: ['profile'] })
              void qc.invalidateQueries({ queryKey: ['goals'] })
              void qc.invalidateQueries({ queryKey: ['needs'] })
              void qc.invalidateQueries({ queryKey: ['identity'] })
              void qc.invalidateQueries({ queryKey: ['academic-records'] })
              void qc.invalidateQueries({ queryKey: ['test-scores'] })
              showToast(`Added ${n} items from your file to your profile.`, 'success')
            }}
          />
        </div>
      </Card>

      {/* Tab strip — finding 8: proper ARIA tablist attributes. Hidden on lg+
          where the My Space rail's Profile group already lists every sub-tab
          (Spec 2026-06-15 §A follow-up); kept below lg, where the rail collapses
          to flat pills that don't expose sub-tabs, so navigation still works. */}
      <div
        ref={tablistRef}
        className="lg:hidden flex gap-1 border-b border-border overflow-x-auto no-scrollbar mb-8 -mx-1 px-1 [mask-image:linear-gradient(to_right,#000_92%,transparent)] [-webkit-mask-image:linear-gradient(to_right,#000_92%,transparent)]"
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
        key={activeTab}
        id={panelId}
        role="tabpanel"
        aria-labelledby={`profile-tab-${activeTab}`}
        tabIndex={0}
        // stagger-list: the active tab's root (and the Suspense fallback) is the
        // single direct child → one fade/rise on tab switch instead of a hard swap.
        className="stagger-list focus-visible:outline-none"
      >
        <Suspense fallback={<div className="space-y-3"><SkeletonCard /><SkeletonCard /></div>}>
          {activeTab === 'overview' && <OverviewTab />}
          {activeTab === 'identity' && <IdentityTab />}
          {activeTab === 'academics' && <AcademicsTab />}
          {activeTab === 'experience' && <ExperienceTab />}
          {activeTab === 'goals' && <GoalsTab />}
          {activeTab === 'needs' && <NeedsTab />}
          {activeTab === 'preferences' && <PreferencesTab />}
          {activeTab === 'strategy' && <StrategyTab />}
          {activeTab === 'analytics' && <AnalyticsTab />}
        </Suspense>
      </div>
    </PageContainer>
  )
}
