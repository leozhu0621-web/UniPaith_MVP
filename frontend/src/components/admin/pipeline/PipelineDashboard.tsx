import { useCallback, useEffect, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import apiClient from '../../../api/client'
import Card from '../../ui/Card'
import Badge from '../../ui/Badge'
import Button from '../../ui/Button'
import type { PipelineStatus } from '../../../types'

function timeAgo(iso: string | null): string {
  if (!iso) return 'never'
  const diff = Date.now() - new Date(iso).getTime()
  if (diff < 5_000) return 'just now'
  if (diff < 60_000) return `${Math.round(diff / 1000)}s ago`
  if (diff < 3_600_000) return `${Math.round(diff / 60_000)}m ago`
  return `${Math.round(diff / 3_600_000)}h ago`
}

function stageVariant(status: string): 'success' | 'warning' | 'danger' | 'neutral' {
  if (['running', 'local_online', 'fallback_running', 'training', 'completed'].includes(status))
    return 'success'
  if (['waiting', 'fallback_waiting', 'local_offline'].includes(status)) return 'warning'
  if (['error'].includes(status)) return 'danger'
  if (['paused', 'off', 'not_started'].includes(status)) return 'neutral'
  return 'neutral'
}

function stageLabel(status: string): string {
  const labels: Record<string, string> = {
    running: 'Running',
    local_online: 'Local Worker Online',
    fallback_running: 'OpenAI Fallback Active',
    fallback_waiting: 'Fallback Idle',
    local_offline: 'Local Offline',
    waiting: 'Waiting',
    training: 'Training',
    completed: 'Completed',
    error: 'Error',
    paused: 'Paused',
    off: 'Off',
    not_started: 'Not Started',
  }
  return labels[status] || status
}

export default function PipelineDashboard() {
  const queryClient = useQueryClient()

  const { data, isLoading } = useQuery<PipelineStatus>({
    queryKey: ['pipeline-status'],
    queryFn: () => apiClient.get('/admin/pipeline/status').then(r => r.data),
    refetchInterval: 5_000,
  })

  const toggleMut = useMutation({
    mutationFn: (enabled: boolean) =>
      apiClient.post('/admin/pipeline/toggle', { enabled }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['pipeline-status'] }),
  })

  const throttleMut = useMutation({
    mutationFn: (budget: number) =>
      apiClient.post('/admin/pipeline/throttle', { budget_per_hour: budget }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['pipeline-status'] }),
  })

  const forceMut = useMutation({
    mutationFn: (action: string) =>
      apiClient.post('/admin/pipeline/force', { action }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['pipeline-status'] }),
  })

  const [budgetInput, setBudgetInput] = useState<number>(5)

  useEffect(() => {
    if (data?.budget?.per_hour) setBudgetInput(data.budget.per_hour)
  }, [data?.budget?.per_hour])

  const [showConfig, setShowConfig] = useState(false)

  if (isLoading || !data) {
    return (
      <Card className="p-6">
        <div className="animate-pulse space-y-4">
          <div className="h-6 bg-gray-200 rounded w-48" />
          <div className="h-32 bg-gray-100 rounded" />
        </div>
      </Card>
    )
  }

  const { stages, totals, budget, enabled } = data
  const crawl = stages.crawl || { status: 'not_started' }
  const extract = stages.extract || { status: 'not_started' }
  const ml = stages.ml || { status: 'not_started' }

  const mlExtra = (ml as any).extra || {}
  const outcomeCount = mlExtra.current_outcomes ?? totals.outcome_count
  const outcomeRequired = mlExtra.required_outcomes ?? 30

  return (
    <div className="space-y-4">
      {/* Top bar: on/off + budget */}
      <Card className="p-4">
        <div className="flex items-center justify-between flex-wrap gap-4">
          <div className="flex items-center gap-4">
            <span className="text-sm font-medium text-gray-500">Pipeline</span>
            <button
              onClick={() => toggleMut.mutate(!enabled)}
              disabled={toggleMut.isPending}
              className={`relative inline-flex h-8 w-14 items-center rounded-full transition-colors ${
                enabled ? 'bg-green-500' : 'bg-gray-300'
              }`}
            >
              <span
                className={`inline-block h-6 w-6 transform rounded-full bg-white shadow transition-transform ${
                  enabled ? 'translate-x-7' : 'translate-x-1'
                }`}
              />
            </button>
            <span className="text-sm font-semibold">
              {enabled ? 'ON' : 'OFF'}
            </span>
          </div>

          <div className="flex items-center gap-3">
            <label className="text-sm text-gray-500">Budget:</label>
            <input
              type="range"
              min={0.5}
              max={50}
              step={0.5}
              value={budgetInput}
              onChange={e => setBudgetInput(Number(e.target.value))}
              onMouseUp={() => throttleMut.mutate(budgetInput)}
              onTouchEnd={() => throttleMut.mutate(budgetInput)}
              className="w-32"
            />
            <span className="text-sm font-mono w-20">${budgetInput.toFixed(2)}/hr</span>
          </div>

          <div className="text-sm text-gray-500">
            Spent: <span className="font-mono font-semibold text-gray-700">
              ${budget.spent_this_hour.toFixed(2)}
            </span>{' '}
            / ${budget.per_hour.toFixed(2)} this hour
          </div>
        </div>
      </Card>

      {/* Three stage cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Crawl */}
        <Card className="p-4">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-semibold">Crawl</h3>
            <Badge variant={stageVariant(crawl.status as string)}>
              {stageLabel(crawl.status as string)}
            </Badge>
          </div>
          <dl className="space-y-1 text-sm">
            <div className="flex justify-between">
              <dt className="text-gray-500">Last activity</dt>
              <dd className="font-mono">{timeAgo((crawl as any).last_activity_at)}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-gray-500">Processed (hour)</dt>
              <dd className="font-mono">{(crawl as any).items_processed_hour ?? 0}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-gray-500">Processed (total)</dt>
              <dd className="font-mono">{(crawl as any).items_processed_total ?? 0}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-gray-500">Frontier pending</dt>
              <dd className="font-mono">{totals.frontier_pending}</dd>
            </div>
          </dl>
          <div className="mt-3">
            <Button
              size="sm"
              variant="secondary"
              onClick={() => forceMut.mutate('discover')}
              disabled={forceMut.isPending}
            >
              Force Discovery
            </Button>
          </div>
        </Card>

        {/* Extract */}
        <Card className="p-4">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-semibold">Extract</h3>
            <Badge variant={stageVariant(extract.status as string)}>
              {stageLabel(extract.status as string)}
            </Badge>
          </div>
          <dl className="space-y-1 text-sm">
            <div className="flex justify-between">
              <dt className="text-gray-500">Last activity</dt>
              <dd className="font-mono">{timeAgo((extract as any).last_activity_at)}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-gray-500">Processed (hour)</dt>
              <dd className="font-mono">{(extract as any).items_processed_hour ?? 0}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-gray-500">Raw queue</dt>
              <dd className="font-mono">{totals.raw_docs_queued}</dd>
            </div>
            {(extract as any).worker_hostname && (
              <div className="flex justify-between">
                <dt className="text-gray-500">Worker</dt>
                <dd className="font-mono text-xs truncate max-w-[120px]">
                  {(extract as any).worker_hostname}
                </dd>
              </div>
            )}
            <div className="flex justify-between">
              <dt className="text-gray-500">Worker seen</dt>
              <dd className="font-mono">{timeAgo((extract as any).worker_heartbeat_at)}</dd>
            </div>
          </dl>
          <div className="mt-3">
            <Button
              size="sm"
              variant="secondary"
              onClick={() => forceMut.mutate('flush_failed')}
              disabled={forceMut.isPending}
            >
              Retry Failed
            </Button>
          </div>
        </Card>

        {/* ML Train */}
        <Card className="p-4">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-semibold">ML Train</h3>
            <Badge variant={stageVariant(ml.status as string)}>
              {stageLabel(ml.status as string)}
            </Badge>
          </div>
          <dl className="space-y-1 text-sm">
            <div className="flex justify-between">
              <dt className="text-gray-500">Last activity</dt>
              <dd className="font-mono">{timeAgo((ml as any).last_activity_at)}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-gray-500">Outcomes</dt>
              <dd className="font-mono">{outcomeCount} / {outcomeRequired}</dd>
            </div>
            <div className="mt-1">
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className="bg-blue-500 h-2 rounded-full transition-all"
                  style={{ width: `${Math.min(100, (outcomeCount / outcomeRequired) * 100)}%` }}
                />
              </div>
            </div>
            <div className="flex justify-between">
              <dt className="text-gray-500">Docs completed</dt>
              <dd className="font-mono">{totals.docs_completed}</dd>
            </div>
          </dl>
          <div className="mt-3">
            <Button
              size="sm"
              variant="secondary"
              onClick={() => forceMut.mutate('train')}
              disabled={forceMut.isPending}
            >
              Force Train
            </Button>
          </div>
        </Card>
      </div>

      {/* Advanced config toggle */}
      <Card className="p-4">
        <button
          onClick={() => setShowConfig(!showConfig)}
          className="text-sm text-blue-600 hover:text-blue-800 font-medium"
        >
          {showConfig ? '▼ Hide Advanced Config' : '▶ Advanced Config'}
        </button>
        {showConfig && (
          <div className="mt-4 grid grid-cols-1 md:grid-cols-3 gap-6 text-sm">
            <div>
              <h4 className="font-semibold mb-2">Crawl</h4>
              <ConfigField label="RPM" configKey="crawl_rpm" defaultVal={10} />
              <ConfigField label="Concurrency" configKey="crawl_concurrent" defaultVal={10} />
            </div>
            <div>
              <h4 className="font-semibold mb-2">Extract</h4>
              <ConfigField label="Ollama Model" configKey="extract_model" defaultVal="qwen2.5:7b" type="text" />
              <ConfigField label="Idle sleep (s)" configKey="extract_idle_seconds" defaultVal={5} />
              <ConfigField label="Heartbeat timeout (s)" configKey="heartbeat_timeout" defaultVal={300} />
            </div>
            <div>
              <h4 className="font-semibold mb-2">ML Train</h4>
              <ConfigField label="Threshold" configKey="ml_threshold" defaultVal={30} />
              <ConfigField label="Cooldown (s)" configKey="ml_cooldown" defaultVal={300} />
            </div>
          </div>
        )}
      </Card>
    </div>
  )
}

function ConfigField({
  label,
  configKey,
  defaultVal,
  type = 'number',
}: {
  label: string
  configKey: string
  defaultVal: number | string
  type?: 'number' | 'text'
}) {
  const [value, setValue] = useState(String(defaultVal))
  const queryClient = useQueryClient()

  const saveMut = useMutation({
    mutationFn: () =>
      apiClient.patch('/admin/pipeline/config', {
        updates: { [configKey]: type === 'number' ? Number(value) : value },
      }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['pipeline-status'] }),
  })

  return (
    <div className="flex items-center gap-2 mb-1">
      <label className="text-gray-500 w-28 text-xs">{label}</label>
      <input
        type={type}
        value={value}
        onChange={e => setValue(e.target.value)}
        onBlur={() => saveMut.mutate()}
        className="border rounded px-2 py-1 text-xs w-24 font-mono"
      />
    </div>
  )
}
