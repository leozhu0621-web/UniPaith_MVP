import { useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { BarChart3, Download } from 'lucide-react'
import Button from '../../components/ui/Button'
import Tabs from '../../components/ui/Tabs'
import InstitutionPageHeader from '../../components/institution/InstitutionPageHeader'
import { exportAnalyticsCsv } from '../../api/institutions'
import type { AnalyticsFilters } from '../../types'
import FilterBar from './analytics/FilterBar'
import OverviewTab from './analytics/OverviewTab'
import FunnelTab from './analytics/FunnelTab'
import AttributionTab from './analytics/AttributionTab'

const TABS = [
  { id: 'overview', label: 'Overview' },
  { id: 'funnel', label: 'Funnel' },
  { id: 'attribution', label: 'Attribution' },
]

// URL param ↔ filter-key map (saved views, §7).
const PARAM: Record<keyof AnalyticsFilters, string> = {
  time_window: 'range',
  program_id: 'program',
  intake_id: 'intake',
  segment_id: 'segment',
  campaign_id: 'campaign',
  source_kind: 'source_kind',
  source_id: 'source_id',
  from: 'from',
  to: 'to',
}

export default function AnalyticsPage() {
  const [searchParams, setSearchParams] = useSearchParams()
  const activeTab = searchParams.get('tab') ?? 'overview'
  const [exporting, setExporting] = useState(false)

  const filters: AnalyticsFilters = {
    time_window: searchParams.get('range') ?? '30d',
    program_id: searchParams.get('program') ?? undefined,
    intake_id: searchParams.get('intake') ?? undefined,
    segment_id: searchParams.get('segment') ?? undefined,
    campaign_id: searchParams.get('campaign') ?? undefined,
  }

  const patchParams = (patch: Record<string, string | undefined>, replace: boolean) => {
    setSearchParams(
      prev => {
        const p = new URLSearchParams(prev)
        for (const [k, v] of Object.entries(patch)) {
          if (v) p.set(k, v)
          else p.delete(k)
        }
        return p
      },
      { replace }
    )
  }

  const onTab = (tab: string) => patchParams({ tab }, false)

  const onFilter = (patch: Partial<AnalyticsFilters>) => {
    const urlPatch: Record<string, string | undefined> = {}
    for (const k of Object.keys(patch) as (keyof AnalyticsFilters)[]) {
      urlPatch[PARAM[k]] = patch[k]
    }
    patchParams(urlPatch, true)
  }

  const onExport = async () => {
    setExporting(true)
    try {
      await exportAnalyticsCsv(activeTab, filters)
    } finally {
      setExporting(false)
    }
  }

  return (
    <div className="p-6 space-y-6">
      <InstitutionPageHeader
        title="Analytics"
        description="Attribution and funnel performance — from exposure to application progress."
        badge={<BarChart3 size={20} className="text-secondary" />}
        actions={
          <Button variant="secondary" size="sm" loading={exporting} onClick={onExport}>
            <span className="inline-flex items-center gap-1.5">
              <Download size={15} />
              Export CSV
            </span>
          </Button>
        }
      />

      <Tabs tabs={TABS} activeTab={activeTab} onChange={onTab} />

      <FilterBar filters={filters} onChange={onFilter} />

      {activeTab === 'overview' && <OverviewTab filters={filters} />}
      {activeTab === 'funnel' && <FunnelTab filters={filters} />}
      {activeTab === 'attribution' && <AttributionTab filters={filters} />}
    </div>
  )
}
