import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { searchPrograms } from '../../api/programs'
import { getFeaturedPromotions } from '../../api/institutions'
import { Search, Star } from 'lucide-react'
import Badge from '../../components/ui/Badge'
import Skeleton from '../../components/ui/Skeleton'
import QueryError from '../../components/ui/QueryError'
import { formatCurrency, formatDate } from '../../utils/format'
import { DEGREE_LABELS } from '../../utils/constants'
import type { ProgramSummary, PaginatedResponse, Promotion } from '../../types'

import usePageTitle from '../../hooks/usePageTitle'

export default function ProgramBrowsePage() {
  usePageTitle('Browse Programs')
  const [q, setQ] = useState('')
  const [country, setCountry] = useState('')
  const [degreeType, setDegreeType] = useState('')
  const [page, setPage] = useState(1)

  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ['programs', { q, country, degree_type: degreeType, page }],
    queryFn: () => searchPrograms({ q: q || undefined, country: country || undefined, degree_type: degreeType || undefined, page, page_size: 20 }),
  })

  const programs: ProgramSummary[] = data?.items ?? []
  const totalPages = (data as PaginatedResponse<ProgramSummary>)?.total_pages ?? 1

  const featuredQ = useQuery({
    queryKey: ['featured-promotions', { country, degree_type: degreeType }],
    queryFn: () => getFeaturedPromotions({
      country: country || undefined,
      degree_type: degreeType || undefined,
    }),
  })
  const featured: Promotion[] = Array.isArray(featuredQ.data) ? featuredQ.data : []
  const featuredProgramIds = new Set(featured.filter(f => f.program_id).map(f => f.program_id!))

  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-8 py-8">
        <h1 className="text-2xl font-bold mb-6">Browse Programs</h1>

        <div className="flex gap-3 mb-6">
          <div className="relative flex-1">
            <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground/70" />
            <input
              type="text"
              value={q}
              onChange={e => { setQ(e.target.value); setPage(1) }}
              placeholder="Search programs..."
              aria-label="Search programs"
              className="w-full pl-9 pr-4 py-2 text-sm border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-ring"
            />
          </div>
          <input
            type="text"
            value={country}
            onChange={e => { setCountry(e.target.value); setPage(1) }}
            placeholder="Country"
            aria-label="Filter by country"
            className="w-40 px-3 py-2 text-sm border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-ring"
          />
          <select
            value={degreeType}
            onChange={e => { setDegreeType(e.target.value); setPage(1) }}
            className="w-40 px-3 py-2 text-sm border border-border rounded-lg bg-card focus:outline-none focus:ring-2 focus:ring-ring"
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
              <div key={i} className="bg-card rounded-lg border p-4 space-y-3">
                <Skeleton className="h-5 w-3/4" />
                <Skeleton className="h-4 w-1/2" />
                <Skeleton className="h-4 w-full" />
              </div>
            ))}
          </div>
        ) : isError ? (
          <QueryError detail="We couldn't load programs." onRetry={() => refetch()} />
        ) : programs.length === 0 ? (
          <div className="text-center py-16 text-muted-foreground">No programs found</div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {programs.map(p => (
              <Link
                key={p.id}
                to={`/program/${p.id}`}
                className="bg-card rounded-lg border p-4 hover:shadow-md transition-shadow"
              >
                <div className="flex items-center gap-2">
                  <h3 className="font-semibold text-foreground truncate">{p.program_name}</h3>
                  {featuredProgramIds.has(p.id) && (
                    <span className="inline-flex items-center gap-0.5 px-1.5 py-0.5 rounded text-xs font-medium bg-warning-soft text-warning">
                      <Star size={10} className="fill-warning" /> Featured
                    </span>
                  )}
                </div>
                <p className="text-sm text-muted-foreground mt-1">
                  <span
                    role="link"
                    tabIndex={0}
                    onClick={e => { e.preventDefault(); e.stopPropagation(); window.location.href = `/school/${p.institution_id}` }}
                    onKeyDown={e => { if (e.key === 'Enter') { e.preventDefault(); e.stopPropagation(); window.location.href = `/school/${p.institution_id}` } }}
                    className="hover:underline hover:text-muted-foreground cursor-pointer"
                  >{p.institution_name}</span> — {p.institution_country}
                </p>
                <div className="flex items-center gap-2 mt-3">
                  <Badge variant="info">{DEGREE_LABELS[p.degree_type] || p.degree_type}</Badge>
                  {p.tuition != null && (
                    <span className="text-xs text-muted-foreground">{formatCurrency(p.tuition)}</span>
                  )}
                </div>
                {p.application_deadline && (
                  <p className="text-xs text-muted-foreground/70 mt-2">Deadline: {formatDate(p.application_deadline)}</p>
                )}
              </Link>
            ))}
          </div>
        )}

        {totalPages > 1 && (
          <nav className="flex justify-center items-center gap-2 mt-8" aria-label="Pagination">
            <button
              onClick={() => setPage(p => Math.max(1, p - 1))}
              disabled={page <= 1}
              className="px-3 py-1 text-sm rounded bg-card border border-border hover:bg-muted disabled:opacity-40 disabled:pointer-events-none"
            >
              Prev
            </button>
            {pageWindow(page, totalPages).map((p, i) =>
              p === 'gap' ? (
                <span key={`gap-${i}`} className="px-2 text-sm text-muted-foreground/60" aria-hidden="true">…</span>
              ) : (
                <button
                  key={p}
                  onClick={() => setPage(p)}
                  aria-current={p === page ? 'page' : undefined}
                  className={`px-3 py-1 text-sm rounded ${p === page ? 'bg-foreground text-background' : 'bg-card border border-border hover:bg-muted'}`}
                >
                  {p}
                </button>
              )
            )}
            <button
              onClick={() => setPage(p => Math.min(totalPages, p + 1))}
              disabled={page >= totalPages}
              className="px-3 py-1 text-sm rounded bg-card border border-border hover:bg-muted disabled:opacity-40 disabled:pointer-events-none"
            >
              Next
            </button>
          </nav>
        )}
    </div>
  )
}

// Windowed page list: first · current±2 · last, with 'gap' markers where pages
// are elided. Keeps the control bounded no matter how many total pages exist.
function pageWindow(current: number, total: number): (number | 'gap')[] {
  const pages = new Set<number>([1, total, current - 2, current - 1, current, current + 1, current + 2])
  const visible = Array.from(pages).filter(p => p >= 1 && p <= total).sort((a, b) => a - b)
  const out: (number | 'gap')[] = []
  let prev = 0
  for (const p of visible) {
    if (prev && p - prev > 1) out.push('gap')
    out.push(p)
    prev = p
  }
  return out
}
