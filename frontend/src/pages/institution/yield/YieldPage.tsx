import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  LabelList,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import {
  TrendingUp,
  Users,
  Droplet,
  ListChecks,
  AlertTriangle,
  Send,
  ArrowRight,
  Megaphone,
} from 'lucide-react'
import { getYield, getWaitlist, offerToNextWaitlisted, bulkOfferWaitlist } from '../../../api/enrollment'
import { getInstitutionPrograms } from '../../../api/institutions'
import Card from '../../../components/ui/Card'
import Badge from '../../../components/ui/Badge'
import Button from '../../../components/ui/Button'
import Select from '../../../components/ui/Select'
import Skeleton from '../../../components/ui/Skeleton'
import AIBadge from '../../../components/ui/AIBadge'
import { showToast } from '../../../stores/toast-store'
import FunnelBars from '../analytics/FunnelBars'
import { AXIS_TICK, CHART, GRID_STROKE, TOOLTIP_STYLE } from '../analytics/constants'
import type { FunnelStageItem, YieldCohort, YieldSnapshot } from '../../../types'

const pct = (v: number | null | undefined) => (v == null ? '—' : `${Math.round(v * 100)}%`)

function Kpi({
  icon,
  label,
  value,
  sub,
  tone,
}: {
  icon: React.ReactNode
  label: string
  value: string
  sub?: string
  tone?: 'warning'
}) {
  return (
    <Card className="p-4">
      <div className="flex items-center gap-2 text-muted-foreground mb-1">
        {icon}
        <span className="text-xs font-medium uppercase tracking-wide">{label}</span>
      </div>
      <p className={`text-2xl font-bold tabular-nums ${tone === 'warning' ? 'text-warning' : 'text-foreground'}`}>
        {value}
      </p>
      {sub && <p className="text-xs text-muted-foreground mt-0.5">{sub}</p>}
    </Card>
  )
}

function CohortCard({ cohort }: { cohort: YieldCohort }) {
  return (
    <Card className={`p-4 ${cohort.fairness_concern ? 'border-l-4 border-l-warning' : ''}`}>
      <div className="flex items-center justify-between mb-2">
        <span className="text-sm font-medium text-foreground">{cohort.label}</span>
        {cohort.fairness_concern ? (
          <Badge variant="warning">
            <AlertTriangle size={11} className="inline -mt-0.5 mr-1" />
            {pct(cohort.disparity)} gap
          </Badge>
        ) : cohort.disparity != null ? (
          <span className="text-xs text-muted-foreground">{pct(cohort.disparity)} spread</span>
        ) : null}
      </div>
      <div className="space-y-1.5">
        {cohort.groups.map(g => (
          <div key={g.group} className="flex items-center gap-2 text-xs">
            <span className="w-28 shrink-0 truncate text-muted-foreground">{g.group}</span>
            <div className="flex-1 h-2 rounded-full bg-muted overflow-hidden">
              <div
                className={`h-full rounded-full ${cohort.fairness_concern ? 'bg-warning' : 'bg-secondary'}`}
                style={{ width: `${Math.round(g.yield_rate * 100)}%` }}
              />
            </div>
            <span className="w-20 shrink-0 text-right tabular-nums text-foreground">
              {pct(g.yield_rate)} ({g.enrolled}/{g.admitted})
            </span>
          </div>
        ))}
      </div>
      {cohort.fairness_concern && (
        <p className="text-xs text-warning mt-2">
          Surfaced for fairness review (46 §6) — yield work is outreach, never selection.
        </p>
      )}
    </Card>
  )
}

