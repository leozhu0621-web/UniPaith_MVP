import { useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  getMLModels, getMLEvaluations, getMLTrainingRuns, getDriftSnapshots,
  getOutcomeStats, runMLCycle, runMLEvaluate, runDriftCheck,
  backfillOutcomes, triggerTraining, promoteModel, rollbackModel,
  getKnowledgeStatus, getRecentKnowledgeDocuments, getKnowledgeFrontier,
  getKnowledgeDirectives, getAdvisorPersona, updateAdvisorPersona,
  triggerKnowledgeTick, triggerKnowledgeDiscovery, pauseKnowledgeEngine,
  resumeKnowledgeEngine, setKnowledgeThrottle, addToKnowledgeFrontier,
  updateKnowledgeDirective,
} from '../../api/admin'
import { formatRelative } from '../../utils/format'
import { useToastStore } from '../../stores/toast-store'
import PipelineDashboard from '../../components/admin/pipeline/PipelineDashboard'
import Card from '../../components/ui/Card'
import Badge from '../../components/ui/Badge'
import Button from '../../components/ui/Button'
import Skeleton from '../../components/ui/Skeleton'
import Tabs from '../../components/ui/Tabs'
import Input from '../../components/ui/Input'
import type {
  FrontierItem,
  KnowledgeDirective,
  KnowledgeDocument,
  KnowledgeStatusResponse,
} from '../../types'
import {
  Play, RotateCcw, AlertTriangle, Zap, BarChart3, Target,
  ArrowUpCircle, Brain, Clock, Pause, Plus, RefreshCw, Search, Settings2,
} from 'lucide-react'

const VALID_TABS = ['pipeline', 'learning', 'knowledge'] as const

function statusBadge(status: string) {
  if (['idle', 'completed', 'ok'].includes(status))
    return <Badge variant="success">{status}</Badge>
  if (['running', 'processing', 'pending'].includes(status))
    return <Badge variant="warning">{status}</Badge>
  if (['failed', 'error', 'paused'].includes(status))
    return <Badge variant="danger">{status}</Badge>
  return <Badge variant="neutral">{status}</Badge>
}

export default function AdminAICenterPage() {
  const [searchParams, setSearchParams] = useSearchParams()
  const tabParam = searchParams.get('tab')
  const activeTab = VALID_TABS.includes(tabParam as any) ? tabParam! : 'pipeline'
  const setTab = (id: string) => setSearchParams({ tab: id }, { replace: true })

  const tabs = [
    { id: 'pipeline', label: 'Pipeline' },
    { id: 'learning', label: 'Learning' },
    { id: 'knowledge', label: 'Knowledge' },
  ]

  return (
    <div className="p-8 space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">AI Center</h1>
        <p className="text-sm text-gray-500">
          Monitor, control, and maintain the AI pipeline, ML models, and knowledge engine.
        </p>
      </div>

      <Tabs tabs={tabs} activeTab={activeTab} onChange={setTab} />

      {activeTab === 'pipeline' && <PipelineDashboard />}
      {activeTab === 'learning' && <LearningTab />}
      {activeTab === 'knowledge' && <KnowledgeTab />}
    </div>
  )
}

/* ─────────────────── Learning Tab ─────────────────── */

