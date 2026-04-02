import { useMemo } from 'react'
import Card from '../../ui/Card'
import Badge from '../../ui/Badge'
import Skeleton from '../../ui/Skeleton'
import StatusBar from '../ops/StatusBar'
import ProcessingTimeline from '../ops/ProcessingTimeline'
import type { ArchitectureRunTrace, ArchitectureStageTrace } from '../../../types'

const STAGE_ORDER = [
  'ingest', 'understand', 'match', 'outcome', 'evaluation', 'training', 'promotion',
]

function statusVariant(status: string | undefined): 'success' | 'warning' | 'danger' | 'neutral' {
  if (!status) return 'neutral'
  if (['ok', 'healthy', 'ready', 'running'].includes(status)) return 'success'
  if (['warning', 'degraded', 'pending'].includes(status)) return 'warning'
  if (['error', 'critical', 'failed'].includes(status)) return 'danger'
  return 'neutral'
}

function formatDurationMs(durationMs: number | null | undefined): string {
  if (durationMs == null) return '—'
  if (durationMs < 1000) return `${Math.round(durationMs)} ms`
  return `${(durationMs / 1000).toFixed(2)} s`
}

interface AuditEvent {
  event_type: string
  timestamp: string
  payload?: { status?: string }
}

interface MonitorSectionProps {
  snapshot: any
  sloData: any
  architectureTrace: any
  mlKpis: any
  isLoading: boolean
}

