import { useEffect, useMemo, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import Button from '../../components/ui/Button'
import Card from '../../components/ui/Card'
import Skeleton from '../../components/ui/Skeleton'
import { useAdminOps } from '../../hooks/useAdminOps'
import ControlPanel from '../../components/admin/ops/ControlPanel'
import MonitorSection from '../../components/admin/ai-center/MonitorSection'
import MaintenanceSection from '../../components/admin/ai-center/MaintenanceSection'
import AdminCrawlerPage from './AdminCrawlerPage'
import AdminMLPage from './AdminMLPage'
import AdminKnowledgePage from './AdminKnowledgePage'
import { useToastStore } from '../../stores/toast-store'

const UNLOCK_TTL_MS = 5 * 60 * 1000

const TABS = [
  { id: 'monitor', label: 'Monitor' },
  { id: 'controls', label: 'Controls' },
  { id: 'pipeline', label: 'Pipeline' },
  { id: 'learning', label: 'Learning' },
  { id: 'knowledge', label: 'Knowledge' },
  { id: 'maintenance', label: 'Maintenance' },
] as const

type TabId = (typeof TABS)[number]['id']

interface OpsError { message?: string }

export default function AdminAICenterPage() {
  const [searchParams, setSearchParams] = useSearchParams()
  const rawTab = searchParams.get('tab')
  const activeTab: TabId = TABS.some(t => t.id === rawTab) ? (rawTab as TabId) : 'monitor'

  const setTab = (tab: TabId) => {
    setSearchParams({ tab }, { replace: true })
  }

  const addToast = useToastStore(s => s.addToast)
  const {
    snapshotQ, sloQ, architectureTraceQ, mlKpisQ,
    policyMut, runLoopMut, runEngineGraphMut, runCrawlAllMut,
    runMLCycleMut, triggerTrainingMut, driftCheckMut, invalidateOps,
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

  const anyMutationBusy = useMemo(
    () =>
      policyMut.isPending || runLoopMut.isPending || runEngineGraphMut.isPending
      || runCrawlAllMut.isPending || runMLCycleMut.isPending
      || triggerTrainingMut.isPending || driftCheckMut.isPending,
    [policyMut.isPending, runLoopMut.isPending, runEngineGraphMut.isPending,
      runCrawlAllMut.isPending, runMLCycleMut.isPending,
      triggerTrainingMut.isPending, driftCheckMut.isPending]
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
    } catch (e: unknown) {
      addToast((e as OpsError)?.message ?? 'Failed to update policy', 'error')
    }
  }

  const runAction = async (name: string, fn: () => Promise<unknown>) => {
    if (!ensureUnlocked()) return
    try {
      await fn()
      addToast(`${name} started`, 'success')
      await invalidateOps()
      await Promise.all([snapshotQ.refetch(), sloQ.refetch(), architectureTraceQ.refetch(), mlKpisQ.refetch()])
    } catch (e: unknown) {
      addToast((e as OpsError)?.message ?? `${name} failed`, 'error')
    }
  }

  const schedulerOn = snapshot?.status?.scheduler?.self_driving_enabled
  const latestTick = snapshot?.processing?.autonomy_loop?.last_tick_at
  const latestEngineRun = snapshot?.processing?.engine?.last_run_completed_at
  const crawler = snapshot?.crawler ?? {}
  const ml = snapshot?.ml ?? {}
  const latestRuns = snapshot?.processing?.latest_runs ?? {}

  const hasProcessingHistory = Boolean(
    latestTick || latestEngineRun
    || (crawler?.active_sources ?? 0) > 0 || (crawler?.active_jobs ?? 0) > 0
    || ml?.active_model?.model_version
    || latestRuns?.training?.id || latestRuns?.evaluation?.id || latestRuns?.drift?.id
  )

  if (snapshotQ.isLoading && activeTab === 'monitor') {
    return (
      <div className="p-8 space-y-4">
        <Skeleton className="h-16" /><Skeleton className="h-44" /><Skeleton className="h-56" />
      </div>
    )
  }

  return (
    <div className="p-8 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">AI Center</h1>
          <p className="text-sm text-gray-500">
            Unified monitoring, controls, data pipeline, learning, knowledge, and maintenance.
          </p>
          {activeTab === 'monitor' && (
            <p className="text-xs text-gray-400 mt-1">Last updated: {snapshot?.timestamp ?? '—'}</p>
          )}
        </div>
        {(activeTab === 'monitor' || activeTab === 'controls') && (
          <Button variant="secondary" onClick={() => { snapshotQ.refetch(); sloQ.refetch() }} disabled={snapshotQ.isFetching}>
            {snapshotQ.isFetching ? 'Refreshing...' : 'Refresh'}
          </Button>
        )}
      </div>

      {/* Tab bar */}
      <Card className="p-1 flex gap-1 flex-wrap">
        {TABS.map(tab => (
          <button
            key={tab.id}
            onClick={() => setTab(tab.id)}
            className={`px-4 py-2 text-sm font-medium rounded-lg transition-colors ${
              activeTab === tab.id
                ? 'bg-indigo-600 text-white'
                : 'text-gray-600 hover:bg-gray-100'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </Card>

      {/* Getting-started hint on Monitor tab when engine is fresh */}
      {activeTab === 'monitor' && !hasProcessingHistory && (
        <Card className="p-5 bg-blue-50 border-blue-200">
          <h3 className="text-sm font-semibold text-blue-900 mb-2">What to do first</h3>
          <div className="text-sm text-blue-800 space-y-1">
            <p>1) Go to <button onClick={() => setTab('controls')} className="font-semibold underline">Controls</button> and unlock.</p>
            <p>2) Run <strong>Crawl All</strong> to ingest data.</p>
            <p>3) Run <strong>ML Full Cycle</strong> to train/evaluate.</p>
            <p>4) Enable <strong>Autonomy</strong> + <strong>Auto-Fix</strong> when ready.</p>
            {!schedulerOn && <p className="pt-1">Scheduler is currently off. You can still run actions manually.</p>}
          </div>
        </Card>
      )}

      {/* === Monitor Tab === */}
      {activeTab === 'monitor' && (
        <MonitorSection
          snapshot={snapshot}
          sloData={sloQ.data}
          architectureTrace={architectureTraceQ.data}
          mlKpis={mlKpisQ.data}
          isLoading={snapshotQ.isLoading}
        />
      )}

      {/* === Controls Tab === */}
      {activeTab === 'controls' && (
        <ControlPanel
          locked={locked}
          unlockExpiresInSec={unlockExpiresInSec}
          policy={policy}
          busy={anyMutationBusy}
          onUnlock={() => setUnlockUntil(Date.now() + UNLOCK_TTL_MS)}
          onLockNow={() => setUnlockUntil(0)}
          onToggleAutonomy={() => safePolicyToggle({ autonomy_enabled: !policy?.autonomy_enabled }, 'Toggle autonomy mode?')}
          onToggleAutoFix={() => safePolicyToggle({ auto_fix_enabled: !policy?.auto_fix_enabled }, 'Toggle auto-fix mode?')}
          onToggleEmergencyStop={() => safePolicyToggle(
            { emergency_stop: !policy?.emergency_stop },
            policy?.emergency_stop ? 'Clear emergency stop?' : 'Enable emergency stop now?'
          )}
          onRunLoop={() => runAction('Self-driving tick', () => runLoopMut.mutateAsync())}
          onRunEngineGraph={() => runAction('Full engine graph', () => runEngineGraphMut.mutateAsync())}
          onRunCrawlAll={() => runAction('Crawl all', () => runCrawlAllMut.mutateAsync())}
          onRunMLCycle={() => runAction('ML full cycle', () => runMLCycleMut.mutateAsync())}
          onTriggerTraining={() => runAction('Training trigger', () => triggerTrainingMut.mutateAsync())}
          onDriftCheck={() => runAction('Drift check', () => driftCheckMut.mutateAsync())}
        />
      )}

      {/* === Pipeline (Crawler) Tab === */}
      {activeTab === 'pipeline' && <AdminCrawlerPage />}

      {/* === Learning (ML) Tab === */}
      {activeTab === 'learning' && <AdminMLPage />}

      {/* === Knowledge Tab === */}
      {activeTab === 'knowledge' && <AdminKnowledgePage />}

      {/* === Maintenance Tab === */}
      {activeTab === 'maintenance' && <MaintenanceSection />}
    </div>
  )
}
