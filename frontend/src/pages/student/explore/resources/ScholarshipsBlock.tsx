// Resources › Financial — real scholarships search + list (Spec 2026-06-14).
// Defaults to a "for your level" match list; typing a query switches to full
// search with level / type filters. All data is real CareerOneStop (U.S. DOL).
import { useState } from 'react'
import { useQuery, keepPreviousData } from '@tanstack/react-query'
import { Award, ChevronLeft, ChevronRight, Search } from 'lucide-react'
import { searchScholarships, getScholarshipMatches } from '../../../../api/scholarships'
import QueryError from '../../../../components/ui/QueryError'
import { SkeletonCard } from '../../../../components/ui/Skeleton'
import ScholarshipCard from './ScholarshipCard'

const LEVELS = ['High School', 'Associate', 'Bachelor', 'Graduate']
const TYPES = ['Scholarship', 'Fellowship', 'Grant', 'Prize']
const PAGE_SIZE = 12

export default function ScholarshipsBlock() {
  const [draft, setDraft] = useState('')
  const [q, setQ] = useState('')
  const [level, setLevel] = useState('')
  const [awardType, setAwardType] = useState('')
  const [page, setPage] = useState(1)

  const searching = q.trim().length > 0 || !!level || !!awardType

  const matchesQ = useQuery({
    queryKey: ['scholarship-matches'],
    queryFn: () => getScholarshipMatches(PAGE_SIZE),
    staleTime: 5 * 60 * 1000,
    enabled: !searching,
    retry: false,
  })
  const searchQ = useQuery({
    queryKey: ['scholarship-search', q, level, awardType, page],
    queryFn: () => searchScholarships({ q: q || undefined, level: level || undefined, award_type: awardType || undefined, page, page_size: PAGE_SIZE }),
    enabled: searching,
    placeholderData: keepPreviousData,
    retry: false,
  })

  const submit = (e: React.FormEvent) => {
    e.preventDefault()
    setQ(draft.trim())
    setPage(1)
  }
  const reset = () => {
    setDraft('')
    setQ('')
    setLevel('')
    setAwardType('')
    setPage(1)
  }

  const items = searching ? searchQ.data?.items ?? [] : matchesQ.data ?? []
  const total = searchQ.data?.total ?? 0
  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE))
  const isLoading = searching ? searchQ.isLoading : matchesQ.isLoading
  const isError = searching ? searchQ.isError : matchesQ.isError

  return (
    <section className="mb-8">
      <div className="mb-3 flex items-center gap-2">
        <Award size={16} className="text-secondary" aria-hidden />
        <h2 className="text-base font-bold text-foreground">Scholarships</h2>
        <span className="text-xs text-muted-foreground">· U.S. Dept of Labor · CareerOneStop</span>
      </div>
      <p className="mb-4 text-xs text-muted-foreground">
        Real scholarship listings. Verify amounts and deadlines on each official listing before applying.
      </p>

      {/* Search + filters */}
      <form onSubmit={submit} className="mb-4 flex flex-wrap items-center gap-2">
        <div className="relative min-w-0 flex-1">
          <Search size={14} className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" />
          <input
            value={draft}
            onChange={e => setDraft(e.target.value)}
            placeholder="Search by field, name, or organization…"
            aria-label="Search scholarships"
            className="h-9 w-full rounded-lg border border-border bg-card pl-9 pr-3 text-sm text-foreground placeholder:text-muted-foreground focus:border-secondary focus:outline-none"
          />
        </div>
        <select
          value={level}
          onChange={e => { setLevel(e.target.value); setPage(1) }}
          aria-label="Level of study"
          className="h-9 rounded-lg border border-border bg-card px-2 text-sm text-foreground focus:border-secondary focus:outline-none"
        >
          <option value="">Any level</option>
          {LEVELS.map(l => <option key={l} value={l}>{l}</option>)}
        </select>
        <select
          value={awardType}
          onChange={e => { setAwardType(e.target.value); setPage(1) }}
          aria-label="Award type"
          className="h-9 rounded-lg border border-border bg-card px-2 text-sm text-foreground focus:border-secondary focus:outline-none"
        >
          <option value="">Any type</option>
          {TYPES.map(t => <option key={t} value={t}>{t}</option>)}
        </select>
        <button type="submit" className="ui-btn h-9 rounded-lg bg-secondary px-3 text-sm font-medium text-secondary-foreground">
          Search
        </button>
        {searching && (
          <button type="button" onClick={reset} className="text-xs font-semibold text-secondary hover:underline">
            Clear
          </button>
        )}
      </form>

      {!searching && !isLoading && items.length > 0 && (
        <p className="mb-3 text-[11px] uppercase tracking-wide text-muted-foreground">Suggested for your level</p>
      )}
      {searching && !isLoading && (
        <p className="mb-3 text-[11px] text-muted-foreground">
          {total.toLocaleString()} result{total !== 1 ? 's' : ''}
        </p>
      )}

      {isError ? (
        <QueryError detail="We couldn't load scholarships." onRetry={() => (searching ? searchQ.refetch() : matchesQ.refetch())} />
      ) : isLoading ? (
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3 [&>*]:min-w-0">
          {[0, 1, 2, 3, 4, 5].map(i => <SkeletonCard key={i} />)}
        </div>
      ) : items.length === 0 ? (
        <div className="rounded-xl border border-border bg-card py-12 text-center">
          <Award size={28} className="mx-auto mb-3 text-muted-foreground" />
          <p className="text-sm font-semibold text-foreground">No scholarships match your search</p>
          <p className="mt-1 text-xs text-muted-foreground">Try a broader term or clear the filters.</p>
        </div>
      ) : (
        <>
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3 [&>*]:min-w-0">
            {items.map(s => <ScholarshipCard key={s.id} s={s} />)}
          </div>
          {searching && totalPages > 1 && (
            <div className="mt-5 flex items-center justify-center gap-3">
              <button
                onClick={() => setPage(p => Math.max(1, p - 1))}
                disabled={page <= 1}
                className="ui-btn inline-flex items-center gap-1 rounded-lg border border-border px-3 py-1.5 text-xs font-medium text-foreground disabled:opacity-40"
              >
                <ChevronLeft size={13} /> Prev
              </button>
              <span className="text-xs text-muted-foreground">Page {page} of {totalPages}</span>
              <button
                onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                disabled={page >= totalPages}
                className="ui-btn inline-flex items-center gap-1 rounded-lg border border-border px-3 py-1.5 text-xs font-medium text-foreground disabled:opacity-40"
              >
                Next <ChevronRight size={13} />
              </button>
            </div>
          )}
        </>
      )}
    </section>
  )
}
