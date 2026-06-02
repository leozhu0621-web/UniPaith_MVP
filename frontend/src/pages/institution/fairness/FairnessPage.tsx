/**
 * Spec 46 §6 — Fairness auto-halt surface. Mounted at /i/admissions?tab=fairness
 * (and ?tab=fairness-overrides, which focuses the override history).
 *
 * Surfaces the verbatim §6 commitment, the per-cohort halt status (green /
 * amber / red), a 4-week disparate-impact sparkline + per-attribute heatmap,
 * per-program threshold config, and the override workflow (rationale ≥100 chars).
 */
import { useMemo, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
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
import { AlertOctagon, AlertTriangle, CheckCircle2, RefreshCw, ShieldCheck } from 'lucide-react'

import Card from '../../../components/ui/Card'
import Badge from '../../../components/ui/Badge'
import Button from '../../../components/ui/Button'
import Modal from '../../../components/ui/Modal'
import Select from '../../../components/ui/Select'
import { SkeletonCard } from '../../../components/ui/Skeleton'
import {
  computeFairness,
  createFairnessOverride,
  getFairnessStatus,
  listFairnessOverrides,
  listFairnessSignals,
  updateFairnessThreshold,
} from '../../../api/fairness'
import type { FairnessProgramStatus, FairnessSignal } from '../../../types/fairness'
import { AXIS_TICK, CHART, GRID_STROKE, TOOLTIP_STYLE } from '../analytics/constants'
import { showToast } from '../../../stores/toast-store'

const ATTR_LABEL: Record<string, string> = {
  gender: 'Gender',
  first_gen: 'First-gen',
  international: 'International',
  nationality_region: 'Region',
  race: 'Race / ethnicity',
  disability: 'Disability',
  veteran: 'Veteran',
}

const shortWeek = (iso: string) => {
  const d = new Date(iso + 'T00:00:00')
  return `${d.getMonth() + 1}/${d.getDate()}`
}

function cellTone(delta: number | null | undefined, threshold: number) {
  if (delta == null) return { cls: 'bg-muted text-muted-foreground', label: '—' }
  const label = delta.toFixed(2)
  if (delta > threshold) return { cls: 'bg-error-soft text-error', label }
  if (delta > threshold * 0.75) return { cls: 'bg-warning-soft text-warning', label }
  return { cls: 'bg-success-soft text-success', label }
}

function StatusBadge({ status }: { status: string }) {
  if (status === 'halted') return <Badge variant="danger">Halted</Badge>
  if (status === 'warning') return <Badge variant="warning">Watch</Badge>
  return <Badge variant="success">Clear</Badge>
}

interface OverrideModalState {
  program: FairnessProgramStatus
  signal: FairnessSignal | null
}

export default function FairnessPage({ focusOverrides = false }: { focusOverrides?: boolean }) {
  const qc = useQueryClient()
  const statusQ = useQuery({ queryKey: ['fairness-status'], queryFn: getFairnessStatus, retry: false })
  const overridesQ = useQuery({
    queryKey: ['fairness-overrides'],
    queryFn: () => listFairnessOverrides(),
    retry: false,
  })

  const [overrideModal, setOverrideModal] = useState<OverrideModalState | null>(null)
  const [rationale, setRationale] = useState('')
  const [expiryWeeks, setExpiryWeeks] = useState('1')

  const recompute = useMutation({
    mutationFn: () => computeFairness(),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['fairness-status'] })
      showToast('Fairness check refreshed', 'success')
    },
    onError: () => showToast("Couldn't refresh the check. Try again.", 'error'),
  })

  const thresholdMut = useMutation({
    mutationFn: (v: { program_id: string; threshold: number }) => updateFairnessThreshold(v),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['fairness-status'] })
      showToast('Threshold updated', 'success')
    },
    onError: (e: any) => showToast(e?.message || 'Update failed', 'error'),
  })

  const overrideMut = useMutation({
    mutationFn: (v: { signal_id: string; rationale: string; expires_weeks: number }) =>
      createFairnessOverride(v),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['fairness-status'] })
      qc.invalidateQueries({ queryKey: ['fairness-overrides'] })
      setOverrideModal(null)
      setRationale('')
      showToast('Override logged — matching resumed for this cohort', 'success')
    },
    onError: (e: any) => showToast(e?.message || 'Override failed', 'error'),
  })

  const openOverride = async (program: FairnessProgramStatus) => {
    setRationale('')
    setExpiryWeeks('1')
    let signal: FairnessSignal | null = null
    try {
      const signals = await listFairnessSignals(program.program_id)
      signal =
        signals.find(s => ['auto_halt', 'override_active', 'high'].includes(s.severity)) ??
        signals[0] ??
        null
    } catch {
      signal = null
    }
    setOverrideModal({ program, signal })
  }

  const submitOverride = () => {
    if (!overrideModal?.signal) {
      showToast('No fairness signal to override yet.', 'error')
      return
    }
    overrideMut.mutate({
      signal_id: overrideModal.signal.id,
      rationale: rationale.trim(),
      expires_weeks: Number(expiryWeeks),
    })
  }

  const status = statusQ.data
  const overrides = overridesQ.data ?? []
  const overall = status?.overall_status ?? 'ok'

  const bannerTone = useMemo(() => {
    if (overall === 'halted')
      return {
        cls: 'border-error/40 bg-error-soft/40',
        icon: <AlertOctagon size={18} className="text-error" />,
        title: 'Matching halted for one or more cohorts',
      }
    if (overall === 'warning')
      return {
        cls: 'border-warning/40 bg-warning-soft/30',
        icon: <AlertTriangle size={18} className="text-warning" />,
        title: 'A cohort is approaching the fairness threshold',
      }
    return {
      cls: 'border-success/30 bg-success-soft/30',
      icon: <CheckCircle2 size={18} className="text-success" />,
      title: 'All cohorts within the fairness threshold',
    }
  }, [overall])

  if (statusQ.isLoading) {
    return (
      <div className="space-y-3">
        <SkeletonCard />
        <SkeletonCard />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* The verbatim §6 commitment. */}
      <Card className="p-5 border-l-4 border-l-secondary">
        <div className="flex items-start gap-3">
          <ShieldCheck size={18} className="text-secondary shrink-0 mt-0.5" />
          <div>
            <p className="text-sm text-foreground font-medium leading-relaxed">
              “If disparate-impact Δ exceeds the threshold for two consecutive weeks, the model
              stops scoring new applicants for that cohort.”
            </p>
            <p className="text-xs text-muted-foreground mt-1">
              Every cohort is audited weekly. Flags escalate to humans; halts are reversible with a
              logged rationale. Existing scores are never changed — only new scoring pauses.
            </p>
          </div>
        </div>
      </Card>

      {/* Overall status banner. */}
      <Card className={`p-4 border ${bannerTone.cls}`}>
        <div className="flex items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            {bannerTone.icon}
            <span className="text-sm font-semibold text-foreground">{bannerTone.title}</span>
          </div>
          <Button
            size="sm"
            variant="tertiary"
            onClick={() => recompute.mutate()}
            loading={recompute.isPending}
          >
            <RefreshCw size={14} /> Run check
          </Button>
        </div>
      </Card>

      {/* Per-program cohorts. */}
      {!status || status.programs.length === 0 ? (
        <Card className="p-8 text-center">
          <p className="text-sm text-muted-foreground">
            No programs to audit yet. Once applicants are scored, weekly disparate-impact readings
            appear here per cohort and protected attribute.
          </p>
        </Card>
      ) : (
        <div className="space-y-4">
          {status.programs.map(program => (
            <ProgramCard
              key={program.program_id}
              program={program}
              weeks={status.weeks}
              thresholdDefault={status.threshold_default}
              onThreshold={(threshold) =>
                thresholdMut.mutate({ program_id: program.program_id, threshold })
              }
              thresholdSaving={thresholdMut.isPending}
              onOverride={() => openOverride(program)}
            />
          ))}
        </div>
      )}

      {/* Override history (§6.3). Focused when arriving via ?tab=fairness-overrides. */}
      <Card className={`p-4 ${focusOverrides ? 'border-secondary/40' : ''}`}>
        <h3 className="text-sm font-semibold text-foreground mb-1">Override history</h3>
        <p className="text-xs text-muted-foreground mb-3">
          Every override is logged with its rationale, actor, and expiry. Expiry re-arms the halt on
          the next weekly check.
        </p>
        {overrides.length === 0 ? (
          <p className="text-sm text-muted-foreground">No overrides recorded.</p>
        ) : (
          <div className="space-y-2">
            {overrides.map(ov => (
              <div key={ov.id} className="rounded-lg border border-border p-3">
                <div className="flex items-center justify-between gap-2">
                  <span className="text-sm font-medium text-foreground">{ov.program_name}</span>
                  <div className="flex items-center gap-2">
                    <Badge variant="neutral">{ATTR_LABEL[ov.protected_attribute] ?? ov.protected_attribute}</Badge>
                    {ov.active ? (
                      <Badge variant="warning">Active</Badge>
                    ) : (
                      <Badge variant="neutral">Expired</Badge>
                    )}
                  </div>
                </div>
                <p className="text-sm text-muted-foreground mt-1.5">{ov.rationale}</p>
                <p className="text-xs text-muted-foreground/70 mt-1">
                  Expires {new Date(ov.override_expires_at).toLocaleDateString()}
                </p>
              </div>
            ))}
          </div>
        )}
      </Card>

      {/* Override request modal. */}
      <Modal
        isOpen={Boolean(overrideModal)}
        onClose={() => setOverrideModal(null)}
        title={`Override halt — ${overrideModal?.program.program_name ?? ''}`}
      >
        <div className="space-y-4">
          <p className="text-sm text-muted-foreground">
            Lifting the halt resumes scoring for this cohort. A written rationale (≥100 characters)
            is required and permanently logged in the audit ledger.
          </p>
          <div>
            <label className="text-sm font-medium text-foreground">Rationale</label>
            <textarea
              value={rationale}
              onChange={e => setRationale(e.target.value)}
              rows={4}
              placeholder="Explain why this override is justified (e.g. a small applicant pool in this round, not a scoring bias)…"
              className="mt-1 w-full rounded-lg border border-border bg-background px-3 py-2 text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-ring"
            />
            <p className={`text-xs mt-1 ${rationale.trim().length < 100 ? 'text-muted-foreground' : 'text-success'}`}>
              {rationale.trim().length}/100 characters
            </p>
          </div>
          <Select
            label="Override expires after"
            value={expiryWeeks}
            onChange={e => setExpiryWeeks(e.target.value)}
            options={[
              { value: '1', label: '1 week' },
              { value: '2', label: '2 weeks' },
              { value: '3', label: '3 weeks' },
              { value: '4', label: '4 weeks (max)' },
            ]}
          />
          <div className="flex justify-end gap-2">
            <Button variant="tertiary" onClick={() => setOverrideModal(null)}>
              Cancel
            </Button>
            <Button
              variant="secondary"
              onClick={submitOverride}
              loading={overrideMut.isPending}
              disabled={rationale.trim().length < 100}
            >
              Log override &amp; resume
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  )
}

