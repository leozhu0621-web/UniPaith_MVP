import { useSearchParams } from 'react-router-dom'
import Tabs from '../../components/ui/Tabs'
import PipelinePage from './PipelinePage'
import InterviewsPage from './InterviewsPage'
import InquiriesPage from './InquiriesPage'
import CohortComparisonPage from './CohortComparisonPage'

// Unified Admissions workspace — Spec/04 §5.1 (?tab=pipeline|interviews|inquiries|cohort-compare).
type AdmissionsTab = 'pipeline' | 'interviews' | 'inquiries' | 'cohort-compare'

const tabs = [
  { id: 'pipeline', label: 'Pipeline' },
  { id: 'interviews', label: 'Interviews' },
  { id: 'inquiries', label: 'Inquiries' },
  { id: 'cohort-compare', label: 'Cohort Compare' },
]

export default function AdmissionsPage() {
  const [searchParams, setSearchParams] = useSearchParams()
  // Tab is driven by the URL so deep links + back/forward work (Spec/04 §13).
  const param = searchParams.get('tab')
  const activeTab: AdmissionsTab = tabs.some(t => t.id === param) ? (param as AdmissionsTab) : 'pipeline'

  const handleTabChange = (tab: string) => {
    // Preserve other params (e.g. ?focus=) — only swap the tab (Spec/04 §8).
    setSearchParams(prev => {
      const next = new URLSearchParams(prev)
      next.set('tab', tab)
      return next
    }, { replace: true })
  }

  return (
    <div className="p-6 space-y-4">
      <Tabs tabs={tabs} activeTab={activeTab} onChange={handleTabChange} />
      {activeTab === 'pipeline' && <PipelinePage />}
      {activeTab === 'interviews' && <InterviewsPage />}
      {activeTab === 'inquiries' && <InquiriesPage />}
      {activeTab === 'cohort-compare' && <CohortComparisonPage />}
    </div>
  )
}
