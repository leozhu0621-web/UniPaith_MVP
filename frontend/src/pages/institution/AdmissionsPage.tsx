import { useEffect, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import Tabs from '../../components/ui/Tabs'
import PipelinePage from './PipelinePage'
import InterviewsPage from './InterviewsPage'
import InquiriesPage from './InquiriesPage'
import IntegrityQueuePage from './IntegrityQueuePage'
import CohortComparisonPage from './CohortComparisonPage'
import YieldPage from './yield/YieldPage'
import InternationalPage from './international/InternationalPage'
import GraduatePage from './graduate/GraduatePage'
import WaiverQueuePage from './WaiverQueuePage'

type AdmissionsTab =
  | 'pipeline'
  | 'integrity'
  | 'interviews'
  | 'inquiries'
  | 'cohort'
  | 'yield'
  | 'international'
  | 'graduate'
  | 'waivers'

const tabs = [
  { id: 'pipeline', label: 'Pipeline' },
  { id: 'integrity', label: 'Integrity' },
  { id: 'interviews', label: 'Interviews' },
  { id: 'inquiries', label: 'Inquiries' },
  { id: 'cohort', label: 'Cohort Compare' },
  { id: 'yield', label: 'Yield' },
  { id: 'international', label: 'International' },
  // Spec 41 — graduate & PhD admissions (faculty matching, funding, dept review).
  { id: 'graduate', label: 'Graduate' },
  // Spec 39 §2.3 / §5 — fee-waiver queue + payments & refunds.
  { id: 'waivers', label: 'Fees & Waivers' },
]

export default function AdmissionsPage() {
  const [searchParams, setSearchParams] = useSearchParams()
  const initialTab = (searchParams.get('tab') as AdmissionsTab) || 'pipeline'
  const [activeTab, setActiveTab] = useState<AdmissionsTab>(initialTab)

  // Keep the active tab in sync with the URL so deep links (e.g. the dashboard's
  // "Review Alerts" → ?tab=integrity) and browser back/forward switch tabs even
  // when AdmissionsPage is already mounted.
  useEffect(() => {
    const t = (searchParams.get('tab') as AdmissionsTab) || 'pipeline'
    setActiveTab(prev => (prev !== t ? t : prev))
  }, [searchParams])

  const handleTabChange = (tab: string) => {
    setActiveTab(tab as AdmissionsTab)
    setSearchParams({ tab })
  }

  return (
    <div className="p-6 space-y-4">
      <Tabs tabs={tabs} activeTab={activeTab} onChange={handleTabChange} />
      {activeTab === 'pipeline' && <PipelinePage embedded />}
      {activeTab === 'integrity' && <IntegrityQueuePage embedded />}
      {activeTab === 'interviews' && <InterviewsPage embedded />}
      {activeTab === 'inquiries' && <InquiriesPage embedded />}
      {activeTab === 'cohort' && <CohortComparisonPage embedded />}
      {activeTab === 'yield' && <YieldPage />}
      {activeTab === 'international' && <InternationalPage embedded />}
      {activeTab === 'graduate' && <GraduatePage />}
      {activeTab === 'waivers' && <WaiverQueuePage />}
    </div>
  )
}
