import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  getMLEvaluations, getMLTrainingRuns, getMLModels, getDriftSnapshots,
  getOutcomeStats,
  runMLCycle, runMLEvaluate, runDriftCheck, backfillOutcomes,
  triggerTraining, promoteModel, rollbackModel,
} from '../../api/admin'
import { formatRelative } from '../../utils/format'
import Card from '../../components/ui/Card'
import Badge from '../../components/ui/Badge'
import Button from '../../components/ui/Button'
import Skeleton from '../../components/ui/Skeleton'
import Tabs from '../../components/ui/Tabs'
import { useToastStore } from '../../stores/toast-store'
import {
  Play, RotateCcw, AlertTriangle,
  Zap, BarChart3, Target, ArrowUpCircle,
} from 'lucide-react'

export default function AdminMLPage() {
  const qc = useQueryClient()
  const addToast = useToastStore(s => s.addToast)
  const [activeTab, setActiveTab] = useState('models')

  const modelsQ = useQuery({ queryKey: ['admin', 'ml', 'models'], queryFn: getMLModels })
  const evalsQ = useQuery({ queryKey: ['admin', 'ml', 'evaluations'], queryFn: () => getMLEvaluations({ limit: 20 }) })
  const trainingQ = useQuery({ queryKey: ['admin', 'ml', 'training'], queryFn: () => getMLTrainingRuns({ limit: 20 }) })
  const driftQ = useQuery({ queryKey: ['admin', 'ml', 'drift'], queryFn: () => getDriftSnapshots({ limit: 20 }) })
  const outcomesQ = useQuery({ queryKey: ['admin', 'ml', 'outcomes'], queryFn: getOutcomeStats })

  const runCycleMut = useMutation({
    mutationFn: runMLCycle,
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['admin', 'ml'] }); addToast('ML cycle started', 'success') },
    onError: (e: any) => addToast(e.message, 'error'),
  })
  const evaluateMut = useMutation({
    mutationFn: runMLEvaluate,
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['admin', 'ml'] }); addToast('Evaluation started', 'success') },
    onError: (e: any) => addToast(e.message, 'error'),
  })
  const driftCheckMut = useMutation({
    mutationFn: runDriftCheck,
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['admin', 'ml'] }); addToast('Drift check complete', 'success') },
    onError: (e: any) => addToast(e.message, 'error'),
  })
  const backfillMut = useMutation({
    mutationFn: backfillOutcomes,
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['admin', 'ml'] }); addToast('Backfill complete', 'success') },
    onError: (e: any) => addToast(e.message, 'error'),
  })
  const trainMut = useMutation({
    mutationFn: triggerTraining,
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['admin', 'ml'] }); addToast('Training triggered', 'success') },
    onError: (e: any) => addToast(e.message, 'error'),
  })
  const promoteMut = useMutation({
    mutationFn: promoteModel,
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['admin', 'ml'] }); addToast('Model promoted', 'success') },
    onError: (e: any) => addToast(e.message, 'error'),
  })
  const rollbackMut = useMutation({
    mutationFn: rollbackModel,
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['admin', 'ml'] }); addToast('Model rolled back', 'success') },
    onError: (e: any) => addToast(e.message, 'error'),
  })

  const models: any[] = Array.isArray(modelsQ.data) ? modelsQ.data : modelsQ.data?.models ?? modelsQ.data?.versions ?? []
  const evals: any[] = Array.isArray(evalsQ.data) ? evalsQ.data : evalsQ.data?.evaluations ?? []
  const trainRuns: any[] = Array.isArray(trainingQ.data) ? trainingQ.data : trainingQ.data?.runs ?? []
  const drifts: any[] = Array.isArray(driftQ.data) ? driftQ.data : driftQ.data?.snapshots ?? []
  const outcomes = outcomesQ.data

  const tabs = [
    { id: 'models', label: `Models (${models.length})` },
    { id: 'evaluations', label: `Evaluations (${evals.length})` },
    { id: 'training', label: `Training (${trainRuns.length})` },
    { id: 'drift', label: `Drift (${drifts.length})` },
    { id: 'outcomes', label: 'Outcomes' },
  ]

  const isLoading = modelsQ.isLoading
  if (isLoading) return <div className="p-8"><Skeleton className="h-96" /></div>

  return (
    <div className="p-8 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">AI Learning Pipeline</h1>
          <p className="text-sm text-gray-500">This is where the engine learns from outcomes, checks quality, and updates models safely.</p>
        </div>
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

      <Card className="p-4 bg-blue-50 border-blue-200">
        <h3 className="text-sm font-semibold text-blue-900 mb-2">What this page does (simple)</h3>
        <div className="text-sm text-blue-800 space-y-1">
          <p><strong>Models</strong>: versions of your AI matching brain.</p>
          <p><strong>Evaluations</strong>: quality checks ("how accurate are we?").</p>
          <p><strong>Training</strong>: learning runs using new data/outcomes.</p>
          <p><strong>Drift</strong>: alerts when data patterns change over time.</p>
          <p className="pt-1">If sections are empty, it usually means no training/evaluation cycle has run yet.</p>
        </div>
      </Card>

      <Tabs tabs={tabs} activeTab={activeTab} onChange={setActiveTab} />

      {/* Models Tab */}
      {activeTab === 'models' && (
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
                      <Badge variant={m.is_active ? 'success' : 'neutral'}>
                        {m.is_active ? 'Active' : 'Inactive'}
                      </Badge>
                    </td>
                    <td className="px-6 py-3 text-sm text-gray-500">
                      {m.metrics ? (
                        <span>NDCG: {m.metrics.ndcg?.toFixed(3) ?? '—'} | Prec: {m.metrics.precision?.toFixed(3) ?? '—'}</span>
                      ) : '—'}
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

      {/* Evaluations Tab */}
      {activeTab === 'evaluations' && (
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
                    <Badge variant={e.status === 'completed' ? 'success' : e.status === 'failed' ? 'danger' : 'warning'}>
                      {e.status}
                    </Badge>
                  </td>
                  <td className="px-6 py-3 text-xs text-gray-500 font-mono">
                    {e.metrics ? JSON.stringify(e.metrics).slice(0, 60) : '—'}
                  </td>
                  <td className="px-6 py-3 text-sm text-gray-500">{formatRelative(e.created_at)}</td>
                </tr>
              ))}
              {evals.length === 0 && (
                <tr><td colSpan={5} className="px-6 py-12 text-center text-gray-500 text-sm">
                  No evaluations yet. Click "Evaluate" to run a quality check on the current model.
                </td></tr>
              )}
            </tbody>
          </table>
        </Card>
      )}

      {/* Training Tab */}
      {activeTab === 'training' && (
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
                    <Badge variant={r.status === 'completed' ? 'success' : r.status === 'failed' ? 'danger' : 'warning'}>
                      {r.status}
                    </Badge>
                  </td>
                  <td className="px-6 py-3 text-sm">{r.trigger ?? r.triggered_by ?? '—'}</td>
                  <td className="px-6 py-3 text-sm font-mono">{r.output_version ?? r.model_version ?? '—'}</td>
                  <td className="px-6 py-3 text-sm text-gray-500">{formatRelative(r.created_at)}</td>
                </tr>
              ))}
              {trainRuns.length === 0 && (
                <tr><td colSpan={5} className="px-6 py-12 text-center text-gray-500 text-sm">
                  No training runs yet. Start one by clicking "Trigger Training".
                </td></tr>
              )}
            </tbody>
          </table>
        </Card>
      )}

      {/* Drift Tab */}
      {activeTab === 'drift' && (
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
                      <Badge variant={d.drift_detected ? 'danger' : 'success'}>
                        {d.drift_detected ? 'Yes' : 'No'}
                      </Badge>
                    </td>
                    <td className="px-6 py-3 text-sm">{d.drift_score?.toFixed(4) ?? d.score?.toFixed(4) ?? '—'}</td>
                    <td className="px-6 py-3 text-sm text-gray-500">{formatRelative(d.created_at ?? d.checked_at)}</td>
                  </tr>
                ))}
                {drifts.length === 0 && (
                  <tr><td colSpan={4} className="px-6 py-12 text-center text-gray-500 text-sm">
                    No drift checks yet. Click "Run Drift Check" to see if your data behavior has changed.
                  </td></tr>
                )}
              </tbody>
            </table>
          </Card>
        </div>
      )}

      {/* Outcomes Tab */}
      {activeTab === 'outcomes' && (
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
                    <p className="text-2xl font-bold mt-1">{typeof val === 'number' ? val.toLocaleString() : String(val)}</p>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-gray-500 text-center py-8">
                No outcome data yet. This usually means admissions/interview decisions are not yet recorded in enough volume.
              </p>
            )}
          </Card>
        </div>
      )}
    </div>
  )
}