export default function YieldPage() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [programId, setProgramId] = useState<string>('')

  const programsQ = useQuery({ queryKey: ['inst-programs'], queryFn: getInstitutionPrograms })
  const params = programId ? { program_id: programId } : undefined
  const yieldQ = useQuery({
    queryKey: ['yield', programId],
    queryFn: () => getYield(params),
  })
  const waitlistQ = useQuery({
    queryKey: ['waitlist', programId],
    queryFn: () => getWaitlist(programId || undefined),
  })

  const invalidate = () => {
    queryClient.invalidateQueries({ queryKey: ['yield'] })
    queryClient.invalidateQueries({ queryKey: ['waitlist'] })
  }
  const offerNextMut = useMutation({
    mutationFn: () => offerToNextWaitlisted(programId),
    onSuccess: () => {
      invalidate()
      showToast('Offer released to the next waitlisted applicant', 'success')
    },
    onError: (err: { response?: { data?: { detail?: string } } }) =>
      showToast(err.response?.data?.detail || 'Could not offer to next', 'error'),
  })
  const bulkOfferMut = useMutation({
    mutationFn: (n: number) => bulkOfferWaitlist(programId, n),
    onSuccess: r => {
      invalidate()
      showToast(`Released ${r.offered_count} waitlist place${r.offered_count !== 1 ? 's' : ''}`, 'success')
    },
    onError: () => showToast('Could not release waitlist places', 'error'),
  })

  if (yieldQ.isLoading) return <Skeleton className="h-96 w-full rounded-xl" />
  if (yieldQ.isError)
    return (
      <Card className="p-10 text-center">
        <p className="mb-2 text-sm text-error">Couldn’t load yield analytics.</p>
        <button onClick={() => yieldQ.refetch()} className="text-secondary hover:underline text-sm">Retry</button>
      </Card>
    )
  const y = yieldQ.data as YieldSnapshot | undefined
  const programOptions = [
    { value: '', label: 'All programs' },
    ...(programsQ.data || []).map(p => ({ value: p.id, label: p.program_name })),
  ]

  // §7 — pre-decisions empty state.
  if (!y || y.empty || y.admitted === 0) {
    return (
      <div className="space-y-4">
        <YieldHeader programOptions={programOptions} programId={programId} setProgramId={setProgramId} />
        <Card className="p-10 text-center">
          <TrendingUp size={28} className="mx-auto mb-3 text-muted-foreground" />
          <p className="text-sm font-medium text-foreground mb-1">No yield to track yet</p>
          <p className="text-sm text-muted-foreground max-w-sm mx-auto">
            Yield tracking begins once you release decisions. Admit applicants from the pipeline and
            their enrollment progress will appear here.
          </p>
        </Card>
      </div>
    )
  }

  const funnelStages: FunnelStageItem[] = y.funnel.map(f => ({
    stage: f.step,
    label: f.step,
    count: f.count,
    conversion_from_prev: f.drop_off == null ? null : 1 - f.drop_off,
  }))
  const topAction = y.next_best_actions[0]
  const waitlist = waitlistQ.data

  return (
    <div className="space-y-4">
      <YieldHeader programOptions={programOptions} programId={programId} setProgramId={setProgramId} />

      {/* Next-best-action banner (§4) — AI-refined, falls back to counts. */}
      {topAction && (
        <Card className="p-4 border-l-4 border-l-cobalt">
          <div className="flex items-start justify-between gap-4 flex-wrap">
            <div className="min-w-0">
              <div className="flex items-center gap-2 mb-1">
                <Megaphone size={15} className="text-secondary" />
                <span className="text-xs font-semibold uppercase tracking-wide text-secondary">
                  Next best action
                </span>
                <AIBadge label="AI assist" />
              </div>
              <p className="text-sm font-medium text-foreground">{topAction.label}</p>
              <p className="text-xs text-muted-foreground mt-0.5">{topAction.rationale}</p>
            </div>
            {topAction.kind === 'nudge_unconfirmed' && (
              <Button variant="secondary" size="sm" onClick={() => navigate('/i/communications?tab=inbox')}>
                <Send size={14} className="mr-1" /> Send nudge
              </Button>
            )}
            {topAction.kind === 'release_waitlist' && programId && (
              <Button
                variant="secondary"
                size="sm"
                loading={offerNextMut.isPending}
                onClick={() => offerNextMut.mutate()}
              >
                Offer to next <ArrowRight size={14} className="ml-1" />
              </Button>
            )}
          </div>
          {y.next_best_actions.length > 1 && (
            <ul className="mt-3 pt-3 border-t border-border space-y-1">
              {y.next_best_actions.slice(1).map((a, i) => (
                <li key={i} className="text-xs text-muted-foreground flex items-center gap-1.5">
                  <ArrowRight size={11} className="shrink-0" /> {a.label}
                </li>
              ))}
            </ul>
          )}
        </Card>
      )}

      {/* KPI row */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        <Kpi
          icon={<TrendingUp size={14} />}
          label="Yield rate"
          value={pct(y.yield_rate)}
          sub={`${y.enrolled} enrolled of ${y.admitted} admitted`}
        />
        <Kpi
          icon={<Users size={14} />}
          label="Predicted class"
          value={
            y.target_class_size
              ? `${y.predicted_final_class_size} / ${y.target_class_size}`
              : String(y.predicted_final_class_size)
          }
          sub={y.target_class_size ? 'predicted vs target' : 'set a target to compare'}
        />
        <Kpi
          icon={<Droplet size={14} />}
          label="Melt"
          value={String(y.melt)}
          sub={`${pct(y.melt_rate)} of confirmed`}
          tone={y.melt_rate > 0.1 ? 'warning' : undefined}
        />
        <Kpi
          icon={<ListChecks size={14} />}
          label="Waitlist conv."
          value={pct(y.waitlist_conversion)}
          sub={`${y.waitlist_count} on waitlist`}
        />
      </div>

      {/* Funnel tail + time-to-confirm */}
      <div className="grid lg:grid-cols-2 gap-4">
        <Card className="p-5">
          <p className="text-eyebrow font-semibold uppercase tracking-[0.22em] text-muted-foreground mb-3">
            Funnel tail
          </p>
          <FunnelBars stages={funnelStages} />
        </Card>
        <Card className="p-5">
          <p className="text-eyebrow font-semibold uppercase tracking-[0.22em] text-muted-foreground mb-1">
            Time to confirm
          </p>
          <p className="text-xs text-muted-foreground mb-3">
            {y.time_to_confirm.count > 0
              ? `Median ${y.time_to_confirm.median_days}d · avg ${y.time_to_confirm.avg_days}d`
              : 'No confirmations yet'}
          </p>
          {y.time_to_confirm.count > 0 ? (
            <ResponsiveContainer width="100%" height={180}>
              <BarChart data={y.time_to_confirm.buckets} margin={{ top: 4, right: 8, left: 8, bottom: 0 }}>
                <CartesianGrid stroke={GRID_STROKE} strokeOpacity={0.5} vertical={false} />
                <XAxis dataKey="label" tick={AXIS_TICK} axisLine={false} tickLine={false} />
                <YAxis tick={AXIS_TICK} axisLine={false} tickLine={false} allowDecimals={false} />
                <Tooltip contentStyle={TOOLTIP_STYLE} cursor={{ fill: 'hsl(var(--muted))', opacity: 0.4 }} />
                <Bar dataKey="count" radius={[4, 4, 0, 0]} maxBarSize={48}>
                  {y.time_to_confirm.buckets.map((_, i) => (
                    <Cell key={i} fill={CHART.cobalt} />
                  ))}
                  <LabelList
                    dataKey="count"
                    position="top"
                    style={{ fontSize: 12, fill: 'hsl(var(--foreground))', fontWeight: 700 }}
                  />
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <p className="text-sm text-muted-foreground py-8 text-center">
              Confirmation timing appears once admits start confirming.
            </p>
          )}
        </Card>
      </div>

      {/* Yield by cohort — fairness lens (§4 / 46 §6) */}
      {y.cohorts.some(c => c.groups.length > 1) && (
        <div>
          <p className="text-eyebrow font-semibold uppercase tracking-[0.22em] text-muted-foreground mb-2">
            Yield by cohort · fairness lens
          </p>
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-3">
            {y.cohorts
              .filter(c => c.groups.length > 1)
              .map(c => (
                <CohortCard key={c.dimension} cohort={c} />
              ))}
          </div>
        </div>
      )}

      {/* Waitlist movement (§3.3) */}
      <Card className="p-5">
        <div className="flex items-center justify-between flex-wrap gap-2 mb-3">
          <p className="text-eyebrow font-semibold uppercase tracking-[0.22em] text-muted-foreground">
            Waitlist movement
          </p>
          <span className="text-sm text-foreground">
            {waitlist?.seats_open != null ? (
              <>
                <span className="font-semibold">{waitlist.seats_open}</span> seat
                {waitlist.seats_open !== 1 ? 's' : ''} open,{' '}
              </>
            ) : null}
            <span className="font-semibold">{waitlist?.waitlist_count ?? 0}</span> on waitlist
          </span>
        </div>
        {!programId ? (
          <p className="text-sm text-muted-foreground">
            Select a program above to release places to its ranked waitlist.
          </p>
        ) : (waitlist?.waitlist_count ?? 0) === 0 ? (
          <p className="text-sm text-muted-foreground">No applicants on the waitlist for this program.</p>
        ) : (
          <>
            <div className="flex items-center gap-2 mb-3">
              <Button
                variant="secondary"
                size="sm"
                loading={offerNextMut.isPending}
                onClick={() => offerNextMut.mutate()}
              >
                Offer to next
              </Button>
              {(waitlist?.waitlist_count ?? 0) > 1 && (
                <Button
                  variant="tertiary"
                  size="sm"
                  loading={bulkOfferMut.isPending}
                  onClick={() => bulkOfferMut.mutate(Math.min(waitlist!.seats_open || 1, waitlist!.waitlist_count))}
                >
                  Release {Math.min(waitlist!.seats_open || 1, waitlist!.waitlist_count)} to fill open seats
                </Button>
              )}
            </div>
            <ol className="space-y-1.5">
              {(waitlist?.waitlist || []).slice(0, 10).map(w => (
                <li key={w.application_id} className="flex items-center gap-2 text-sm">
                  <span className="w-6 text-xs text-muted-foreground tabular-nums">
                    #{w.waitlist_rank ?? '—'}
                  </span>
                  <button
                    onClick={() => navigate(`/i/pipeline/${w.application_id}?tab=enrollment`)}
                    className="text-foreground hover:text-secondary hover:underline"
                  >
                    {w.student_name || 'Applicant'}
                  </button>
                  <span className="text-xs text-muted-foreground">· {w.program_name}</span>
                </li>
              ))}
            </ol>
          </>
        )}
      </Card>
    </div>
  )
}

function YieldHeader({
  programOptions,
  programId,
  setProgramId,
}: {
  programOptions: { value: string; label: string }[]
  programId: string
  setProgramId: (v: string) => void
}) {
  return (
    <div className="flex items-center justify-between flex-wrap gap-3">
      <div>
        <h2 className="text-lg font-bold text-foreground">Enrollment & yield</h2>
        <p className="text-sm text-muted-foreground">
          Where your admitted class stands — confirmations, deposits, and melt.
        </p>
      </div>
      <div className="w-56">
        <Select
          value={programId}
          onChange={e => setProgramId(e.target.value)}
          options={programOptions}
        />
      </div>
    </div>
  )
}
