import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  CartesianGrid,
  Line,
  LineChart,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { ShieldCheck, ShieldAlert, AlertTriangle, RefreshCw, ShieldX } from 'lucide-react'
import Card from '../../../components/ui/Card'
import Badge from '../../../components/ui/Badge'
import Button from '../../../components/ui/Button'
import Select from '../../../components/ui/Select'
import Modal from '../../../components/ui/Modal'
import Textarea from '../../../components/ui/Textarea'
import Skeleton from '../../../components/ui/Skeleton'
import EmptyState from '../../../components/ui/EmptyState'
import QueryError from '../../../components/ui/QueryError'
import { showToast } from '../../../stores/toast-store'
import { AXIS_TICK, CHART, GRID_STROKE, TOOLTIP_STYLE } from '../analytics/constants'
import {
  getFairnessOverview,
  getFairnessCohorts,
  applyFairnessOverride,
  revokeFairnessOverride,
  setFairnessThreshold,
  recomputeFairness,
  type FairnessProgramBlock,
  type FairnessStatus,
} from '../../../api/fairness'
import { attributeLabel, severityBadge, severityDotClass } from './fairnessUi'

const MIN_RATIONALE = 100

const STATUS_META: Record<
  FairnessStatus,
  { Icon: typeof ShieldCheck; tone: string; label: string; cardClass: string; blurb: string }
> = {
  green: {
    Icon: ShieldCheck,
    tone: 'text-success',
    label: 'All clear',
    cardClass: 'border-success/30',
    blurb: 'No cohort is over its disparate-impact threshold.',
  },
  yellow: {
    Icon: AlertTriangle,
    tone: 'text-warning',
    label: 'Approaching threshold',
    cardClass: 'border-warning-soft bg-warning-soft/30',
    blurb: 'One or more cohorts are approaching the disparate-impact threshold.',
  },
  red: {
    Icon: ShieldAlert,
    tone: 'text-error',
    label: 'Action needed',
    cardClass: 'border-error/40 bg-error-soft/20',
    blurb: 'A cohort breached the threshold for two consecutive weeks — scoring is paused.',
  },
}

const THRESHOLD_OPTIONS = [0.05, 0.1, 0.15, 0.2, 0.25, 0.3, 0.35, 0.4].map(v => ({
  value: v.toFixed(2),
  label: `Δ ${v.toFixed(2)}`,
}))

const fmtWeek = (iso: string) => {
  const [, m, d] = iso.split('-')
  return `${m}/${d}`
}

