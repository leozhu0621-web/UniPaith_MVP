import { useState, useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { listSaved } from '../../api/saved-lists'
import { listMyApplications } from '../../api/applications'
import Card from '../../components/ui/Card'
import EmptyState from '../../components/ui/EmptyState'
import { SkeletonCard } from '../../components/ui/Skeleton'
import { formatCurrency } from '../../utils/format'
import { DollarSign, TrendingDown, TrendingUp, ArrowUpDown } from 'lucide-react'

// Rough living cost estimates by country (annual, USD)
const LIVING_COSTS: Record<string, number> = {
  'United States': 18000,
  'United Kingdom': 15000,
  'Canada': 14000,
  'Australia': 16000,
  'Germany': 11000,
  'Netherlands': 13000,
  'France': 12000,
  'Singapore': 15000,
  'Japan': 10000,
  'South Korea': 9000,
}
const DEFAULT_LIVING_COST = 12000

interface ProgramCost {
  id: string
  name: string
  institution: string
  country: string
  tuition: number | null
  livingCost: number
  expectedAid: number
  netCost: number
}

export default function FinancialAidPage() {
  const navigate = useNavigate()
  const [expectedAid, setExpectedAid] = useState<Record<string, string>>({})
  const [sortBy, setSortBy] = useState<'net' | 'tuition'>('net')

  const { data: saved, isLoading: savedLoading } = useQuery({ queryKey: ['saved'], queryFn: listSaved })
  const { data: applications, isLoading: appsLoading } = useQuery({ queryKey: ['my-applications'], queryFn: listMyApplications })

  const isLoading = savedLoading || appsLoading

  // Combine saved + applied programs (deduplicate by program_id)
  const allPrograms = useMemo(() => {
    const sl: any[] = Array.isArray(saved) ? saved : []
    const al: any[] = Array.isArray(applications) ? applications : []
    const seen = new Set<string>()
    const result: { id: string; name: string; institution: string; country: string; tuition: number | null }[] = []

    sl.forEach((s: any) => {
      if (s.program && !seen.has(s.program_id)) {
        seen.add(s.program_id)
        result.push({
          id: s.program_id,
          name: s.program.program_name,
          institution: s.program.institution_name,
          country: s.program.institution_country || '',
          tuition: s.program.tuition,
        })
      }
    })

    al.forEach((a: any) => {
      if (a.program && !seen.has(a.program_id)) {
        seen.add(a.program_id)
        result.push({
          id: a.program_id,
          name: a.program.program_name || 'Program',
          institution: a.program.institution_name || '',
          country: a.program.institution_country || '',
          tuition: a.program.tuition ?? null,
        })
      }
    })

    return result
  }, [saved, applications])

  // Compute costs
  const programCosts: ProgramCost[] = useMemo(() => {
    return allPrograms.map(p => {
      const livingCost = LIVING_COSTS[p.country] ?? DEFAULT_LIVING_COST
      const aid = Number(expectedAid[p.id] || 0)
      const tuition = p.tuition ?? 0
      const netCost = tuition + livingCost - aid
      return {
        id: p.id,
        name: p.name,
        institution: p.institution,
        country: p.country,
        tuition: p.tuition,
        livingCost,
        expectedAid: aid,
        netCost: Math.max(0, netCost),
      }
    }).sort((a, b) => {
      if (sortBy === 'net') return a.netCost - b.netCost
      return (a.tuition ?? Infinity) - (b.tuition ?? Infinity)
    })
  }, [allPrograms, expectedAid, sortBy])

  // Summary stats
  const cheapest = programCosts.length > 0 ? programCosts[0] : null
  const mostExpensive = programCosts.length > 0 ? programCosts[programCosts.length - 1] : null
  const avgNet = programCosts.length > 0
    ? Math.round(programCosts.reduce((sum, p) => sum + p.netCost, 0) / programCosts.length)
    : 0

  if (isLoading) return <div className="space-y-4">{Array.from({ length: 3 }).map((_, i) => <SkeletonCard key={i} />)}</div>

  return (
    <div>
      {allPrograms.length === 0 ? (
        <EmptyState
          icon={<DollarSign size={48} />}
          title="No programs to compare"
          description="Save or apply to programs to see cost estimates here."
          action={{ label: 'Discover Programs', onClick: () => navigate('/s/explore') }}
        />
      ) : (
        <>
          {/* Summary Cards */}
          <div className="grid grid-cols-3 gap-4 mb-6">
            <Card className="p-4 text-center">
              <TrendingDown size={20} className="mx-auto text-success mb-1" />
              <p className="text-xs text-muted-foreground">Lowest net cost</p>
              <p className="text-lg font-bold text-foreground">{cheapest ? formatCurrency(cheapest.netCost) : '—'}</p>
              {cheapest && <p className="text-xs text-muted-foreground truncate">{cheapest.name}</p>}
            </Card>
            <Card className="p-4 text-center">
              <ArrowUpDown size={20} className="mx-auto text-secondary mb-1" />
              <p className="text-xs text-muted-foreground">Average net cost</p>
              <p className="text-lg font-bold text-foreground">{formatCurrency(avgNet)}</p>
              <p className="text-xs text-muted-foreground">{programCosts.length} programs</p>
            </Card>
            <Card className="p-4 text-center">
              <TrendingUp size={20} className="mx-auto text-error mb-1" />
              <p className="text-xs text-muted-foreground">Highest net cost</p>
              <p className="text-lg font-bold text-foreground">{mostExpensive ? formatCurrency(mostExpensive.netCost) : '—'}</p>
              {mostExpensive && <p className="text-xs text-muted-foreground truncate">{mostExpensive.name}</p>}
            </Card>
          </div>

          {/* Sort toggle */}
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-h3 text-foreground">Cost breakdown</h3>
            <div className="flex gap-2">
              <button
                onClick={() => setSortBy('net')}
                className={`px-3 py-1 text-xs font-semibold rounded-pill ${sortBy === 'net' ? 'bg-secondary text-secondary-foreground' : 'bg-muted text-muted-foreground'}`}
              >
                Sort by net cost
              </button>
              <button
                onClick={() => setSortBy('tuition')}
                className={`px-3 py-1 text-xs font-semibold rounded-pill ${sortBy === 'tuition' ? 'bg-secondary text-secondary-foreground' : 'bg-muted text-muted-foreground'}`}
              >
                Sort by tuition
              </button>
            </div>
          </div>

          {/* Program cost cards */}
          <div className="space-y-4">
            {programCosts.map(pc => (
              <Card key={pc.id} className="p-4">
                <div className="flex items-start justify-between mb-3">
                  <div>
                    <p className="font-semibold text-sm text-foreground cursor-pointer hover:underline" onClick={() => navigate(`/s/programs/${pc.id}`)}>
                      {pc.name}
                    </p>
                    <p className="text-xs text-muted-foreground">{pc.institution} — {pc.country}</p>
                  </div>
                  <div className="text-right">
                    <p className="text-lg font-bold text-foreground">{formatCurrency(pc.netCost)}</p>
                    <p className="text-xs text-muted-foreground">Net annual cost</p>
                  </div>
                </div>

                <div className="grid grid-cols-4 gap-3 text-sm">
                  <div>
                    <p className="text-xs text-muted-foreground">Tuition</p>
                    <p className="font-medium text-foreground">{formatCurrency(pc.tuition)}</p>
                  </div>
                  <div>
                    <p className="text-xs text-muted-foreground">Living cost</p>
                    <p className="font-medium text-foreground">{formatCurrency(pc.livingCost)}</p>
                  </div>
                  <div>
                    <p className="text-xs text-muted-foreground">Expected aid</p>
                    <div className="flex items-center gap-1">
                      <span className="text-muted-foreground">$</span>
                      <input
                        type="number"
                        value={expectedAid[pc.id] || ''}
                        onChange={e => setExpectedAid(prev => ({ ...prev, [pc.id]: e.target.value }))}
                        placeholder="0"
                        className="w-24 text-sm bg-transparent border-b border-border focus:border-secondary focus:outline-none py-0.5"
                      />
                    </div>
                  </div>
                  <div>
                    <p className="text-xs text-muted-foreground">Net cost</p>
                    <p className="font-bold text-success">{formatCurrency(pc.netCost)}</p>
                  </div>
                </div>

                {/* Visual bar — cobalt tuition + gold living (Spec 02 §14 palette) */}
                <div className="mt-3 flex h-2 rounded-pill overflow-hidden bg-muted">
                  {pc.tuition != null && pc.tuition > 0 && (
                    <div
                      className="bg-secondary h-full"
                      style={{ width: `${((pc.tuition ?? 0) / ((pc.tuition ?? 0) + pc.livingCost)) * 100}%` }}
                      title="Tuition"
                    />
                  )}
                  <div
                    className="bg-primary h-full"
                    style={{ width: `${(pc.livingCost / ((pc.tuition ?? 0) + pc.livingCost)) * 100}%` }}
                    title="Living"
                  />
                </div>
                <div className="flex gap-4 mt-1 text-[10px] text-muted-foreground">
                  <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-secondary" /> Tuition</span>
                  <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-primary" /> Living</span>
                </div>
              </Card>
            ))}
          </div>
        </>
      )}
    </div>
  )
}
