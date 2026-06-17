import { Fragment, useEffect, useState } from 'react'
import clsx from 'clsx'
import { useLocation, useNavigate } from 'react-router-dom'
import { useMutation } from '@tanstack/react-query'
import { useCompareStore } from '../../stores/compare-store'
import { showToast } from '../../stores/toast-store'
import { confirmDialog } from '../../stores/confirm-store'
import { comparePrograms } from '../../api/saved-lists'
import Badge from '../ui/Badge'
import Button from '../ui/Button'
import StatBar from '../ui/StatBar'
import Coachmark from '../ui/Coachmark'
import { usePresence } from '../ui/usePresence'
import { X, ArrowRightLeft, ChevronUp, ChevronDown, GraduationCap } from 'lucide-react'
import { COMPARE_DIMENSIONS, type CompareProgram } from './compareDimensions'

interface CompareTrayProps {
  initialExpanded?: boolean
  syncUrl?: boolean
}

export default function CompareTray({ initialExpanded = false, syncUrl = false }: CompareTrayProps) {
  const { items, remove, clear, hydrate, hydrated, compareRunTick } = useCompareStore()
  const location = useLocation()
  const navigate = useNavigate()
  const [expanded, setExpanded] = useState(initialExpanded)
  const [comparisonResult, setComparisonResult] = useState<any>(null)

  // Spec 10 §8 — load the server-persisted compare set once per session so it
  // accumulates across reloads/devices.
  useEffect(() => {
    if (!hydrated) hydrate()
  }, [hydrated, hydrate])

  const compareMut = useMutation({
    mutationFn: () => comparePrograms(items.map(i => i.program_id)),
    onSuccess: (data) => {
      setComparisonResult(data)
      setExpanded(true)
    },
    onError: (e: unknown) =>
      showToast((e as Error).message ?? 'Could not build the comparison.', 'error'),
  })

  useEffect(() => {
    if (!syncUrl || !location.pathname.startsWith('/s/explore')) return
    const params = new URLSearchParams(location.search)
    if (items.length === 0) params.delete('compareIds')
    else params.set('compareIds', items.map(i => i.program_id).join(','))
    const qs = params.toString()
    const target = qs ? `/s/explore?${qs}` : '/s/explore'
    if (`${location.pathname}${location.search}` !== target) navigate(target, { replace: true })
  }, [items, syncUrl, location.pathname, location.search, navigate])

  useEffect(() => {
    if (initialExpanded && items.length >= 2 && !comparisonResult && !compareMut.isPending) {
      compareMut.mutate()
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [initialExpanded, items.length])

  useEffect(() => {
    if (compareRunTick > 0 && items.length >= 2 && !compareMut.isPending) {
      compareMut.mutate()
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [compareRunTick])

  // Clearing the whole set is destructive enough to confirm (Ship D §4) —
  // a stray tap otherwise wipes a carefully built compare list.
  const handleClear = async () => {
    const n = items.length
    const ok = await confirmDialog({
      title: `Remove all ${n} program${n === 1 ? '' : 's'} from compare?`,
      body: 'This empties the compare tray. You can re-add programs from any card.',
      confirmLabel: 'Remove all',
      destructive: true,
    })
    if (ok) clear()
  }

  // Slide the tray up when the first program is added and back down when the
  // set empties (usePresence holds it mounted for the exit beat). No backdrop.
  const { mounted, closing } = usePresence(items.length > 0)
  if (!mounted) return null

  return (
    <div
      className={clsx(
        'fixed inset-x-0 bottom-[calc(56px+env(safe-area-inset-bottom))] lg:bottom-0 z-40',
        closing ? 'animate-tray-out pointer-events-none' : 'animate-tray-in'
      )}
    >
      {expanded && comparisonResult && items.length > 0 && (
        <div className="bg-card border-t border-border elev-raised max-h-[60vh] overflow-y-auto">
          <div className="max-w-5xl mx-auto p-4 sm:p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-h3 text-foreground">Side-by-side comparison</h3>
              <button onClick={() => setExpanded(false)} aria-label="Collapse" className="p-3 -m-3 text-muted-foreground hover:text-foreground">
                <X size={18} />
              </button>
            </div>
            {comparisonResult.ai_analysis &&
              comparisonResult.ai_analysis !== 'AI analysis unavailable.' && (
                <div className="p-4 mb-4 rounded-lg bg-muted border border-border">
                  <p className="text-sm text-foreground">{comparisonResult.ai_analysis}</p>
                </div>
              )}
            {Array.isArray(comparisonResult.programs) && comparisonResult.programs.length > 0 && (
              <div className="overflow-x-auto rounded-lg border border-border">
                {/* Spec 10 §8 — five dimensions, side by side. */}
                <table className="w-full text-sm border-collapse">
                  <thead>
                    <tr className="bg-muted">
                      <th className="sticky left-0 z-10 bg-muted text-left py-2.5 px-3 text-xs text-muted-foreground font-semibold w-40">
                        Dimension
                      </th>
                      {(comparisonResult.programs as CompareProgram[]).map(p => (
                        <th
                          key={p.id}
                          className="text-left py-2.5 px-3 text-xs text-foreground font-semibold min-w-[150px] align-top"
                        >
                          {p.program_name}
                          {p.institution_name && (
                            <span className="block text-[11px] font-normal text-muted-foreground">
                              {p.institution_name}
                            </span>
                          )}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {COMPARE_DIMENSIONS.map(dim => (
                      <Fragment key={dim.title}>
                        <tr>
                          <td
                            colSpan={1 + comparisonResult.programs.length}
                            className="bg-muted/50 py-1.5 px-3 text-[11px] uppercase tracking-wide text-secondary font-semibold"
                          >
                            {dim.title}
                          </td>
                        </tr>
                        {dim.rows.map(row => {
                          const programs = comparisonResult.programs as CompareProgram[]
                          // Numeric rows get a magnitude bar (relative to the row
                          // max). The winning column is crowned only where "more is
                          // plainly better" (higherIsBetter); lower-better rows show
                          // bars but no winner.
                          const nums = row.num ? programs.map(p => row.num!(p)) : null
                          const rowMax = nums
                            ? Math.max(0, ...nums.filter((v): v is number => v != null))
                            : 0
                          let bestIdx = -1
                          if (nums && row.higherIsBetter && rowMax > 0) {
                            bestIdx = nums.findIndex(v => v === rowMax)
                          }
                          return (
                            <tr key={row.label} className="border-t border-border">
                              <td className="sticky left-0 z-10 bg-card py-2 px-3 text-xs text-muted-foreground font-medium">
                                {row.label}
                              </td>
                              {programs.map((p, idx) => {
                                const isBest = idx === bestIdx
                                const v = nums ? nums[idx] : null
                                return (
                                  <td
                                    key={p.id}
                                    className={`py-2 px-3 text-xs ${isBest ? 'text-secondary font-semibold' : 'text-foreground'}`}
                                  >
                                    <span className="tabular-nums">{row.get(p)}</span>
                                    {nums && v != null && (
                                      <StatBar value={v} max={rowMax} best={isBest} className="mt-1" />
                                    )}
                                  </td>
                                )
                              })}
                            </tr>
                          )
                        })}
                      </Fragment>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      )}

      <div className="bg-foreground text-background elev-raised">
        <div className="max-w-5xl mx-auto px-4 py-2.5 flex items-center gap-3">
          <ArrowRightLeft size={16} className="text-background/60 flex-shrink-0" />
          <span className="hidden sm:inline text-xs text-background/60 flex-shrink-0">Compare</span>
          <div className="flex items-center gap-2 flex-1 overflow-x-auto no-scrollbar">
            {items.map(item => (
              <span key={item.program_id} className="inline-flex items-center gap-1.5 px-2.5 py-1 bg-background/10 rounded-full text-xs whitespace-nowrap flex-shrink-0">
                <GraduationCap size={12} className="text-background/60" />
                <span className="max-w-[140px] truncate">{item.program_name}</span>
                {item.degree_type && <Badge variant="info" size="sm">{item.degree_type}</Badge>}
                {/* ≥40px tap target via padding + negative margin — no visual size jump (Ship D §4). */}
                <button onClick={() => remove(item.program_id)} aria-label={`Remove ${item.program_name} from compare`} className="p-3.5 -m-3.5 text-background/50 hover:text-background">
                  <X size={12} />
                </button>
              </span>
            ))}
          </div>
          <div className="flex items-center gap-2 flex-shrink-0">
            <Coachmark
              id="compare"
              title="Compare side by side"
              body="Add 2+ programs, then compare structure, cost, access, and outcomes in one view."
              placement="top"
            >
              <Button size="sm" variant="secondary" onClick={() => compareMut.mutate()} disabled={items.length < 2 || compareMut.isPending} loading={compareMut.isPending}>
                Compare selected ({items.length}) →
              </Button>
            </Coachmark>
            {comparisonResult && (
              <button onClick={() => setExpanded(!expanded)} aria-label={expanded ? 'Collapse' : 'Expand'} className="p-3 -m-2 text-background/60 hover:text-background">
                {expanded ? <ChevronDown size={16} /> : <ChevronUp size={16} />}
              </button>
            )}
            <button onClick={handleClear} className="px-2 py-3 -my-3 text-background/60 hover:text-background text-xs">Clear</button>
          </div>
        </div>
      </div>
    </div>
  )
}
