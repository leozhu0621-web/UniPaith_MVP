import { useEffect, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import Tabs from '../../components/ui/Tabs'
import PipelinePage from './PipelinePage'
import InterviewsPage from './InterviewsPage'
import InquiriesPage from './InquiriesPage'
import IntegrityQueuePage from './IntegrityQueuePage'
import CohortComparisonPage from './CohortComparisonPage'

type AdmissionsTab = 'pipeline' | 'integrity' | 'interviews' | 'inquiries' | 'cohort'

const tabs = [
  { id: 'pipeline', label: 'Pipeline' },
  { id: 'integrity', label: 'Integrity' },
  { id: 'interviews', label: 'Interviews' },
  { id: 'inquiries', label: 'Inquiries' },
  { id: 'cohort', label: 'Cohort Compare' },
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
      {activeTab === 'pipeline' && <PipelinePage />}
      {activeTab === 'integrity' && <IntegrityQueuePage />}
      {activeTab === 'interviews' && <InterviewsPage />}
      {activeTab === 'inquiries' && <InquiriesPage />}
      {activeTab === 'cohort' && <CohortComparisonPage />}
    </div>
  )
}