export default function FairnessPage() {
  const queryClient = useQueryClient()
  const [override, setOverride] = useState<{ programId: string; programName: string } | null>(null)
  const [rationale, setRationale] = useState('')
  const [weeks, setWeeks] = useState('1')
  const [ack, setAck] = useState(false)

  const overviewQ = useQuery({ queryKey: ['fairness-overview'], queryFn: getFairnessOverview })
  const cohortsQ = useQuery({ queryKey: ['fairness-cohorts'], queryFn: getFairnessCohorts })

  const invalidate = () => {
    queryClient.invalidateQueries({ queryKey: ['fairness-overview'] })
    queryClient.invalidateQueries({ queryKey: ['fairness-cohorts'] })
  }

  const recomputeMut = useMutation({
    mutationFn: () => recomputeFairness(4),
    onSuccess: r => {
      invalidate()
      showToast(`Recomputed ${r.computations} cohort-week${r.computations !== 1 ? 's' : ''}`, 'success')
    },
    onError: () => showToast('Could not recompute fairness signals', 'error'),
  })

  const thresholdMut = useMutation({
    mutationFn: ({ programId, threshold }: { programId: string; threshold: number }) =>
      setFairnessThreshold(programId, threshold),
    onSuccess: () => {
      invalidate()
      showToast('Threshold updated', 'success')
    },
    onError: () => showToast('Could not update threshold', 'error'),
  })

  const overrideMut = useMutation({
    mutationFn: () =>
      applyFairnessOverride({
        program_id: override!.programId,
        rationale: rationale.trim(),
        weeks: Number(weeks),
      }),
    onSuccess: () => {
      invalidate()
      showToast('Override applied — scoring resumed', 'success')
      closeModal()
    },
    onError: (err: { response?: { data?: { detail?: string } } }) =>
      showToast(err.response?.data?.detail || 'Could not apply override', 'error'),
  })

  const revokeMut = useMutation({
    mutationFn: (programId: string) => revokeFairnessOverride(programId),
    onSuccess: () => {
      invalidate()
      showToast('Override revoked — scoring re-halted', 'success')
    },
    onError: () => showToast('Could not revoke override', 'error'),
  })

  const closeModal = () => {
    setOverride(null)
    setRationale('')
    setWeeks('1')
    setAck(false)
  }

  const overview = overviewQ.data
  const programs = cohortsQ.data?.programs ?? []
  const overrides = cohortsQ.data?.overrides ?? []
  const meta = STATUS_META[overview?.status ?? 'green']
  const hasSignals = programs.some(p => p.attributes.length > 0)

  if (overviewQ.isLoading || cohortsQ.isLoading) {
    return <Skeleton className="h-96 w-full rounded-xl" />
  }

  // A failed load must not read as "No fairness readings yet" (false all-clear
  // on a compliance surface). Surface the error with a retry instead.
  if (overviewQ.isError || cohortsQ.isError) {
    return (
      <QueryError
        title="We couldn't load fairness status."
        detail="This is not an all-clear — the readings failed to load. Try again."
        onRetry={() => {
          overviewQ.refetch()
          cohortsQ.refetch()
        }}
      />
    )
  }

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-start justify-between flex-wrap gap-3">
        <div>
          <h2 className="text-lg font-bold text-foreground">Fairness governance</h2>
        </div>
        <Button
          variant="secondary"
          size="sm"
          loading={recomputeMut.isPending}
          onClick={() => recomputeMut.mutate()}
        >
          <RefreshCw size={14} className="mr-1.5" /> Recompute
        </Button>
      </div>

      {/* Status banner */}
      {overview && (
        <Card pad={false} className={`p-4 ${meta.cardClass}`}>
          <div className="flex items-center gap-2 mb-1">
            <meta.Icon size={18} className={meta.tone} />
            <h3 className="text-sm font-semibold text-foreground">{meta.label}</h3>
            {overview.halted_count > 0 && (
              <Badge variant="error">
                {overview.halted_count} paused
              </Badge>
            )}
          </div>
          <p className="text-sm text-muted-foreground">{meta.blurb}</p>
        </Card>
      )}

      {/* Empty state */}
      {!hasSignals && (
        <EmptyState
          title="No fairness readings yet"
          action={{ label: 'Recompute now', onClick: () => recomputeMut.mutate() }}
        />
      )}

      {/* Per-program cards */}
      {programs
        .filter(p => p.attributes.length > 0)
        .map(p => (
          <ProgramCard
            key={p.program_id}
            program={p}
            onThreshold={(threshold: number) => thresholdMut.mutate({ programId: p.program_id, threshold })}
            onOverride={() => setOverride({ programId: p.program_id, programName: p.program_name })}
            onRevoke={() => revokeMut.mutate(p.program_id)}
            revoking={revokeMut.isPending}
          />
        ))}

      {/* Override history */}
      {overrides.length > 0 && (
        <Card pad={false} className="p-5">
          <p className="text-eyebrow font-semibold uppercase tracking-[0.22em] text-muted-foreground mb-3">
            Override history
          </p>
          <div className="space-y-2">
            {overrides.map(o => (
              <div key={o.id} className="text-sm border-l-2 border-secondary/40 pl-3">
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="font-medium text-foreground">{o.program_name ?? 'Program'}</span>
                  <Badge variant={o.active ? 'info' : 'neutral'}>{o.active ? 'Active' : 'Ended'}</Badge>
                  {o.created_at && (
                    <span className="text-xs text-muted-foreground">
                      {new Date(o.created_at).toLocaleDateString()}
                    </span>
                  )}
                </div>
                <p className="text-xs text-muted-foreground mt-0.5">{o.rationale}</p>
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* Override modal */}
      <Modal
        isOpen={override !== null}
        onClose={closeModal}
        title="Override fairness halt"
        footer={
          <div className="flex justify-end gap-2">
            <Button variant="tertiary" size="sm" onClick={closeModal}>
              Cancel
            </Button>
            <Button
              variant="secondary"
              size="sm"
              loading={overrideMut.isPending}
              disabled={rationale.trim().length < MIN_RATIONALE || !ack}
              onClick={() => overrideMut.mutate()}
            >
              Resume scoring
            </Button>
          </div>
        }
      >
        <div className="space-y-3">
          <p className="text-sm text-muted-foreground">
            Resuming scoring for <span className="font-medium text-foreground">{override?.programName}</span>{' '}
            overrides the automatic pause. This is logged with your name and rationale (Spec 46 §6.3).
          </p>
          <div>
            <Textarea
              value={rationale}
              onChange={e => setRationale(e.target.value)}
              rows={4}
              placeholder="Explain why scoring should resume (e.g. the gap reflects a small applicant pool this cycle, not scoring bias). Minimum 100 characters."
            />
            <p
              className={`text-xs mt-1 ${
                rationale.trim().length < MIN_RATIONALE ? 'text-muted-foreground' : 'text-success'
              }`}
            >
              {rationale.trim().length}/{MIN_RATIONALE} characters
            </p>
          </div>
          <Select
            label="Override window"
            value={weeks}
            onChange={e => setWeeks(e.target.value)}
            options={[
              { value: '1', label: '1 week' },
              { value: '2', label: '2 weeks' },
              { value: '3', label: '3 weeks' },
              { value: '4', label: '4 weeks (max)' },
            ]}
          />
          <label className="flex items-start gap-2 text-sm text-foreground cursor-pointer">
            <input
              type="checkbox"
              checked={ack}
              onChange={e => setAck(e.target.checked)}
              className="mt-0.5 accent-secondary"
            />
            I acknowledge this override is recorded in the audit log and expires automatically.
          </label>
        </div>
      </Modal>
    </div>
  )
}

function ProgramCard({
  program,
  onThreshold,
  onOverride,
  onRevoke,
  revoking,
}: {
  program: FairnessProgramBlock
  onThreshold: (threshold: number) => void
  onOverride: () => void
  onRevoke: () => void
  revoking: boolean
}) {
  return (
    <Card pad={false} className={`p-5 ${program.matching_halted ? 'border-l-4 border-l-error' : ''}`}>
      <div className="flex items-start justify-between flex-wrap gap-3 mb-3">
        <div className="flex items-center gap-2 flex-wrap">
          <h3 className="text-base font-semibold text-foreground">{program.program_name}</h3>
          {program.matching_halted ? (
            <Badge variant="error">
              <ShieldX size={11} className="inline -mt-0.5 mr-1" /> Scoring paused
            </Badge>
          ) : program.fairness_override_active ? (
            <Badge variant="info">Override active</Badge>
          ) : (
            <Badge variant="success">Scoring active</Badge>
          )}
          {program.fairness_override_active && program.override_expires_at && (
            <span className="text-xs text-muted-foreground">
              until {new Date(program.override_expires_at).toLocaleDateString()}
            </span>
          )}
        </div>
        <div className="flex items-center gap-2">
          <div className="w-32">
            <Select
              uiSize="sm"
              value={(program.fairness_threshold ?? 0.2).toFixed(2)}
              onChange={e => onThreshold(Number(e.target.value))}
              options={THRESHOLD_OPTIONS}
            />
          </div>
          {program.matching_halted ? (
            <Button variant="secondary" size="sm" onClick={onOverride}>
              Override
            </Button>
          ) : program.fairness_override_active ? (
            <Button variant="tertiary" size="sm" loading={revoking} onClick={onRevoke}>
              Re-halt
            </Button>
          ) : null}
        </div>
      </div>

      <div className="grid gap-3 md:grid-cols-2">
        {program.attributes.map(a => {
          const latest = a.latest
          const chartData = a.series.map(s => ({
            week: fmtWeek(s.week_start),
            delta: s.delta,
          }))
          const threshold = (latest?.detail?.threshold as number) ?? program.fairness_threshold ?? 0.2
          return (
            <div key={a.attribute} className="rounded-lg border border-border p-3">
              <div className="flex items-center justify-between gap-2 mb-1">
                <div className="flex items-center gap-2">
                  <span
                    className={`inline-block w-2 h-2 rounded-full ${severityDotClass(
                      latest?.severity ?? 'info',
                      latest?.sample_sufficient ?? false
                    )}`}
                  />
                  <span className="text-sm font-medium text-foreground">
                    {attributeLabel(a.attribute)}
                  </span>
                </div>
                {latest && latest.sample_sufficient
                  ? severityBadge(latest.severity)
                  : <span className="text-xs text-muted-foreground">insufficient sample</span>}
              </div>

              {latest?.sample_sufficient && latest.delta != null ? (
                <p className="text-xs text-muted-foreground mb-1">
                  Δ {latest.delta.toFixed(2)} · DI {latest.di_ratio?.toFixed(2) ?? '—'} · n=
                  {latest.cohort_size}
                </p>
              ) : (
                <p className="text-xs text-muted-foreground mb-1">
                  n={latest?.cohort_size ?? 0} — need ≥50 for a reading
                </p>
              )}

              {chartData.length >= 2 && (
                <ResponsiveContainer width="100%" height={56}>
                  <LineChart data={chartData} margin={{ top: 4, right: 4, left: 0, bottom: 0 }}>
                    <CartesianGrid stroke={GRID_STROKE} strokeOpacity={0.4} vertical={false} />
                    <XAxis dataKey="week" tick={AXIS_TICK} axisLine={false} tickLine={false} />
                    <YAxis hide domain={[0, 'dataMax']} />
                    <Tooltip
                      contentStyle={TOOLTIP_STYLE}
                      formatter={value => [typeof value === 'number' ? value.toFixed(2) : '—', 'Δ']}
                    />
                    <ReferenceLine y={threshold} stroke={CHART.amber} strokeDasharray="3 3" />
                    <Line
                      type="monotone"
                      dataKey="delta"
                      stroke={CHART.cobalt}
                      strokeWidth={2}
                      dot={{ r: 2 }}
                      connectNulls
                    />
                  </LineChart>
                </ResponsiveContainer>
              )}
            </div>
          )
        })}
      </div>
    </Card>
  )
}
