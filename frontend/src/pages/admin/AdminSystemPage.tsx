import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { getAdminActionAudit, getPipelineConfig, patchPipelineConfig, setPipelineBudget } from '../../api/admin'
import { useToastStore } from '../../stores/toast-store'
import Card from '../../components/ui/Card'
import Button from '../../components/ui/Button'
import Input from '../../components/ui/Input'
import Skeleton from '../../components/ui/Skeleton'
import { RefreshCw, Settings, DollarSign } from 'lucide-react'

export default function AdminSystemPage() {
  const qc = useQueryClient()
  const addToast = useToastStore(s => s.addToast)

  const adminAuditQ = useQuery({
    queryKey: ['admin', 'audit', 'actions', 'system'],
    queryFn: () => getAdminActionAudit({ limit: 100 }),
    refetchInterval: 10000,
  })

  const configQ = useQuery({
    queryKey: ['admin', 'pipeline', 'config'],
    queryFn: getPipelineConfig,
    refetchInterval: 30000,
  })

  const [budgetInput, setBudgetInput] = useState('')
  const budgetMut = useMutation({
    mutationFn: (budget: number) => setPipelineBudget(budget),
    onSuccess: () => { addToast('Budget updated', 'success'); qc.invalidateQueries({ queryKey: ['admin', 'pipeline'] }) },
    onError: (e: any) => addToast(e.message, 'error'),
  })

  const [editingKey, setEditingKey] = useState<string | null>(null)
  const [editValue, setEditValue] = useState('')
  const configMut = useMutation({
    mutationFn: (updates: Record<string, unknown>) => patchPipelineConfig(updates),
    onSuccess: () => { addToast('Config updated', 'success'); setEditingKey(null); qc.invalidateQueries({ queryKey: ['admin', 'pipeline', 'config'] }) },
    onError: (e: any) => addToast(e.message, 'error'),
  })

  const configEntries = Object.entries(configQ.data?.config ?? {}) as [string, { value: any; description: string | null; updated_at: string | null; updated_by: string | null }][]

  return (
    <div className="p-8 space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">System Settings</h1>
        <p className="text-sm text-gray-500">Environment, pipeline configuration, and admin action history</p>
      </div>

      {/* Environment */}
      <Card className="p-6">
        <h3 className="text-sm font-semibold text-gray-700 mb-4">Environment</h3>
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="bg-gray-50 rounded-lg p-3">
            <p className="text-xs text-gray-500">API URL</p>
            <p className="text-sm font-mono text-gray-800 mt-1">{import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'}</p>
          </div>
          <div className="bg-gray-50 rounded-lg p-3">
            <p className="text-xs text-gray-500">Frontend Build</p>
            <p className="text-sm font-mono text-gray-800 mt-1">{import.meta.env.MODE}</p>
          </div>
          <div className="bg-gray-50 rounded-lg p-3">
            <p className="text-xs text-gray-500">Node Env</p>
            <p className="text-sm font-mono text-gray-800 mt-1">{import.meta.env.PROD ? 'production' : 'development'}</p>
          </div>
          <div className="bg-gray-50 rounded-lg p-3">
            <p className="text-xs text-gray-500">Version</p>
            <p className="text-sm font-mono text-gray-800 mt-1">MVP 0.1.0</p>
          </div>
        </div>
      </Card>

      {/* Pipeline Budget */}
      <Card className="p-6">
        <h3 className="text-sm font-semibold text-gray-700 mb-4 flex items-center gap-2">
          <DollarSign size={16} /> Pipeline Budget
        </h3>
        <div className="flex items-end gap-4">
          <div>
            <label className="text-xs text-gray-500 block mb-1">Budget per hour ($)</label>
            <Input value={budgetInput} onChange={e => setBudgetInput(e.target.value)}
              placeholder="5.00" className="w-32" type="number" />
          </div>
          <Button size="sm" disabled={!budgetInput || budgetMut.isPending}
            onClick={() => { const v = parseFloat(budgetInput); if (v > 0) budgetMut.mutate(v) }}>
            Update Budget
          </Button>
        </div>
      </Card>

      {/* Pipeline Config */}
      <Card className="p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-sm font-semibold text-gray-700 flex items-center gap-2">
            <Settings size={16} /> Pipeline Config
          </h3>
          <Button variant="secondary" size="sm" onClick={() => configQ.refetch()} disabled={configQ.isFetching}>
            <RefreshCw size={14} className={configQ.isFetching ? 'animate-spin' : ''} />
          </Button>
        </div>
        {configQ.isLoading ? <Skeleton className="h-32" /> : configEntries.length === 0 ? (
          <p className="text-sm text-gray-400">No pipeline config entries yet.</p>
        ) : (
          <div className="space-y-2">
            {configEntries.map(([key, entry]) => (
              <div key={key} className="border border-gray-200 rounded-lg p-3">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-mono font-medium text-gray-900">{key}</p>
                    {entry.description && <p className="text-xs text-gray-500 mt-0.5">{entry.description}</p>}
                  </div>
                  {editingKey === key ? (
                    <div className="flex items-center gap-2">
                      <Input value={editValue} onChange={e => setEditValue(e.target.value)} className="w-48 text-sm" />
                      <Button size="sm" onClick={() => {
                        try { configMut.mutate({ [key]: JSON.parse(editValue) }) }
                        catch { configMut.mutate({ [key]: editValue }) }
                      }} disabled={configMut.isPending}>Save</Button>
                      <Button size="sm" variant="secondary" onClick={() => setEditingKey(null)}>Cancel</Button>
                    </div>
                  ) : (
                    <div className="flex items-center gap-2">
                      <code className="text-xs bg-gray-100 px-2 py-1 rounded text-gray-700 max-w-xs truncate">
                        {JSON.stringify(entry.value)}
                      </code>
                      <Button size="sm" variant="secondary" onClick={() => { setEditingKey(key); setEditValue(JSON.stringify(entry.value)) }}>
                        Edit
                      </Button>
                    </div>
                  )}
                </div>
                {entry.updated_at && (
                  <p className="text-xs text-gray-400 mt-1">Updated {entry.updated_at} by {entry.updated_by ?? 'system'}</p>
                )}
              </div>
            ))}
          </div>
        )}
      </Card>

      {/* AI Center link */}
      <Card className="p-4 bg-blue-50 border-blue-200">
        <p className="text-sm text-blue-800">
          AI policy, controls, bootstrap, and maintenance actions have moved to{' '}
          <a href="/admin/ai" className="font-semibold underline">AI Center</a>.
        </p>
      </Card>

      {/* Admin Action History */}
      <Card className="p-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="font-semibold text-gray-900">Admin Action History</h3>
            <p className="text-xs text-gray-500">Full feed of user, institution, and AI admin actions</p>
          </div>
          <Button variant="secondary" onClick={() => adminAuditQ.refetch()} disabled={adminAuditQ.isFetching}>
            <RefreshCw size={14} className={`mr-2 ${adminAuditQ.isFetching ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
        </div>
        <div className="space-y-2 max-h-96 overflow-auto">
          {(adminAuditQ.data?.items ?? []).length === 0 ? (
            <p className="text-sm text-gray-500">No admin actions recorded yet.</p>
          ) : (
            (adminAuditQ.data?.items ?? []).map((event: any) => (
              <div key={event.id} className="border border-gray-200 rounded-lg p-3">
                <div className="flex items-center justify-between">
                  <p className="text-sm font-medium text-gray-900">{event.action}</p>
                  <p className="text-xs text-gray-500">{event.created_at}</p>
                </div>
                <p className="text-xs text-gray-600 mt-1">{event.entity_type} · {event.entity_id}</p>
                {event.payload_json?.reason && (
                  <p className="text-xs text-gray-500 mt-1">Reason: {event.payload_json.reason}</p>
                )}
              </div>
            ))
          )}
        </div>
      </Card>
    </div>
  )
}
