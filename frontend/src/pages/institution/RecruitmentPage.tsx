import { useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import Tabs from '../../components/ui/Tabs'
import { getRecruitmentSummary } from '../../api/recruitment'
import ProspectsTab from './recruitment/ProspectsTab'
import TravelTab from './recruitment/TravelTab'
import FairsTab from './recruitment/FairsTab'
import TerritoriesTab from './recruitment/TerritoriesTab'

type RecruitTab = 'prospects' | 'travel' | 'fairs' | 'territories'

const TABS = [
  { id: 'prospects', label: 'Prospects' },
  { id: 'travel', label: 'Travel' },
  { id: 'fairs', label: 'Fairs & Schools' },
  { id: 'territories', label: 'Territories' },
]

export default function RecruitmentPage() {
  const [searchParams, setSearchParams] = useSearchParams()
  const initial = (searchParams.get('tab') as RecruitTab) || 'prospects'
  const [activeTab, setActiveTab] = useState<RecruitTab>(initial)

  const { data: summary } = useQuery({
    queryKey: ['recruitment-summary'],
    queryFn: getRecruitmentSummary,
  })

  const handleTab = (tab: string) => {
    setActiveTab(tab as RecruitTab)
    setSearchParams({ tab })
  }

  return (
    <div className="w-full space-y-5 p-6">
      <header>
        <h1 className="text-2xl font-semibold tracking-tight text-foreground">Recruitment</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Manage prospects before they apply — travel, fairs, and territories. The top of your
          funnel.
        </p>
        {summary && !summary.is_empty && (
          <div className="mt-3 flex flex-wrap gap-x-5 gap-y-1 text-sm text-muted-foreground">
            <span>
              <span className="font-semibold text-foreground">{summary.prospect_count}</span>{' '}
              prospects
            </span>
            <span>
              <span className="font-semibold text-foreground">{summary.applicant_count}</span>{' '}
              converted
            </span>
            <span>
              <span className="font-semibold text-foreground">{summary.trip_count}</span> trips
            </span>
            <span>
              <span className="font-semibold text-foreground">{summary.fair_count}</span> fairs/schools
            </span>
            {summary.unassigned_territory_count > 0 && (
              <span className="text-warning">
                {summary.unassigned_territory_count} territory without an owner
              </span>
            )}
          </div>
        )}
      </header>

      <Tabs tabs={TABS} activeTab={activeTab} onChange={handleTab} />

      {activeTab === 'prospects' && <ProspectsTab />}
      {activeTab === 'travel' && <TravelTab />}
      {activeTab === 'fairs' && <FairsTab />}
      {activeTab === 'territories' && <TerritoriesTab />}
    </div>
  )
}
