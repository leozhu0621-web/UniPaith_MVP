import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { searchPrograms } from '../../api/programs'
import { Search } from 'lucide-react'
import Badge from '../../components/ui/Badge'
import Skeleton from '../../components/ui/Skeleton'
import { formatCurrency, formatDate } from '../../utils/format'
import { DEGREE_LABELS } from '../../utils/constants'
import type { ProgramSummary, PaginatedResponse } from '../../types'

export default function ProgramBrowsePage() {
  const [q, setQ] = useState('')
  const [country, setCountry] = useState('')
  const [degreeType, setDegreeType] = useState('')
  const [page, setPage] = useState(1)

  const { data, isLoading } = useQuery({
    queryKey: ['programs', { q, country, degree_type: degreeType, page }],
    queryFn: () => searchPrograms({ q: q || undefined, country: country || undefined, degree_type: degreeType || undefined, page, page_size: 20 }),
  })

  const programs: ProgramSummary[] = data?.items ?? []
  const totalPages = (data as PaginatedResponse<ProgramSummary>)?.total_pages ?? 1

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between">
        <Link to="/" className="text-lg font-bold">UniPaith</Link>
        <div className="flex gap-3">
          <Link to="/login" className="text-sm text-gray-600 hover:text-gray-900">Log in</Link>
          <Link to="/signup" className="text-sm bg-gray-900 text-white px-3 py-1 rounded hover:bg-gray-800">Sign up</Link>
        </div>
      </header>

      <div className="max-w-6xl mx-auto px-6 py-8">
        <h1 className="text-2xl font-bold mb-6">Browse Programs</h1>

        <div className="flex gap-3 mb-6">
          <div className="relative flex-1">
            <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
            <input
              type="text"
              value={q}
              onChange={e => { setQ(e.target.value); setPage(1) }}
              placeholder="Search programs..."
              className="w-full pl-9 pr-4 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-gray-900"
            />
          </div>
          <input
            type="text"
            value={country}
            onChange={e => { setCountry(e.target.value); setPage(1) }}
            placeholder="Country"
            className="w-40 px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-gray-900"
          />
          <select
            value={degreeType}
            onChange={e => { setDegreeType(e.target.value); setPage(1) }}
            className="w-40 px-3 py-2 text-sm border border-gray-300 rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-gray-900"
          >
            <option value="">All Degrees</option>
            {Object.entries(DEGREE_LABELS).map(([v, l]) => (
              <option key={v} value={v}>{l}</option>
            ))}
          </select>
        </div>

        {isLoading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {Array.from({ length: 6 }).map((_, i) => (
              <div key={i} className="bg-white rounded-lg border p-4 space-y-3">
                <Skeleton className="h-5 w-3/4" />
                <Skeleton className="h-4 w-1/2" />
                <Skeleton className="h-4 w-full" />
              </div>
            ))}
          </div>
        ) : programs.length === 0 ? (
          <div className="text-center py-16 text-gray-500">No programs found</div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {programs.map(p => (
              <Link
                key={p.id}
                to={`/s/programs/${p.id}`}
                className="bg-white rounded-lg border p-4 hover:shadow-md transition-shadow"
              >
                <h3 className="font-semibold text-gray-900 truncate">{p.program_name}</h3>
                <p className="text-sm text-gray-500 mt-1">{p.institution_name} — {p.institution_country}</p>
                <div className="flex items-center gap-2 mt-3">
                  <Badge variant="info">{DEGREE_LABELS[p.degree_type] || p.degree_type}</Badge>
                  {p.tuition != null && (
                    <span className="text-xs text-gray-500">{formatCurrency(p.tuition)}</span>
                  )}
                </div>
                {p.application_deadline && (
                  <p className="text-xs text-gray-400 mt-2">Deadline: {formatDate(p.application_deadline)}</p>
                )}
              </Link>
            ))}
          </div>
        )}

        {totalPages > 1 && (
          <div className="flex justify-center gap-2 mt-8">
            {Array.from({ length: totalPages }, (_, i) => i + 1).map(p => (
              <button
                key={p}
                onClick={() => setPage(p)}
                className={`px-3 py-1 text-sm rounded ${p === page ? 'bg-gray-900 text-white' : 'bg-white border hover:bg-gray-50'}`}
              >
                {p}
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
