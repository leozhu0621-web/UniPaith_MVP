import { useState, useEffect, useMemo } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import QueryError from '../../components/ui/QueryError'
import Skeleton from '../../components/ui/Skeleton'
import Coachmark from '../../components/ui/Coachmark'
import { PageContainer, PageHeader } from '../../components/student/density'
import usePageTitle from '../../hooks/usePageTitle'
import { searchInstitutions, getFeaturedPromotions, recordPromotionClick } from '../../api/institutions'
import { listSaved, saveProgram, unsaveProgram } from '../../api/saved-lists'
import { qk } from '../../api/queryKeys'
import { getConnectEvents, getFollowing, followInstitution, unfollowInstitution, getPeersStatus } from '../../api/connect'
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
import DiscoverTabBar, { DISCOVER_TABS, type DiscoverTab } from './explore/DiscoverTabBar'
import DiscoverRail from './explore/rail/DiscoverRail'
import UpdatesTab from './connect/UpdatesTab'
import EventsTab from './connect/EventsTab'
import PeersTab from './connect/PeersTab'
import ManageFollowingPanel from './connect/ManageFollowingPanel'
import type {
  InstitutionClassification,
  SatTier,
  TuitionTier,
} from './explore/shared/classifyInstitution'

/**
 * ExplorePage — the Discover hub (Spec 2026-06-12: Discover + Connect merge).
 *
 * Sub-tabs: For you (the Stage-2 Match surface, Spec 09 + 10) · Updates ·
 * Events · Peers (the absorbed Connect surface, Spec 20). The For-you tab
 * keeps the original scroll — strategy, ranked dual-score matches, the
 * Spec-10 type-first program search, and the universities browse — plus a
 * live right rail (xl+) with updates / events / deadline radar / follow
 * suggestions. When a program search is active (chips/filters in the URL)
 * the matches + universities browse step aside so the results own the screen.
 */

