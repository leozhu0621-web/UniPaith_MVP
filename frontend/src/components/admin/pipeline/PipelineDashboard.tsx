import { useEffect, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import apiClient from '../../../api/client'
import Card from '../../ui/Card'
import Button from '../../ui/Button'
import type { PipelineStatus, PipelineStageStatus } from '../../../types'

function timeAgo(iso: string | null): string {
  if (!iso) return 'never'
  const diff = Date.now() - new Date(iso).getTime()
  if (diff < 5_000) return 'just now'
  if (diff < 60_000) return `${Math.round(diff / 1000)}s ago`
  if (diff < 3_600_000) return `${Math.round(diff / 60_000)}m ago`
  return `${Math.round(diff / 3_600_000)}h ago`
}

const STATUS_COLORS: Record<string, string> = {
  running: 'bg-green-500',
  local_online: 'bg-green-500',
  fallback_running: 'bg-blue-500',
  training: 'bg-green-500',
  completed: 'bg-green-500',
  waiting: 'bg-yellow-400',
  fallback_waiting: 'bg-yellow-400',
  local_offline: 'bg-orange-400',
  error: 'bg-red-500',
  paused: 'bg-gray-400',
  off: 'bg-gray-300',
  not_started: 'bg-gray-300',
}

const STATUS_LABELS: Record<string, string> = {
  running: 'Running',
  local_online: 'Local Online',
  fallback_running: 'OpenAI Fallback',
  fallback_waiting: 'Fallback Idle',
  local_offline: 'Local Offline',
  waiting: 'Waiting',
  training: 'Training',
  completed: 'Done',
  error: 'Error',
  paused: 'Paused',
  off: 'Off',
  not_started: 'Not Started',
}

function StatusDot({ status }: { status: string }) {
  const color = STATUS_COLORS[status] || 'bg-gray-300'
  const isActive = ['running', 'local_online', 'fallback_running', 'training'].includes(status)
  return (
    <span className="relative flex h-3 w-3">
      {isActive && (
        <span className={`absolute inline-flex h-full w-full animate-ping rounded-full opacity-75 ${color}`} />
      )}
      <span className={`relative inline-flex h-3 w-3 rounded-full ${color}`} />
    </span>
  )
}

function Arrow({ count, label }: { count: number; label: string }) {
  return (
    <div className="flex flex-col items-center justify-center px-2 min-w-[80px]">
      <span className="text-xs font-semibold text-gray-700">{count.toLocaleString()}</span>
      <div className="flex items-center w-full">
        <div className="flex-1 h-px bg-gray-300" />
        <svg className="w-3 h-3 text-gray-400 -ml-px flex-shrink-0" viewBox="0 0 12 12" fill="currentColor">
          <path d="M2 6l8-4v8z" />
        </svg>
      </div>
      <span className="text-[10px] text-gray-400">{label}</span>
    </div>
  )
}

interface StageBoxProps {
  title: string
  subtitle: string
  stage: PipelineStageStatus | { status: string }
  rows: { label: string; value: string | number }[]
  action?: { label: string; onClick: () => void; disabled?: boolean }
  progress?: { current: number; max: number }
}

function StageBox({ title, subtitle, stage, rows, action, progress }: StageBoxProps) {
  const status = stage.status || 'not_started'
  return (
    <div className="flex-1 border border-gray-200 rounded-lg p-4 bg-white min-w-[200px]">
      <div className="flex items-center gap-2 mb-1">
        <StatusDot status={status} />
        <h3 className="text-sm font-semibold text-gray-900">{title}</h3>
      </div>
      <p className="text-[11px] text-gray-400 mb-3">{subtitle}</p>
      <div className="flex items-center gap-1.5 mb-3">
        <span
          className={`text-xs font-medium px-2 py-0.5 rounded-full ${
            ['running', 'local_online', 'fallback_running', 'training'].includes(status)
              ? 'bg-green-50 text-green-700'
              : status === 'error'
                ? 'bg-red-50 text-red-700'
                : ['waiting', 'fallback_waiting', 'local_offline'].includes(status)
                  ? 'bg-yellow-50 text-yellow-700'
                  : 'bg-gray-100 text-gray-500'
          }`}
        >
          {STATUS_LABELS[status] || status}
        </span>
      </div>
      <dl className="space-y-1.5">
        {rows.map(r => (
          <div key={r.label} className="flex justify-between text-xs">
            <dt className="text-gray-500">{r.label}</dt>
            <dd className="font-mono text-gray-800">{r.value}</dd>
          </div>
        ))}
      </dl>
      {progress && (
        <div className="mt-2">
          <div className="w-full bg-gray-100 rounded-full h-1.5">
            <div
              className="bg-blue-500 h-1.5 rounded-full transition-all duration-500"
              style={{ width: `${Math.min(100, (progress.current / Math.max(progress.max, 1)) * 100)}%` }}
            />
          </div>
          <p className="text-[10px] text-gray-400 mt-0.5 text-right">
            {progress.current} / {progress.max}
          </p>
        </div>
      )}
      {action && (
        <div className="mt-3 pt-2 border-t border-gray-100">
          <Button size="sm" variant="secondary" onClick={action.onClick} disabled={action.disabled}>
            {action.label}
          </Button>
        </div>
      )}
    </div>
  )
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

  const [budgetInput, setBudgetInput] = useState(5)
  const [showConfig, setShowConfig] = useState(false)

  useEffect(() => {
    if (data?.budget?.per_hour) setBudgetInput(data.budget.per_hour)
  }, [data?.budget?.per_hour])

  if (isLoading || !data) {
    return (
      <Card className="p-6">
        <div className="animate-pulse space-y-4">
          <div className="h-8 bg-gray-200 rounded w-64" />
          <div className="h-40 bg-gray-100 rounded" />
        </div>
      </Card>
    )
  }

  const { stages, totals, budget, enabled } = data
  const crawl = stages.crawl || { status: 'not_started' } as PipelineStageStatus
  const extract = stages.extract || { status: 'not_started' } as PipelineStageStatus
  const ml = stages.ml || { status: 'not_started' } as PipelineStageStatus

  const mlExtra = (ml as PipelineStageStatus).extra || {}
  const outcomeCount = (mlExtra as any).current_outcomes ?? totals.outcome_count
  const outcomeRequired = (mlExtra as any).required_outcomes ?? 30
  const extractExtra = (extract as PipelineStageStatus).extra || {}

  const spentPct = budget.per_hour > 0
    ? Math.min(100, (budget.spent_this_hour / budget.per_hour) * 100)
    : 0

  return (
    <div className="space-y-4">
      {/* Controls bar */}
      <Card className="p-4">
        <div className="flex items-center justify-between flex-wrap gap-4">
          <div className="flex items-center gap-3">
            <button
              onClick={() => toggleMut.mutate(!enabled)}
              disabled={toggleMut.isPending}
              className={`relative inline-flex h-7 w-12 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-offset-1 ${
                enabled ? 'bg-green-500 focus:ring-green-400' : 'bg-gray-300 focus:ring-gray-400'
              }`}
            >
              <span
                className={`inline-block h-5 w-5 transform rounded-full bg-white shadow transition-transform ${
                  enabled ? 'translate-x-6' : 'translate-x-1'
                }`}
              />
            </button>
            <span className={`text-sm font-semibold ${enabled ? 'text-green-700' : 'text-gray-500'}`}>
              {enabled ? 'Pipeline ON' : 'Pipeline OFF'}
            </span>
          </div>

          <div className="flex items-center gap-3">
            <span className="text-xs text-gray-500">Budget</span>
            <input
              type="range"
              min={0.5}
              max={50}
              step={0.5}
              value={budgetInput}
              onChange={e => setBudgetInput(Number(e.target.value))}
              onMouseUp={() => throttleMut.mutate(budgetInput)}
              onTouchEnd={() => throttleMut.mutate(budgetInput)}
              className="w-28 accent-blue-500"
            />
            <span className="text-xs font-mono font-semibold w-16">${budgetInput.toFixed(2)}/hr</span>
          </div>

          <div className="flex items-center gap-2 text-xs">
            <span className="text-gray-500">Spent:</span>
            <div className="w-20 bg-gray-100 rounded-full h-2">
              <div
                className={`h-2 rounded-full transition-all ${spentPct > 80 ? 'bg-red-500' : 'bg-blue-500'}`}
                style={{ width: `${spentPct}%` }}
              />
            </div>
            <span className="font-mono text-gray-700">
              ${budget.spent_this_hour.toFixed(2)} / ${budget.per_hour.toFixed(2)}
            </span>
          </div>
        </div>
      </Card>

      {/* Streamline pipeline flow */}
      <Card className="p-6 overflow-x-auto">
        <div className="flex items-stretch min-w-[700px]">
          <StageBox
            title="Crawl"
            subtitle="AWS Fargate 24/7"
            stage={crawl}
            rows={[
              { label: 'Last activity', value: timeAgo((crawl as PipelineStageStatus).last_activity_at ?? null) },
              { label: 'This hour', value: (crawl as PipelineStageStatus).items_processed_hour ?? 0 },
              { label: 'Total', value: (crawl as PipelineStageStatus).items_processed_total ?? 0 },
              { label: 'Frontier', value: `${totals.frontier_pending} pending` },
            ]}
            action={{
              label: 'Force Discovery',
              onClick: () => forceMut.mutate('discover'),
              disabled: forceMut.isPending,
            }}
          />

          <Arrow count={totals.raw_docs_queued} label="raw docs" />

          <StageBox
            title="Extract"
            subtitle={
              (extract as PipelineStageStatus).worker_hostname
                ? `Local: ${(extract as PipelineStageStatus).worker_hostname}`
                : 'Local Ollama + OpenAI fallback'
            }
            stage={extract}
            rows={[
              { label: 'Last activity', value: timeAgo((extract as PipelineStageStatus).last_activity_at ?? null) },
              { label: 'This hour', value: (extract as PipelineStageStatus).items_processed_hour ?? 0 },
              { label: 'Model', value: String((extractExtra as any).worker_model ?? 'pending') },
              { label: 'Worker seen', value: timeAgo((extract as PipelineStageStatus).worker_heartbeat_at ?? null) },
            ]}
            action={{
              label: 'Retry Failed',
              onClick: () => forceMut.mutate('flush_failed'),
              disabled: forceMut.isPending,
            }}
          />

          <Arrow count={totals.docs_completed} label="completed" />

          <StageBox
            title="ML Train"
            subtitle="AWS Fargate 24/7"
            stage={ml}
            rows={[
              { label: 'Last activity', value: timeAgo((ml as PipelineStageStatus).last_activity_at ?? null) },
              { label: 'Outcomes', value: `${outcomeCount} / ${outcomeRequired}` },
              { label: 'Knowledge base', value: `${totals.docs_completed} docs` },
            ]}
            progress={{ current: outcomeCount, max: outcomeRequired }}
            action={{
              label: 'Force Train',
              onClick: () => forceMut.mutate('train'),
              disabled: forceMut.isPending,
            }}
          />
        </div>
      </Card>

      {/* Advanced config */}
      <Card className="p-4">
        <button
          onClick={() => setShowConfig(!showConfig)}
          className="text-sm text-gray-500 hover:text-gray-700 font-medium flex items-center gap-1"
        >
          <span className="text-xs">{showConfig ? '▼' : '▶'}</span>
          Advanced Config
        </button>
        {showConfig && (
          <div className="mt-4 grid grid-cols-1 md:grid-cols-3 gap-6 text-sm">
            <div>
              <h4 className="font-semibold text-gray-700 mb-2 text-xs uppercase tracking-wide">Crawl</h4>
              <ConfigField label="RPM" configKey="crawl_rpm" defaultVal={10} />
              <ConfigField label="Concurrency" configKey="crawl_concurrent" defaultVal={10} />
            </div>
            <div>
              <h4 className="font-semibold text-gray-700 mb-2 text-xs uppercase tracking-wide">Extract</h4>
              <ConfigField label="Ollama Model" configKey="extract_model" defaultVal="qwen2.5:7b" type="text" />
              <ConfigField label="Idle sleep (s)" configKey="extract_idle_seconds" defaultVal={5} />
              <ConfigField label="Heartbeat (s)" configKey="heartbeat_timeout" defaultVal={300} />
            </div>
            <div>
              <h4 className="font-semibold text-gray-700 mb-2 text-xs uppercase tracking-wide">ML Train</h4>
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
    <div className="flex items-center gap-2 mb-1.5">
      <label className="text-gray-500 w-24 text-xs">{label}</label>
      <input
        type={type}
        value={value}
        onChange={e => setValue(e.target.value)}
        onBlur={() => saveMut.mutate()}
        className="border border-gray-200 rounded px-2 py-1 text-xs w-24 font-mono focus:outline-none focus:ring-1 focus:ring-blue-400"
      />
    </div>
  )
}
