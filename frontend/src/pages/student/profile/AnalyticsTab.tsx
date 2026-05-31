/**
 * Profile → Analytics tab (spec 10 §15).
 * 15.1 Profile analytics (completion + signal density) · 15.2 Peer comparison.
 * Peer comparison is gated on analytics consent (consent_research).
 * Uses lightweight CSS bars (brand tokens) rather than a chart lib.
 */
import { useQuery } from '@tanstack/react-query'
import { BarChart3, Lock } from 'lucide-react'

import { getAnalytics, getDataRights, getPeerComparison, getProfileOverview } from '../../../api/students'
import Card from '../../../components/ui/Card'
import { SkeletonCard } from '../../../components/ui/Skeleton'
import type { ProfileOverview } from '../../../types'
import CompletionRing from './CompletionRing'
import { EmptyHint } from './_shared'

const CATEGORY_LABEL: Record<string, string> = {
  identity: 'Identity', academics: 'Academics', experience: 'Experience', goals: 'Goals',
  needs: 'Needs', strategy: 'Strategy', preparation: 'Preparation', preferences: 'Preferences',
  financial: 'Financial', data: 'Data',
}

function BarRow({
  label,
  value,
  max = 100,
  suffix = '%',
  color = 'bg-cobalt',
}: {
  label: string
  value: number
  max?: number
  suffix?: string
  color?: string
}) {
  const pct = max > 0 ? Math.min(100, Math.round((value / max) * 100)) : 0
  return (
    <div className="flex items-center gap-3">
      <span className="text-xs text-charcoal w-28 shrink-0 truncate capitalize">{label}</span>
      <div className="flex-1 h-2.5 rounded-full bg-student-mist overflow-hidden">
        <div className={`h-full ${color} rounded-full transition-all duration-500`} style={{ width: `${pct}%` }} />
      </div>
      <span className="text-xs text-slate tabular-nums w-12 text-right">{value}{suffix}</span>
    </div>
  )
}

export default function AnalyticsTab() {
  const { data: overview, isLoading } = useQuery<ProfileOverview>({ queryKey: ['profile-overview'], queryFn: getProfileOverview })
  const { data: analytics } = useQuery({ queryKey: ['analytics'], queryFn: getAnalytics, retry: false })
  const { data: dataRights } = useQuery({ queryKey: ['data-rights'], queryFn: getDataRights, retry: false })
  const analyticsConsent = dataRights?.consent_research !== false
  const { data: peer } = useQuery({
    queryKey: ['peer-comparison'],
    queryFn: getPeerComparison,
    retry: false,
    enabled: analyticsConsent,
  })

  if (isLoading) return <div className="space-y-4"><SkeletonCard /><SkeletonCard /></div>

  const cats = overview?.completion?.per_category ?? []
  const sectionCounts: Record<string, number> = analytics?.profile?.section_counts ?? {}
  const densityEntries = Object.entries(sectionCounts) as [string, number][]
  const maxCount = Math.max(1, ...densityEntries.map(([, v]) => v))
  const sorted = [...cats].sort((a, b) => b.pct - a.pct)
  const strongest = sorted[0]
  const weakest = sorted[sorted.length - 1]
  const peerMetrics: any[] = peer?.metrics ?? []

  return (
    <div className="space-y-6">
      {/* 15.1 Profile analytics */}
      <Card className="p-5">
        <div className="flex items-center gap-2 mb-4">
          <BarChart3 size={16} className="text-cobalt" />
          <h3 className="font-semibold text-charcoal">Profile analytics</h3>
        </div>
        <div className="flex flex-col sm:flex-row items-start gap-6">
          <CompletionRing value={overview?.completion?.overall_pct ?? 0} size={96} label="overall" />
          <div className="flex-1 w-full min-w-0 space-y-2">
            {cats.map(c => (
              <BarRow key={c.category} label={CATEGORY_LABEL[c.category] ?? c.category} value={c.pct} />
            ))}
          </div>
        </div>
        {strongest && weakest && (
          <div className="grid grid-cols-2 gap-3 mt-5">
            <div className="rounded-lg bg-student-mist p-3">
              <p className="text-xs text-slate">Strongest section</p>
              <p className="text-sm font-semibold text-charcoal">{CATEGORY_LABEL[strongest.category] ?? strongest.category} · {strongest.pct}%</p>
            </div>
            <div className="rounded-lg bg-student-mist p-3">
              <p className="text-xs text-slate">Needs attention</p>
              <p className="text-sm font-semibold text-charcoal">{CATEGORY_LABEL[weakest.category] ?? weakest.category} · {weakest.pct}%</p>
            </div>
          </div>
        )}
      </Card>

      {densityEntries.length > 0 && (
        <Card className="p-5">
          <h3 className="font-semibold text-charcoal mb-4">Signal density</h3>
          <div className="space-y-2">
            {densityEntries.map(([name, count]) => (
              <BarRow key={name} label={name.replace(/_/g, ' ')} value={count} max={maxCount} suffix="" color="bg-gold" />
            ))}
          </div>
        </Card>
      )}

      {/* 15.2 Peer comparison — gated on analytics consent */}
      <Card className="p-5">
        <h3 className="font-semibold text-charcoal mb-3">Peer comparison</h3>
        {!analyticsConsent ? (
          <div className="flex items-start gap-2">
            <Lock size={15} className="text-slate mt-0.5 shrink-0" />
            <EmptyHint>Peer comparison requires analytics consent. Manage in Data Rights.</EmptyHint>
          </div>
        ) : peerMetrics.length === 0 ? (
          <EmptyHint>Not enough data to compare yet. Add more to your profile to see how you stack up.</EmptyHint>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            {peerMetrics.map((m: any) => (
              <div key={m.metric} className="rounded-lg bg-student-mist p-3">
                <p className="text-xs text-slate">{m.metric}</p>
                <p className="text-lg font-semibold text-charcoal">{m.value}</p>
                <p className="text-[11px] text-slate">{m.label} · {m.percentile}th pct</p>
              </div>
            ))}
          </div>
        )}
      </Card>
    </div>
  )
}
