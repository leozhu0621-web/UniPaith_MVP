import { useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { ShieldCheck, ShieldAlert, AlertTriangle, ArrowRight } from 'lucide-react'
import Card from '../../../components/ui/Card'
import Badge from '../../../components/ui/Badge'
import Button from '../../../components/ui/Button'
import { getFairnessOverview, type FairnessStatus } from '../../../api/fairness'
import { attributeLabel, severityBadge } from './fairnessUi'

const STATUS_META: Record<
  FairnessStatus,
  { Icon: typeof ShieldCheck; tone: string; label: string; cardClass: string }
> = {
  green: { Icon: ShieldCheck, tone: 'text-success', label: 'All clear', cardClass: '' },
  yellow: {
    Icon: AlertTriangle,
    tone: 'text-warning',
    label: 'Watch',
    cardClass: 'border-warning-soft bg-warning-soft/30',
  },
  red: {
    Icon: ShieldAlert,
    tone: 'text-error',
    label: 'Action needed',
    cardClass: 'border-error/40 bg-error-soft/20',
  },
}

/** Spec 46 §6.4 — the dashboard fairness card: halt status + latest signals +
 *  a link to the full Fairness page. */
export default function FairnessPanel() {
  const navigate = useNavigate()
  const { data, isLoading } = useQuery({
    queryKey: ['fairness-overview'],
    queryFn: getFairnessOverview,
  })

  if (isLoading || !data) return null
  const meta = STATUS_META[data.status] ?? STATUS_META.green
  const { Icon } = meta
  const flagged = data.latest_signals
    .filter(s => s.severity === 'high' || s.severity === 'auto_halt' || s.severity === 'warning')
    .slice(0, 3)

  return (
    <Card className={`p-4 ${meta.cardClass}`}>
      <div className="flex items-center justify-between gap-2 mb-1">
        <div className="flex items-center gap-2">
          <Icon size={16} className={meta.tone} />
          <h3 className="text-sm font-semibold text-foreground">Fairness</h3>
          <Badge variant={data.status === 'red' ? 'error' : data.status === 'yellow' ? 'warning' : 'success'}>
            {meta.label}
          </Badge>
        </div>
        <Button
          size="sm"
          variant="link"
          onClick={() => navigate('/i/admissions?tab=fairness')}
          className="flex items-center gap-1 text-secondary"
        >
          Open <ArrowRight size={13} />
        </Button>
      </div>

      {data.halted_count > 0 ? (
        <p className="text-sm text-error mb-2">
          {data.halted_count} program{data.halted_count !== 1 ? 's' : ''} paused — disparate-impact
          threshold breached two weeks running.
        </p>
      ) : (
        <p className="text-sm text-muted-foreground mb-2">
          Disparate-impact monitored across {data.program_count} program
          {data.program_count !== 1 ? 's' : ''}. Bias is a practice, not a checkbox.
        </p>
      )}

      {flagged.length > 0 && (
        <ul className="space-y-1">
          {flagged.map(s => (
            <li key={s.id} className="flex items-center gap-2 text-xs">
              {severityBadge(s.severity)}
              <span className="text-muted-foreground truncate">
                {s.program_name ? `${s.program_name} · ` : ''}
                {attributeLabel(s.attribute)}
                {s.delta != null ? ` · Δ ${s.delta.toFixed(2)}` : ''}
              </span>
            </li>
          ))}
        </ul>
      )}
    </Card>
  )
}
