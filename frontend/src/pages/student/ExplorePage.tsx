import { useState, useEffect, useMemo, useRef } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import QueryError from '../../components/ui/QueryError'
import Skeleton from '../../components/ui/Skeleton'
import Coachmark from '../../components/ui/Coachmark'
import { PageContainer } from '../../components/student/density'
import usePageTitle from '../../hooks/usePageTitle'
import { searchAllInstitutions, getFeaturedPromotions, recordPromotionClick } from '../../api/institutions'
import { listSaved, saveProgram, unsaveProgram } from '../../api/saved-lists'
import { qk } from '../../api/queryKeys'
import { getConnectEvents, getFollowing, followInstitution, unfollowInstitution } from '../../api/connect'
import { getActiveStrategy } from '../../api/strategy'
import { showToast } from '../../stores/toast-store'
import { getRecentPrograms, type RecentProgram } from '../../lib/recentPrograms'
import UniversityCard from './explore/cards/UniversityCard'
import UniversityListRow from './explore/cards/UniversityListRow'
import ViewToggle from '../../components/ui/ViewToggle'
import useBrowseView from '../../hooks/useBrowseView'
import ExploreFilters, { EMPTY_FILTERS, applyFilters, countActiveFilters, type FilterState } from './explore/shared/ExploreFilters'
import { Building2, GraduationCap, MapPin, Users } from 'lucide-react'
import StrategyView from './match/StrategyView'
import MatchesSection from './match/MatchesSection'
import PromoCard from './explore/cards/PromoCard'
import DiscoverySearch from './explore/discovery/DiscoverySearch'
import { resolveBrowseMode } from './explore/browseMode'
import Pagination from '../../components/ui/Pagination'
import { parseChipsParam } from './explore/discovery/chipUtils'
import { hasActiveFilters as hasProgramFilters, parseFiltersParam } from './explore/discovery/filterUtils'
import DiscoverTabBar, { type DiscoverTab } from './explore/DiscoverTabBar'
import AcademicTabBar, { normalizeAcademicSub, type AcademicSub } from './explore/AcademicTabBar'
import ResourcesFinancial from './explore/resources/ResourcesFinancial'
import ResourcesInternational from './explore/resources/ResourcesInternational'
import DiscoverRail from './explore/rail/DiscoverRail'
import UpdatesTab from './connect/UpdatesTab'
import EventsTab from './connect/EventsTab'
import ManageFollowingPanel from './connect/ManageFollowingPanel'
import type {
  InstitutionClassification,
  SatTier,
  TuitionTier,
} from './explore/shared/classifyInstitution'

