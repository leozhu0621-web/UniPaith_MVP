import { useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import Tabs from '../../components/ui/Tabs'
import PipelinePage from './PipelinePage'
import InterviewsPage from './InterviewsPage'
import InquiriesPage from './InquiriesPage'
import CohortComparisonPage from './CohortComparisonPage'
import YieldPage from './yield/YieldPage'

type AdmissionsTab = 'pipeline' | 'interviews' | 'inquiries' | 'cohort' | 'yield'

const tabs = [
  { id: 'pipeline', label: 'Pipeline' },
  { id: 'interviews', label: 'Interviews' },
  { id: 'inquiries', label: 'Inquiries' },
  { id: 'cohort', label: 'Cohort Compare' },
  { id: 'yield', label: 'Yield' },
]

export default function AdmissionsPage() {
  const [searchParams, setSearchParams] = useSearchParams()
  const initialTab = (searchParams.get('tab') as AdmissionsTab) || 'pipeline'
  const [activeTab, setActiveTab] = useState<AdmissionsTab>(initialTab)

  const handleTabChange = (tab: string) => {
    setActiveTab(tab as AdmissionsTab)
    setSearchParams({ tab })
  }

  return (
    <div className="p-6 space-y-4">
      <Tabs tabs={tabs} activeTab={activeTab} onChange={handleTabChange} />
      {activeTab === 'pipeline' && <PipelinePage />}
      {activeTab === 'interviews' && <InterviewsPage />}
      {activeTab === 'inquiries' && <InquiriesPage />}
      {activeTab === 'cohort' && <CohortComparisonPage />}
      {activeTab === 'yield' && <YieldPage />}
    </div>
  )
}