function LearningTab() {
  const qc = useQueryClient()
  const addToast = useToastStore(s => s.addToast)
  const [subTab, setSubTab] = useState('models')

  const modelsQ = useQuery({ queryKey: ['admin', 'ml', 'models'], queryFn: getMLModels })
  const evalsQ = useQuery({ queryKey: ['admin', 'ml', 'evaluations'], queryFn: () => getMLEvaluations({ limit: 20 }) })
  const trainingQ = useQuery({ queryKey: ['admin', 'ml', 'training'], queryFn: () => getMLTrainingRuns({ limit: 20 }) })
  const driftQ = useQuery({ queryKey: ['admin', 'ml', 'drift'], queryFn: () => getDriftSnapshots({ limit: 20 }) })
  const outcomesQ = useQuery({ queryKey: ['admin', 'ml', 'outcomes'], queryFn: getOutcomeStats })

  const mut = (fn: () => Promise<any>, msg: string) => ({
    mutationFn: fn,
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['admin', 'ml'] }); addToast(msg, 'success') },
    onError: (e: any) => addToast(e.message, 'error'),
  })

  const runCycleMut = useMutation(mut(runMLCycle, 'ML cycle started'))
  const evaluateMut = useMutation(mut(runMLEvaluate, 'Evaluation started'))
  const driftCheckMut = useMutation(mut(runDriftCheck, 'Drift check complete'))
  const backfillMut = useMutation(mut(backfillOutcomes, 'Backfill complete'))
  const trainMut = useMutation(mut(() => triggerTraining(), 'Training triggered'))
  const promoteMut = useMutation({
    mutationFn: promoteModel,
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['admin', 'ml'] }); addToast('Model promoted', 'success') },
    onError: (e: any) => addToast(e.message, 'error'),
  })
  const rollbackMut = useMutation(mut(rollbackModel, 'Model rolled back'))

  const models: any[] = Array.isArray(modelsQ.data) ? modelsQ.data : modelsQ.data?.models ?? modelsQ.data?.versions ?? []
  const evals: any[] = Array.isArray(evalsQ.data) ? evalsQ.data : evalsQ.data?.evaluations ?? []
  const trainRuns: any[] = Array.isArray(trainingQ.data) ? trainingQ.data : trainingQ.data?.runs ?? []
  const drifts: any[] = Array.isArray(driftQ.data) ? driftQ.data : driftQ.data?.snapshots ?? []
  const outcomes = outcomesQ.data

  const formatOutcomeValue = (value: unknown): string => {
    if (value == null) return '—'
    if (typeof value === 'number') return value.toLocaleString()
    if (typeof value === 'string' || typeof value === 'boolean') return String(value)
    if (Array.isArray(value)) return value.length ? value.join(', ') : '—'
    if (typeof value === 'object') {
      const entries = Object.entries(value as Record<string, unknown>)
      if (!entries.length) return '—'
      return entries.map(([k, v]) => `${k}: ${typeof v === 'number' ? v.toLocaleString() : String(v)}`).join(' · ')
    }
    return String(value)
  }

  const subTabs = [
    { id: 'models', label: `Models (${models.length})` },
    { id: 'evaluations', label: `Evaluations (${evals.length})` },
    { id: 'training', label: `Training (${trainRuns.length})` },
    { id: 'drift', label: `Drift (${drifts.length})` },
    { id: 'outcomes', label: 'Outcomes' },
  ]

  if (modelsQ.isLoading) return <Skeleton className="h-96" />

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <p className="text-sm text-gray-500">
          Manage models, evaluate quality, monitor drift, and track training outcomes.
        </p>
        <div className="flex items-center gap-2">
          <Button variant="secondary" size="sm" onClick={() => evaluateMut.mutate()} disabled={evaluateMut.isPending}>
            <BarChart3 size={14} className="mr-1" /> Evaluate
          </Button>
          <Button variant="secondary" size="sm" onClick={() => driftCheckMut.mutate()} disabled={driftCheckMut.isPending}>
            <AlertTriangle size={14} className="mr-1" /> Drift Check
          </Button>
          <Button size="sm" onClick={() => runCycleMut.mutate()} disabled={runCycleMut.isPending}>
            <Zap size={14} className="mr-1" /> Run Full Cycle
          </Button>
        </div>
      </div>

      <Tabs tabs={subTabs} activeTab={subTab} onChange={setSubTab} />

      {/* Models */}
      {subTab === 'models' && (
        <div className="space-y-4">
          <div className="flex gap-2">
            <Button size="sm" onClick={() => trainMut.mutate()} disabled={trainMut.isPending}>
              <Play size={14} className="mr-1" /> Trigger Training
            </Button>
            <Button variant="secondary" size="sm" onClick={() => rollbackMut.mutate()} disabled={rollbackMut.isPending}>
              <RotateCcw size={14} className="mr-1" /> Rollback
            </Button>
          </div>
          <Card className="overflow-hidden">
            <table className="w-full">
              <thead>
                <tr className="bg-gray-50 border-b">
                  <th className="text-left px-6 py-3 text-xs font-medium text-gray-500 uppercase">Version</th>
                  <th className="text-left px-6 py-3 text-xs font-medium text-gray-500 uppercase">Status</th>
                  <th className="text-left px-6 py-3 text-xs font-medium text-gray-500 uppercase">Metrics</th>
                  <th className="text-left px-6 py-3 text-xs font-medium text-gray-500 uppercase">Created</th>
                  <th className="text-right px-6 py-3 text-xs font-medium text-gray-500 uppercase">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {models.map((m: any) => (
                  <tr key={m.version ?? m.id} className="hover:bg-gray-50">
                    <td className="px-6 py-3 text-sm font-mono">{m.version ?? m.model_version ?? m.id?.slice(0, 12)}</td>
                    <td className="px-6 py-3">
                      <Badge variant={m.is_active ? 'success' : 'neutral'}>{m.is_active ? 'Active' : 'Inactive'}</Badge>
                    </td>
                    <td className="px-6 py-3 text-sm text-gray-500">
                      {m.metrics ? <span>NDCG: {m.metrics.ndcg?.toFixed(3) ?? '—'} | Prec: {m.metrics.precision?.toFixed(3) ?? '—'}</span> : '—'}
                    </td>
                    <td className="px-6 py-3 text-sm text-gray-500">{formatRelative(m.created_at)}</td>
                    <td className="px-6 py-3 text-right">
                      {!m.is_active && (
                        <Button size="sm" variant="secondary"
                          onClick={() => promoteMut.mutate({ model_version: m.version ?? m.model_version })}
                          disabled={promoteMut.isPending}>
                          <ArrowUpCircle size={14} className="mr-1" /> Promote
                        </Button>
                      )}
                    </td>
                  </tr>
                ))}
                {models.length === 0 && (
                  <tr><td colSpan={5} className="px-6 py-12 text-center text-gray-500 text-sm">
                    No model versions yet. Click "Trigger Training" to create your first trained model.
                  </td></tr>
                )}
              </tbody>
            </table>
          </Card>
        </div>
      )}

      {/* Evaluations */}
      {subTab === 'evaluations' && (
        <Card className="overflow-hidden">
          <table className="w-full">
            <thead>
              <tr className="bg-gray-50 border-b">
                <th className="text-left px-6 py-3 text-xs font-medium text-gray-500 uppercase">ID</th>
                <th className="text-left px-6 py-3 text-xs font-medium text-gray-500 uppercase">Model</th>
                <th className="text-left px-6 py-3 text-xs font-medium text-gray-500 uppercase">Status</th>
                <th className="text-left px-6 py-3 text-xs font-medium text-gray-500 uppercase">Metrics</th>
                <th className="text-left px-6 py-3 text-xs font-medium text-gray-500 uppercase">Date</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {evals.map((e: any) => (
                <tr key={e.id} className="hover:bg-gray-50">
                  <td className="px-6 py-3"><code className="text-xs text-gray-500">{e.id?.slice(0, 8)}...</code></td>
                  <td className="px-6 py-3 text-sm">{e.model_version ?? '—'}</td>
                  <td className="px-6 py-3">
                    <Badge variant={e.status === 'completed' ? 'success' : e.status === 'failed' ? 'danger' : 'warning'}>{e.status}</Badge>
                  </td>
                  <td className="px-6 py-3 text-xs text-gray-500 font-mono">{e.metrics ? JSON.stringify(e.metrics).slice(0, 60) : '—'}</td>
                  <td className="px-6 py-3 text-sm text-gray-500">{formatRelative(e.created_at)}</td>
                </tr>
              ))}
              {evals.length === 0 && (
                <tr><td colSpan={5} className="px-6 py-12 text-center text-gray-500 text-sm">No evaluations yet.</td></tr>
              )}
            </tbody>
          </table>
        </Card>
      )}

      {/* Training */}
      {subTab === 'training' && (
        <Card className="overflow-hidden">
          <table className="w-full">
            <thead>
              <tr className="bg-gray-50 border-b">
                <th className="text-left px-6 py-3 text-xs font-medium text-gray-500 uppercase">ID</th>
                <th className="text-left px-6 py-3 text-xs font-medium text-gray-500 uppercase">Status</th>
                <th className="text-left px-6 py-3 text-xs font-medium text-gray-500 uppercase">Trigger</th>
                <th className="text-left px-6 py-3 text-xs font-medium text-gray-500 uppercase">Output Version</th>
                <th className="text-left px-6 py-3 text-xs font-medium text-gray-500 uppercase">Date</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {trainRuns.map((r: any) => (
                <tr key={r.id} className="hover:bg-gray-50">
                  <td className="px-6 py-3"><code className="text-xs text-gray-500">{r.id?.slice(0, 8)}...</code></td>
                  <td className="px-6 py-3">
                    <Badge variant={r.status === 'completed' ? 'success' : r.status === 'failed' ? 'danger' : 'warning'}>{r.status}</Badge>
                  </td>
                  <td className="px-6 py-3 text-sm">{r.trigger ?? r.triggered_by ?? '—'}</td>
                  <td className="px-6 py-3 text-sm font-mono">{r.output_version ?? r.model_version ?? '—'}</td>
                  <td className="px-6 py-3 text-sm text-gray-500">{formatRelative(r.created_at)}</td>
                </tr>
              ))}
              {trainRuns.length === 0 && (
                <tr><td colSpan={5} className="px-6 py-12 text-center text-gray-500 text-sm">No training runs yet.</td></tr>
              )}
            </tbody>
          </table>
        </Card>
      )}

      {/* Drift */}
      {subTab === 'drift' && (
        <div className="space-y-4">
          <Button size="sm" onClick={() => driftCheckMut.mutate()} disabled={driftCheckMut.isPending}>
            <AlertTriangle size={14} className="mr-1" /> Run Drift Check
          </Button>
          <Card className="overflow-hidden">
            <table className="w-full">
              <thead>
                <tr className="bg-gray-50 border-b">
                  <th className="text-left px-6 py-3 text-xs font-medium text-gray-500 uppercase">ID</th>
                  <th className="text-left px-6 py-3 text-xs font-medium text-gray-500 uppercase">Drift Detected</th>
                  <th className="text-left px-6 py-3 text-xs font-medium text-gray-500 uppercase">Score</th>
                  <th className="text-left px-6 py-3 text-xs font-medium text-gray-500 uppercase">Date</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {drifts.map((d: any) => (
                  <tr key={d.id} className="hover:bg-gray-50">
                    <td className="px-6 py-3"><code className="text-xs text-gray-500">{d.id?.slice(0, 8)}...</code></td>
                    <td className="px-6 py-3">
                      <Badge variant={d.drift_detected ? 'danger' : 'success'}>{d.drift_detected ? 'Yes' : 'No'}</Badge>
                    </td>
                    <td className="px-6 py-3 text-sm">{d.drift_score?.toFixed(4) ?? d.score?.toFixed(4) ?? '—'}</td>
                    <td className="px-6 py-3 text-sm text-gray-500">{formatRelative(d.created_at ?? d.checked_at)}</td>
                  </tr>
                ))}
                {drifts.length === 0 && (
                  <tr><td colSpan={4} className="px-6 py-12 text-center text-gray-500 text-sm">No drift checks yet.</td></tr>
                )}
              </tbody>
            </table>
          </Card>
        </div>
      )}

      {/* Outcomes */}
      {subTab === 'outcomes' && (
        <div className="space-y-4">
          <Button size="sm" onClick={() => backfillMut.mutate()} disabled={backfillMut.isPending}>
            <Target size={14} className="mr-1" /> Backfill Outcomes
          </Button>
          <Card className="p-6">
            <h3 className="text-sm font-semibold text-gray-700 mb-4">Outcome Statistics</h3>
            {outcomes ? (
              <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
                {Object.entries(outcomes).map(([key, val]) => (
                  <div key={key} className="bg-gray-50 rounded-lg p-4">
                    <p className="text-xs text-gray-500 uppercase">{key.replace(/_/g, ' ')}</p>
                    <p className="text-sm font-semibold mt-1 text-gray-900 break-words">{formatOutcomeValue(val)}</p>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-gray-500 text-center py-8">No outcome data yet.</p>
            )}
          </Card>
        </div>
      )}
    </div>
  )
}

/* ─────────────────── Knowledge Tab ─────────────────── */

function KnowledgeTab() {
  const addToast = useToastStore(s => s.addToast)
  const qc = useQueryClient()
  const invalidate = () => {
    qc.invalidateQueries({ queryKey: ['knowledge-status'] })
    qc.invalidateQueries({ queryKey: ['knowledge-docs'] })
    qc.invalidateQueries({ queryKey: ['knowledge-frontier'] })
    qc.invalidateQueries({ queryKey: ['knowledge-directives'] })
  }

  const statusQ = useQuery<KnowledgeStatusResponse>({
    queryKey: ['knowledge-status'],
    queryFn: getKnowledgeStatus,
    refetchInterval: 5000,
  })
  const docsQ = useQuery<KnowledgeDocument[]>({
    queryKey: ['knowledge-docs'],
    queryFn: () => getRecentKnowledgeDocuments(15),
    refetchInterval: 10000,
  })
  const frontierQ = useQuery<FrontierItem[]>({
    queryKey: ['knowledge-frontier'],
    queryFn: () => getKnowledgeFrontier({ limit: 15 }),
    refetchInterval: 10000,
  })
  const directivesQ = useQuery<KnowledgeDirective[]>({
    queryKey: ['knowledge-directives'],
    queryFn: getKnowledgeDirectives,
    refetchInterval: 30000,
  })
  const personaQ = useQuery<Record<string, unknown>>({
    queryKey: ['advisor-persona'],
    queryFn: getAdvisorPersona,
    refetchInterval: 30000,
  })

  const tickMut = useMutation({ mutationFn: triggerKnowledgeTick, onSuccess: () => { addToast('Engine tick triggered', 'success'); invalidate() }, onError: () => addToast('Tick failed', 'error') })
  const discoveryMut = useMutation({ mutationFn: triggerKnowledgeDiscovery, onSuccess: () => { addToast('Discovery triggered', 'success'); invalidate() }, onError: () => addToast('Discovery failed', 'error') })
  const pauseMut = useMutation({ mutationFn: pauseKnowledgeEngine, onSuccess: () => { addToast('Engine paused', 'success'); invalidate() } })
  const resumeMut = useMutation({ mutationFn: resumeKnowledgeEngine, onSuccess: () => { addToast('Engine resumed', 'success'); invalidate() } })

  const [rpmInput, setRpmInput] = useState('')
  const throttleMut = useMutation({ mutationFn: (rpm: number) => setKnowledgeThrottle(rpm), onSuccess: () => { addToast('RPM updated', 'success'); invalidate() } })

  const [addUrlInput, setAddUrlInput] = useState('')
  const addUrlMut = useMutation({
    mutationFn: (url: string) => addToKnowledgeFrontier(url),
    onSuccess: (data: { status: string }) => { addToast(data.status === 'added' ? 'URL added to frontier' : 'URL skipped (duplicate)', 'success'); setAddUrlInput(''); invalidate() },
    onError: () => addToast('Failed to add URL', 'error'),
  })

  const personaMut = useMutation({
    mutationFn: (data: Record<string, unknown>) => updateAdvisorPersona(data as Parameters<typeof updateAdvisorPersona>[0]),
    onSuccess: () => { addToast('Persona updated', 'success'); qc.invalidateQueries({ queryKey: ['advisor-persona'] }) },
    onError: () => addToast('Persona update failed', 'error'),
  })

  const toggleDirectiveMut = useMutation({
    mutationFn: ({ id, active }: { id: string; active: boolean }) => updateKnowledgeDirective(id, { is_active: active }),
    onSuccess: () => { addToast('Directive updated', 'success'); invalidate() },
  })

  const engine = statusQ.data?.engine
  const knowledge = statusQ.data?.knowledge
  const frontier = statusQ.data?.frontier

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <p className="text-sm text-gray-500">
          Perpetual learning loop — ingests, understands, and links public knowledge.
        </p>
        <Button size="sm" variant="secondary" onClick={() => invalidate()}>
          <RefreshCw size={14} className="mr-1" /> Refresh
        </Button>
      </div>

      {/* Engine Status */}
      {statusQ.isLoading ? <Skeleton className="h-24" /> : engine ? (
        <Card className="p-4">
          <div className="flex flex-wrap items-center gap-6">
            <div className="flex items-center gap-2">
              <Brain size={20} className="text-indigo-600" />
              <span className="font-semibold">Status:</span>
              {statusBadge(engine.paused ? 'paused' : engine.status)}
            </div>
            <div className="flex items-center gap-2">
              <Zap size={16} className="text-amber-500" />
              <span className="text-sm"><span className="font-medium">{engine.rpm}</span> RPM</span>
            </div>
            <div className="text-sm text-gray-600">Processed: <span className="font-medium">{engine.total_processed}</span></div>
            <div className="text-sm text-gray-600">Errors: <span className="font-medium text-red-600">{engine.total_errors}</span></div>
            <div className="text-sm text-gray-600">Discovered: <span className="font-medium text-blue-600">{engine.total_discovered}</span></div>
            {engine.last_tick_at && (
              <div className="text-xs text-gray-400 flex items-center gap-1">
                <Clock size={12} /> Last tick: {new Date(engine.last_tick_at).toLocaleTimeString()}
              </div>
            )}
          </div>
        </Card>
      ) : null}

      {/* Controls */}
      <Card className="p-4">
        <h2 className="text-sm font-semibold text-gray-700 mb-3 flex items-center gap-2">
          <Settings2 size={16} /> Engine Controls
        </h2>
        <div className="flex flex-wrap items-end gap-4">
          {engine?.paused ? (
            <Button size="sm" onClick={() => resumeMut.mutate()} disabled={resumeMut.isPending}>
              <Play size={14} className="mr-1" /> Resume
            </Button>
          ) : (
            <Button size="sm" variant="secondary" onClick={() => pauseMut.mutate()} disabled={pauseMut.isPending}>
              <Pause size={14} className="mr-1" /> Pause
            </Button>
          )}
          <Button size="sm" onClick={() => tickMut.mutate()} disabled={tickMut.isPending}>
            <Zap size={14} className="mr-1" /> Run Tick
          </Button>
          <Button size="sm" variant="secondary" onClick={() => discoveryMut.mutate()} disabled={discoveryMut.isPending}>
            <Search size={14} className="mr-1" /> Run Discovery
          </Button>
          <div className="flex items-end gap-1">
            <div>
              <label className="text-xs text-gray-500 block mb-1">RPM</label>
              <Input value={rpmInput} onChange={e => setRpmInput(e.target.value)} placeholder={String(engine?.rpm ?? 10)} className="w-20" />
            </div>
            <Button size="sm" variant="secondary" disabled={!rpmInput || throttleMut.isPending}
              onClick={() => { const v = parseInt(rpmInput, 10); if (v >= 1 && v <= 100) throttleMut.mutate(v) }}>Set</Button>
          </div>
          <div className="flex items-end gap-1">
            <div>
              <label className="text-xs text-gray-500 block mb-1">Add URL</label>
              <Input value={addUrlInput} onChange={e => setAddUrlInput(e.target.value)} placeholder="https://..." className="w-72" />
            </div>
            <Button size="sm" disabled={!addUrlInput || addUrlMut.isPending} onClick={() => addUrlMut.mutate(addUrlInput)}>
              <Plus size={14} className="mr-1" /> Add
            </Button>
          </div>
        </div>
      </Card>

      {/* Knowledge Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="p-4 text-center">
          <div className="text-3xl font-bold text-indigo-600">{knowledge?.total_documents ?? '—'}</div>
          <div className="text-xs text-gray-500 mt-1">Total Documents</div>
        </Card>
        <Card className="p-4 text-center">
          <div className="text-3xl font-bold text-green-600">{knowledge?.active_documents ?? '—'}</div>
          <div className="text-xs text-gray-500 mt-1">Active & Completed</div>
        </Card>
        <Card className="p-4 text-center">
          <div className="text-3xl font-bold text-blue-600">{frontier?.pending ?? '—'}</div>
          <div className="text-xs text-gray-500 mt-1">Frontier Pending</div>
        </Card>
        <Card className="p-4 text-center">
          <div className="text-3xl font-bold text-red-500">{frontier?.failed ?? '—'}</div>
          <div className="text-xs text-gray-500 mt-1">Frontier Failed</div>
        </Card>
      </div>

      {/* Directives */}
      <Card className="p-4">
        <h2 className="text-sm font-semibold text-gray-700 mb-3 flex items-center gap-2">
          <Settings2 size={16} /> Steering Directives
        </h2>
        {directivesQ.isLoading ? <Skeleton className="h-16" /> : (directivesQ.data ?? []).length === 0 ? (
          <p className="text-sm text-gray-400">No directives configured</p>
        ) : (
          <div className="space-y-2">
            {(directivesQ.data ?? []).map((d: KnowledgeDirective) => (
              <div key={d.id} className="flex items-center justify-between border rounded-lg px-3 py-2 text-sm">
                <div className="flex items-center gap-3">
                  <Badge variant={d.is_active ? 'success' : 'neutral'}>{d.is_active ? 'active' : 'off'}</Badge>
                  <span className="font-medium">{d.directive_type}:{d.directive_key}</span>
                  {d.description && <span className="text-gray-400 text-xs truncate max-w-xs">{d.description}</span>}
                </div>
                <Button size="sm" variant="secondary"
                  onClick={() => toggleDirectiveMut.mutate({ id: d.id, active: !d.is_active })}
                  disabled={toggleDirectiveMut.isPending}>
                  {d.is_active ? 'Disable' : 'Enable'}
                </Button>
              </div>
            ))}
          </div>
        )}
      </Card>

      {/* Advisor Persona */}
      <Card className="p-4">
        <h2 className="text-sm font-semibold text-gray-700 mb-3 flex items-center gap-2">
          <Brain size={16} /> Advisor Persona
        </h2>
        {personaQ.isLoading ? <Skeleton className="h-32" /> : personaQ.data && !('status' in personaQ.data && personaQ.data.status === 'no_active_persona') ? (
          <div className="space-y-3">
            {[
              { key: 'warmth', label: 'Warmth', desc: 'warm vs professional' },
              { key: 'directness', label: 'Directness', desc: 'direct vs gentle' },
              { key: 'formality', label: 'Formality', desc: 'casual vs formal' },
              { key: 'challenge_level', label: 'Challenge', desc: 'supportive vs challenging' },
              { key: 'data_reference_frequency', label: 'Data Usage', desc: 'human vs data-driven' },
              { key: 'humor', label: 'Humor', desc: 'serious vs playful' },
              { key: 'proactivity', label: 'Proactivity', desc: 'reactive vs proactive' },
              { key: 'empathy_depth', label: 'Empathy', desc: 'surface vs deep' },
            ].map(({ key, label, desc }) => (
              <div key={key} className="flex items-center gap-3">
                <label className="w-28 text-sm text-gray-600">{label}</label>
                <input type="range" min={0} max={100} value={Number(personaQ.data?.[key] ?? 50)}
                  onChange={e => personaMut.mutate({ [key]: parseInt(e.target.value, 10) })}
                  className="flex-1 h-2 rounded-lg appearance-none bg-gray-200 cursor-pointer" />
                <span className="w-8 text-xs text-gray-500 text-right">{String(personaQ.data?.[key] ?? 50)}</span>
                <span className="text-xs text-gray-400 w-32 truncate">{desc}</span>
              </div>
            ))}
            <div className="mt-4">
              <label className="text-sm text-gray-600 block mb-1">Custom Instructions</label>
              <textarea className="w-full border rounded-lg p-2 text-sm h-20 resize-none"
                defaultValue={String(personaQ.data?.custom_instructions ?? '')}
                onBlur={e => { if (e.target.value !== personaQ.data?.custom_instructions) personaMut.mutate({ custom_instructions: e.target.value }) }}
                placeholder="e.g., Always mention scholarships for international students..." />
            </div>
          </div>
        ) : (
          <p className="text-sm text-gray-400">No active persona configured. The system uses default settings.</p>
        )}
      </Card>

      {/* Recent Documents */}
      <Card className="p-4">
        <h2 className="text-sm font-semibold text-gray-700 mb-3">Recent Documents</h2>
        {docsQ.isLoading ? <Skeleton className="h-32" /> : (docsQ.data ?? []).length === 0 ? (
          <p className="text-sm text-gray-400 text-center py-4">No documents ingested yet</p>
        ) : (
          <div className="max-h-64 overflow-y-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-gray-400 border-b border-gray-100">
                  <th className="text-left py-1 font-medium">Title / URL</th>
                  <th className="text-left py-1 font-medium">Format</th>
                  <th className="text-left py-1 font-medium">Status</th>
                  <th className="text-right py-1 font-medium">Quality</th>
                </tr>
              </thead>
              <tbody>
                {(docsQ.data ?? []).map((doc: KnowledgeDocument) => (
                  <tr key={doc.id} className="border-b border-gray-50 hover:bg-gray-50">
                    <td className="py-1.5 text-gray-700 truncate max-w-[250px]" title={doc.source_url ?? ''}>{doc.title ?? doc.source_url ?? doc.id.slice(0, 12)}</td>
                    <td className="py-1.5 text-gray-500">{doc.content_format}</td>
                    <td className="py-1.5">{statusBadge(doc.processing_status)}</td>
                    <td className="py-1.5 text-right font-mono text-gray-600">{doc.quality_score != null ? `${(doc.quality_score * 100).toFixed(0)}%` : '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      {/* Frontier */}
      <Card className="p-4">
        <h2 className="text-sm font-semibold text-gray-700 mb-3">Frontier Queue</h2>
        {frontierQ.isLoading ? <Skeleton className="h-32" /> : (frontierQ.data ?? []).length === 0 ? (
          <p className="text-sm text-gray-400 text-center py-4">Frontier is empty</p>
        ) : (
          <div className="max-h-52 overflow-y-auto">
            <table className="w-full text-xs">
              <thead>
                <tr className="text-gray-400 border-b border-gray-100">
                  <th className="text-left py-1 font-medium">URL</th>
                  <th className="text-left py-1 font-medium">Domain</th>
                  <th className="text-left py-1 font-medium">Status</th>
                  <th className="text-right py-1 font-medium">Priority</th>
                  <th className="text-right py-1 font-medium">Method</th>
                </tr>
              </thead>
              <tbody>
                {(frontierQ.data ?? []).map((item: FrontierItem) => (
                  <tr key={item.id} className="border-b border-gray-50 hover:bg-gray-50">
                    <td className="py-1.5 text-gray-700 truncate max-w-[200px]" title={item.url}>{item.url}</td>
                    <td className="py-1.5 text-gray-500">{item.domain}</td>
                    <td className="py-1.5">{statusBadge(item.status)}</td>
                    <td className="py-1.5 text-right font-mono text-gray-600">{item.priority}</td>
                    <td className="py-1.5 text-right text-gray-400">{item.discovery_method ?? '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </div>
  )
}
