import { useMemo } from 'react'
import { useSearchParams } from 'react-router-dom'

export type AnalyticsTab = 'overview' | 'funnel' | 'attribution'
export type FunnelKind = 'discovery' | 'event' | 'application'
export type TimeWindow = '7d' | '30d' | '90d' | 'yoy' | 'all'

export interface AnalyticsFilters {
  tab: AnalyticsTab
  funnel: FunnelKind
  programId: string
  intakeId: string
  segmentId: string
  campaignId: string
  timeWindow: TimeWindow
}

const DEFAULTS: AnalyticsFilters = {
  tab: 'overview',
  funnel: 'discovery',
  programId: '',
  intakeId: '',
  segmentId: '',
  campaignId: '',
  timeWindow: '30d',
}

export function filtersToParams(f: AnalyticsFilters): Record<string, string> {
  const p: Record<string, string> = { tab: f.tab, window: f.timeWindow }
  if (f.funnel !== 'discovery') p.funnel = f.funnel
  if (f.programId) p.program_id = f.programId
  if (f.intakeId) p.intake_id = f.intakeId
  if (f.segmentId) p.segment_id = f.segmentId
  if (f.campaignId) p.campaign_id = f.campaignId
  return p
}

export function paramsToQueryString(f: AnalyticsFilters): string {
  const p = filtersToParams(f)
  return new URLSearchParams(p).toString()
}

export function useAnalyticsFilters(): [AnalyticsFilters, (patch: Partial<AnalyticsFilters>) => void] {
  const [searchParams, setSearchParams] = useSearchParams()

  const filters = useMemo((): AnalyticsFilters => {
    const tab = (searchParams.get('tab') as AnalyticsTab) || DEFAULTS.tab
    return {
      tab: ['overview', 'funnel', 'attribution'].includes(tab) ? tab : 'overview',
      funnel: (['discovery', 'event', 'application'].includes(searchParams.get('funnel') || '')
        ? searchParams.get('funnel')
        : 'discovery') as FunnelKind,
      programId: searchParams.get('program_id') || '',
      intakeId: searchParams.get('intake_id') || '',
      segmentId: searchParams.get('segment_id') || '',
      campaignId: searchParams.get('campaign_id') || '',
      timeWindow: (['7d', '30d', '90d', 'yoy', 'all'].includes(searchParams.get('window') || '')
        ? searchParams.get('window')
        : '30d') as TimeWindow,
    }
  }, [searchParams])

  const setFilters = (patch: Partial<AnalyticsFilters>) => {
    const next = { ...filters, ...patch }
    setSearchParams(filtersToParams(next), { replace: true })
  }

  return [filters, setFilters]
}

export function filtersToApiParams(f: AnalyticsFilters) {
  return {
    program_id: f.programId || undefined,
    intake_round_id: f.intakeId || undefined,
    segment_id: f.segmentId || undefined,
    campaign_id: f.campaignId || undefined,
    time_window: f.timeWindow,
  }
}
