import { useEffect, useState } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import { useMutation } from '@tanstack/react-query'
import { useCompareStore } from '../../stores/compare-store'
import { comparePrograms } from '../../api/saved-lists'
import Badge from '../ui/Badge'
import Button from '../ui/Button'
import Card from '../ui/Card'
import { X, ArrowRightLeft, ChevronUp, ChevronDown, GraduationCap } from 'lucide-react'

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
            {comparisonResult.ai_analysis && (
              <Card variant="card-flush" className="p-4 mb-4 bg-muted">
                <p className="text-sm text-foreground">{comparisonResult.ai_analysis}</p>
              </Card>
            )}
            {comparisonResult.comparison_data && (
              <div className="overflow-x-auto rounded-lg border border-border">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="bg-muted">
                      <th className="sticky left-0 z-10 bg-muted text-left py-2 px-3 text-xs text-muted-foreground font-semibold">Field</th>
                      {items.map(item => (
                        <th key={item.program_id} className="text-left py-2 px-3 text-xs text-foreground font-semibold whitespace-nowrap">
                          {item.program_name}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {Object.entries(comparisonResult.comparison_data as Record<string, Record<string, string>>).map(([field, values]) => (
                      <tr key={field} className="border-t border-border">
                        <td className="sticky left-0 z-10 bg-card py-2 px-3 text-xs text-muted-foreground font-medium capitalize">
                          {field.replace(/_/g, ' ')}
                        </td>
                        {items.map(item => (
                          <td key={item.program_id} className="py-2 px-3 text-xs text-foreground">
                            {String(values[item.program_id] ?? '—')}
                          </td>
                        ))}
                      </tr>
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
