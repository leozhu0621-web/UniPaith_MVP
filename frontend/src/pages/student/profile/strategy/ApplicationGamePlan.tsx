/**
 * Application game-plan (Spec 2026-06-15 Ship B §2) — a sub-section of the
 * living strategy doc. Shows the reach / target / safer balance across the
 * student's applications, flags portfolio gaps, and surfaces the nearest
 * deadlines. Computed client-side from the applications + saved lists (same
 * fit_band → reach/target/safer mapping the portfolio uses); no new backend.
 */
import { useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { ArrowRight, Target as TargetIcon, ShieldCheck, Flame, CalendarClock } from 'lucide-react'
import Card from '../../../../components/ui/Card'
import { listMyApplications } from '../../../../api/applications'
import { listSaved } from '../../../../api/saved-lists'
import type { Application } from '../../../../types'

type Band = 'reach' | 'target' | 'safer'

// fit_band low/medium/high → reach/target/safer (matches ApplicationsPage).
function bandOf(app: Application): Band | null {
  switch (app.fit_band) {
    case 'low': return 'reach'
    case 'medium': return 'target'
    case 'high': return 'safer'
    default: return null
  }
}

function daysUntil(iso?: string | null): number | null {
  if (!iso) return null
  return Math.ceil((new Date(iso).getTime() - Date.now()) / 86_400_000)
}

export default function ApplicationGamePlan() {
  const navigate = useNavigate()
  const { data: appsData } = useQuery({ queryKey: ['my-applications'], queryFn: listMyApplications, staleTime: 60_000 })
  const { data: savedData } = useQuery({ queryKey: ['saved-programs'], queryFn: listSaved, staleTime: 60_000 })

  const apps: Application[] = useMemo(() => (Array.isArray(appsData) ? appsData : []), [appsData])
  const savedCount = Array.isArray(savedData) ? savedData.length : 0

  const { counts, unclassified, deadlines } = useMemo(() => {
    const c: Record<Band, number> = { reach: 0, target: 0, safer: 0 }
    let unknown = 0
    for (const a of apps) {
      const b = bandOf(a)
      if (b) c[b] += 1
      else unknown += 1
    }
    const dl = apps
      .map(a => ({ app: a, d: daysUntil(a.program?.application_deadline) }))
      .filter(x => x.d != null && x.d >= 0)
      .sort((a, b) => (a.d as number) - (b.d as number))
      .slice(0, 3)
    return { counts: c, unclassified: unknown, deadlines: dl }
  }, [apps])

  const total = apps.length
  // The one most useful nudge about portfolio balance.
  const nudge = (() => {
    if (total === 0) return 'No applications yet — start one from your saved list to build your game-plan.'
    if (counts.safer === 0) return 'No safer schools yet — add one to balance your list.'
    if (counts.reach === 0) return 'Every target looks safe — consider adding a reach school you would love.'
    if (counts.target === 0) return 'Add a few target schools to anchor your list.'
    return null
  })()

  const tiles: { band: Band; label: string; icon: typeof TargetIcon; tone: string }[] = [
    { band: 'reach', label: 'Reach', icon: Flame, tone: 'text-error' },
    { band: 'target', label: 'Target', icon: TargetIcon, tone: 'text-secondary' },
    { band: 'safer', label: 'Safer', icon: ShieldCheck, tone: 'text-success' },
  ]

  return (
    <div>
      <div className="flex items-center justify-between mb-2">
        <h3 className="text-sm font-semibold text-foreground">Application game-plan</h3>
        <button onClick={() => navigate('/s/applications')} className="inline-flex items-center gap-1 text-xs text-secondary hover:underline">
          Your portfolio <ArrowRight size={12} />
        </button>
      </div>
      <Card pad={false} className="p-5 space-y-4">
        <div className="grid grid-cols-3 gap-3">
          {tiles.map(t => (
            <div key={t.band} className="rounded-lg border border-border px-3 py-2.5">
              <div className="flex items-center gap-1.5">
                <t.icon size={14} className={t.tone} />
                <span className="text-xs uppercase tracking-wide text-muted-foreground">{t.label}</span>
              </div>
              <div className="mt-1 text-xl font-semibold text-foreground">{counts[t.band]}</div>
            </div>
          ))}
        </div>

        {unclassified > 0 && (
          <p className="text-xs text-muted-foreground">
            {unclassified} application{unclassified === 1 ? '' : 's'} not yet scored for fit — open them to generate a match.
          </p>
        )}

        {nudge && (
          <div className="flex items-start gap-2 rounded-lg border border-border border-l-2 border-l-primary bg-muted px-3 py-2.5 text-sm text-foreground">
            <span className="min-w-0">{nudge}</span>
            <button onClick={() => navigate('/s/saved')} className="ml-auto shrink-0 text-xs text-secondary hover:underline whitespace-nowrap">
              Balance your list
            </button>
          </div>
        )}

        {deadlines.length > 0 && (
          <div>
            <div className="text-xs uppercase tracking-wide text-muted-foreground mb-1.5">What's next</div>
            <div className="space-y-1">
              {deadlines.map(({ app, d }) => (
                <button
                  key={app.id}
                  onClick={() => navigate(`/s/applications/${app.id}`)}
                  className="flex w-full items-center gap-2 rounded-md px-1 py-1 text-left text-sm hover:bg-muted/50 transition-colors"
                >
                  <CalendarClock size={14} className="shrink-0 text-muted-foreground" />
                  <span className="min-w-0 flex-1 truncate text-foreground">{app.program?.program_name ?? 'Application'}</span>
                  <span className={`shrink-0 text-xs ${(d as number) <= 7 ? 'text-error font-medium' : 'text-muted-foreground'}`}>
                    {(d as number) === 0 ? 'today' : `${d}d`}
                  </span>
                </button>
              ))}
            </div>
          </div>
        )}

        <p className="text-xs text-muted-foreground">
          {savedCount > 0
            ? `${savedCount} program${savedCount === 1 ? '' : 's'} saved. `
            : ''}
          Reach / target / safer reflects each application's fitness band.
        </p>
      </Card>
    </div>
  )
}