export default function MonitorSection({ snapshot, sloData, architectureTrace, mlKpis, isLoading }: MonitorSectionProps) {
  const reliability = snapshot?.reliability ?? {}
  const crawler = snapshot?.crawler ?? {}
  const ml = snapshot?.ml ?? {}
  const latestRuns = snapshot?.processing?.latest_runs ?? {}
  const schedulerOn = snapshot?.status?.scheduler?.self_driving_enabled
  const latestEngineRun = snapshot?.processing?.engine?.last_run_completed_at
  const auditPreview: AuditEvent[] = Array.isArray(snapshot?.audit_preview) ? snapshot.audit_preview : []

  const stageById = useMemo(() => {
    const stages: ArchitectureStageTrace[] = Array.isArray(architectureTrace?.stages) ? architectureTrace.stages : []
    return new Map(stages.map((stage) => [stage.stage_id, stage]))
  }, [architectureTrace?.stages])

  const orderedStages = STAGE_ORDER
    .map(id => stageById.get(id))
    .filter((stage): stage is ArchitectureStageTrace => Boolean(stage))

  const traceRuns: ArchitectureRunTrace[] = Array.isArray(architectureTrace?.runs) ? architectureTrace.runs : []

  if (isLoading) {
    return <div className="space-y-4"><Skeleton className="h-16" /><Skeleton className="h-44" /><Skeleton className="h-56" /></div>
  }

  return (
    <div className="space-y-6">
      <StatusBar snapshot={snapshot} />

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        <div className="xl:col-span-2 space-y-6">
          <ProcessingTimeline snapshot={snapshot} />

          <Card className="p-5">
            <h3 className="text-sm font-semibold text-gray-800 mb-3">Architecture Stage Health</h3>
            <div className="space-y-2">
              {orderedStages.map((stage) => (
                <div key={stage.stage_id} className="border border-gray-200 rounded-lg p-3">
                  <div className="flex items-center justify-between gap-2">
                    <div>
                      <p className="text-sm font-medium text-gray-900">{stage.label}</p>
                      <p className="text-xs text-gray-500">{stage.source}</p>
                    </div>
                    <Badge variant={statusVariant(stage.status)}>{stage.status}</Badge>
                  </div>
                  <div className="mt-2 grid grid-cols-2 gap-2 text-xs text-gray-600">
                    <p>Last run: {stage.last_run_at ?? '—'}</p>
                    <p>Duration: {formatDurationMs(stage.duration_ms)}</p>
                  </div>
                  {stage.error && <p className="mt-2 text-xs text-red-600">Error: {stage.error}</p>}
                  <div className="mt-2 flex flex-wrap gap-2">
                    {Object.entries(stage.counts || {})
                      .filter(([, value]) => value !== null && value !== undefined && value !== '')
                      .slice(0, 4)
                      .map(([key, value]) => (
                        <span key={key} className="text-[11px] text-gray-600 bg-gray-100 rounded px-2 py-1">
                          {key}: {String(value)}
                        </span>
                      ))}
                  </div>
                </div>
              ))}
            </div>
          </Card>

          <Card className="p-5">
            <h3 className="text-sm font-semibold text-gray-800 mb-3">Recent Run Traces</h3>
            {traceRuns.length === 0 ? (
              <p className="text-sm text-gray-500">No recent run traces yet.</p>
            ) : (
              <div className="space-y-2 max-h-96 overflow-auto">
                {traceRuns.map((run) => (
                  <div key={`${run.run_type}-${run.run_id}`} className="border border-gray-200 rounded-lg p-3">
                    <div className="flex items-center justify-between gap-2">
                      <p className="text-sm font-medium text-gray-900">{run.run_type} · {run.stage_id}</p>
                      <Badge variant={statusVariant(run.status)}>{run.status}</Badge>
                    </div>
                    <div className="mt-2 grid grid-cols-2 gap-2 text-xs text-gray-600">
                      <p>Start: {run.started_at ?? '—'}</p>
                      <p>End: {run.completed_at ?? '—'}</p>
                      <p>Duration: {formatDurationMs(run.duration_ms)}</p>
                      <p>Mode: {run.mode ?? '—'}</p>
                    </div>
                    {run.trigger_reason && <p className="mt-2 text-xs text-gray-600">Trigger: {run.trigger_reason}</p>}
                  </div>
                ))}
              </div>
            )}
          </Card>

          <Card className="p-5">
            <h3 className="text-sm font-semibold text-gray-800 mb-3">Incidents & Audit Feed</h3>
            <div className="space-y-2 max-h-80 overflow-auto">
              {auditPreview.length === 0 ? (
                <p className="text-sm text-gray-500">No recent incidents yet.</p>
              ) : (
                auditPreview.slice().reverse().map((event, idx) => (
                  <div key={`${event.timestamp}-${idx}`} className="border border-gray-200 rounded-lg p-3">
                    <div className="flex items-center justify-between">
                      <p className="text-sm font-medium text-gray-900">{event.event_type}</p>
                      <p className="text-xs text-gray-500">{event.timestamp}</p>
                    </div>
                    <p className="text-xs text-gray-600 mt-1">Status: {event.payload?.status ?? 'unknown'}</p>
                  </div>
                ))
              )}
            </div>
          </Card>
        </div>

        <div className="space-y-6">
          <Card className="p-5">
            <h3 className="text-sm font-semibold text-gray-800 mb-3">Reliability & Speed</h3>
            <div className="space-y-2">
              <div className="flex items-center justify-between text-sm">
                <span className="text-gray-600">LLM p95</span>
                <span className="font-medium">{sloData?.llm?.p95_ms ?? 0} ms</span>
              </div>
              <div className="flex items-center justify-between text-sm">
                <span className="text-gray-600">Embedding p95</span>
                <span className="font-medium">{sloData?.embedding?.p95_ms ?? 0} ms</span>
              </div>
              <div className="flex items-center justify-between text-sm">
                <span className="text-gray-600">Self-driving tick p95</span>
                <span className="font-medium">{sloData?.self_driving_tick?.p95_ms ?? 0} ms</span>
              </div>
              <div className="border-t pt-2 mt-2 space-y-1 text-xs text-gray-500">
                <p>Crawl failures: {reliability?.crawl_failures_total ?? 0}</p>
                <p>Training failures: {reliability?.training_failures_total ?? 0}</p>
                <p>Consecutive autonomy failures: {reliability?.consecutive_autonomy_failures ?? 0}</p>
                <p>Scheduler: {schedulerOn ? 'enabled' : 'disabled'}</p>
                <p>Runtime provider: {mlKpis?.runtime_provider ?? '—'} ({mlKpis?.runtime_mode ?? '—'})</p>
                <p>Promotion hit-rate (7d): {mlKpis?.promotion_hit_rate_7d ?? 0}</p>
                <p>Outcome → Eval lag (hrs): {mlKpis?.hours_outcome_to_eval_latest ?? '—'}</p>
                <p>Eval → Train lag (hrs): {mlKpis?.hours_eval_to_training_latest ?? '—'}</p>
              </div>
            </div>
          </Card>

          <Card className="p-5">
            <h3 className="text-sm font-semibold text-gray-800 mb-3">Crawler Processing</h3>
            <div className="space-y-2 text-sm">
              <p>Active sources: <span className="font-medium">{crawler?.active_sources ?? 0}</span></p>
              <p>Active jobs: <span className="font-medium">{crawler?.active_jobs ?? 0}</span></p>
              <p>Pending review: <span className="font-medium">{crawler?.pending_review_items ?? 0}</span></p>
              <div className="pt-1">
                <Badge variant={statusVariant(crawler?.latest_crawl?.status)}>
                  Last crawl {crawler?.latest_crawl?.status ?? 'none'}
                </Badge>
              </div>
            </div>
          </Card>

          <Card className="p-5">
            <h3 className="text-sm font-semibold text-gray-800 mb-3">ML Processing</h3>
            <div className="space-y-2 text-sm">
              <p>Active model: <span className="font-medium">{ml?.active_model?.model_version ?? 'none'}</span></p>
              <p>Training: <span className="font-medium">{latestRuns?.training?.status ?? 'none'}</span></p>
              <p>Evaluation: <span className="font-medium">{latestRuns?.evaluation?.id ? 'available' : 'none'}</span></p>
              <p>Drift: <span className="font-medium">{latestRuns?.drift?.drift_detected ? 'detected' : 'clear'}</span></p>
              <p>Last engine run: <span className="font-medium">{latestEngineRun ?? 'none'}</span></p>
            </div>
          </Card>
        </div>
      </div>
    </div>
  )
}
