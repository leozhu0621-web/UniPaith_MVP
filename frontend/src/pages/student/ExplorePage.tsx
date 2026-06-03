import { useState, useEffect, useMemo } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { searchInstitutions, getFeaturedPromotions, recordPromotionClick } from '../../api/institutions'
import { listSaved, saveProgram, unsaveProgram } from '../../api/saved-lists'
import UniversityCard from './explore/cards/UniversityCard'
import ExploreFilters, { EMPTY_FILTERS, applyFilters, countActiveFilters, type FilterState } from './explore/shared/ExploreFilters'
import { Building2 } from 'lucide-react'
import StrategyView from './match/StrategyView'
import MatchesSection from './match/MatchesSection'
import PromoCard from './explore/cards/PromoCard'
import DiscoverySearch from './explore/discovery/DiscoverySearch'
import { parseChipsParam } from './explore/discovery/chipUtils'
import { hasActiveFilters as hasProgramFilters, parseFiltersParam } from './explore/discovery/filterUtils'
import type {
  InstitutionClassification,
  SatTier,
  TuitionTier,
} from './explore/shared/classifyInstitution'

/**
 * ExplorePage — the Stage-2 "Match" surface (Spec 09 + 10) at /s/explore.
 *
 * Top: the active strategy (Spec 09 §2) and the ranked dual-score matches.
 * Then the Spec-10 type-first program search (DiscoverySearch): search box,
 * constraint chips, genre tiles, sort, and a programs-only results grid.
 * When a search is active (chips/query in the URL) the matches + universities
 * browse step aside so the results own the screen; otherwise the universities
 * browse grid remains available below the genre tiles.
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

/** Serialize filter state into URL search params (preserves other keys). */
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

  // A Spec-10 program search is "active" once there are constraint chips in the
  // URL (matching DiscoverySearch's own notion) — drives whether the matches +
  // universities browse stand aside so the programs results own the screen.
  const searchActive =
    parseChipsParam(searchParams.get('chips')).length > 0 ||
    hasProgramFilters(parseFiltersParam(searchParams.get('filters')))

  // Universities browse filter state lives in the URL.
  const filters = useMemo(() => filtersFromURL(searchParams), [searchParams])
  const setFilters = (next: FilterState) => {
    setSearchParams(filtersToURL(searchParams, next), { replace: true })
  }

  const { data: universities, isLoading: uniLoading } = useQuery({
    queryKey: ['explore-universities'],
    queryFn: () => searchInstitutions({ page_size: 50 }),
    staleTime: 5 * 60 * 1000,
    enabled: !searchActive,
  })

  // Saved programs — for the MatchesSection cards.
  const { data: savedData } = useQuery({ queryKey: ['saved-programs'], queryFn: listSaved, retry: false })

  const { data: featuredPromos } = useQuery({
    queryKey: ['featured-promotions', 'explore'],
    queryFn: () => getFeaturedPromotions(),
    staleTime: 5 * 60 * 1000,
    enabled: !searchActive,
  })

  const [savedIds, setSavedIds] = useState<Set<string>>(new Set())
  useEffect(() => {
    if (savedData) setSavedIds(new Set(savedData.map((s: { program_id: string }) => String(s.program_id))))
  }, [savedData])

  const toggleSave = async (programId: string) => {
    try {
      if (savedIds.has(programId)) {
        await unsaveProgram(programId)
        setSavedIds(prev => { const n = new Set(prev); n.delete(programId); return n })
      } else {
        await saveProgram(programId)
        setSavedIds(prev => new Set(prev).add(programId))
      }
      queryClient.invalidateQueries({ queryKey: ['saved-programs'] })
    } catch { /* non-blocking */ }
  }

  const uniList: UniversityRow[] = universities?.items ?? []
  const filteredUniList = useMemo(() => applyFilters(uniList, filters), [uniList, filters])
  const hasActiveFilters = countActiveFilters(filters) > 0

  return (
    <div className="p-6 max-w-6xl mx-auto">
      {/* Spec 09 §13 H1 + brand framing ("Fit, not fame", Spec 07 §2/§6). */}
      <div className="mb-5">
        <p className="text-eyebrow uppercase text-secondary font-semibold">Match</p>
        <h1 className="text-2xl font-bold text-foreground mt-1">Your strategy and your matches</h1>
        <p className="text-sm text-muted-foreground mt-0.5">Ranked for fit, not fame — and every score explains itself.</p>
      </div>

      {/* Spec 09 §2 — strategy lands first. */}
      <div className="mb-4">
        <StrategyView forceExpanded={searchParams.get('showStrategy') === 'open'} />
      </div>

      {/* Spec 27 §6 — featured promotions from followed / matched institutions. */}
      {!searchActive && featuredPromos && featuredPromos.length > 0 && (
        <div className="mb-6">
          <h2 className="text-eyebrow uppercase text-muted-foreground font-semibold mb-3">Featured programs</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {featuredPromos.slice(0, 3).map(promo => (
              <PromoCard
                key={promo.id}
                promo={promo}
                onView={() => {
                  recordPromotionClick(promo.id).catch(() => {})
                  if (promo.program_id) navigate(`/s/programs/${promo.program_id}`)
                  else if (promo.target_url) window.open(promo.target_url, '_blank', 'noopener,noreferrer')
                }}
              />
            ))}
          </div>
        </div>
      )}

      {/* Ranked matches — hidden while a program search owns the screen. */}
      {!searchActive && (
        <div className="mb-6">
          <MatchesSection savedIds={savedIds} onToggleSave={toggleSave} />
        </div>
      )}

      {/* Spec 10 — type-first program search (search box · chips · genre tiles · sort · results). */}
      <div className="mb-8">
        <DiscoverySearch />
      </div>

      {/* Browse universities — secondary, idle-only (no entity-mixing with the program results). */}
      {!searchActive && (
        <div>
          <h2 className="text-eyebrow uppercase text-muted-foreground font-semibold mb-3">Browse universities</h2>

          {uniList.length > 0 && (
            <ExploreFilters universities={uniList} filters={filters} onChange={setFilters} />
          )}

          {uniLoading ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {[1, 2, 3].map(i => <div key={i} className="h-80 bg-card rounded-xl border border-border animate-pulse" />)}
            </div>
          ) : uniList.length === 0 ? (
            <div className="text-center py-16 bg-card rounded-xl border border-border">
              <Building2 size={32} className="mx-auto text-muted-foreground mb-3" />
              <p className="text-sm text-foreground font-semibold mb-1">No universities yet</p>
              <p className="text-xs text-muted-foreground">Universities will appear here as they join the platform.</p>
            </div>
          ) : filteredUniList.length === 0 ? (
            <div className="text-center py-16 bg-card rounded-xl border border-border">
              <Building2 size={32} className="mx-auto text-muted-foreground mb-3" />
              <p className="text-sm text-foreground font-semibold mb-1">No universities match your filters</p>
              <p className="text-xs text-muted-foreground mb-4">Try removing a filter or broadening your search.</p>
              <button
                onClick={() => setFilters(EMPTY_FILTERS)}
                className="text-xs font-semibold text-secondary hover:underline"
              >
                Clear all filters
              </button>
            </div>
          ) : (
            <>
              {hasActiveFilters && (
                <p className="text-[11px] text-muted-foreground mb-3">
                  Showing <span className="font-semibold text-foreground">{filteredUniList.length}</span> of {uniList.length} universities
                </p>
              )}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {filteredUniList.map((inst: UniversityRow) => (
                  <UniversityCard
                    key={inst.id}
                    institution={inst}
                    onClick={() => navigate(`/s/institutions/${inst.id}`)}
                  />
                ))}
              </div>
            </>
          )}
        </div>
      )}
    </div>
  )
}

// The institution browse rows are loosely typed by the API; ExploreFilters and
// UniversityCard consume the wider shape.
// eslint-disable-next-line @typescript-eslint/no-explicit-any
type UniversityRow = any
