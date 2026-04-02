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
  const savedList: any[] = Array.isArray(saved) ? saved : []
  const applicationsList: any[] = Array.isArray(applications) ? applications : []

  // Combine saved + applied programs (deduplicate by program_id)
  const allPrograms = useMemo(() => {
    const seen = new Set<string>()
    const result: { id: string; name: string; institution: string; country: string; tuition: number | null }[] = []

    savedList.forEach((s: any) => {
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

    applicationsList.forEach((a: any) => {
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
  }, [savedList, applicationsList])

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

  if (isLoading) return <div className="p-6 max-w-4xl mx-auto space-y-4">{Array.from({ length: 3 }).map((_, i) => <SkeletonCard key={i} />)}</div>

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <div className="mb-6">
        <h1 className="text-2xl font-semibold">Financial Aid Calculator</h1>
        <p className="text-sm text-gray-500 mt-1">Estimate and compare costs across your saved and applied programs.</p>
      </div>

      {allPrograms.length === 0 ? (
        <EmptyState
          icon={<DollarSign size={48} />}
          title="No programs to compare"
          description="Save or apply to programs to see cost estimates here."
          action={{ label: 'Discover Programs', onClick: () => navigate('/s/discover') }}
        />
      ) : (
        <>
          {/* Summary Cards */}
          <div className="grid grid-cols-3 gap-4 mb-6">
            <Card className="p-4 text-center">
              <TrendingDown size={20} className="mx-auto text-green-600 mb-1" />
              <p className="text-xs text-gray-500">Lowest Net Cost</p>
              <p className="text-lg font-bold">{cheapest ? formatCurrency(cheapest.netCost) : '—'}</p>
              {cheapest && <p className="text-xs text-gray-400 truncate">{cheapest.name}</p>}
            </Card>
            <Card className="p-4 text-center">
              <ArrowUpDown size={20} className="mx-auto text-blue-600 mb-1" />
              <p className="text-xs text-gray-500">Average Net Cost</p>
              <p className="text-lg font-bold">{formatCurrency(avgNet)}</p>
              <p className="text-xs text-gray-400">{programCosts.length} programs</p>
            </Card>
            <Card className="p-4 text-center">
              <TrendingUp size={20} className="mx-auto text-red-600 mb-1" />
              <p className="text-xs text-gray-500">Highest Net Cost</p>
              <p className="text-lg font-bold">{mostExpensive ? formatCurrency(mostExpensive.netCost) : '—'}</p>
              {mostExpensive && <p className="text-xs text-gray-400 truncate">{mostExpensive.name}</p>}
            </Card>
          </div>

          {/* Sort toggle */}
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-medium">Cost Breakdown</h2>
            <div className="flex gap-2">
              <button
                onClick={() => setSortBy('net')}
                className={`px-3 py-1 text-xs rounded-full ${sortBy === 'net' ? 'bg-gray-900 text-white' : 'bg-gray-100 text-gray-600'}`}
              >
                Sort by Net Cost
              </button>
              <button
                onClick={() => setSortBy('tuition')}
                className={`px-3 py-1 text-xs rounded-full ${sortBy === 'tuition' ? 'bg-gray-900 text-white' : 'bg-gray-100 text-gray-600'}`}
              >
                Sort by Tuition
              </button>
            </div>
          </div>

          {/* Program cost cards */}
          <div className="space-y-4">
            {programCosts.map(pc => (
              <Card key={pc.id} className="p-4">
                <div className="flex items-start justify-between mb-3">
                  <div>
                    <p className="font-semibold text-sm cursor-pointer hover:underline" onClick={() => navigate(`/s/schools/${pc.id}`)}>
                      {pc.name}
                    </p>
                    <p className="text-xs text-gray-500">{pc.institution} — {pc.country}</p>
                  </div>
                  <div className="text-right">
                    <p className="text-lg font-bold">{formatCurrency(pc.netCost)}</p>
                    <p className="text-xs text-gray-500">Net annual cost</p>
                  </div>
                </div>

                <div className="grid grid-cols-4 gap-3 text-sm">
                  <div>
                    <p className="text-xs text-gray-500">Tuition</p>
                    <p className="font-medium">{formatCurrency(pc.tuition)}</p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-500">Living Cost</p>
                    <p className="font-medium">{formatCurrency(pc.livingCost)}</p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-500">Expected Aid</p>
                    <div className="flex items-center gap-1">
                      <span className="text-gray-400">$</span>
                      <input
                        type="number"
                        value={expectedAid[pc.id] || ''}
                        onChange={e => setExpectedAid(prev => ({ ...prev, [pc.id]: e.target.value }))}
                        placeholder="0"
                        className="w-24 text-sm border-b border-gray-300 focus:border-gray-900 focus:outline-none py-0.5"
                      />
                    </div>
                  </div>
                  <div>
                    <p className="text-xs text-gray-500">Net Cost</p>
                    <p className="font-bold text-green-700">{formatCurrency(pc.netCost)}</p>
                  </div>
                </div>

                {/* Visual bar */}
                <div className="mt-3 flex h-2 rounded-full overflow-hidden bg-gray-100">
                  {pc.tuition != null && pc.tuition > 0 && (
                    <div
                      className="bg-blue-400 h-full"
                      style={{ width: `${((pc.tuition ?? 0) / ((pc.tuition ?? 0) + pc.livingCost)) * 100}%` }}
                      title="Tuition"
                    />
                  )}
                  <div
                    className="bg-purple-400 h-full"
                    style={{ width: `${(pc.livingCost / ((pc.tuition ?? 0) + pc.livingCost)) * 100}%` }}
                    title="Living"
                  />
                </div>
                <div className="flex gap-4 mt-1 text-[10px] text-gray-400">
                  <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-blue-400" /> Tuition</span>
                  <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-purple-400" /> Living</span>
                </div>
              </Card>
            ))}
          </div>
        </>
      )}
    </div>
  )
}
