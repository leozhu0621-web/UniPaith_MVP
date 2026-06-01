import { useState } from 'react'
import { ChevronDown, ChevronUp } from 'lucide-react'
import Alert from '../../../components/ui/Alert'
import type { DropOffAlert } from '../../../types'

const STAGE_LABELS: Record<string, string> = {
  impression: 'Impressions',
  view: 'Views',
  click: 'Clicks',
  save: 'Saves',
  compare: 'Compare',
  request_info: 'Request info',
  apply_started: 'Apps started',
  submitted: 'Submitted',
}

interface DropOffPanelProps {
  alerts: DropOffAlert[]
}

export default function DropOffPanel({ alerts }: DropOffPanelProps) {
  const [expanded, setExpanded] = useState(false)
  if (!alerts.length) return null

  const top = alerts[0]
  const fromLabel = STAGE_LABELS[top.from_stage] || top.from_stage
  const toLabel = STAGE_LABELS[top.to_stage] || top.to_stage
  const dropPct = Math.round(top.drop_pct * 100)

  return (
    <Alert
      variant="warning"
      title={`Biggest drop: ${fromLabel} → ${toLabel} (${dropPct}% drop).`}
      action={(
        <button
          type="button"
          className="inline-flex items-center gap-1 text-sm font-medium text-warning hover:underline"
          onClick={() => setExpanded(v => !v)}
        >
          Investigate
          {expanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
        </button>
      )}
    >
      {expanded ? (
        <p className="text-sm mt-1">{top.hint}</p>
      ) : null}
    </Alert>
  )
}