// Per-tab header copy (Spec 2026-06-12 §4).
const TAB_HEADERS: Record<DiscoverTab, { title: string }> = {
  foryou: { title: 'Strategy & matches' },
  updates: { title: 'Updates' },
  events: { title: 'Events' },
  peers: { title: 'Peers' },
}

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

  // Peers ships behind a flag (connect_peers_enabled). When off, the body is a
  // "coming soon" stub — so we hide the tab entirely rather than leave a hub tab
  // that dead-ends (Discover review 2026-06-14). Optimistic: show Peers until the
  // status query confirms it's disabled, so an enabled deep-link never flickers.
  const { data: peersStatus } = useQuery({
    queryKey: ['peers-status'],
    queryFn: getPeersStatus,
    staleTime: 5 * 60 * 1000,
    retry: false,
  })
  const peersEnabled = peersStatus ? peersStatus.enabled : true

  // Hub sub-tabs (Spec 2026-06-12 §2). Unknown/absent tab → For you; a
  // ?tab=peers deep-link falls back to For you once we KNOW peers is disabled.
  const urlTab = searchParams.get('tab') as DiscoverTab | null
  const rawTab: DiscoverTab = urlTab && DISCOVER_TABS.includes(urlTab) ? urlTab : 'foryou'
  const tab: DiscoverTab = rawTab === 'peers' && peersStatus && !peersStatus.enabled ? 'foryou' : rawTab
  const setTab = (t: DiscoverTab) =>
    setSearchParams(prev => {
      const next = new URLSearchParams(prev)
      if (t === 'foryou') next.delete('tab')
      else next.set('tab', t)
      return next
    }, { replace: true })
  const [managing, setManaging] = useState(false)

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
    enabled: !searchActive && tab === 'foryou',
  })

  // Saved programs — for the MatchesSection cards.
  const { data: savedData, refetch: refetchSaved } = useQuery({ queryKey: qk.savedPrograms(), queryFn: listSaved, retry: false })

  const { data: featuredPromos } = useQuery({
    queryKey: ['featured-promotions', 'explore'],
    queryFn: () => getFeaturedPromotions(),
    staleTime: 5 * 60 * 1000,
    enabled: !searchActive && tab === 'foryou',
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
      queryClient.invalidateQueries({ queryKey: qk.savedPrograms() })
    } catch {
      showToast(`We couldn't ${wasSaved ? 'remove' : 'save'} this program. Please try again.`, 'error')
      // Re-sync from the server so the toggle reflects true state, not the failed flip.
      queryClient.invalidateQueries({ queryKey: qk.savedPrograms() })
      refetchSaved()
    }
  }

  // Followed institutions — drives card follow toggles + rail suggestions
  // (Spec 2026-06-12 §6.1/§6.6). Optimistic, same pattern as savedIds.
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

  // Next upcoming event per institution — for the Handshake-style event chips
  // on cards (Spec 2026-06-12 §6.4). Events arrive start_time-asc.
  const { data: upcomingEvents } = useQuery({
    queryKey: ['connect-events', 'upcoming'],
    queryFn: () => getConnectEvents('upcoming'),
    staleTime: 5 * 60 * 1000,
    retry: false,
    enabled: tab === 'foryou',
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
    <PageContainer>
      {/* Spec 09 §13 H1 + brand framing ("Fit, not fame", Spec 07 §2/§6). */}
      <PageHeader eyebrow="Discover" title={TAB_HEADERS[tab].title} />

      {/* First-visit tour (Ship C) — orients the hub's tabs. */}
      <Coachmark id="discover-tabs" title="Discover tabs" body="For you = your strategy and ranked matches. Updates, Events, and Peers bring news from the schools you follow." placement="bottom">
        <DiscoverTabBar tab={tab} onChange={setTab} onManageFollowing={() => setManaging(true)} peersEnabled={peersEnabled} />
      </Coachmark>

      {tab === 'foryou' ? (
        <div
          id="discover-panel-foryou"
          role="tabpanel"
          aria-labelledby="discover-tab-foryou"
          className="grid grid-cols-1 xl:grid-cols-[minmax(0,1fr)_minmax(0,19rem)] gap-6 items-start"
        >
          <div className="min-w-0">
            {/* Spec 09 §2 — strategy lands first. */}
            <div className="mb-4">
              <StrategyView forceExpanded={searchParams.get('showStrategy') === 'open'} />
            </div>

            {/* Spec 27 §6 — featured promotions from followed / matched institutions. */}
            {!searchActive && featuredPromos && featuredPromos.length > 0 && (
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

            {/* Ranked matches — hidden while a program search owns the screen. */}
            {!searchActive && (
              <div className="mb-6">
                <MatchesSection
                  savedIds={savedIds}
                  onToggleSave={toggleSave}
                  nextEventByInstitution={nextEventByInst}
                  onEventClick={() => setTab('events')}
                />
              </div>
            )}

            {/* Spec 10 — type-first program search (search box · chips · genre tiles · sort · results). */}
            <div className="mb-8">
              <DiscoverySearch
                followedIds={followedIds}
                onToggleFollow={toggleFollow}
                nextEventByInstitution={nextEventByInst}
                onEventClick={() => setTab('events')}
              />
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
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 [&>*]:min-w-0">
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
                  <>
                    {hasActiveFilters && (
                      <p className="text-[11px] text-muted-foreground mb-3">
                        Showing <span className="font-semibold text-foreground">{filteredUniList.length}</span> of {uniList.length} universities
                      </p>
                    )}
                    {/* 3 per row at lg+ — explicit founder direction (#498); do not add a 4th column. */}
                    <div className="stagger-list grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 [&>*]:min-w-0">
                      {displayUniList.map((inst: UniversityRow) => (
                        <UniversityCard
                          key={inst.id}
                          institution={inst}
                          onClick={() => navigate(`/s/institutions/${inst.id}`)}
                          following={followedIds.has(String(inst.id))}
                          onToggleFollow={() => toggleFollow(String(inst.id))}
                        />
                      ))}
                    </div>
                  </>
                )}
              </div>
            )}
          </div>

          {/* Live rail (Spec 2026-06-12 §2) — xl+ only; tab badges carry the signal below xl.
              Caps at the visible window (h-16 header + top-4 + breathing room) and scrolls
              within itself so a tall rail never pins the page. */}
          <aside className="hidden xl:block sticky top-4 min-w-0">
            {/* minViewport: the aside is CSS-hidden below xl — an invisible mark must not
                block the one-at-a-time queue. The scroll cap lives on the inner div so the
                coachmark bubble isn't clipped by overflow. */}
            <Coachmark id="discover-rail" title="Live rail" body="Updates, upcoming events, deadline radar, and schools worth following." placement="left" minViewport="xl">
              <div className="xl:max-h-[calc(100dvh-6rem)] overflow-y-auto">
                <DiscoverRail
                  followedIds={followedIds}
                  onToggleFollow={toggleFollow}
                  onOpenTab={t => setTab(t)}
                  onManageFollowing={() => setManaging(true)}
                />
              </div>
            </Coachmark>
          </aside>
        </div>
      ) : (
        <div
          id={`discover-panel-${tab}`}
          role="tabpanel"
          aria-labelledby={`discover-tab-${tab}`}
          tabIndex={0}
          className="focus-visible:outline-none"
        >
          {tab === 'updates' && <UpdatesTab onOpenEvents={() => setTab('events')} />}
          {tab === 'events' && <EventsTab />}
          {tab === 'peers' && <PeersTab />}
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
