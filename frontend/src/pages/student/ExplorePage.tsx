import { useState, useEffect, useMemo } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import QueryError from '../../components/ui/QueryError'
import { PageHeader } from '../../components/student/density'
import { searchInstitutions, getFeaturedPromotions, recordPromotionClick } from '../../api/institutions'
import { listSaved, saveProgram, unsaveProgram } from '../../api/saved-lists'
import { showToast } from '../../stores/toast-store'
import UniversityCard from './explore/cards/UniversityCard'
import ExploreFilters, { EMPTY_FILTERS, applyFilters, countActiveFilters, type FilterState } from './explore/shared/ExploreFilters'
import { Building2, MapPin } from 'lucide-react'
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

  const { data: universities, isLoading: uniLoading, isError: uniError, refetch: refetchUni } = useQuery({
    queryKey: ['explore-universities'],
    queryFn: () => searchInstitutions({ page_size: 50 }),
    staleTime: 5 * 60 * 1000,
    enabled: !searchActive,
  })

  // Saved programs — for the MatchesSection cards.
  const { data: savedData, refetch: refetchSaved } = useQuery({ queryKey: ['saved-programs'], queryFn: listSaved, retry: false })

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
    const wasSaved = savedIds.has(programId)
    // Optimistic flip for snappy UI; reconcile on failure.
    setSavedIds(prev => {
      const n = new Set(prev)
      if (wasSaved) n.delete(programId)
      else n.add(programId)
      return n
    })
    try {
      if (wasSaved) await unsaveProgram(programId)
      else await saveProgram(programId)
      queryClient.invalidateQueries({ queryKey: ['saved-programs'] })
    } catch {
      showToast(`We couldn't ${wasSaved ? 'remove' : 'save'} this program. Please try again.`, 'error')
      // Re-sync from the server so the toggle reflects true state, not the failed flip.
      queryClient.invalidateQueries({ queryKey: ['saved-programs'] })
      refetchSaved()
    }
  }

  const uniList: UniversityRow[] = universities?.items ?? []
  const filteredUniList = useMemo(() => applyFilters(uniList, filters), [uniList, filters])
  const hasActiveFilters = countActiveFilters(filters) > 0

  // "Near me" — sort universities by distance to the student's location (geo
  // feature: choose schools near me). Browser geolocation; no data leaves the page.
  const [nearMe, setNearMe] = useState<{ lat: number; lng: number } | null>(null)
  const [geoBusy, setGeoBusy] = useState(false)
  const requestNearMe = () => {
    if (nearMe) {
      setNearMe(null)
      return
    }
    if (!navigator.geolocation) return
    setGeoBusy(true)
    navigator.geolocation.getCurrentPosition(
      pos => {
        setNearMe({ lat: pos.coords.latitude, lng: pos.coords.longitude })
        setGeoBusy(false)
      },
      () => setGeoBusy(false),
      { timeout: 10000 },
    )
  }
  const displayUniList = useMemo(() => {
    if (!nearMe) return filteredUniList
    const hav = (la1: number, lo1: number, la2: number, lo2: number) => {
      const R = 6371
      const d = (x: number) => (x * Math.PI) / 180
      const a =
        Math.sin(d(la2 - la1) / 2) ** 2 +
        Math.cos(d(la1)) * Math.cos(d(la2)) * Math.sin(d(lo2 - lo1) / 2) ** 2
      return 2 * R * Math.asin(Math.sqrt(a))
    }
    return [...filteredUniList]
      .map((u: any) => ({
        u,
        dist:
          u.latitude != null && u.longitude != null
            ? hav(nearMe.lat, nearMe.lng, u.latitude, u.longitude)
            : Infinity,
      }))
      .sort((a, b) => a.dist - b.dist)
      .map(x => ({ ...x.u, _distance_km: Number.isFinite(x.dist) ? Math.round(x.dist) : null }))
  }, [filteredUniList, nearMe])

  return (
    <div className="p-4 w-full">
      {/* Spec 09 §13 H1 + brand framing ("Fit, not fame", Spec 07 §2/§6). */}
      <PageHeader
        eyebrow="Discover"
        title="Your strategy and your matches"
        sub="Ranked for fit, not fame — and every score explains itself."
      />

      {/* Spec 09 §2 — strategy lands first. */}
      <div className="mb-4">
        <StrategyView forceExpanded={searchParams.get('showStrategy') === 'open'} />
      </div>

      {/* Spec 27 §6 — featured promotions from followed / matched institutions. */}
      {!searchActive && featuredPromos && featuredPromos.length > 0 && (
        <div className="mb-6">
          <h2 className="text-eyebrow uppercase text-muted-foreground font-semibold mb-3">Featured programs</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
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
          <div className="flex items-center justify-between gap-3 mb-3">
            <h2 className="text-eyebrow uppercase text-muted-foreground font-semibold">Browse universities</h2>
            <button
              onClick={requestNearMe}
              aria-pressed={!!nearMe}
              className={`inline-flex items-center gap-1.5 text-xs font-semibold rounded-md px-2.5 py-1.5 border transition-colors ${
                nearMe
                  ? 'bg-secondary text-secondary-foreground border-secondary'
                  : 'text-secondary border-border hover:bg-muted'
              }`}
            >
              <MapPin size={13} />
              {nearMe ? 'Near me · on' : geoBusy ? 'Locating…' : 'Near me'}
            </button>
          </div>

          {uniList.length > 0 && (
            <ExploreFilters universities={uniList} filters={filters} onChange={setFilters} />
          )}

          {uniError ? (
            <QueryError detail="We couldn't load universities." onRetry={() => refetchUni()} />
          ) : uniLoading ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
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
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
                {displayUniList.map((inst: UniversityRow) => (
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
