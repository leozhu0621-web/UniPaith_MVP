import { useState } from 'react'
import Button from '../../components/ui/Button'
import Card from '../../components/ui/Card'
import Skeleton from '../../components/ui/Skeleton'
import { useAdminOps } from '../../hooks/useAdminOps'
import PipelineDashboard from '../../components/admin/pipeline/PipelineDashboard'

interface AuditEvent {
  event_type: string
  timestamp: string
  payload?: {
    status?: string
  }
}

export default function AdminOpsCenterPage() {
  const { snapshotQ, sloQ, mlKpisQ } = useAdminOps()
  const [showDetails, setShowDetails] = useState(false)

  const snapshot = snapshotQ.data
  const reliability = snapshot?.reliability ?? {}
  const ml = snapshot?.ml ?? {}
  const latestRuns = snapshot?.processing?.latest_runs ?? {}
  const schedulerOn = snapshot?.status?.scheduler?.self_driving_enabled
  const mlKpis = mlKpisQ.data
  const auditPreview: AuditEvent[] = Array.isArray(snapshot?.audit_preview)
    ? snapshot.audit_preview
    : []

  if (snapshotQ.isLoading) {
    return (
      <div className="p-8 space-y-4">
        <Skeleton className="h-12" />
        <Skeleton className="h-16" />
        <Skeleton className="h-48" />
      </div>
    )
  }

  return (
    <div className="p-8 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">
            AI Operations Center
          </h1>
          <p className="text-sm text-gray-500">
            Continuous pipeline: crawl, extract, train — 24/7.
          </p>
        </div>
        <Button
          variant="secondary"
          size="sm"
          onClick={() => snapshotQ.refetch()}
          disabled={snapshotQ.isFetching}
        >
          {snapshotQ.isFetching ? 'Refreshing...' : 'Refresh'}
        </Button>
      </div>

      <PipelineDashboard />

      {/* Collapsible details section */}
      <Card className="p-4">
        <button
          onClick={() => setShowDetails(!showDetails)}
          className="text-sm text-gray-500 hover:text-gray-700 font-medium flex items-center gap-1"
        >
          <span className="text-xs">{showDetails ? '▼' : '▶'}</span>
          System Details
        </button>

        {showDetails && (
          <div className="mt-4 grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Reliability */}
            <div className="space-y-2">
              <h4 className="text-xs font-semibold text-gray-700 uppercase tracking-wide">
                Reliability
              </h4>
              <div className="space-y-1 text-xs text-gray-600">
                <div className="flex justify-between">
                  <span>LLM p95</span>
                  <span className="font-mono">{sloQ.data?.llm?.p95_ms ?? 0} ms</span>
                </div>
                <div className="flex justify-between">
                  <span>Embedding p95</span>
                  <span className="font-mono">{sloQ.data?.embedding?.p95_ms ?? 0} ms</span>
                </div>
                <div className="flex justify-between">
                  <span>Crawl failures</span>
                  <span className="font-mono">{reliability?.crawl_failures_total ?? 0}</span>
                </div>
                <div className="flex justify-between">
                  <span>Training failures</span>
                  <span className="font-mono">{reliability?.training_failures_total ?? 0}</span>
                </div>
                <div className="flex justify-between">
                  <span>Scheduler</span>
                  <span className="font-mono">{schedulerOn ? 'on' : 'off'}</span>
                </div>
              </div>
            </div>

            {/* ML info */}
            <div className="space-y-2">
              <h4 className="text-xs font-semibold text-gray-700 uppercase tracking-wide">
                ML Status
              </h4>
              <div className="space-y-1 text-xs text-gray-600">
                <div className="flex justify-between">
                  <span>Active model</span>
                  <span className="font-mono">{ml?.active_model?.model_version ?? 'none'}</span>
                </div>
                <div className="flex justify-between">
                  <span>Last training</span>
                  <span className="font-mono">{latestRuns?.training?.status ?? 'none'}</span>
                </div>
                <div className="flex justify-between">
                  <span>Last evaluation</span>
                  <span className="font-mono">{latestRuns?.evaluation?.id ? 'done' : 'none'}</span>
                </div>
                <div className="flex justify-between">
                  <span>Provider</span>
                  <span className="font-mono">{mlKpis?.runtime_provider ?? '—'}</span>
                </div>
                <div className="flex justify-between">
                  <span>Outcome-to-eval lag</span>
                  <span className="font-mono">{mlKpis?.hours_outcome_to_eval_latest ?? '—'} hrs</span>
                </div>
              </div>
            </div>

            {/* Audit feed */}
            <div className="space-y-2">
              <h4 className="text-xs font-semibold text-gray-700 uppercase tracking-wide">
                Recent Events
              </h4>
              <div className="space-y-1 max-h-40 overflow-auto">
                {auditPreview.length === 0 ? (
                  <p className="text-xs text-gray-400">No events yet.</p>
                ) : (
                  auditPreview.slice(-8).reverse().map((event, idx) => (
                    <div key={`${event.timestamp}-${idx}`} className="text-xs text-gray-600 flex justify-between">
                      <span className="truncate max-w-[150px]">{event.event_type}</span>
                      <span className="text-gray-400 font-mono text-[10px]">
                        {event.payload?.status ?? ''}
                      </span>
                    </div>
                  ))
                )}
              </div>
            </div>
          </div>
        )}
      </Card>

      {/* Quick nav */}
      <div className="flex gap-2">
        <Button variant="secondary" size="sm" onClick={() => window.location.assign('/admin/crawler')}>Crawler</Button>
        <Button variant="secondary" size="sm" onClick={() => window.location.assign('/admin/ml')}>ML</Button>
        <Button variant="secondary" size="sm" onClick={() => window.location.assign('/admin/knowledge')}>Knowledge</Button>
        <Button variant="secondary" size="sm" onClick={() => window.location.assign('/admin/users')}>Users</Button>
        <Button variant="secondary" size="sm" onClick={() => window.location.assign('/admin/system')}>System</Button>
      </div>
    </div>
  )
}
