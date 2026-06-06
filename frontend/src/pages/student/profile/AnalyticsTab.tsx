/**
 * Profile → Analytics tab (Spec/08 §15).
 * 15.1 Profile analytics — completion ring, per-category bars, progress over
 *      time, signal density, strongest/weakest callouts.
 * 15.2 Peer comparison — gated on the analytics consent lever.
 */
import { useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { Area, AreaChart, Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { TrendingUp, TrendingDown } from 'lucide-react'

import Card from '../../../components/ui/Card'
import { SkeletonCard } from '../../../components/ui/Skeleton'
import { getAnalytics, getDataRights, getPeerComparison, getTimeline } from '../../../api/students'
import { SectionHeader, CompletionRing } from './shared'
import { useCompletion } from './useCompletion'

// Read a CSS custom property from the document root at call time.
// Must be called inside a render body so theme changes re-read the value.
const cssVar = (name: string): string =>
  `hsl(${getComputedStyle(document.documentElement).getPropertyValue(name).trim()})`

function CategoryBars({ stats }: { stats: ReturnType<typeof useCompletion>['stats'] }) {
  return (
    <div className="space-y-3">
      {stats.map(s => (
        <div key={s.key}>
          <div className="flex items-center justify-between mb-1">
            <span className="text-sm text-foreground">{s.label}</span>
            <span className="text-xs font-bold text-foreground tabular-nums">{s.pct}%</span>
          </div>
          <div className="h-2 w-full rounded-pill bg-border overflow-hidden">
            <div className="h-full rounded-pill bg-secondary transition-all duration-500" style={{ width: `${s.pct}%` }} />
          </div>
        </div>
      ))}
    </div>
  )
}

export default function AnalyticsTab() {
  const navigate = useNavigate()
  const { stats, overall, isLoading } = useCompletion()
  const { data: analytics } = useQuery({ queryKey: ['analytics'], queryFn: getAnalytics, retry: false })
  const { data: timeline } = useQuery({ queryKey: ['timeline'], queryFn: getTimeline, retry: false })
  const { data: dataRights } = useQuery({ queryKey: ['data-rights'], queryFn: getDataRights, retry: false })
  const { data: peer } = useQuery({ queryKey: ['peer-comparison'], queryFn: getPeerComparison, retry: false })

  // Default to false until the data-rights query resolves, so we never flash
  // gated peer-comparison content the student hasn't consented to.
  const analyticsConsent = dataRights ? Boolean(dataRights.consent_research) : false

  // Theme-aware chart palette + tooltip surface.
  // Reading inside the render body means a theme change (light→dark) causes a
  // re-render that re-reads the updated CSS vars rather than using stale values.
  const COBALT = cssVar('--secondary')
  const GOLD = cssVar('--primary')
  const tooltipStyle = {
    background: cssVar('--card'),
    border: `1px solid ${cssVar('--border')}`,
    borderRadius: 8,
    color: cssVar('--foreground'),
    fontSize: 12,
  } as const
  const tooltipLabelStyle = { color: cssVar('--foreground') }
  const tooltipItemStyle = { color: cssVar('--muted-foreground') }

  const densityData = useMemo(() => {
    const counts: Record<string, number> = analytics?.profile?.section_counts ?? {}
    return Object.entries(counts).map(([name, value]) => ({
      name: name.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase()),
      value: value as number,
    }))
  }, [analytics])

  const progressData = useMemo(() => {
    const list: any[] = Array.isArray(timeline) ? timeline : []
    const sorted = [...list].sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime())
    let cum = 0
    return sorted.map(i => {
      cum += 1
      return { date: new Date(i.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }), signals: cum }
    })
  }, [timeline])

  const ranked = [...stats].sort((a, b) => b.pct - a.pct)
  const strongest = ranked.slice(0, 2)
  const weakest = [...ranked].reverse().filter(s => s.pct < 100).slice(0, 2)

  const peerMetrics: any[] = peer?.metrics ?? []

  if (isLoading) return <div className="space-y-3"><SkeletonCard /><SkeletonCard /></div>

  return (
    <div className="space-y-10">
      {/* 15.1 Profile analytics */}
      <section>
        <SectionHeader title="Profile analytics" description="How complete your record is and where the gaps are." />
        <div className="grid lg:grid-cols-2 gap-4">
          <Card className="p-5 flex items-center gap-5">
            <CompletionRing value={overall} size={96} stroke={8} />
            <div>
              <p className="up-eyebrow">Overall completion</p>
              <p className="text-h2 text-foreground mt-1">{overall}%</p>
              <p className="text-sm text-muted-foreground mt-0.5">across {stats.length} clusters</p>
            </div>
          </Card>
          <Card className="p-5">
            <p className="up-eyebrow mb-3">By cluster</p>
            <CategoryBars stats={stats} />
          </Card>
        </div>
      </section>

      <section className="grid lg:grid-cols-2 gap-4">
        <Card className="p-5">
          <p className="up-eyebrow mb-3">Progress over time</p>
          {progressData.length < 2 ? (
            <p className="text-sm text-muted-foreground py-8 text-center">
              Not enough data to plot yet. Keep building your profile and this fills in.
            </p>
          ) : (
            <ResponsiveContainer width="100%" height={200}>
              <AreaChart data={progressData} margin={{ top: 8, right: 8, left: -20, bottom: 0 }}>
                <defs>
                  <linearGradient id="signalFill" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor={COBALT} stopOpacity={0.25} />
                    <stop offset="100%" stopColor={COBALT} stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid stroke="hsl(var(--border))" strokeOpacity={0.5} vertical={false} />
                <XAxis dataKey="date" tick={{ fontSize: 11, fill: 'hsl(var(--muted-foreground))' }} tickLine={false} axisLine={false} />
                <YAxis tick={{ fontSize: 11, fill: 'hsl(var(--muted-foreground))' }} tickLine={false} axisLine={false} allowDecimals={false} />
                <Tooltip contentStyle={tooltipStyle} labelStyle={tooltipLabelStyle} itemStyle={tooltipItemStyle} cursor={{ stroke: 'hsl(var(--border))' }} />
                <Area type="monotone" dataKey="signals" stroke={COBALT} strokeWidth={2} fill="url(#signalFill)" />
              </AreaChart>
            </ResponsiveContainer>
          )}
        </Card>
        <Card className="p-5">
          <p className="up-eyebrow mb-3">Signal density</p>
          {densityData.length === 0 ? (
            <p className="text-sm text-muted-foreground py-8 text-center">Add records to see how your signals stack up by area.</p>
          ) : (
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={densityData} margin={{ top: 8, right: 8, left: -20, bottom: 0 }}>
                <CartesianGrid stroke="hsl(var(--border))" strokeOpacity={0.5} vertical={false} />
                <XAxis dataKey="name" tick={{ fontSize: 10, fill: 'hsl(var(--muted-foreground))' }} tickLine={false} axisLine={false} interval={0} angle={-20} textAnchor="end" height={50} />
                <YAxis tick={{ fontSize: 11, fill: 'hsl(var(--muted-foreground))' }} tickLine={false} axisLine={false} allowDecimals={false} />
                <Tooltip contentStyle={tooltipStyle} labelStyle={tooltipLabelStyle} itemStyle={tooltipItemStyle} cursor={{ fill: 'hsl(var(--muted))' }} />
                <Bar dataKey="value" fill={COBALT} radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          )}
        </Card>
      </section>

      <section className="grid sm:grid-cols-2 gap-4">
        <Card className="p-5">
          <div className="flex items-center gap-2 mb-2">
            <TrendingUp size={16} className="text-success" />
            <p className="font-semibold text-foreground">Strongest sections</p>
          </div>
          <ul className="text-sm text-muted-foreground space-y-1">
            {strongest.map(s => (
              <li key={s.key}>{s.label} — <span className="font-semibold text-foreground">{s.pct}%</span></li>
            ))}
          </ul>
        </Card>
        <Card className="p-5">
          <div className="flex items-center gap-2 mb-2">
            <TrendingDown size={16} className="text-warning" />
            <p className="font-semibold text-foreground">Room to grow</p>
          </div>
          {weakest.length === 0 ? (
            <p className="text-sm text-muted-foreground">Every cluster is complete. Nicely done.</p>
          ) : (
            <ul className="text-sm text-muted-foreground space-y-1">
              {weakest.map(s => (
                <li key={s.key}>{s.label} — <span className="font-semibold text-foreground">{s.pct}%</span></li>
              ))}
            </ul>
          )}
        </Card>
      </section>

      {/* 15.2 Peer comparison */}
      <section>
        <SectionHeader title="Peer comparison" description="Anonymized benchmarks vs students with similar targets." />
        {!analyticsConsent ? (
          <Card className="p-5">
            <p className="text-sm text-muted-foreground">
              Peer comparison requires analytics consent. Manage in{' '}
              <button
                onClick={() => navigate('/s/profile?tab=data')}
                className="font-semibold text-secondary hover:underline"
              >
                Data Rights →
              </button>
            </p>
          </Card>
        ) : peerMetrics.length === 0 ? (
          <Card className="p-5">
            <p className="text-sm text-muted-foreground">
              Not enough data to plot yet. Add a GPA or test score and we'll benchmark you against similar students.
            </p>
          </Card>
        ) : (
          <div className="grid sm:grid-cols-2 gap-3">
            {peerMetrics.map((m: any) => (
              <Card key={m.metric} className="p-4">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-semibold text-foreground">{m.metric}</span>
                  <span className="text-sm font-bold text-foreground tabular-nums">{m.value}</span>
                </div>
                <div className="mt-2 h-2 w-full rounded-pill bg-border overflow-hidden">
                  <div className="h-full rounded-pill" style={{ width: `${m.percentile}%`, backgroundColor: GOLD }} />
                </div>
                <p className="text-xs text-muted-foreground mt-1.5">{m.label} · {m.percentile}th percentile</p>
              </Card>
            ))}
          </div>
        )}
      </section>
    </div>
  )
}
