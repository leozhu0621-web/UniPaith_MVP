import Badge from '../../ui/Badge'
import Card from '../../ui/Card'

function phaseVariant(status: string): 'success' | 'warning' | 'danger' | 'neutral' {
  if (status === 'ok' || status === 'success') return 'success'
  if (status === 'running' || status === 'pending') return 'warning'
  if (status === 'error' || status === 'failed') return 'danger'
  return 'neutral'
}

interface ProcessingTimelineProps {
  snapshot: any
}

export default function ProcessingTimeline({ snapshot }: ProcessingTimelineProps) {
  const engine = snapshot?.processing?.engine ?? {}
  const phases = snapshot?.processing?.autonomy_loop?.last_tick_phase_summary ?? {}
  const stageStatuses = engine?.last_stage_statuses ?? {}
  const stageDurations = engine?.last_stage_durations_ms ?? {}

  const stages = [
    { key: 'ingest', label: 'Ingest' },
    { key: 'feature_embedding', label: 'Feature + Embedding' },
    { key: 'ml', label: 'ML' },
  ]

  const loopPhases = ['detect', 'diagnose', 'remediate', 'verify', 'rollback']

  return (
    <Card className="p-5">
      <h3 className="text-sm font-semibold text-gray-800 mb-3">Live Processing Timeline</h3>
      <div className="space-y-2">
        {stages.map(stage => (
          <div key={stage.key} className="flex items-center justify-between rounded-lg border border-gray-200 px-3 py-2">
            <div className="text-sm text-gray-700">{stage.label}</div>
            <div className="flex items-center gap-2">
              {engine?.current_stage === stage.key && <Badge variant="warning">running</Badge>}
              <Badge variant={phaseVariant(stageStatuses?.[stage.key] ?? 'idle')}>
                {stageStatuses?.[stage.key] ?? 'idle'}
              </Badge>
              <span className="text-xs text-gray-500">{Math.round(stageDurations?.[stage.key] ?? 0)} ms</span>
            </div>
          </div>
        ))}
      </div>

      <div className="mt-4">
        <h4 className="text-xs font-semibold uppercase tracking-wide text-gray-500 mb-2">Autonomy Tick Phases</h4>
        <div className="flex flex-wrap gap-2">
          {loopPhases.map(phase => (
            <Badge
              key={phase}
              variant={phaseVariant(phases?.[phase]?.status ?? 'pending')}
            >
              {phase}: {phases?.[phase]?.status ?? 'pending'}
            </Badge>
          ))}
        </div>
      </div>
    </Card>
  )
}
