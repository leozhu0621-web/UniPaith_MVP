import { useState, useEffect, useMemo } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { searchPrograms, nlpSearch } from '../../api/programs'
import { searchInstitutions } from '../../api/institutions'
import { listSaved, saveProgram, unsaveProgram } from '../../api/saved-lists'
import { useCompareStore } from '../../stores/compare-store'
import UniversityCard from './explore/cards/UniversityCard'
import ProgramCard from './explore/cards/ProgramCard'
import ExploreFilters, { EMPTY_FILTERS, applyFilters, countActiveFilters, type FilterState } from './explore/shared/ExploreFilters'
import {
  Search, X, Loader2, Sparkles, Building2,
} from 'lucide-react'
import type { ProgramSummary } from '../../types'
import type {
  InstitutionClassification,
  SatTier,
  TuitionTier,
} from './explore/shared/classifyInstitution'

interface NlpResult {
  filters_applied: Record<string, any>
  results: { items: ProgramSummary[]; total: number }
  interpretation: string
}

/**
 * ExplorePage — top-level universities grid plus flat program search.
 *
 * Schools and programs each live on their own URL-routed detail page — this
 * page no longer drills down in-place. Clicking a university card navigates
 * to /s/institutions/:id, which exposes a Schools tab that leads to the
 * per-school detail page.
 */
/** Parse filter state from URL search params. List filters are comma-
 *  separated on their own key; boolean toggles are '1' or absent. */
function filtersFromURL(params: URLSearchParams): FilterState {
  const split = (key: string) =>
    (params.get(key) || '').split(',').map(s => s.trim()).filter(Boolean)
  const bool = (key: string) => params.get(key) === '1'
  return {
    country: split('country'),
    setting: split('setting'),
    type: split('type') as InstitutionClassification[],
    degreeLevel: split('degree'),
    deliveryFormat: split('format'),
    subjects: split('subjects'),
    industries: split('industries'),
    satTier: split('sat') as SatTier[],
    tuitionTier: split('tuition') as TuitionTier[],
    appOpen: bool('open'),
    international: bool('intl'),
    studyAbroad: bool('abroad'),
    honors: bool('honors'),
  }
}

/** Serialize filter state into URL search params (preserves `q`). */
function filtersToURL(base: URLSearchParams, f: FilterState): URLSearchParams {
  const next = new URLSearchParams(base)
  const listKeys: Array<{ key: keyof FilterState; param: string }> = [
    { key: 'country', param: 'country' },
    { key: 'setting', param: 'setting' },
    { key: 'type', param: 'type' },
    { key: 'degreeLevel', param: 'degree' },
    { key: 'deliveryFormat', param: 'format' },
    { key: 'subjects', param: 'subjects' },
    { key: 'industries', param: 'industries' },
    { key: 'satTier', param: 'sat' },
    { key: 'tuitionTier', param: 'tuition' },
  ]
  for (const { key, param } of listKeys) {
    const v = (f[key] as string[]).join(',')
    if (v) next.set(param, v)
    else next.delete(param)
  }
  const boolKeys: Array<{ key: keyof FilterState; param: string }> = [
    { key: 'appOpen', param: 'open' },
    { key: 'international', param: 'intl' },
    { key: 'studyAbroad', param: 'abroad' },
    { key: 'honors', param: 'honors' },
  ]
  for (const { key, param } of boolKeys) {
    if (f[key]) next.set(param, '1')
    else next.delete(param)
  }
  return next
}

