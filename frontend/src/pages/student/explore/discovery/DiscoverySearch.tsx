import { useEffect, useMemo, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { AlertTriangle, Search, Sparkles, X } from 'lucide-react'
import Button from '../../../../components/ui/Button'
import { interpretQuery, searchProgramsTyped } from '../../../../api/search'
import { listSaved, saveProgram, unsaveProgram } from '../../../../api/saved-lists'
import { MAX_COMPARE, useCompareStore } from '../../../../stores/compare-store'
import { showToast } from '../../../../stores/toast-store'
import type { ConstraintChip, SearchFilters, SortOption } from '../../../../types/search'
import type { ProgramSummary } from '../../../../types'
import ProgramCard from '../cards/ProgramCard'
import ConstraintChips from './ConstraintChips'
import FiltersPanel from './FiltersPanel'
import GenreTiles from './GenreTiles'
import SortMenu from './SortMenu'
import { encodeChipsParam, parseChipsParam, withChipId } from './chipUtils'
import { encodeFiltersParam, hasActiveFilters, normalizeFilters, parseFiltersParam } from './filterUtils'

// Spec 10 — Discovery type-first program search. Sits inside /s/explore below
// the StrategyView. Type a query → constraint chips → programs-only results.
// chips/q/sort live in the URL so reload + share reproduce the view (§10).

const PAGE_SIZE = 24

export default function DiscoverySearch() {
  const [params, setParams] = useSearchParams()
  const navigate = useNavigate()
  const qc = useQueryClient()
  const compare = useCompareStore()

  const chips = useMemo(() => parseChipsParam(params.get('chips')), [params])
  const chipsKey = params.get('chips') || ''
  const filters = useMemo(() => parseFiltersParam(params.get('filters')), [params])
  const filtersKey = params.get('filters') || ''
  const sort = (params.get('sort') as SortOption) || 'relevance'
  const urlQuery = params.get('q') || ''
  const [draft, setDraft] = useState(urlQuery)
  const [degraded, setDegraded] = useState(false)
  const [serviceDown, setServiceDown] = useState(false)

  // A search is "active" once any constraint exists — a chip OR a panel filter.
  const active = chips.length > 0 || hasActiveFilters(filters)

  const writeUrl = (next: {
    q: string
    chips: ConstraintChip[]
    sort: SortOption
    filters: SearchFilters
  }) => {
    const p = new URLSearchParams(params)
    if (next.q.trim()) p.set('q', next.q.trim())
    else p.delete('q')
    if (next.chips.length) p.set('chips', encodeChipsParam(next.chips))
    else p.delete('chips')
    if (next.sort && next.sort !== 'relevance') p.set('sort', next.sort)
    else p.delete('sort')
    const nf = normalizeFilters(next.filters)
    if (Object.keys(nf).length) p.set('filters', encodeFiltersParam(nf))
    else p.delete('filters')
    setParams(p, { replace: true })
  }

  // ── Interpret (NL → chips), with rule-based fallback surfaced via `degraded` ──
  const interpretMut = useMutation({
    mutationFn: interpretQuery,
    onSuccess: res => {
      setDegraded(res.degraded)
      setServiceDown(false)
      writeUrl({ q: draft, chips: res.chips, sort, filters })
    },
    onError: () => setServiceDown(true),
  })

  const runInterpret = (text: string) => {
    const t = text.trim()
    if (t.length < 2) return
    interpretMut.mutate(t)
  }

  // Spec §3 — 800ms debounce auto-interpret (Enter/Search button also trigger).
  useEffect(() => {
    const t = draft.trim()
    if (t.length < 2 || t === urlQuery) return
    const id = setTimeout(() => runInterpret(t), 800)
    return () => clearTimeout(id)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [draft])

  // ── Search execution ──
  const searchQuery = useQuery({
    queryKey: ['discovery-search', chipsKey, filtersKey, sort],
    queryFn: () =>
      searchProgramsTyped({
        query: urlQuery || null,
        chips,
        filters,
        sort,
        page: 1,
        page_size: PAGE_SIZE,
      }),
    enabled: active,
    placeholderData: prev => prev,
  })

  // ── Saved state ──
  const { data: savedData } = useQuery({ queryKey: ['saved-programs'], queryFn: listSaved, retry: false })
  const [savedIds, setSavedIds] = useState<Set<string>>(new Set())
  useEffect(() => {
    if (savedData) setSavedIds(new Set(savedData.map((s: { program_id: string }) => String(s.program_id))))
  }, [savedData])

  const toggleSave = async (id: string) => {
    try {
      if (savedIds.has(id)) {
        await unsaveProgram(id)
        setSavedIds(prev => {
          const n = new Set(prev)
          n.delete(id)
          return n
        })
      } else {
        await saveProgram(id)
        setSavedIds(prev => new Set(prev).add(id))
      }
      qc.invalidateQueries({ queryKey: ['saved-programs'] })
    } catch {
      showToast("Couldn't update your list. Try again.", 'error')
    }
  }

  // ── Chip operations (all re-write the URL → re-run search) ──
  const setChips = (next: ConstraintChip[]) => writeUrl({ q: urlQuery, chips: next, sort, filters })
  const removeChip = (id: string) => setChips(chips.filter(c => c.id !== id))
  const applyEdit = (id: string, edited: ConstraintChip) => {
    const replacement = withChipId(edited)
    const next = chips
      .map(c => (c.id === id ? replacement : c))
      // de-dupe if the edit collides with an existing chip
      .filter((c, i, arr) => arr.findIndex(o => o.id === c.id) === i)
    setChips(next)
  }
  const addChip = (chip: ConstraintChip) => {
    const c = withChipId(chip)
    if (chips.some(x => x.id === c.id)) return
    setChips([...chips, c])
  }
  const confirmChip = (id: string) =>
    setChips(chips.map(c => (c.id === id ? { ...c, user_confirmed: true } : c)))
  const setSort = (s: SortOption) => writeUrl({ q: urlQuery, chips, sort: s, filters })
  const setFilters = (next: SearchFilters) =>
    writeUrl({ q: urlQuery, chips, sort, filters: next })
  const clearAll = () => {
    setDraft('')
    setDegraded(false)
    setServiceDown(false)
    writeUrl({ q: '', chips: [], sort: 'relevance', filters: {} })
  }

  const onCompareToggle = (p: ProgramSummary) => {
    if (compare.has(p.id)) {
      compare.remove(p.id)
      return
    }
    if (compare.isFull()) {
      showToast(`You can compare up to ${MAX_COMPARE} programs. Remove one to add another.`, 'warning')
      return
    }
    compare.add({
      program_id: p.id,
      program_name: p.program_name,
      institution_name: p.institution_name,
      degree_type: p.degree_type,
    })
  }

  const results = searchQuery.data?.results ?? []
  const total = searchQuery.data?.total ?? 0
  const loading = active && searchQuery.isLoading

  return (
    <section className="space-y-4" data-testid="discovery-search">
      {/* Search bar (Spec §2/§16). */}
      <div className="relative">
        <Search size={18} className="absolute left-4 top-1/2 -translate-y-1/2 text-muted-foreground" />
        <input
          type="text"
          value={draft}
          onChange={e => setDraft(e.target.value)}
          onKeyDown={e => {
            if (e.key === 'Enter') runInterpret(draft)
          }}
          placeholder="What kind of program are you looking for?"
          aria-label="Search for programs"
          className="w-full h-12 pl-11 pr-28 bg-card border border-border rounded-xl text-base text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:border-secondary transition-colors"
        />
        <div className="absolute right-2 top-1/2 -translate-y-1/2 flex items-center gap-1">
          {(draft || active) && (
            <button
              type="button"
              onClick={clearAll}
              aria-label="Clear search"
              className="p-1.5 text-muted-foreground hover:text-foreground"
            >
              <X size={16} />
            </button>
          )}
          <Button
            size="sm"
            variant="secondary"
            onClick={() => runInterpret(draft)}
            loading={interpretMut.isPending}
            disabled={draft.trim().length < 2}
          >
            Search
          </Button>
        </div>
      </div>

      {/* Fallback notices (Spec §11). */}
      {serviceDown && (
        <div className="flex items-center gap-2 px-3 py-2 rounded-lg bg-warning-soft border border-warning/30 text-sm text-foreground">
          <AlertTriangle size={14} className="text-warning shrink-0" />
          Limited search active — interpreting your query with keywords.
        </div>
      )}
      {degraded && active && !serviceDown && (
        <p className="flex items-center gap-1.5 text-xs text-muted-foreground">
          <Sparkles size={12} className="text-secondary" />
          Interpreted with basic rules. Edit any chip to refine.
        </p>
      )}

      {active && (
        <ConstraintChips
          chips={chips}
          onApplyEdit={applyEdit}
          onRemove={removeChip}
          onAdd={addChip}
          onConfirm={confirmChip}
        />
      )}

      {/* Toolbar — Filters (always available) · results count + Sort (when active). Spec §2/§5/§6. */}
      <div className="flex items-center justify-between gap-3 flex-wrap">
        <div className="flex items-center gap-3">
          <FiltersPanel filters={filters} onApply={setFilters} />
          {active && (
            <p className="text-sm text-muted-foreground" data-testid="results-count" aria-live="polite">
              {loading ? 'Searching…' : `Showing ${total} program${total === 1 ? '' : 's'}`}
            </p>
          )}
        </div>
        {active && <SortMenu value={sort} onChange={setSort} />}
      </div>

      {active ? (
        <>
          {searchQuery.isError ? (
            <div className="text-center py-16 bg-card rounded-xl border border-border">
              <AlertTriangle size={28} className="mx-auto text-warning mb-3" />
              <p className="text-sm text-foreground font-semibold mb-1">Something didn't work.</p>
              <p className="text-xs text-muted-foreground mb-4">We couldn't run that search.</p>
              <Button size="sm" variant="tertiary" onClick={() => searchQuery.refetch()}>
                Try again
              </Button>
            </div>
          ) : loading ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {Array.from({ length: 6 }).map((_, i) => (
                <div key={i} className="h-72 bg-card rounded-xl border border-border animate-pulse" />
              ))}
            </div>
          ) : total === 0 ? (
            <div className="text-center py-16 bg-card rounded-xl border border-border">
              <Search size={28} className="mx-auto text-stone mb-3" />
              <p className="text-sm text-foreground font-semibold mb-1">No programs match.</p>
              <p className="text-xs text-muted-foreground mb-4">
                Try removing a {chips.length ? 'chip' : 'filter'}
                {chips.some(c => c.category === 'budget') ||
                filters.max_tuition != null ||
                filters.min_tuition != null
                  ? ' or widening your budget'
                  : ''}
                .
              </p>
              {chips.length > 0 ? (
                <Button
                  size="sm"
                  variant="tertiary"
                  onClick={() => removeChip(chips[chips.length - 1].id as string)}
                >
                  Remove last filter
                </Button>
              ) : hasActiveFilters(filters) ? (
                <Button size="sm" variant="tertiary" onClick={() => setFilters({})}>
                  Clear filters
                </Button>
              ) : null}
            </div>
          ) : (
            <>
              {total > 100 && (
                <p className="text-xs text-muted-foreground">
                  Showing the top matches — add a constraint to narrow {total} programs.
                </p>
              )}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {results.map(p => (
                  <ProgramCard
                    key={p.id}
                    program={p}
                    saved={savedIds.has(p.id)}
                    comparing={compare.has(p.id)}
                    onSave={() => toggleSave(p.id)}
                    onCompare={() => onCompareToggle(p)}
                    onAskCounselor={() =>
                      navigate(
                        `/s?prefill=${encodeURIComponent(
                          `Tell me about ${p.program_name} at ${p.institution_name}. Is it a good fit?`,
                        )}`,
                      )
                    }
                    onView={() => navigate(`/s/programs/${p.id}`)}
                  />
                ))}
              </div>
            </>
          )}
        </>
      ) : (
        <GenreTiles
          onPick={tile =>
            addChip({
              category: 'major',
              value: tile.value,
              display: tile.label,
              confidence: 100,
              user_confirmed: true,
            })
          }
        />
      )}
    </section>
  )
}