/**
 * ExplorePage — the Discover hub (Spec 2026-06-14 restructure).
 *
 * Top tabs: For you · Academic · Financial · International.
 *  - For you: strategy · recently-viewed · featured · ranked matches + the live
 *    right rail (xl+) and an Academic hand-off button.
 *  - Academic: a sub-tab bar — Universities (the program search + universities
 *    browse), Updates, Events (news from the schools you follow).
 *  - Financial / International: the Resources guides (authored + personalized).
 * Old links migrate: ?tab=resources|browse → academic; ?sub=financial|international
 * → the top tab; ?tab=updates|events → academic sub; ?tab=peers → for you.
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
  usePageTitle('Discover')
  const navigate = useNavigate()
  const [searchParams, setSearchParams] = useSearchParams()
  const queryClient = useQueryClient()

  // A Spec-10 program search is "active" once there are constraint chips/filters
  // in the URL. Program search lives under Academic › Universities; a chips/filters
  // deep-link (e.g. a saved search) opens it.
  const searchActive =
    parseChipsParam(searchParams.get('chips')).length > 0 ||
    hasProgramFilters(parseFiltersParam(searchParams.get('filters')))

  // Resolve the top tab + the Academic sub-tab, migrating old-structure links.
  const { tab, sub } = useMemo(() => {
    const tp = searchParams.get('tab')
    const sp = searchParams.get('sub')
    const resolve = (): { tab: DiscoverTab; sub: AcademicSub } => {
      if (tp === 'financial' || tp === 'international') return { tab: tp, sub: 'universities' }
      if (tp === 'academic') return { tab: 'academic', sub: normalizeAcademicSub(sp) }
      if (tp === 'updates') return { tab: 'academic', sub: 'updates' }
      if (tp === 'events') return { tab: 'academic', sub: 'events' }
      if (tp === 'peers' || tp === 'foryou') return { tab: 'foryou', sub: 'universities' }
      if (tp === 'resources' || tp === 'browse') {
        if (sp === 'financial') return { tab: 'financial', sub: 'universities' }
        if (sp === 'international') return { tab: 'international', sub: 'universities' }
        return { tab: 'academic', sub: 'universities' }
      }
      return { tab: searchActive ? 'academic' : 'foryou', sub: normalizeAcademicSub(sp) }
    }
    return resolve()
  }, [searchParams, searchActive])

  const setTab = (t: DiscoverTab) =>
    setSearchParams(prev => {
      const next = new URLSearchParams(prev)
      if (t === 'foryou') next.delete('tab')
      else next.set('tab', t)
      next.delete('sub')
      // Leaving Academic → drop the program-search params so other tabs stay clean.
      if (t !== 'academic') {
        next.delete('q')
        next.delete('chips')
        next.delete('filters')
      }
      return next
    }, { replace: true })

  const setSub = (s: AcademicSub) =>
    setSearchParams(prev => {
      const next = new URLSearchParams(prev)
      next.set('tab', 'academic')
      if (s === 'universities') next.delete('sub')
      else next.set('sub', s)
      return next
    }, { replace: true })

  const [managing, setManaging] = useState(false)
  const onUniversities = tab === 'academic' && sub === 'universities'

  // Academic › Universities holds two distinct searches over two entity types.
  // Make the mode an EXPLICIT choice (Discover review 2026-06-19 #3) instead of a
  // silent swap driven by whether a program search is active: ?umode= owns it,
  // and the default follows the URL so a shared program-search deep-link still
  // opens in Programs.
  const browseMode = resolveBrowseMode(searchParams.get('umode'), searchActive)
  const setBrowseMode = (m: 'programs' | 'universities') =>
    setSearchParams(
      prev => {
        const next = new URLSearchParams(prev)
        next.set('tab', 'academic')
        next.delete('sub')
        if (m === 'universities') next.delete('umode')
        else next.set('umode', m)
        return next
      },
      { replace: true },
    )

  // Universities browse filter state lives in the URL.
  const filters = useMemo(() => filtersFromURL(searchParams), [searchParams])
  const setFilters = (next: FilterState) => {
    setSearchParams(filtersToURL(searchParams, next), { replace: true })
  }

  const { data: universities, isLoading: uniLoading, isError: uniError, refetch: refetchUni } = useQuery({
    queryKey: ['explore-universities'],
    queryFn: () => searchAllInstitutions(),
    staleTime: 5 * 60 * 1000,
    enabled: onUniversities && browseMode === 'universities',
  })

  // Saved programs — for the MatchesSection cards.
  const { data: savedData, refetch: refetchSaved } = useQuery({ queryKey: qk.savedPrograms(), queryFn: listSaved, retry: false })

  // Active strategy presence — drives the strategy→matches bridge line in
  // MatchesSection. Same query key as StrategyView (shared cache). For-you only.
  const { data: activeStrategy } = useQuery({
    queryKey: ['strategy', 'active'],
    queryFn: () => getActiveStrategy(),
    enabled: tab === 'foryou',
  })

  // Recently-viewed programs (localStorage). Re-entry shortcut on For-you.
  const [recentPrograms] = useState<RecentProgram[]>(() => getRecentPrograms())

  const { data: featuredPromos } = useQuery({
    queryKey: ['featured-promotions', 'explore'],
    queryFn: () => getFeaturedPromotions(),
    staleTime: 5 * 60 * 1000,
    enabled: tab === 'foryou',
  })

  const [savedIds, setSavedIds] = useState<Set<string>>(new Set())
  useEffect(() => {
    if (savedData) setSavedIds(new Set(savedData.map((s: { program_id: string }) => String(s.program_id))))
  }, [savedData])

  const toggleSave = async (programId: string) => {
    const wasSaved = savedIds.has(programId)
    setSavedIds(prev => {
      const n = new Set(prev)
      if (wasSaved) n.delete(programId)
      else n.add(programId)
      return n
    })
    try {
      if (wasSaved) await unsaveProgram(programId)
      else await saveProgram(programId)
      queryClient.invalidateQueries({ queryKey: qk.savedPrograms() })
    } catch {
      showToast(`We couldn't ${wasSaved ? 'remove' : 'save'} this program. Please try again.`, 'error')
      queryClient.invalidateQueries({ queryKey: qk.savedPrograms() })
      refetchSaved()
    }
  }

  // Followed institutions — drives card follow toggles + rail suggestions.
  const { data: follows, refetch: refetchFollows } = useQuery({
    queryKey: ['connect-follows'],
    queryFn: getFollowing,
    retry: false,
  })
  const [followedIds, setFollowedIds] = useState<Set<string>>(new Set())
  useEffect(() => {
    if (follows) setFollowedIds(new Set(follows.map(f => String(f.institution_id))))
  }, [follows])

  const toggleFollow = async (institutionId: string) => {
    const was = followedIds.has(institutionId)
    setFollowedIds(prev => {
      const n = new Set(prev)
      if (was) n.delete(institutionId)
      else n.add(institutionId)
      return n
    })
    try {
      if (was) await unfollowInstitution(institutionId)
      else await followInstitution(institutionId)
      queryClient.invalidateQueries({ queryKey: ['connect-follows'] })
      queryClient.invalidateQueries({ queryKey: ['connect-feed-rail'] })
    } catch {
      showToast(`We couldn't ${was ? 'unfollow' : 'follow'} this school. Please try again.`, 'error')
      queryClient.invalidateQueries({ queryKey: ['connect-follows'] })
      refetchFollows()
    }
  }

  // Next upcoming event per institution — Handshake-style event chips on cards.
  const { data: upcomingEvents } = useQuery({
    queryKey: ['connect-events', 'upcoming'],
    queryFn: () => getConnectEvents('upcoming'),
    staleTime: 5 * 60 * 1000,
    retry: false,
    enabled: tab === 'foryou' || onUniversities,
  })
  const nextEventByInst = useMemo(() => {
    const m = new Map<string, { event_name: string; start_time: string }>()
    for (const e of upcomingEvents?.events ?? []) {
      if (!m.has(e.institution_id)) m.set(e.institution_id, { event_name: e.event_name, start_time: e.start_time })
    }
    return m
  }, [upcomingEvents])

  const uniList: UniversityRow[] = universities?.items ?? []
  const filteredUniList = useMemo(() => applyFilters(uniList, filters), [uniList, filters])
  const hasActiveFilters = countActiveFilters(filters) > 0

  // "Near me" — sort universities by distance to the student's location.
  const [nearMe, setNearMe] = useState<{ lat: number; lng: number } | null>(null)
  const [geoBusy, setGeoBusy] = useState(false)
  const requestNearMe = () => {
    if (nearMe) {
      setNearMe(null)
      return
    }
    if (!navigator.geolocation) {
      showToast("Location isn't available in this browser.", 'error')
      return
    }
    setGeoBusy(true)
    navigator.geolocation.getCurrentPosition(
      pos => {
        setNearMe({ lat: pos.coords.latitude, lng: pos.coords.longitude })
        setGeoBusy(false)
      },
      () => {
        setGeoBusy(false)
        showToast("We couldn't get your location. Please check your browser's location permission.", 'error')
      },
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

  // The browse grid is paginated — 24 per page. Filters / near-me reset to page 1.
  const BROWSE_PAGE_SIZE = 24
  const [browsePage, setBrowsePage] = useState(1)
  const browseTopRef = useRef<HTMLDivElement>(null)
  useEffect(() => { setBrowsePage(1) }, [filteredUniList, nearMe])
  const browsePageCount = Math.max(1, Math.ceil(displayUniList.length / BROWSE_PAGE_SIZE))
  const goToBrowsePage = (p: number) => {
    setBrowsePage(Math.min(Math.max(1, p), browsePageCount))
    browseTopRef.current?.scrollIntoView({ block: 'start' })
  }

  // Grid (photo cards) vs list (dense rows) — shared across browse surfaces.
  const [browseView, setBrowseView] = useBrowseView()

  return (
    <PageContainer>
      {/* First-visit tour (Ship C) — orients the hub's tabs. */}
      <Coachmark id="discover-tabs" title="Discover tabs" body="For you = your strategy and ranked matches. Academic browses universities and school news; Financial and International hold scholarship and visa resources." placement="bottom">
        <DiscoverTabBar tab={tab} onChange={setTab} />
      </Coachmark>

      {tab === 'foryou' ? (
        <div
          id="discover-panel-foryou"
          role="tabpanel"
          aria-labelledby="discover-tab-foryou"
          tabIndex={0}
          className="grid grid-cols-1 xl:grid-cols-[minmax(0,1fr)_minmax(0,19rem)] gap-6 items-start focus-visible:outline-none"
        >
          <div className="min-w-0">
            <div className="mb-4">
              <StrategyView forceExpanded={searchParams.get('showStrategy') === 'open'} />
            </div>

            {recentPrograms.length > 0 && (
              <div className="mb-6">
                <h2 className="text-eyebrow uppercase text-muted-foreground font-semibold mb-3">Pick up where you left off</h2>
                <div className="flex flex-wrap gap-2">
                  {recentPrograms.slice(0, 5).map(p => (
                    <Link
                      key={p.id}
                      to={`/s/programs/${p.id}`}
                      className="group flex min-w-0 max-w-[15rem] items-center gap-2 rounded-lg border border-border bg-card px-3 py-2 transition-colors hover:bg-muted"
                    >
                      <GraduationCap size={14} className="shrink-0 text-muted-foreground" />
                      <span className="min-w-0">
                        <span className="block truncate text-xs font-semibold text-foreground group-hover:text-secondary">
                          {p.program_name}
                        </span>
                        {p.institution_name && (
                          <span className="block truncate text-[11px] text-muted-foreground">{p.institution_name}</span>
                        )}
                      </span>
                    </Link>
                  ))}
                </div>
              </div>
            )}

            {featuredPromos && featuredPromos.length > 0 && (
              <div className="mb-6">
                <h2 className="text-eyebrow uppercase text-muted-foreground font-semibold mb-3">Featured programs</h2>
                <div className="stagger-list grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 2xl:grid-cols-4 gap-4 [&>*]:min-w-0">
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

            <div className="mb-6">
              <MatchesSection
                savedIds={savedIds}
                onToggleSave={toggleSave}
                nextEventByInstitution={nextEventByInst}
                onEventClick={() => setSub('events')}
                strategyActive={!!activeStrategy}
              />
            </div>

            <div className="flex flex-wrap items-center gap-2">
              <button
                onClick={() => setTab('academic')}
                className="ui-btn inline-flex items-center gap-1.5 rounded-lg border border-border px-3 py-2 text-sm font-medium text-foreground hover:bg-muted"
              >
                <Building2 size={15} className="text-secondary" /> Browse universities &amp; programs
              </button>
              {/* "Manage following" lives in the xl rail; mirror it here below xl
                  so laptop/tablet students (where the rail never mounts) can still
                  reach the follow manager (Discover review 2026-06-19 #1). */}
              <button
                onClick={() => setManaging(true)}
                className="ui-btn xl:hidden inline-flex items-center gap-1.5 rounded-lg border border-border px-3 py-2 text-sm font-medium text-foreground hover:bg-muted"
              >
                <Users size={15} className="text-secondary" /> Manage following
              </button>
            </div>
          </div>

          {/* Live rail (xl+ only) — updates / events / deadline radar / following. */}
          <aside className="hidden xl:block sticky top-4 min-w-0">
            <Coachmark id="discover-rail" title="Live rail" body="Updates, upcoming events, deadline radar, and schools worth following." placement="left" minViewport="xl">
              <div className="xl:max-h-[calc(100dvh-6rem)] overflow-y-auto">
                <DiscoverRail
                  followedIds={followedIds}
                  onToggleFollow={toggleFollow}
                  onOpenTab={t => setSub(t)}
                  onManageFollowing={() => setManaging(true)}
                />
              </div>
            </Coachmark>
          </aside>
        </div>
      ) : tab === 'financial' ? (
        <div id="discover-panel-financial" role="tabpanel" aria-labelledby="discover-tab-financial" tabIndex={0} className="focus-visible:outline-none">
          <ResourcesFinancial />
        </div>
      ) : tab === 'international' ? (
        <div id="discover-panel-international" role="tabpanel" aria-labelledby="discover-tab-international" tabIndex={0} className="focus-visible:outline-none">
          <ResourcesInternational />
        </div>
      ) : (
        <div
          id="discover-panel-academic"
          role="tabpanel"
          aria-labelledby="discover-tab-academic"
          tabIndex={0}
          className="focus-visible:outline-none"
        >
          <AcademicTabBar sub={sub} onChange={setSub} />

          {sub === 'updates' ? (
            <UpdatesTab onOpenEvents={() => setSub('events')} />
          ) : sub === 'events' ? (
            <EventsTab />
          ) : (
            <>
              {/* Universities sub-tab: an EXPLICIT Programs vs Universities mode
                  (Discover review 2026-06-19 #3) — one entity, one result set, one
                  filter control per mode, instead of a silent swap on whether a
                  program search happens to be active. */}
              <div className="mb-5 flex justify-center">
                <div
                  role="group"
                  aria-label="Browse universities or programs"
                  className="inline-flex rounded-lg border border-border bg-card p-0.5"
                >
                  {(
                    [
                      { key: 'universities', label: 'Universities', Icon: Building2 },
                      { key: 'programs', label: 'Programs', Icon: GraduationCap },
                    ] as const
                  ).map(m => {
                    const on = browseMode === m.key
                    return (
                      <button
                        key={m.key}
                        type="button"
                        aria-pressed={on}
                        onClick={() => setBrowseMode(m.key)}
                        className={`inline-flex items-center gap-1.5 rounded-md px-4 py-1.5 text-sm font-medium transition-colors ${
                          on ? 'bg-secondary text-secondary-foreground' : 'text-muted-foreground hover:text-foreground'
                        }`}
                      >
                        <m.Icon size={14} aria-hidden />
                        {m.label}
                      </button>
                    )
                  })}
                </div>
              </div>

              {browseMode === 'programs' ? (
                <div className="mb-8">
                  <DiscoverySearch
                    followedIds={followedIds}
                    onToggleFollow={toggleFollow}
                    nextEventByInstitution={nextEventByInst}
                    onEventClick={() => setSub('events')}
                  />
                </div>
              ) : (
                <div ref={browseTopRef} className="scroll-mt-4">
                  <div className="flex items-center justify-center gap-3 mb-3">
                    <h2 className="text-base font-bold text-foreground">Browse universities</h2>
                    <button
                      onClick={requestNearMe}
                      aria-pressed={!!nearMe}
                      aria-busy={geoBusy}
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
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 2xl:grid-cols-4 gap-4 [&>*]:min-w-0">
                      {[1, 2, 3].map(i => (
                        <div key={i} className="bg-card rounded-lg border border-border overflow-hidden">
                          <div className="up-skeleton h-36" />
                          <div className="p-5 space-y-2.5">
                            <Skeleton className="h-4 w-3/4" />
                            <Skeleton className="h-3 w-1/2" />
                            <Skeleton className="h-3 w-2/3" />
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : uniList.length === 0 ? (
                    <div className="text-center py-16 bg-card rounded-xl border border-border">
                      <Building2 size={32} className="mx-auto text-muted-foreground mb-3" />
                      <p className="text-sm text-foreground font-semibold">No universities yet</p>
                    </div>
                  ) : filteredUniList.length === 0 ? (
                    <div className="text-center py-16 bg-card rounded-xl border border-border">
                      <Building2 size={32} className="mx-auto text-muted-foreground mb-3" />
                      <p className="text-sm text-foreground font-semibold mb-4">No universities match your filters</p>
                      <button
                        onClick={() => setFilters(EMPTY_FILTERS)}
                        className="text-xs font-semibold text-secondary hover:underline"
                      >
                        Clear all filters
                      </button>
                    </div>
                  ) : (
                    (() => {
                      const total = displayUniList.length
                      // Clamp to the last page so a filter that shrinks the set
                      // never flashes a negative/out-of-range range for a frame.
                      const safePage = Math.min(browsePage, Math.max(1, Math.ceil(total / BROWSE_PAGE_SIZE)))
                      const from = (safePage - 1) * BROWSE_PAGE_SIZE
                      const pageItems = displayUniList.slice(from, from + BROWSE_PAGE_SIZE)
                      return (
                        <>
                          <div className="flex items-center justify-between gap-3 mb-3">
                            <p className="text-[11px] text-muted-foreground" aria-live="polite" aria-atomic="true">
                              Showing <span className="font-semibold text-foreground">{from + 1}–{from + pageItems.length}</span> of {total}{hasActiveFilters ? ' matching' : ''} universities
                            </p>
                            <ViewToggle value={browseView} onChange={setBrowseView} />
                          </div>
                          {/* key on the page so the stagger entrance replays as each page flips in */}
                          {browseView === 'grid' ? (
                            <div key={browsePage} className="stagger-list grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 2xl:grid-cols-4 gap-4 [&>*]:min-w-0">
                              {pageItems.map((inst: UniversityRow) => (
                                <UniversityCard
                                  key={inst.id}
                                  institution={inst}
                                  onClick={() => navigate(`/s/institutions/${inst.id}`)}
                                  following={followedIds.has(String(inst.id))}
                                  onToggleFollow={() => toggleFollow(String(inst.id))}
                                />
                              ))}
                            </div>
                          ) : (
                            <div key={browsePage} className="stagger-list flex flex-col gap-2 [&>*]:min-w-0">
                              {pageItems.map((inst: UniversityRow) => (
                                <UniversityListRow
                                  key={inst.id}
                                  institution={inst}
                                  onClick={() => navigate(`/s/institutions/${inst.id}`)}
                                  following={followedIds.has(String(inst.id))}
                                  onToggleFollow={() => toggleFollow(String(inst.id))}
                                />
                              ))}
                            </div>
                          )}
                          <Pagination
                            page={browsePage}
                            pageCount={browsePageCount}
                            onChange={goToBrowsePage}
                            className="mt-6"
                          />
                        </>
                      )
                    })()
                  )}
                </div>
              )}
            </>
          )}
        </div>
      )}

      {managing && <ManageFollowingPanel onClose={() => setManaging(false)} />}
    </PageContainer>
  )
}

// The institution browse rows are loosely typed by the API; ExploreFilters and
// UniversityCard consume the wider shape.
// eslint-disable-next-line @typescript-eslint/no-explicit-any
type UniversityRow = any
