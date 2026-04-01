import { useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import Button from '../../components/ui/Button'
import Card from '../../components/ui/Card'
import Badge from '../../components/ui/Badge'
import Skeleton from '../../components/ui/Skeleton'
import { useAdminOps } from '../../hooks/useAdminOps'
import StatusBar from '../../components/admin/ops/StatusBar'
import ProcessingTimeline from '../../components/admin/ops/ProcessingTimeline'
import ControlPanel from '../../components/admin/ops/ControlPanel'
import { useToastStore } from '../../stores/toast-store'

const UNLOCK_TTL_MS = 5 * 60 * 1000

function statusVariant(status: string | undefined): 'success' | 'warning' | 'danger' | 'neutral' {
  if (!status) return 'neutral'
  if (['ok', 'healthy', 'ready', 'running'].includes(status)) return 'success'
  if (['warning', 'degraded', 'pending'].includes(status)) return 'warning'
  if (['error', 'critical', 'failed'].includes(status)) return 'danger'
  return 'neutral'
}

export default function AdminOpsCenterPage() {
  const navigate = useNavigate()
  const addToast = useToastStore(s => s.addToast)
  const {
    snapshotQ,
    sloQ,
    policyMut,
    runLoopMut,
    runEngineGraphMut,
    runCrawlAllMut,
    runMLCycleMut,
    triggerTrainingMut,
    driftCheckMut,
    invalidateOps,
  } = useAdminOps()

  const [unlockUntil, setUnlockUntil] = useState<number>(0)
  const [nowMs, setNowMs] = useState<number>(Date.now())
  const locked = nowMs >= unlockUntil
  const unlockExpiresInSec = Math.max(0, Math.ceil((unlockUntil - nowMs) / 1000))

  useEffect(() => {
    const id = window.setInterval(() => setNowMs(Date.now()), 1000)
    return () => window.clearInterval(id)
  }, [])

  const snapshot = snapshotQ.data
  const policy = snapshot?.status?.policy ?? {}
  const reliability = snapshot?.reliability ?? {}
  const crawler = snapshot?.crawler ?? {}
  const ml = snapshot?.ml ?? {}
  const latestRuns = snapshot?.processing?.latest_runs ?? {}
  const auditPreview = Array.isArray(snapshot?.audit_preview) ? snapshot.audit_preview : []
  const schedulerOn = snapshot?.status?.scheduler?.self_driving_enabled
  const latestTick = snapshot?.processing?.autonomy_loop?.last_tick_at
  const latestEngineRun = snapshot?.processing?.engine?.last_run_completed_at

  const hasProcessingHistory = Boolean(
    latestTick
    || latestEngineRun
    || (crawler?.active_sources ?? 0) > 0
    || (crawler?.active_jobs ?? 0) > 0
    || ml?.active_model?.model_version
    || latestRuns?.training?.id
    || latestRuns?.evaluation?.id
    || latestRuns?.drift?.id
  )

  const anyMutationBusy = useMemo(
    () =>
      policyMut.isPending
      || runLoopMut.isPending
      || runEngineGraphMut.isPending
      || runCrawlAllMut.isPending
      || runMLCycleMut.isPending
      || triggerTrainingMut.isPending
      || driftCheckMut.isPending,
    [
      policyMut.isPending,
      runLoopMut.isPending,
      runEngineGraphMut.isPending,
      runCrawlAllMut.isPending,
      runMLCycleMut.isPending,
      triggerTrainingMut.isPending,
      driftCheckMut.isPending,
    ]
  )

  const ensureUnlocked = () => {
    if (!locked) return true
    addToast('Controls are locked. Unlock first.', 'warning')
    return false
  }

  const safePolicyToggle = async (
    patch: { autonomy_enabled?: boolean; auto_fix_enabled?: boolean; emergency_stop?: boolean },
    confirmMessage?: string
  ) => {
    if (!ensureUnlocked()) return
    if (confirmMessage && !window.confirm(confirmMessage)) return
    try {
      await policyMut.mutateAsync(patch)
      addToast('Policy updated', 'success')
    } catch (e: any) {
      addToast(e?.message ?? 'Failed to update policy', 'error')
    }
  }

  const runAction = async (
    name: string,
    fn: () => Promise<any>,
    confirmMessage?: string
  ) => {
    if (!ensureUnlocked()) return
    if (confirmMessage && !window.confirm(confirmMessage)) return
    try {
      await fn()
      addToast(`${name} started`, 'success')
      await invalidateOps()
    } catch (e: any) {
      addToast(e?.message ?? `${name} failed`, 'error')
    }
  }

  if (snapshotQ.isLoading) {
    return (
      <div className="p-8 space-y-4">
        <Skeleton className="h-16" />
        <Skeleton className="h-44" />
        <Skeleton className="h-56" />
      </div>
    )
  }

  return (
    <div className="p-8 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">AI Operations Center</h1>
          <p className="text-sm text-gray-500">Unified live processing and controls for AI engine, crawler, and ML.</p>
          <p className="text-xs text-gray-400 mt-1">Last updated: {snapshot?.timestamp ?? '—'}</p>
        </div>
        <Button variant="secondary" onClick={() => { snapshotQ.refetch(); sloQ.refetch() }} disabled={snapshotQ.isFetching}>
          {snapshotQ.isFetching ? 'Refreshing...' : 'Refresh'}
        </Button>
      </div>

      <StatusBar snapshot={snapshot} />

      {!hasProcessingHistory && (
        <Card className="p-5 bg-blue-50 border-blue-200">
          <h3 className="text-sm font-semibold text-blue-900 mb-2">What to do first</h3>
          <div className="text-sm text-blue-800 space-y-1">
            <p>1) Click <strong>Unlock Controls (5 min)</strong>.</p>
            <p>2) Run <strong>Crawl All</strong> to ingest data.</p>
            <p>3) Run <strong>ML Full Cycle</strong> to train/evaluate.</p>
            <p>4) Enable <strong>Autonomy</strong> + <strong>Auto-Fix</strong> when ready.</p>
            {!schedulerOn && (
              <p className="pt-1">
                Scheduler is currently off. You can still run actions manually from this page.
              </p>
            )}
          </div>
        </Card>
      )}

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        <div className="xl:col-span-2 space-y-6">
          <ProcessingTimeline snapshot={snapshot} />
          <ControlPanel
            locked={locked}
            unlockExpiresInSec={unlockExpiresInSec}
            policy={policy}
            busy={anyMutationBusy}
            onUnlock={() => setUnlockUntil(Date.now() + UNLOCK_TTL_MS)}
            onLockNow={() => setUnlockUntil(0)}
            onToggleAutonomy={() =>
              safePolicyToggle({ autonomy_enabled: !policy?.autonomy_enabled }, 'Toggle autonomy mode?')
            }
            onToggleAutoFix={() =>
              safePolicyToggle({ auto_fix_enabled: !policy?.auto_fix_enabled }, 'Toggle auto-fix mode?')
            }
            onToggleEmergencyStop={() =>
              safePolicyToggle(
                { emergency_stop: !policy?.emergency_stop },
                policy?.emergency_stop ? 'Clear emergency stop?' : 'Enable emergency stop now?'
              )
            }
            onRunLoop={() => runAction('Self-driving tick', () => runLoopMut.mutateAsync())}
            onRunEngineGraph={() => runAction('Full engine graph', () => runEngineGraphMut.mutateAsync())}
            onRunCrawlAll={() => runAction('Crawl all', () => runCrawlAllMut.mutateAsync())}
            onRunMLCycle={() => runAction('ML full cycle', () => runMLCycleMut.mutateAsync())}
            onTriggerTraining={() => runAction('Training trigger', () => triggerTrainingMut.mutateAsync())}
            onDriftCheck={() => runAction('Drift check', () => driftCheckMut.mutateAsync())}
          />

          <Card className="p-5">
            <h3 className="text-sm font-semibold text-gray-800 mb-3">Incidents & Audit Feed</h3>
            <div className="space-y-2 max-h-80 overflow-auto">
              {auditPreview.length === 0 ? (
                <p className="text-sm text-gray-500">No recent incidents yet.</p>
              ) : (
                auditPreview.slice().reverse().map((event: any, idx: number) => (
                  <div key={`${event.timestamp}-${idx}`} className="border border-gray-200 rounded-lg p-3">
                    <div className="flex items-center justify-between">
                      <p className="text-sm font-medium text-gray-900">{event.event_type}</p>
                      <p className="text-xs text-gray-500">{event.timestamp}</p>
                    </div>
                    <p className="text-xs text-gray-600 mt-1">
                      Status: {event.payload?.status ?? 'unknown'}
                    </p>
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
                <span className="font-medium">{sloQ.data?.llm?.p95_ms ?? 0} ms</span>
              </div>
              <div className="flex items-center justify-between text-sm">
                <span className="text-gray-600">Embedding p95</span>
                <span className="font-medium">{sloQ.data?.embedding?.p95_ms ?? 0} ms</span>
              </div>
              <div className="flex items-center justify-between text-sm">
                <span className="text-gray-600">Self-driving tick p95</span>
                <span className="font-medium">{sloQ.data?.self_driving_tick?.p95_ms ?? 0} ms</span>
              </div>
              <div className="border-t pt-2 mt-2 space-y-1 text-xs text-gray-500">
                <p>Crawl failures: {reliability?.crawl_failures_total ?? 0}</p>
                <p>Training failures: {reliability?.training_failures_total ?? 0}</p>
                <p>Consecutive autonomy failures: {reliability?.consecutive_autonomy_failures ?? 0}</p>
                <p>Scheduler: {schedulerOn ? 'enabled' : 'disabled'}</p>
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

          <Card className="p-5">
            <h3 className="text-sm font-semibold text-gray-800 mb-3">Quick Drilldowns</h3>
            <div className="grid grid-cols-2 gap-2">
              <Button variant="secondary" size="sm" onClick={() => navigate('/admin/crawler')}>Crawler</Button>
              <Button variant="secondary" size="sm" onClick={() => navigate('/admin/ml')}>ML</Button>
              <Button variant="secondary" size="sm" onClick={() => navigate('/admin/users')}>Users</Button>
              <Button variant="secondary" size="sm" onClick={() => navigate('/admin/system')}>System</Button>
            </div>
          </Card>
        </div>
      </div>
    </div>
  )
}