export default function ExplorePage() {
  const navigate = useNavigate()
  const [searchParams, setSearchParams] = useSearchParams()
  const queryClient = useQueryClient()
  const compareStore = useCompareStore()

  // Search state
  const [q, setQ] = useState(searchParams.get('q') || '')
  const [isSearching, setIsSearching] = useState(false)
  const [nlpResult, setNlpResult] = useState<NlpResult | null>(null)

  // Filter state lives in the URL so refresh + share + back all work.
  const filters = useMemo(() => filtersFromURL(searchParams), [searchParams])
  const setFilters = (next: FilterState) => {
    setSearchParams(filtersToURL(searchParams, next), { replace: true })
  }

  // ─── Queries ───

  const { data: universities, isLoading: uniLoading } = useQuery({
    queryKey: ['explore-universities'],
    queryFn: () => searchInstitutions({ page_size: 50 }),
    staleTime: 5 * 60 * 1000,
  })

  // Search mode: flat program search
  const { data: searchResults, isLoading: searchLoading } = useQuery({
    queryKey: ['explore-search', q],
    queryFn: () => searchPrograms({ q: q || undefined, page_size: 21 }),
    enabled: isSearching && q.length >= 2 && !nlpResult,
  })

  // Saved programs
  const { data: savedData } = useQuery({ queryKey: ['saved-programs'], queryFn: listSaved, retry: false })
  const [savedIds, setSavedIds] = useState<Set<string>>(new Set())
  useEffect(() => { if (savedData) setSavedIds(new Set(savedData.map((s: any) => String(s.program_id)))) }, [savedData])

  const nlpMut = useMutation({
    mutationFn: nlpSearch,
    onSuccess: (data: NlpResult) => setNlpResult(data),
    onError: () => setNlpResult(null),
  })

  const toggleSave = async (programId: string) => {
    try {
      if (savedIds.has(programId)) { await unsaveProgram(programId); setSavedIds(prev => { const n = new Set(prev); n.delete(programId); return n }) }
      else { await saveProgram(programId); setSavedIds(prev => new Set(prev).add(programId)) }
      queryClient.invalidateQueries({ queryKey: ['saved-programs'] })
    } catch { /* */ }
  }

  // Search handling
  const handleSearch = () => {
    if (q.trim().length >= 3) {
      setIsSearching(true)
      nlpMut.mutate(q.trim())
    }
  }

  const clearSearch = () => {
    setQ('')
    setIsSearching(false)
    setNlpResult(null)
  }

  const exitSearch = () => {
    setIsSearching(false)
    setNlpResult(null)
  }

  // ─── Data ───

  const uniList: any[] = universities?.items ?? []
  const filteredUniList = useMemo(() => applyFilters(uniList, filters), [uniList, filters])
  const hasActiveFilters = countActiveFilters(filters) > 0
  const searchProgramList: ProgramSummary[] = nlpResult
    ? (nlpResult.results?.items ?? [])
    : (searchResults?.items ?? [])

  // ─── Render ───

  return (
    <div className="p-6 max-w-6xl mx-auto">
      {/* Search bar */}
      <div className="relative mb-4">
        <Search size={16} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-student-text" />
        <input
          type="text"
          value={q}
          onChange={e => { setQ(e.target.value); if (!e.target.value.trim()) clearSearch() }}
          onKeyDown={e => { if (e.key === 'Enter') handleSearch() }}
          onFocus={() => { if (q.length >= 2) setIsSearching(true) }}
          placeholder="Search universities, schools, or programs..."
          className="w-full pl-10 pr-24 py-3 bg-white border border-stone rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-student"
        />
        <div className="absolute right-2 top-1/2 -translate-y-1/2 flex items-center gap-1">
          {q && <button onClick={clearSearch} className="p-1 text-student-text hover:text-student-ink"><X size={14} /></button>}
          <button
            onClick={handleSearch}
            disabled={q.trim().length < 3 || nlpMut.isPending}
            className="px-3 py-1.5 bg-student text-white text-xs font-medium rounded-lg hover:bg-student-hover disabled:opacity-40 transition-colors"
          >
            {nlpMut.isPending ? <Loader2 size={12} className="animate-spin" /> : 'Search'}
          </button>
        </div>
      </div>

      {/* NLP interpretation chips */}
      {nlpResult && isSearching && (
        <div className="mb-4 space-y-2">
          <div className="flex items-center gap-2 px-3 py-2 bg-gold-soft rounded-lg border border-gold/20">
            <Sparkles size={12} className="text-gold flex-shrink-0" />
            <p className="text-xs text-student-ink flex-1">{nlpResult.interpretation}</p>
            <button onClick={exitSearch} className="text-xs text-student-text hover:text-student-ink">Back to browse</button>
          </div>
        </div>
      )}

      {/* ── SEARCH MODE: Flat program results ── */}
      {isSearching && (
        <>
          {(searchLoading || nlpMut.isPending) ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {[1, 2, 3].map(i => <div key={i} className="h-72 bg-white rounded-xl border border-divider animate-pulse" />)}
            </div>
          ) : searchProgramList.length === 0 ? (
            <div className="text-center py-16 bg-white rounded-xl border border-divider">
              <Search size={32} className="mx-auto text-stone mb-3" />
              <p className="text-sm text-student-ink font-medium mb-1">No results found</p>
              <p className="text-xs text-student-text">Try a different search term.</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {searchProgramList.map(p => (
                <ProgramCard
                  key={p.id}
                  program={p}
                  saved={savedIds.has(p.id)}
                  comparing={compareStore.has(p.id)}
                  onSave={() => toggleSave(p.id)}
                  onCompare={() => compareStore.has(p.id) ? compareStore.remove(p.id) : compareStore.add({ program_id: p.id, program_name: p.program_name, institution_name: p.institution_name, degree_type: p.degree_type })}
                  onAskCounselor={() => navigate(`/s?prefill=${encodeURIComponent(`Tell me about ${p.program_name} at ${p.institution_name}. Is it a good fit?`)}`)}
                  onView={() => navigate(`/s/programs/${p.id}`)}
                />
              ))}
            </div>
          )}
        </>
      )}

      {/* ── BROWSE MODE: Filter bar + Universities grid ── */}
      {!isSearching && (
        <>
          {uniList.length > 0 && (
            <ExploreFilters
              universities={uniList}
              filters={filters}
              onChange={setFilters}
            />
          )}

          {uniLoading ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {[1, 2, 3].map(i => <div key={i} className="h-80 bg-white rounded-xl border border-divider animate-pulse" />)}
            </div>
          ) : uniList.length === 0 ? (
            <div className="text-center py-16 bg-white rounded-xl border border-divider">
              <Building2 size={32} className="mx-auto text-stone mb-3" />
              <p className="text-sm text-student-ink font-medium mb-1">No universities yet</p>
              <p className="text-xs text-student-text">Universities will appear here as they join the platform.</p>
            </div>
          ) : filteredUniList.length === 0 ? (
            <div className="text-center py-16 bg-white rounded-xl border border-divider">
              <Building2 size={32} className="mx-auto text-stone mb-3" />
              <p className="text-sm text-student-ink font-medium mb-1">No universities match your filters</p>
              <p className="text-xs text-student-text mb-4">Try removing a filter or broadening your search.</p>
              <button
                onClick={() => setFilters(EMPTY_FILTERS)}
                className="text-xs font-medium text-student hover:text-student-hover"
              >
                Clear all filters
              </button>
            </div>
          ) : (
            <>
              {hasActiveFilters && (
                <p className="text-[11px] text-student-text/70 mb-3">
                  Showing <span className="font-semibold text-student-ink">{filteredUniList.length}</span> of {uniList.length} universities
                </p>
              )}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {filteredUniList.map((inst: any) => (
                  <UniversityCard
                    key={inst.id}
                    institution={inst}
                    onClick={() => navigate(`/s/institutions/${inst.id}`)}
                  />
                ))}
              </div>
            </>
          )}
        </>
      )}
    </div>
  )
}
