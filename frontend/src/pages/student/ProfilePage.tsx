/**
 * Universal Profile — the student's durable record (spec 10).
 * Thin layout shell: eyebrow + H1 + completion ring + 13-tab strip, routed by
 * `?tab=`. Each tab is a self-contained, lazy-loaded component under ./profile.
 */
import { lazy, Suspense, type ComponentType } from 'react'
import { useSearchParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'

import { getProfileOverview } from '../../api/students'
import { SkeletonCard } from '../../components/ui/Skeleton'
import type { ProfileOverview } from '../../types'
import CompletionRing from './profile/CompletionRing'
import { relativeTime } from './profile/_shared'

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

const TABS: { key: string; label: string; Component: ComponentType }[] = [
  { key: 'overview', label: 'Overview', Component: OverviewTab },
  { key: 'identity', label: 'Identity', Component: IdentityTab },
  { key: 'academics', label: 'Academics', Component: AcademicsTab },
  { key: 'experience', label: 'Experience', Component: ExperienceTab },
  { key: 'goals', label: 'Goals', Component: GoalsTab },
  { key: 'needs', label: 'Needs', Component: NeedsTab },
  { key: 'strategy', label: 'Strategy', Component: StrategyTab },
  { key: 'preparation', label: 'Preparation', Component: PreparationTab },
  { key: 'preferences', label: 'Preferences', Component: PreferencesTab },
  { key: 'financial', label: 'Financial', Component: FinancialTab },
  { key: 'timeline', label: 'Timeline', Component: TimelineTab },
  { key: 'analytics', label: 'Analytics', Component: AnalyticsTab },
  { key: 'data', label: 'Data', Component: DataTab },
]

export default function ProfilePage() {
  const [searchParams, setSearchParams] = useSearchParams()
  const tabParam = searchParams.get('tab') || 'overview'
  const active = TABS.find(t => t.key === tabParam) ?? TABS[0]
  const ActiveComponent = active.Component

  const { data: overview } = useQuery<ProfileOverview>({ queryKey: ['profile-overview'], queryFn: getProfileOverview })
  const overallPct = overview?.completion?.overall_pct ?? 0
  const sortedDates = (overview?.completion?.per_category ?? [])
    .map(c => c.last_updated)
    .filter(Boolean)
    .sort()
  const lastUpdated = sortedDates.length ? sortedDates[sortedDates.length - 1] : undefined

  const selectTab = (key: string) => setSearchParams(key === 'overview' ? {} : { tab: key })

  return (
    <div className="p-6 max-w-5xl mx-auto">
      <p className="up-eyebrow mb-1">PROFILE</p>
      <h1 className="text-2xl font-semibold text-charcoal mb-5">Your record</h1>

      <div className="flex items-start gap-5 mb-6">
        <div className="flex flex-col items-center shrink-0">
          <CompletionRing value={overallPct} size={64} />
          <span className="text-[11px] text-slate mt-1 text-center w-20 leading-tight">
            {lastUpdated ? `Updated ${relativeTime(lastUpdated)}` : 'Get started'}
          </span>
        </div>
        <nav className="flex flex-wrap gap-x-1 gap-y-1 overflow-x-auto no-scrollbar -mb-px" aria-label="Profile sections">
          {TABS.map(tab => {
            const isActive = tab.key === active.key
            return (
              <button
                key={tab.key}
                onClick={() => selectTab(tab.key)}
                aria-current={isActive ? 'page' : undefined}
                className={`px-3 py-2 text-sm whitespace-nowrap border-b-2 transition-colors ${
                  isActive
                    ? 'border-gold text-charcoal font-semibold'
                    : 'border-transparent text-slate hover:text-charcoal'
                }`}
              >
                {tab.label}
              </button>
            )
          })}
        </nav>
      </div>

      <Suspense fallback={<div className="space-y-4"><SkeletonCard /><SkeletonCard /></div>}>
        <ActiveComponent />
      </Suspense>
    </div>
  )
}
