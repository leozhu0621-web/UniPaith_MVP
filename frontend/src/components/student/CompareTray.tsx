import { Fragment, useEffect, useState } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import { useMutation } from '@tanstack/react-query'
import { useCompareStore } from '../../stores/compare-store'
import { comparePrograms } from '../../api/saved-lists'
import Badge from '../ui/Badge'
import Button from '../ui/Button'
import { X, ArrowRightLeft, ChevronUp, ChevronDown, GraduationCap } from 'lucide-react'
import { COMPARE_DIMENSIONS, type CompareProgram } from './compareDimensions'

interface CompareTrayProps {
  initialExpanded?: boolean
  syncUrl?: boolean
}

export default function CompareTray({ initialExpanded = false, syncUrl = false }: CompareTrayProps) {
  const { items, remove, clear, hydrate, hydrated } = useCompareStore()
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

  if (items.length === 0) return null

  return (
    <div className="fixed inset-x-0 bottom-[calc(56px+env(safe-area-inset-bottom))] lg:bottom-0 z-40">
      {expanded && comparisonResult && (
        <div className="bg-card border-t border-border elev-raised max-h-[60vh] overflow-y-auto">
          <div className="max-w-5xl mx-auto p-4 sm:p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-h3 text-foreground">Side-by-side comparison</h3>
              <button onClick={() => setExpanded(false)} aria-label="Collapse" className="text-muted-foreground hover:text-foreground">
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
                        {dim.rows.map(row => (
                          <tr key={row.label} className="border-t border-border">
                            <td className="sticky left-0 z-10 bg-card py-2 px-3 text-xs text-muted-foreground font-medium">
                              {row.label}
                            </td>
                            {(comparisonResult.programs as CompareProgram[]).map(p => (
                              <td key={p.id} className="py-2 px-3 text-xs text-foreground">
                                {row.get(p)}
                              </td>
                            ))}
                          </tr>
                        ))}
                      </Fragment>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      )}

      <div className="bg-ink text-white elev-raised">
        <div className="max-w-5xl mx-auto px-4 py-2.5 flex items-center gap-3">
          <ArrowRightLeft size={16} className="text-cream/60 flex-shrink-0" />
          <span className="hidden sm:inline text-xs text-cream/60 flex-shrink-0">Compare</span>
          <div className="flex items-center gap-2 flex-1 overflow-x-auto no-scrollbar">
            {items.map(item => (
              <span key={item.program_id} className="inline-flex items-center gap-1.5 px-2.5 py-1 bg-white/10 rounded-full text-xs whitespace-nowrap flex-shrink-0">
                <GraduationCap size={12} className="text-cream/60" />
                <span className="max-w-[140px] truncate">{item.program_name}</span>
                {item.degree_type && <Badge variant="info" size="sm">{item.degree_type}</Badge>}
                <button onClick={() => remove(item.program_id)} aria-label="Remove" className="text-cream/50 hover:text-white">
                  <X size={12} />
                </button>
              </span>
            ))}
          </div>
          <div className="flex items-center gap-2 flex-shrink-0">
            <Button size="sm" onClick={() => compareMut.mutate()} disabled={items.length < 2 || compareMut.isPending} loading={compareMut.isPending} className="!bg-primary !text-primary-foreground hover:brightness-95">
              Compare ({items.length})
            </Button>
            {comparisonResult && (
              <button onClick={() => setExpanded(!expanded)} aria-label={expanded ? 'Collapse' : 'Expand'} className="p-1 text-cream/60 hover:text-white">
                {expanded ? <ChevronDown size={16} /> : <ChevronUp size={16} />}
              </button>
            )}
            <button onClick={clear} className="text-cream/60 hover:text-white text-xs">Clear</button>
          </div>
        </div>
      </div>
    </div>
  )
}
