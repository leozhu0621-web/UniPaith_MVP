import { useQuery } from '@tanstack/react-query'
import Select from '../../../components/ui/Select'
import {
  getCampaigns,
  getInstitutionPrograms,
  getIntakeRounds,
  getSegments,
} from '../../../api/institutions'
import type { AnalyticsFilters } from '../../../types'
import { TIME_WINDOWS } from './constants'

interface Props {
  filters: AnalyticsFilters
  onChange: (patch: Partial<AnalyticsFilters>) => void
  /** Hide the segment + campaign selects (e.g. tabs that don't break down by them). */
  compact?: boolean
}

export default function FilterBar({ filters, onChange, compact = false }: Props) {
  const programsQ = useQuery({ queryKey: ['inst-programs'], queryFn: getInstitutionPrograms })
  const segmentsQ = useQuery({ queryKey: ['inst-segments'], queryFn: getSegments, enabled: !compact })
  const campaignsQ = useQuery({
    queryKey: ['inst-campaigns-all'],
    queryFn: () => getCampaigns(),
    enabled: !compact,
  })
  const intakeQ = useQuery({
    queryKey: ['inst-intakes', filters.program_id],
    queryFn: () => getIntakeRounds(filters.program_id!),
    enabled: Boolean(filters.program_id),
  })

  const programOptions = [
    { value: '', label: 'All programs' },
    ...(programsQ.data ?? []).map(p => ({ value: p.id, label: p.program_name })),
  ]
  const intakeOptions = [
    { value: '', label: 'All intakes' },
    ...(intakeQ.data ?? []).map(r => ({ value: r.id, label: r.round_name })),
  ]
  const segmentOptions = [
    { value: '', label: 'All segments' },
    ...(segmentsQ.data ?? []).map(s => ({ value: s.id, label: s.segment_name })),
  ]
  const campaignOptions = [
    { value: '', label: 'All campaigns' },
    ...(campaignsQ.data ?? []).map(c => ({ value: c.id, label: c.name })),
  ]

  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
      <Select
        uiSize="sm"
        aria-label="Time window"
        options={TIME_WINDOWS}
        value={filters.time_window ?? '30d'}
        onChange={e => onChange({ time_window: e.target.value })}
      />
      <Select
        uiSize="sm"
        aria-label="Program"
        options={programOptions}
        value={filters.program_id ?? ''}
        onChange={e => onChange({ program_id: e.target.value || undefined, intake_id: undefined })}
      />
      <Select
        uiSize="sm"
        aria-label="Intake round"
        options={intakeOptions}
        value={filters.intake_id ?? ''}
        disabled={!filters.program_id}
        onChange={e => onChange({ intake_id: e.target.value || undefined })}
      />
      {!compact && (
        <Select
          uiSize="sm"
          aria-label="Segment"
          options={segmentOptions}
          value={filters.segment_id ?? ''}
          onChange={e => onChange({ segment_id: e.target.value || undefined })}
        />
      )}
      {!compact && (
        <Select
          uiSize="sm"
          aria-label="Campaign"
          options={campaignOptions}
          value={filters.campaign_id ?? ''}
          onChange={e => onChange({ campaign_id: e.target.value || undefined })}
        />
      )}
    </div>
  )
}