function ProgramCard({
  program,
  weeks,
  thresholdDefault,
  onThreshold,
  thresholdSaving,
  onOverride,
}: {
  program: FairnessProgramStatus
  weeks: string[]
  thresholdDefault: number
  onThreshold: (v: number) => void
  thresholdSaving: boolean
  onOverride: () => void
}) {
  const [threshold, setThreshold] = useState(String(program.fairness_threshold ?? thresholdDefault))
  const attrs = Object.keys(program.attributes)
  const trendData = program.trend.map(t => ({ week: shortWeek(t.week_start), delta: t.delta }))
  const showOverride = program.status !== 'ok' || program.fairness_override_active
  const lowThresholdWarn = Number(threshold) < 0.1

  return (
    <Card className="p-4">
      <div className="flex items-start justify-between gap-3 mb-3">
        <div className="flex items-center gap-2">
          <h3 className="text-sm font-semibold text-foreground">{program.program_name}</h3>
          <StatusBadge status={program.status} />
          {program.fairness_override_active && <Badge variant="info">Override active</Badge>}
        </div>
        {showOverride && (
          <Button size="sm" variant="secondary" onClick={onOverride}>
            {program.matching_halted ? 'Override halt' : 'Pre-authorize override'}
          </Button>
        )}
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        {/* 4-week DI trend sparkline. */}
        <div>
          <p className="text-xs uppercase tracking-wide text-muted-foreground font-semibold mb-1">
            Disparate-impact Δ (4 weeks)
          </p>
          <div className="h-28">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={trendData} margin={{ top: 6, right: 8, bottom: 0, left: -20 }}>
                <CartesianGrid strokeDasharray="3 3" stroke={GRID_STROKE} vertical={false} />
                <XAxis dataKey="week" tick={AXIS_TICK} axisLine={false} tickLine={false} />
                <YAxis tick={AXIS_TICK} axisLine={false} tickLine={false} domain={[0, 1]} />
                <Tooltip contentStyle={TOOLTIP_STYLE} formatter={(v) => Number(v).toFixed(2)} />
                <ReferenceLine
                  y={program.fairness_threshold}
                  stroke={CHART.amber}
                  strokeDasharray="4 4"
                />
                <Line
                  type="monotone"
                  dataKey="delta"
                  stroke={CHART.cobalt}
                  strokeWidth={2}
                  dot={{ r: 3 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Per-attribute × week heatmap. */}
        <div className="overflow-x-auto">
          <p className="text-xs uppercase tracking-wide text-muted-foreground font-semibold mb-1">
            By protected attribute
          </p>
          {attrs.length === 0 ? (
            <p className="text-sm text-muted-foreground">No readings yet.</p>
          ) : (
            <table className="w-full text-xs">
              <thead>
                <tr className="text-muted-foreground">
                  <th className="text-left font-medium py-1 pr-2">Attribute</th>
                  {weeks.map(w => (
                    <th key={w} className="font-medium py-1 px-1 text-center">
                      {shortWeek(w)}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {attrs.map(attr => (
                  <tr key={attr}>
                    <td className="py-0.5 pr-2 text-foreground whitespace-nowrap">
                      {ATTR_LABEL[attr] ?? attr}
                    </td>
                    {weeks.map(w => {
                      const tone = cellTone(program.attributes[attr]?.[w], program.fairness_threshold)
                      return (
                        <td key={w} className="px-1 py-0.5">
                          <div
                            className={`rounded text-center py-1 font-semibold tabular-nums ${tone.cls}`}
                          >
                            {tone.label}
                          </div>
                        </td>
                      )
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>

      {/* Threshold config (§9). */}
      <div className="flex items-center gap-2 mt-4 pt-3 border-t border-border">
        <label className="text-xs text-muted-foreground">Threshold</label>
        <input
          type="number"
          step="0.01"
          min="0.05"
          max="0.40"
          value={threshold}
          onChange={e => setThreshold(e.target.value)}
          className="w-20 rounded-lg border border-border bg-background px-2 h-8 text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-ring"
        />
        <Button
          size="sm"
          variant="tertiary"
          onClick={() => onThreshold(Number(threshold))}
          loading={thresholdSaving}
          disabled={Number(threshold) < 0.05 || Number(threshold) > 0.4}
        >
          Save
        </Button>
        {lowThresholdWarn && (
          <span className="text-xs text-warning">
            Below 0.10 with a small sample tends to false-positive.
          </span>
        )}
      </div>
    </Card>
  )
}
