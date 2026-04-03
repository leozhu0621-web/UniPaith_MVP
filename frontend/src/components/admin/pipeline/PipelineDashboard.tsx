import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
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
  const navigate = useNavigate()

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

  const forceMut = useMutation({
    mutationFn: (action: string) =>
      apiClient.post('/admin/pipeline/force', { action }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['pipeline-status'] }),
  })

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

  const { stages, totals, enabled } = data
  const crawl = stages.crawl || { status: 'not_started' } as PipelineStageStatus
  const extract = stages.extract || { status: 'not_started' } as PipelineStageStatus
  const ml = stages.ml || { status: 'not_started' } as PipelineStageStatus

  const mlExtra = (ml as PipelineStageStatus).extra || {}
  const outcomeCount = totals.outcome_count
  const outcomeRequired = (mlExtra as any).required_outcomes ?? 30
  const extractExtra = (extract as PipelineStageStatus).extra || {}

  const cycleResult = (mlExtra as any).cycle_result || {}
  const evalResult = cycleResult.evaluation || null
  const trainResult = cycleResult.training || null
  const promoResult = cycleResult.promotion || null
  const bestAccuracy: number | null =
    promoResult?.success && trainResult?.test_metrics?.accuracy != null
      ? trainResult.test_metrics.accuracy
      : trainResult?.status === 'completed' && trainResult?.test_metrics?.accuracy != null
        ? trainResult.test_metrics.accuracy
        : evalResult?.metrics?.accuracy ?? null

  return (
    <div className="space-y-4">
      {/* Controls bar */}
      <Card className="p-4">
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
              label: 'Details',
              onClick: () => navigate('/admin/crawler'),
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

          <MLStageCard
            stage={ml as PipelineStageStatus}
            outcomeCount={outcomeCount}
            outcomeRequired={outcomeRequired}
            bestAccuracy={bestAccuracy}
            activeModel={promoResult?.promoted || trainResult?.model_version || evalResult?.model_version || null}
            promoResult={promoResult}
            onForceTrain={() => forceMut.mutate('train')}
            forceDisabled={forceMut.isPending}
          />
        </div>
      </Card>

    </div>
  )
}

function AccuracyRing({ value, size = 48 }: { value: number; size?: number }) {
  const pct = Math.round(value * 100)
  const r = (size - 6) / 2
  const circ = 2 * Math.PI * r
  const offset = circ * (1 - value)
  const color = value >= 0.7 ? 'text-green-500' : value >= 0.5 ? 'text-yellow-500' : 'text-red-500'
  return (
    <div className="relative" style={{ width: size, height: size }}>
      <svg width={size} height={size} className="-rotate-90">
        <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke="#f3f4f6" strokeWidth={5} />
        <circle
          cx={size / 2} cy={size / 2} r={r} fill="none"
          strokeWidth={5} strokeLinecap="round"
          className={`${color} transition-all duration-700`}
          stroke="currentColor"
          strokeDasharray={circ}
          strokeDashoffset={offset}
        />
      </svg>
      <span className="absolute inset-0 flex items-center justify-center text-[11px] font-bold text-gray-800">
        {pct}%
      </span>
    </div>
  )
}


function MLStageCard({
  stage,
  outcomeCount,
  outcomeRequired,
  bestAccuracy,
  activeModel,
  promoResult,
  onForceTrain,
  forceDisabled,
}: {
  stage: PipelineStageStatus
  outcomeCount: number
  outcomeRequired: number
  bestAccuracy: number | null
  activeModel: string | null
  promoResult: any
  onForceTrain: () => void
  forceDisabled: boolean
}) {
  const status = stage.status || 'not_started'
  const isReady = outcomeCount >= outcomeRequired
  const promoted = promoResult?.success === true

  return (
    <div className="flex-1 border border-gray-200 rounded-lg p-4 bg-white min-w-[220px]">
      <div className="flex items-center gap-2 mb-1">
        <StatusDot status={status} />
        <h3 className="text-sm font-semibold text-gray-900">ML Train</h3>
      </div>

      {/* Subtitle: active model or waiting reason */}
      <p className="text-[11px] text-gray-400 mb-3">
        {activeModel ? activeModel : isReady ? 'Ready to train' : `Need ${outcomeRequired - outcomeCount} more outcomes`}
      </p>

      <div className="flex items-center gap-1.5 mb-3">
        <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${
          ['training'].includes(status)
            ? 'bg-green-50 text-green-700'
            : status === 'completed'
              ? 'bg-green-50 text-green-700'
              : status === 'error'
                ? 'bg-red-50 text-red-700'
                : status === 'waiting'
                  ? (isReady ? 'bg-blue-50 text-blue-700' : 'bg-yellow-50 text-yellow-700')
                  : 'bg-gray-100 text-gray-500'
        }`}>
          {status === 'waiting' && !isReady
            ? 'Collecting data'
            : status === 'waiting' && isReady
              ? 'Ready'
              : STATUS_LABELS[status] || status}
        </span>
        {promoResult && (
          <span className={`text-[10px] px-1.5 py-0.5 rounded-full ${
            promoted ? 'bg-green-50 text-green-600' : 'bg-orange-50 text-orange-600'
          }`}>
            {promoted ? 'promoted' : 'kept prev'}
          </span>
        )}
      </div>

      {/* Accuracy ring or waiting indicator */}
      {bestAccuracy != null ? (
        <div className="flex items-center gap-3 mb-3">
          <AccuracyRing value={bestAccuracy} />
          <div className="text-[11px] space-y-0.5">
            <p className="text-gray-500">Model accuracy</p>
            <p className="font-mono text-gray-800 font-semibold">
              {(bestAccuracy * 100).toFixed(1)}%
            </p>
            <p className="text-gray-400">
              {stage.items_processed_total ?? 0} cycle{(stage.items_processed_total ?? 0) !== 1 ? 's' : ''} run
            </p>
          </div>
        </div>
      ) : !isReady ? (
        <div className="mb-3">
          <div className="w-full bg-gray-100 rounded-full h-1.5">
            <div
              className="bg-blue-500 h-1.5 rounded-full transition-all duration-500"
              style={{ width: `${Math.min(100, (outcomeCount / Math.max(outcomeRequired, 1)) * 100)}%` }}
            />
          </div>
          <p className="text-[10px] text-gray-400 mt-1">
            {outcomeCount} / {outcomeRequired} outcomes
          </p>
        </div>
      ) : (
        <p className="text-xs text-gray-400 mb-3">No training results yet</p>
      )}

      <dl className="space-y-1.5">
        <div className="flex justify-between text-xs">
          <dt className="text-gray-500">Last check</dt>
          <dd className="font-mono text-gray-800">{timeAgo(stage.last_activity_at ?? null)}</dd>
        </div>
        <div className="flex justify-between text-xs">
          <dt className="text-gray-500">Training data</dt>
          <dd className="font-mono text-gray-800">{outcomeCount} outcomes</dd>
        </div>
      </dl>

      <div className="mt-3 pt-2 border-t border-gray-100">
        <Button size="sm" variant="secondary" onClick={onForceTrain} disabled={forceDisabled}>
          Force Train
        </Button>
      </div>
    </div>
  )
}

