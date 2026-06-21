import { Fragment, useEffect, useState } from 'react'
import QueryError from '../../components/ui/QueryError'
import { useParams, useNavigate, useSearchParams, Link } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  getProgram, getProgramReviews, getEmployerFeedback, getNetPrice,
  searchPrograms, semanticSearch,
} from '../../api/programs'
import { getPublicPosts } from '../../api/institutions'
import { getProfile } from '../../api/students'
import SocialLinks from '../../components/SocialLinks'
import { pushRecentProgram } from '../../lib/recentPrograms'
import usePageTitle from '../../hooks/usePageTitle'
import { getMatchDetail, logEngagement } from '../../api/matching'
import { listEvents } from '../../api/events'
import { saveProgram, unsaveProgram, listSaved } from '../../api/saved-lists'
import { qk } from '../../api/queryKeys'
import { showToast } from '../../stores/toast-store'
import { useCompareStore } from '../../stores/compare-store'
import Card from '../../components/ui/Card'
import Badge from '../../components/ui/Badge'
import Button from '../../components/ui/Button'
import Skeleton from '../../components/ui/Skeleton'
import { formatCurrency, formatDate } from '../../utils/format'
import { daysUntil } from '../../utils/deadline'
import {
  BookOpen, GraduationCap, DollarSign, TrendingUp, MessageSquare, Megaphone,
  Briefcase, Building2, Users, Clock, Sparkles, Mail, Archive,
  Bookmark, BookmarkCheck, ArrowRightLeft, ChevronRight, ArrowLeft, ExternalLink, Star,
} from 'lucide-react'
import { DEGREE_LABELS } from '../../utils/constants'
import type { EventItem } from '../../types'
import {
  normalizeCostData,
  normalizeOutcomes,
  normalizeRequirements,
  intakeDeadlineFromArray,
  intakeTimelineFromArray,
  extractTracksMeta,
  extractPrerequisites,
  extractRecommendations,
  extractFundingSignals,
  extractSalaryBands,
} from '../../utils/programNormalize'

import RationalePopover from './match/RationalePopover'
import ProbabilityBands from './match/ProbabilityBands'
import StatGroup from './program/StatGroup'
import WhereYouStand from './program/WhereYouStand'
import AboutCard from './program/AboutCard'
import RelatedSidebar from './program/RelatedSidebar'
import InsightsPanel from './program/InsightsPanel'
// (NextStepsCard removed — applications start from the saved list.)
import NetPriceEstimator from './program/NetPriceEstimator'
import NewsGrid from '../../components/NewsGrid'
import ProfileIntelligenceSections from '../../components/profile/ProfileIntelligenceSections'

// Spec 11 §3 — tabs; Insights merges student reviews + employer feedback (§3.6).
type Tab = 'overview' | 'admissions' | 'costs' | 'outcomes' | 'insights' | 'events'
const TAB_IDS: Tab[] = ['overview', 'events', 'admissions', 'costs', 'outcomes', 'insights']

const TABS: { id: Tab; label: string; icon: typeof BookOpen }[] = [
  { id: 'overview', label: 'Overview', icon: BookOpen },
  { id: 'events', label: 'Events & Updates', icon: Megaphone },
  { id: 'admissions', label: 'Admissions', icon: GraduationCap },
  { id: 'costs', label: 'Costs & Aid', icon: DollarSign },
  { id: 'outcomes', label: 'Outcomes', icon: TrendingUp },
  { id: 'insights', label: 'Insights', icon: MessageSquare },
]

// Legacy `?tab=reviews` redirects to `?tab=insights` (§3.6).
function normalizeTab(raw: string | null): Tab {
  if (raw === 'reviews') return 'insights'
  return TAB_IDS.includes(raw as Tab) ? (raw as Tab) : 'overview'
}

export default function ProgramDetailPage() {
  const { programId } = useParams<{ programId: string }>()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const compareStore = useCompareStore()

  // Spec 11 §10 — active tab + Insights filters live in the URL so they
  // persist on reload and are shareable.
  const [searchParams, setSearchParams] = useSearchParams()
  const tab = normalizeTab(searchParams.get('tab'))
  const reviewerType = searchParams.get('reviewer') ?? ''
  const degreeFilter = searchParams.get('degree') ?? ''
  const cohortFilter = searchParams.get('cohort') ?? ''
  const minRating = searchParams.get('dim') ?? ''
  const industry = searchParams.get('industry') ?? ''

  // Spec 06 §3/§5.5 — student (redacted) "why this match" popover.
  const [rationaleOpen, setRationaleOpen] = useState(false)
  const [curTerm, setCurTerm] = useState(0) // active curriculum term tab

  const setTab = (t: Tab) =>
    setSearchParams(prev => {
      const n = new URLSearchParams(prev)
      n.set('tab', t)
      return n
    })
  const setFilter = (key: 'reviewer' | 'degree' | 'cohort' | 'dim' | 'industry', value: string) =>
    setSearchParams(prev => {
      const n = new URLSearchParams(prev)
      if (value) n.set(key, value)
      else n.delete(key)
      return n
    }, { replace: true })
  const clearFilters = () =>
    setSearchParams(prev => {
      const n = new URLSearchParams(prev)
      for (const k of ['reviewer', 'degree', 'cohort', 'dim', 'industry']) n.delete(k)
      return n
    }, { replace: true })

  // Rewrite the legacy ?tab=reviews into ?tab=insights in the address bar.
  useEffect(() => {
    if (searchParams.get('tab') === 'reviews') {
      const n = new URLSearchParams(searchParams)
      n.set('tab', 'insights')
      setSearchParams(n, { replace: true })
    }
  }, [searchParams, setSearchParams])

  // Data
  const { data: program, isLoading, isError, refetch } = useQuery({ queryKey: ['program', programId], queryFn: () => getProgram(programId!) })
  usePageTitle((program as any)?.program_name || 'Program')
  // Track the visit for the global command palette's "Recently viewed".
  useEffect(() => { if (program) pushRecentProgram(program) }, [program])
  const { data: matchResult } = useQuery({ queryKey: ['match', programId], queryFn: () => getMatchDetail(programId!), retry: false })
  const { data: netPrice } = useQuery({ queryKey: ['net-price', programId], queryFn: () => getNetPrice(programId!), enabled: !!programId, retry: false })
  const { data: events } = useQuery({ queryKey: ['events', { program_id: programId }], queryFn: () => listEvents({ program_id: programId, limit: 5 }) })
  // Channel-sourced program Updates (news tagged to this program).
  const { data: programPostsData } = useQuery({
    queryKey: ['program-posts', (program as any)?.institution_id, programId],
    queryFn: () => getPublicPosts((program as any).institution_id, { program_id: programId }),
    enabled: !!(program as any)?.institution_id && !!programId,
  })
  const programPosts = Array.isArray(programPostsData) ? programPostsData : []
  const { data: saved } = useQuery({ queryKey: qk.savedPrograms(), queryFn: listSaved })
  // Student's own profile — powers the "Where you stand" cohort comparison. The
  // profile response embeds academic_records + test_scores, so this is the
  // single read; no new endpoint. Soft-fail so the page renders for anyone.
  const { data: myProfile } = useQuery({ queryKey: ['profile'], queryFn: getProfile, retry: false })
  const { data: reviewsData } = useQuery({ queryKey: ['program-reviews', programId], queryFn: () => getProgramReviews(programId!), retry: false })
  const { data: employerData } = useQuery({ queryKey: ['employer-feedback', programId], queryFn: () => getEmployerFeedback(programId!), retry: false })
  const { data: sameSchoolData } = useQuery({
    queryKey: ['same-school-programs', (program as any)?.institution_id],
    queryFn: () => searchPrograms({ institution_id: (program as any)?.institution_id, page_size: 7 }),
    enabled: !!(program as any)?.institution_id,
    retry: false,
  })
  const { data: similarData } = useQuery({
    queryKey: ['similar-programs', (program as any)?.program_name],
    queryFn: () => semanticSearch((program as any).program_name, 7),
    enabled: !!(program as any)?.program_name,
    retry: false,
  })

  useEffect(() => {
    if (programId) logEngagement(programId, 'viewed_program', 1).catch(() => {})
    const start = Date.now()
    return () => {
      const secs = Math.round((Date.now() - start) / 1000)
      if (programId && secs > 5) logEngagement(programId, 'time_spent', secs).catch(() => {})
    }
  }, [programId])

  const savedList: any[] = Array.isArray(saved) ? saved : []
  const isSaved = savedList.some((s: any) => s.program_id === programId)
  const eventsList: EventItem[] = Array.isArray(events) ? events : []

  // Optimistic save/unsave (Ship D §4): flip the cached shortlist instantly so
  // the button responds; roll back + toast on failure. `wasSaved` is passed as
  // the mutation variable so the flip direction is pinned at click time.
  const saveMut = useMutation({
    mutationFn: async (wasSaved: boolean): Promise<void> => {
      if (wasSaved) await unsaveProgram(programId!)
      else await saveProgram(programId!)
    },
    onMutate: async (wasSaved: boolean) => {
      await queryClient.cancelQueries({ queryKey: qk.savedPrograms() })
      const previous = queryClient.getQueryData(qk.savedPrograms())
      queryClient.setQueryData(qk.savedPrograms(), (old: unknown) => {
        const list: any[] = Array.isArray(old) ? old : []
        return wasSaved
          ? list.filter((s: any) => s.program_id !== programId)
          : [...list, { program_id: programId }]
      })
      return { previous, wasSaved }
    },
    onError: (_err, wasSaved, ctx) => {
      if (ctx) queryClient.setQueryData(qk.savedPrograms(), ctx.previous)
      showToast(`We couldn't ${wasSaved ? 'remove' : 'save'} this program. Please try again.`, 'error')
    },
    onSettled: () => queryClient.invalidateQueries({ queryKey: qk.savedPrograms() }),
  })

  if (isLoading) return <ProgramDetailSkeleton />

  if (isError) {
    return (
      <div className="p-6 max-w-3xl mx-auto">
        <QueryError detail="We couldn't load this program." onRetry={() => refetch()} />
      </div>
    )
  }

  if (!program) {
    return (
      <div className="p-6 max-w-3xl mx-auto">
        <p className="text-sm text-foreground mb-3">Program details are unavailable right now.</p>
        <Button size="sm" variant="secondary" onClick={() => navigate('/s/explore')}>Back to Explore</Button>
      </div>
    )
  }

  const p: any = program
  // Untyped (dual-score `MatchResultDual` ∪ legacy `MatchResult`) — getMatchDetail
  // returns `any` and this page reads both shapes; matches the `p: any` style.
  const match: any = matchResult ?? null
  const hasMatch = !!(match && (match.fitness_score != null || match.match_score != null))
  const rd: any = p.ranking_data || {}
  // Spec 23 bridge: project the institution editor's canonical cost/outcomes
  // blobs onto the legacy keys this page renders (canonical-first, legacy
  // fallback). See utils/programNormalize.ts.
  const cd: any = normalizeCostData(p.cost_data)
  const odn: any = normalizeOutcomes(p.outcomes_data)
  const tracksMeta = extractTracksMeta(p.tracks)
  const prerequisites = extractPrerequisites(p.application_requirements)
  const recommendations = extractRecommendations(p.application_requirements)
  const fundingSignals = extractFundingSignals(p.cost_data)
  const salaryBands = extractSalaryBands(p.outcomes_data)
  const instName = p.institution_name || ''

  // Spec 11 §6 — archived program. No dedicated column exists yet, so key on the
  // signals that would mark a program closed; harmless (all falsy) for live ones.
  const isArchived = p.status === 'archived' || p.is_archived === true ||
    p.accepting_applications === false || p.is_published === false

  /* ── Fallback derivations so the page never shows blanks when data exists
     elsewhere in the payload (intake_rounds, cost_data, ranking_data). ── */

  const effectiveTuition: number | null =
    p.tuition ?? cd.tuition_annual_institution ?? cd.tuition_annual
    ?? rd.tuition_out_of_state ?? rd.tuition_in_state ?? null

  function pickDeadline(ir: any): string | null {
    // Spec 23 — the editor now writes intake_rounds as an array.
    if (Array.isArray(ir)) return intakeDeadlineFromArray(ir)
    if (!ir || typeof ir !== 'object') return null
    const pick = (t: any) =>
      t?.regular_decision?.deadline ?? t?.early_decision_2?.deadline ?? t?.early_decision_1?.deadline ?? null
    for (const [k, v] of Object.entries(ir)) {
      if (k === 'source') continue
      const d = pick(v)
      if (d) return d
    }
    return pick(ir)
  }
  const effectiveDeadline: string | null = p.application_deadline ?? pickDeadline(p.intake_rounds)

  function extractTimeline(ir: any): { term: string; rounds: any[]; enrollment_deadline: string | null } | null {
    // Spec 23 — array shape from the editor takes the dedicated path.
    if (Array.isArray(ir)) return intakeTimelineFromArray(ir)
    if (!ir || typeof ir !== 'object') return null
    const buildFrom = (term: any, termKey: string) => {
      if (!term || typeof term !== 'object') return null
      const rounds: any[] = []
      if (term.early_decision_1) rounds.push({ name: 'Early Decision 1', ...term.early_decision_1 })
      if (term.early_decision_2) rounds.push({ name: 'Early Decision 2', ...term.early_decision_2 })
      if (term.early_action) rounds.push({ name: 'Early Action', ...term.early_action })
      if (term.regular_decision) rounds.push({ name: 'Regular Decision', ...term.regular_decision })
      if (term.rolling) rounds.push({ name: 'Rolling Admission', ...term.rolling })
      if (rounds.length === 0) return null
      return { term: term.term ?? termKey.replace(/_/g, ' '), rounds, enrollment_deadline: term.enrollment_deadline ?? null }
    }
    const direct = buildFrom(ir, 'intake')
    if (direct) return direct
    for (const [k, v] of Object.entries(ir)) {
      if (k === 'source') continue
      const t = buildFrom(v, k)
      if (t) return t
    }
    return null
  }
  const admissionTimeline = extractTimeline(p.intake_rounds)

  const handleCompare = () => {
    if (compareStore.has(p.id)) compareStore.remove(p.id)
    else compareStore.add({ program_id: p.id, program_name: p.program_name, institution_name: instName, degree_type: p.degree_type })
  }

  const sameSchool = (sameSchoolData?.items ?? []).filter((sp: any) => sp.id !== programId).slice(0, 5)
  const similar = (Array.isArray(similarData) ? similarData : []).filter((sp: any) => sp.id !== programId).slice(0, 5)

  // Deep-link back to Discovery with this program's attributes pre-applied (§4).
  const discoveryBackHref = `/s/explore?${new URLSearchParams({
    ...(p.degree_type ? { degree_type: p.degree_type } : {}),
    ...(p.institution_country ? { country: p.institution_country } : {}),
    ...(p.program_name ? { q: p.program_name } : {}),
  }).toString()}`

  const degreeLabel = DEGREE_LABELS[p.degree_type] || p.degree_type || ''
  // Eyebrow = degree label when we have one, else the institution name.
  const heroEyebrow = degreeLabel || instName || null

  // Stat strip — real fields only, NO location. Omit anything absent.
  const heroStats: { value: string; label: string }[] = []
  const heroAcceptance = p.acceptance_rate ?? rd.acceptance_rate
  if (heroAcceptance != null && Number.isFinite(Number(heroAcceptance))) {
    const ar = Number(heroAcceptance)
    heroStats.push({ value: `${(ar * 100).toFixed(ar < 0.1 ? 1 : 0)}%`, label: 'acceptance' })
  }
  if (effectiveTuition != null && Number.isFinite(Number(effectiveTuition)) && Number(effectiveTuition) > 0) {
    heroStats.push({ value: formatCurrency(Number(effectiveTuition)), label: 'tuition / yr' })
  }

  return (
    <div className="p-6 w-full animate-page-in">
      {/* ── Archived banner (§6) ── */}
      {isArchived && (
        <div className="mb-4 flex items-center gap-2 rounded-lg border border-warning/30 bg-warning-soft px-4 py-3">
          <Archive size={16} className="text-warning flex-shrink-0" />
          <p className="text-sm text-foreground">This program is no longer accepting applications.</p>
        </div>
      )}

      {/* ── Back to the last level (falls back to the institution when there's
            no in-app history, e.g. the page was opened directly) ── */}
      <button
        onClick={() => {
          if (window.history.length > 1) navigate(-1)
          else navigate(`/s/institutions/${p.institution_id}`)
        }}
        className="inline-flex items-center gap-1.5 text-[13px] font-medium text-secondary hover:underline mb-3"
      >
        <ArrowLeft size={15} /> Back
      </button>

      {/* ── Breadcrumb (mirrors the school pages) ── */}
      <nav className="flex items-center gap-1.5 text-[13px] text-muted-foreground mb-4 flex-wrap" aria-label="Breadcrumb">
        <button onClick={() => navigate('/s/explore')} className="hover:text-secondary transition-colors">Discover</button>
        <span className="text-muted-foreground" aria-hidden="true">·</span>
        <Link to={`/s/institutions/${p.institution_id}`} className="hover:text-secondary transition-colors truncate max-w-[28ch]">
          {instName || 'School'}
        </Link>
        <span className="text-muted-foreground" aria-hidden="true">·</span>
        <span className="text-foreground font-medium truncate max-w-[40ch]" aria-current="page">{p.program_name}</span>
      </nav>

      <div className="rounded-lg border border-border mb-5 bg-background px-5 sm:px-7 py-6">
          {heroEyebrow && <p className="text-xs uppercase font-semibold text-muted-foreground mb-1.5">{heroEyebrow}</p>}

          <div className="flex flex-wrap items-end justify-between gap-4">
            <div className="min-w-0">
              <h1 className="text-2xl sm:text-3xl md:text-[2.5rem] font-bold text-foreground leading-[1.08] max-w-[24ch]">
                {p.program_name}
              </h1>

              {/* Institution + department line (links to the school; NO geo). */}
              <div className="flex items-center gap-1.5 mt-2 text-[13px] text-muted-foreground flex-wrap">
                <Link to={`/s/institutions/${p.institution_id}`} className="text-secondary hover:underline font-medium">
                  {instName || 'School'}
                </Link>
                {p.department && (
                  <>
                    <ChevronRight size={12} className="text-muted-foreground/50" aria-hidden="true" />
                    <span>{p.department}</span>
                  </>
                )}
              </div>

              {/* Headline stats — real fields only, NO location. */}
              {heroStats.length > 0 && (
                <div className="flex flex-wrap items-center gap-x-2.5 gap-y-1 mt-2.5 text-[13px] text-muted-foreground">
                  {heroStats.map((s, i) => (
                    <Fragment key={s.label}>
                      {i > 0 && <span className="text-border" aria-hidden="true">·</span>}
                      <span><span className="font-semibold text-foreground">{s.value}</span> {s.label}</span>
                    </Fragment>
                  ))}
                </div>
              )}
            </div>

            {hasMatch && (
              <div className="flex flex-col items-start gap-2 flex-shrink-0 rounded-lg border border-border px-3 py-2">
                {match.band_label && (
                  <p className="text-xs text-muted-foreground">
                    Match view: <span className="font-semibold text-foreground">{match.band_label}</span>
                  </p>
                )}
                <button
                  onClick={() => setRationaleOpen(true)}
                  className="inline-flex items-center gap-1 text-[12px] font-medium text-foreground hover:underline"
                >
                  <Sparkles size={12} /> Decision brief
                </button>
              </div>
            )}
          </div>

          {/* Actions — Save + Ask counselor + Compare. Applications are started
              from the saved list, not here; only a link to an existing app shows. */}
          <div className="flex flex-wrap items-center gap-2 mt-5">
            <Button
              size="sm"
              variant={isSaved ? 'secondary' : 'tertiary'}
              onClick={() => saveMut.mutate(isSaved)}
              disabled={isArchived || saveMut.isPending}
              aria-pressed={isSaved}
            >
              {isSaved ? <BookmarkCheck size={14} className="mr-1.5" /> : <Bookmark size={14} className="mr-1.5" />}
              {isSaved ? 'Saved' : 'Save'}
            </Button>
            <Button
              size="sm"
              variant="tertiary"
              onClick={() => navigate(`/s?prefill=${encodeURIComponent(`Is ${p.program_name} at ${instName} a good fit for me? Why or why not?`)}`)}
            >
              <Sparkles size={14} className="mr-1.5" /> Ask counselor
            </Button>
            <Button
              size="sm"
              variant="ghost"
              onClick={handleCompare}
              disabled={isArchived}
              aria-pressed={compareStore.has(p.id)}
            >
              <ArrowRightLeft size={14} className="mr-1.5" />
              {compareStore.has(p.id) ? 'Comparing' : 'Compare'}
            </Button>
          </div>
      </div>

      {/* ── Basic-info strip — the program's defining facts (length / degree /
            format / department). Outcomes live on the Outcomes tab. ── */}
      {(() => {
        const DEG: Record<string, string> = { bachelors: "Bachelor's", masters: "Master's", phd: 'PhD', doctoral: 'Doctorate', associate: 'Associate', certificate: 'Certificate', diploma: 'Diploma', professional: 'Professional' }
        const FMT: Record<string, string> = { in_person: 'In-person', online: 'Online', hybrid: 'Hybrid' }
        const lengthLabel = p.duration_months
          ? (p.duration_months % 12 === 0
              ? `${p.duration_months / 12} year${p.duration_months === 12 ? '' : 's'}`
              : `${p.duration_months} months`)
          : null
        const tiles = [
          lengthLabel && { icon: Clock, label: 'Length', value: lengthLabel },
          p.degree_type && { icon: GraduationCap, label: 'Degree', value: DEG[p.degree_type] || p.degree_type },
          p.delivery_format && { icon: Briefcase, label: 'Format', value: FMT[p.delivery_format] || p.delivery_format },
          p.department && { icon: Building2, label: 'Department', value: p.department },
        ].filter(Boolean) as { icon: typeof Clock; label: string; value: string }[]
        if (tiles.length === 0) return null
        return (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-5">
            {tiles.map(t => (
              <Card pad={false} key={t.label} className="p-4">
                <div className="flex items-center gap-2 mb-2">
                  <t.icon size={13} className="text-secondary" />
                  <span className="text-[10px] uppercase tracking-wide font-semibold text-muted-foreground">{t.label}</span>
                </div>
                <p className="text-xl font-bold text-foreground leading-tight">{t.value}</p>
              </Card>
            ))}
          </div>
        )
      })()}

      {/* ── Your realistic shot — probability bands (Spec 09 §4A). ── */}
      {hasMatch && (
        <Card pad={false} className="mb-5 p-4">
          <ProbabilityBands
            bands={match.probability_bands ?? null}
            reason={match.acceptance_rate == null ? 'no_history' : 'not_match_ready'}
          />
        </Card>
      )}

      {/* ── Tabs (underline in --accent) ── */}
      <div className="border-b border-border mb-5">
        <div className="flex gap-1 overflow-x-auto">
          {TABS.map(t => {
            const isActive = tab === t.id
            let badge: string | null = null
            if (t.id === 'insights' && reviewsData?.total_reviews) badge = String(reviewsData.total_reviews)
            return (
              <button
                key={t.id}
                onClick={() => setTab(t.id)}
                className={`flex items-center gap-1.5 px-4 py-2.5 text-sm font-medium border-b-2 transition-colors whitespace-nowrap ${
                  isActive
                    ? 'border-secondary text-secondary'
                    : 'border-transparent text-foreground hover:text-foreground'
                }`}
              >
                <t.icon size={14} />
                {t.label}
                {badge && (
                  <span className={`px-1.5 py-0.5 text-[10px] rounded-full ${
                    isActive ? 'bg-muted text-secondary' : 'bg-muted text-foreground'
                  }`}>{badge}</span>
                )}
              </button>
            )
          })}
        </div>
      </div>

      {/* ── Two-column body ── */}
      <div className="grid grid-cols-1 lg:grid-cols-[1fr_320px] gap-6">
        {/* Main column */}
        <div className="min-w-0 space-y-4">
          {tab === 'overview' && (
            <>
              <AboutCard
                description={p.description_text || p.institution_description || ''}
                institutionName={instName}
                programName={p.program_name}
                websiteUrl={p.website_url}
              />
              <ProfileIntelligenceSections intelligence={p.profile_intelligence ?? null} />
              {/* Social links + channel-sourced Updates/Events now live in the
                  dedicated "Events & Updates" tab (NewsGrid). */}

              {(tracksMeta.concentrations.length > 0 || tracksMeta.note || tracksMeta.learning_format || tracksMeta.curriculum.length > 0) && (
                <Card pad={false} className="p-5">
                  <div className="flex items-center gap-2 mb-3">
                    <BookOpen size={14} className="text-secondary" />
                    <h3 className="font-semibold text-foreground">Curriculum & Structure</h3>
                  </div>
                  {tracksMeta.note && tracksMeta.curriculum.length === 0 && (
                    <p className="text-sm text-foreground mb-3">{tracksMeta.note}</p>
                  )}
                  {tracksMeta.concentrations.length > 0 && (
                    <div className="mb-3">
                      <p className="text-[10px] font-semibold text-foreground/70 uppercase tracking-wider mb-2">Concentrations</p>
                      <div className="flex flex-wrap gap-2">
                        {tracksMeta.concentrations.map((t, i) => (
                          <Badge key={i} variant="neutral" size="sm">{t}</Badge>
                        ))}
                      </div>
                    </div>
                  )}
                  {tracksMeta.curriculum.length > 0 && (() => {
                    const active = Math.min(curTerm, tracksMeta.curriculum.length - 1)
                    const term = tracksMeta.curriculum[active]
                    return (
                      <div>
                        {/* Term tabs — one consistent format for every program */}
                        <div className="flex flex-wrap gap-1.5 mb-3" role="tablist">
                          {tracksMeta.curriculum.map((t, i) => (
                            <button
                              key={i}
                              role="tab"
                              aria-selected={active === i}
                              onClick={() => setCurTerm(i)}
                              className={`px-3 py-1 rounded-full text-[11px] font-semibold uppercase tracking-wider border transition-colors ${
                                active === i
                                  ? 'bg-secondary text-secondary-foreground border-secondary'
                                  : 'bg-card text-muted-foreground border-border hover:bg-muted hover:text-foreground'
                              }`}
                            >
                              {t.term}
                            </button>
                          ))}
                        </div>
                        <ul className="space-y-1">
                          {(term?.courses ?? []).map((c, j) => (
                            <li key={j} className="flex items-start gap-2 text-sm text-foreground">
                              <span className="mt-[7px] w-1 h-1 rounded-full bg-secondary/50 flex-shrink-0" aria-hidden="true" />
                              {c}
                            </li>
                          ))}
                        </ul>
                      </div>
                    )
                  })()}
                  {tracksMeta.learning_format && (
                    <div className="mt-3">
                      <p className="text-[10px] font-semibold text-foreground/70 uppercase tracking-wider mb-1">Learning format</p>
                      <p className="text-sm text-foreground leading-relaxed">{tracksMeta.learning_format}</p>
                    </div>
                  )}
                </Card>
              )}

              {(() => {
                const cp = p.class_profile && typeof p.class_profile === 'object'
                  ? p.class_profile as Record<string, any> : null
                if (!cp) return null
                const pct = (v: any) => `${Math.round(Number(v) * 100)}%`
                const rows: Array<{ label: string; value: string }> = []
                if (cp.cohort_size) rows.push({ label: 'Cohort size', value: String(cp.cohort_size) })
                if (cp.international_pct != null) rows.push({ label: 'International', value: pct(cp.international_pct) })
                if (cp.countries != null) rows.push({ label: 'Countries', value: String(cp.countries) })
                if (cp.women_pct != null) rows.push({ label: 'Women', value: pct(cp.women_pct) })
                if (cp.stem_pct != null) rows.push({ label: 'STEM background', value: pct(cp.stem_pct) })
                if (cp.median_gpa != null) rows.push({ label: 'Median GPA', value: String(cp.median_gpa) })
                if (cp.median_gre_quant != null) rows.push({ label: 'Median GRE (Quant)', value: String(cp.median_gre_quant) })
                if (cp.median_gmat != null) rows.push({ label: 'Median GMAT', value: String(cp.median_gmat) })
                if (cp.avg_work_experience_months != null) rows.push({ label: 'Avg work experience', value: `${cp.avg_work_experience_months} mo` })
                if (!rows.length) return null
                return (
                  <Card pad={false} className="p-5">
                    <div className="flex items-center gap-2 mb-3">
                      <Users size={14} className="text-secondary" />
                      <h3 className="font-semibold text-foreground">Class Profile</h3>
                    </div>
                    <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                      {rows.map(r => (
                        <div key={r.label} className="px-3 py-2.5 rounded-lg bg-muted/50 border border-border">
                          <p className="text-[10px] uppercase tracking-wider font-semibold text-muted-foreground leading-none">{r.label}</p>
                          <p className="text-[17px] font-bold text-foreground tabular-nums mt-1 leading-tight">{r.value}</p>
                        </div>
                      ))}
                    </div>
                    <WhereYouStand
                      classProfile={cp}
                      academicRecords={myProfile?.academic_records}
                      testScores={myProfile?.test_scores}
                    />
                    {cp.source && (
                      <p className="mt-3 text-[11px] text-muted-foreground/70">
                        Source:{' '}
                        {cp.source_url ? (
                          <a href={String(cp.source_url)} target="_blank" rel="noopener noreferrer" className="text-secondary hover:underline">{String(cp.source)}</a>
                        ) : String(cp.source)}
                      </p>
                    )}
                  </Card>
                )
              })()}

              {(() => {
                const fc = p.faculty_contacts
                const facObj = (fc && !Array.isArray(fc) && typeof fc === 'object')
                  ? fc as Record<string, any> : null
                const lead: Array<Record<string, any>> = facObj && Array.isArray(facObj.lead) ? facObj.lead : []
                if (!facObj || (!lead.length && !facObj.directory_url && !facObj.note)) return null
                return (
                  <Card pad={false} className="p-5">
                    <div className="flex items-center gap-2 mb-3">
                      <Users size={14} className="text-secondary" />
                      <h3 className="font-semibold text-foreground">Faculty</h3>
                    </div>
                    {lead.length > 0 && (
                      <div className="space-y-2 mb-3">
                        {lead.map((f, i) => (
                          <div key={i} className="flex items-center justify-between gap-2 px-3 py-2 rounded-lg bg-muted/50 border border-border">
                            <div className="min-w-0">
                              <p className="text-sm font-medium text-foreground">{String(f.name)}</p>
                              {f.title && <p className="text-[11px] text-muted-foreground">{String(f.title)}</p>}
                            </div>
                            {f.url && (
                              <a href={String(f.url)} target="_blank" rel="noopener noreferrer" className="text-secondary hover:text-secondary/80 flex-shrink-0" aria-label="Faculty profile">
                                <ExternalLink size={13} />
                              </a>
                            )}
                          </div>
                        ))}
                      </div>
                    )}
                    {facObj.note && <p className="text-sm text-foreground/80 mb-3">{String(facObj.note)}</p>}
                    {facObj.directory_url && (
                      <a href={String(facObj.directory_url)} target="_blank" rel="noopener noreferrer" className="inline-flex items-center gap-1.5 text-[13px] font-medium text-secondary hover:underline">
                        <ExternalLink size={13} /> Full faculty directory
                      </a>
                    )}
                  </Card>
                )
              })()}


              {/* Highlights as editorial chips */}
              {Array.isArray(p.highlights) && p.highlights.length > 0 && (
                <Card pad={false} className="p-5">
                  <div className="flex items-center gap-2 mb-3">
                    <Sparkles size={14} className="text-secondary" />
                    <h3 className="font-semibold text-foreground">Program Highlights</h3>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {p.highlights.map((h: string, i: number) => (
                      <span key={i} className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs rounded-lg bg-secondary/10 text-foreground border border-secondary/20">
                        <Sparkles size={11} className="text-secondary" />
                        {h}
                      </span>
                    ))}
                  </div>
                </Card>
              )}

              {/* Faculty contacts */}
              {(() => {
                const fc = p.faculty_contacts
                let rows: Array<{ name?: string; email?: string; role?: string; source_url?: string }> = []
                if (Array.isArray(fc)) rows = fc
                else if (fc && typeof fc === 'object') rows = [fc as any]
                rows = rows.filter(r => r && (r.name || r.email))
                if (!rows.length) return null
                return (
                  <Card pad={false} className="p-5">
                    <div className="flex items-center gap-2 mb-3">
                      <Mail size={14} className="text-secondary" />
                      <h3 className="font-semibold text-foreground">Program Contacts</h3>
                    </div>
                    <div className="space-y-2 text-sm">
                      {rows.map((c, i) => (
                        <div key={i} className="flex justify-between items-start gap-2 border-b border-border pb-2">
                          <div className="flex-1">
                            {c.name && <div className="font-medium text-foreground">{c.name}</div>}
                            {c.role && <div className="text-xs text-foreground">{c.role}</div>}
                          </div>
                          {c.email && (
                            <a href={`mailto:${c.email}`} className="text-xs text-secondary hover:underline">
                              {c.email}
                            </a>
                          )}
                        </div>
                      ))}
                      {rows[0]?.source_url && (
                        <p className="text-[10px] text-foreground/50 mt-2">
                          Source:{' '}
                          <a href={rows[0].source_url} target="_blank" rel="noopener noreferrer" className="hover:underline">
                            {rows[0].source_url}
                          </a>
                        </p>
                      )}
                    </div>
                  </Card>
                )
              })()}
            </>
          )}

          {tab === 'admissions' && (() => {
            const appReqs: Array<{ label: string; required?: boolean; note?: string }> =
              normalizeRequirements(p.application_requirements)
            const legacyReqs = p.requirements && typeof p.requirements === 'object' ? Object.entries(p.requirements) : []
            const requiredItems = appReqs.filter(r => r.required !== false)
            const optionalItems = appReqs.filter(r => r.required === false)
            // Recommendations live inside Application Requirements (no separate card).
            if (recommendations && recommendations.required_count > 0) {
              requiredItems.push({
                label: `${recommendations.required_count} letter${recommendations.required_count === 1 ? '' : 's'} of recommendation`,
                required: true,
                note: recommendations.types.length > 0
                  ? recommendations.types.map(t => t.replace(/_/g, ' ')).join(', ')
                  : undefined,
              })
            }
            // Enriched admissions detail (rounds, fee, how-you're-evaluated).
            const reqObj = (p.application_requirements && !Array.isArray(p.application_requirements)
              ? p.application_requirements : {}) as Record<string, any>
            const deadlineRounds: Array<{ round: string; date: string }> = Array.isArray(reqObj.deadlines)
              ? reqObj.deadlines.filter((d: any) => d && d.round && d.date)
                .map((d: any) => ({ round: String(d.round), date: String(d.date) }))
              : []
            const intl = reqObj.international && typeof reqObj.international === 'object'
              ? reqObj.international as Record<string, any> : null

            return (
              <>
                <StatGroup
                  acceptanceRate={p.acceptance_rate ?? rd.acceptance_rate}
                  satAvg={rd.sat_avg}
                  actMidpoint={rd.act_midpoint}
                  applicationDeadline={effectiveDeadline}
                />

                {/* Application Requirements */}
                <Card pad={false} className="p-5">
                  <div className="flex items-center gap-2 mb-3">
                    <GraduationCap size={14} className="text-secondary" />
                    <h3
                      className="font-semibold text-foreground"
                      title={
                        appReqs.length > 0
                          ? `${requiredItems.length} required${optionalItems.length > 0 ? ` · ${optionalItems.length} optional` : ''}`
                          : undefined
                      }
                    >
                      Application Requirements
                    </h3>
                  </div>

                  {appReqs.length > 0 ? (
                    <div className="space-y-3">
                      {requiredItems.length > 0 && (
                        <div>
                          <p className="text-[10px] font-semibold text-foreground/70 uppercase tracking-wider mb-2">Required</p>
                          <ul className="grid grid-cols-1 md:grid-cols-2 gap-2">
                            {requiredItems.map((r, i) => (
                              <li key={i} className="flex items-start gap-2 px-3 py-2 rounded-lg bg-muted/50 border border-border">
                                <span className="w-5 h-5 rounded-full bg-success-soft text-success flex items-center justify-center flex-shrink-0 mt-0.5">
                                  <svg width="10" height="10" viewBox="0 0 20 20" fill="currentColor"><path fillRule="evenodd" clipRule="evenodd" d="M16.7 5.3a1 1 0 010 1.4l-8 8a1 1 0 01-1.4 0l-4-4a1 1 0 011.4-1.4L8 12.6l7.3-7.3a1 1 0 011.4 0z" /></svg>
                                </span>
                                <div className="min-w-0">
                                  <p className="text-sm font-medium text-foreground leading-tight">{r.label}</p>
                                  {r.note && <p className="text-[11px] text-foreground/70 mt-0.5">{r.note}</p>}
                                </div>
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}
                      {optionalItems.length > 0 && (
                        <div>
                          <p className="text-[10px] font-semibold text-foreground/70 uppercase tracking-wider mb-2">Optional / Flexible</p>
                          <ul className="grid grid-cols-1 md:grid-cols-2 gap-2">
                            {optionalItems.map((r, i) => (
                              <li key={i} className="flex items-start gap-2 px-3 py-2 rounded-lg bg-card border border-border">
                                <span className="w-5 h-5 rounded-full bg-muted text-foreground/60 flex items-center justify-center flex-shrink-0 mt-0.5 text-[10px]">~</span>
                                <div className="min-w-0">
                                  <p className="text-sm font-medium text-foreground leading-tight">{r.label}</p>
                                  {r.note && <p className="text-[11px] text-foreground/70 mt-0.5">{r.note}</p>}
                                </div>
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                  ) : legacyReqs.length > 0 ? (
                    <dl className="grid grid-cols-1 md:grid-cols-2 gap-3 text-sm">
                      {legacyReqs.map(([k, v]) => (
                        <div key={k} className="flex justify-between border-b border-border pb-2">
                          <dt className="text-foreground capitalize">{k.replace(/_/g, ' ')}</dt>
                          <dd className="font-medium text-foreground">{String(v)}</dd>
                        </div>
                      ))}
                    </dl>
                  ) : (
                    <p className="text-sm text-foreground">Application requirements not yet listed. Contact the program for details.</p>
                  )}
                </Card>

                {prerequisites.length > 0 && (
                  <Card pad={false} className="p-5">
                    <div className="flex items-center gap-2 mb-3">
                      <GraduationCap size={14} className="text-secondary" />
                      <h3 className="font-semibold text-foreground">Prerequisites</h3>
                    </div>
                    <ul className="space-y-2">
                      {prerequisites.map((pr, i) => (
                        <li key={i} className="rounded-lg border border-border px-3 py-2 text-sm">
                          <div className="flex items-center justify-between gap-2">
                            <span className="font-medium text-foreground">{pr.name}</span>
                            <Badge variant={pr.required ? 'warning' : 'neutral'} size="sm">
                              {pr.required ? 'Required' : 'Recommended'}
                            </Badge>
                          </div>
                          {pr.allowed_substitutes.length > 0 && (
                            <p className="text-[11px] text-foreground/70 mt-1">
                              Substitutes: {pr.allowed_substitutes.join(', ')}
                            </p>
                          )}
                        </li>
                      ))}
                    </ul>
                  </Card>
                )}

                {/* Application Timeline */}
                {admissionTimeline && (
                  <Card pad={false} className="p-5">
                    <div className="flex items-center gap-2 mb-4">
                      <Clock size={14} className="text-secondary" />
                      <h3 className="font-semibold text-foreground" title={admissionTimeline.term || undefined}>Application Timeline</h3>
                    </div>
                    <div className="space-y-2">
                      {admissionTimeline.rounds.map((r: any, i: number) => {
                        const days = daysUntil(r.deadline) ?? 0
                        const isPast = days < 0
                        const isUrgent = !isPast && days <= 30
                        return (
                          <div
                            key={i}
                            className={`flex items-center gap-3 px-3 py-2.5 rounded-lg border ${
                              isPast
                                ? 'bg-muted/40 border-border opacity-60'
                                : isUrgent
                                  ? 'bg-warning-soft border-warning/30'
                                  : 'bg-card border-border'
                            }`}
                          >
                            <div className="flex-1 min-w-0">
                              <div className="flex items-center gap-2">
                                <p className="text-sm font-semibold text-foreground">{r.name}</p>
                                {r.binding && <Badge variant="warning" size="sm">Binding</Badge>}
                                {isUrgent && <Badge variant="warning" size="sm">{days}d left</Badge>}
                                {isPast && <Badge variant="neutral" size="sm">Closed</Badge>}
                              </div>
                              <p className="text-[11px] text-foreground/70 mt-0.5">
                                Apply by <span className="font-medium text-foreground">{formatDate(r.deadline)}</span>
                                {r.decision_release && (
                                  <> · Decision <span className="font-medium text-foreground">{formatDate(r.decision_release)}</span></>
                                )}
                              </p>
                            </div>
                          </div>
                        )
                      })}
                      {admissionTimeline.enrollment_deadline && (
                        <div className="flex items-center gap-3 px-3 py-2.5 rounded-lg bg-muted border border-secondary/15">
                          <div className="flex-1 min-w-0">
                            <p className="text-sm font-semibold text-secondary">Enrollment Deadline</p>
                            <p className="text-[11px] text-foreground/70 mt-0.5">
                              Commit by <span className="font-medium text-foreground">{formatDate(admissionTimeline.enrollment_deadline)}</span>
                            </p>
                          </div>
                        </div>
                      )}
                    </div>
                  </Card>
                )}

                {/* Application Timeline — rounds + key dates merged into one card. */}
                {!admissionTimeline && (deadlineRounds.length > 0 || effectiveDeadline || p.program_start_date) && (
                  <Card pad={false} className="p-5">
                    <div className="flex items-center gap-2 mb-3">
                      <Clock size={14} className="text-secondary" />
                      <h3 className="font-semibold text-foreground">Application Timeline</h3>
                    </div>
                    <ul className="space-y-2 text-sm">
                      {deadlineRounds.map((d, i) => (
                        <li key={`r${i}`} className="flex justify-between border-b border-border pb-2 last:border-0 last:pb-0">
                          <span className="text-foreground">{d.round}</span>
                          <span className="font-medium text-foreground">{d.date}</span>
                        </li>
                      ))}
                      {effectiveDeadline && (
                        <li className="flex justify-between border-b border-border pb-2 last:border-0 last:pb-0">
                          <span className="text-foreground">Application deadline</span>
                          <span className="font-medium text-foreground">{formatDate(effectiveDeadline)}</span>
                        </li>
                      )}
                      {p.program_start_date && (
                        <li className="flex justify-between border-b border-border pb-2 last:border-0 last:pb-0">
                          <span className="text-foreground">Program starts</span>
                          <span className="font-medium text-foreground">{formatDate(p.program_start_date)}</span>
                        </li>
                      )}
                    </ul>
                  </Card>
                )}

                {/* International students — English proficiency + visa */}
                {intl && (() => {
                  const eng = intl.english && typeof intl.english === 'object' ? intl.english as Record<string, any> : null
                  const visa = intl.visa && typeof intl.visa === 'object' ? intl.visa as Record<string, any> : null
                  const engTests: string[] = eng && Array.isArray(eng.tests) ? eng.tests.map(String) : []
                  const intlSources: Array<Record<string, any>> = Array.isArray(intl.sources) ? intl.sources : []
                  if (!eng && !visa && !intl.opt) return null
                  return (
                    <Card pad={false} className="p-5">
                      <div className="flex items-center gap-2 mb-3">
                        <Building2 size={14} className="text-secondary" />
                        <h3 className="font-semibold text-foreground">International Students</h3>
                      </div>
                      <div className="space-y-3">
                        {eng && (
                          <div className="px-3 py-2.5 rounded-lg bg-muted/50 border border-border">
                            <div className="flex items-center gap-2 flex-wrap mb-1">
                              <p className="text-sm font-medium text-foreground">English proficiency</p>
                              {eng.required != null && (
                                <Badge variant={eng.required ? 'warning' : 'neutral'} size="sm">
                                  {eng.required ? 'Required' : 'Not required'}
                                </Badge>
                              )}
                              {engTests.map(t => <Badge key={t} variant="neutral" size="sm">{t}</Badge>)}
                            </div>
                            {eng.note && <p className="text-[12px] text-foreground/80">{String(eng.note)}</p>}
                          </div>
                        )}
                        {visa && (
                          <div className="px-3 py-2.5 rounded-lg bg-muted/50 border border-border">
                            <p className="text-sm font-medium text-foreground mb-1">Visa{visa.type ? ` — ${String(visa.type)}` : ''}</p>
                            {visa.note && <p className="text-[12px] text-foreground/80">{String(visa.note)}</p>}
                          </div>
                        )}
                        {intl.opt && (
                          <p className="text-[12px] text-foreground/80 flex items-start gap-2">
                            <Sparkles size={13} className="text-secondary flex-shrink-0 mt-0.5" />
                            {String(intl.opt)}
                          </p>
                        )}
                      </div>
                      {intlSources.length > 0 && (
                        <div className="mt-3 pt-2 border-t border-border flex flex-wrap gap-x-3 gap-y-1">
                          {intlSources.map((s, i) => (
                            <a key={i} href={String(s.url)} target="_blank" rel="noopener noreferrer" className="inline-flex items-center gap-1 text-[12px] text-secondary hover:underline">
                              <ExternalLink size={11} /> {String(s.label)}
                            </a>
                          ))}
                        </div>
                      )}
                    </Card>
                  )
                })()}

                {/* Admissions profile (Key Dates merged into Application Timeline above) */}
                <div className="grid grid-cols-1 gap-4">
                  {(p.acceptance_rate ?? rd.acceptance_rate) != null && (
                    <Card pad={false} className="p-5">
                      <div className="flex items-center gap-2 mb-3">
                        <Sparkles size={14} className="text-secondary" />
                        <h3 className="font-semibold text-foreground">Admissions Profile</h3>
                      </div>
                      <ul className="space-y-2 text-sm">
                        {(() => {
                          const ar = p.acceptance_rate ?? rd.acceptance_rate
                          const pct = ar * 100
                          const items: string[] = []
                          if (pct < 10) items.push(`Highly selective — fewer than 1 in 10 applicants admitted`)
                          else if (pct < 25) items.push(`Very selective — about 1 in ${Math.round(100 / pct)} applicants admitted`)
                          else if (pct < 50) items.push(`Selective — ${Math.round(pct)}% of applicants admitted`)
                          else items.push(`Accessible — ${Math.round(pct)}% of applicants admitted`)
                          if (rd.sat_avg) items.push(`Middle 50% SAT: ~${rd.sat_avg - 40}–${rd.sat_avg + 40}`)
                          if (rd.act_25_75) items.push(`Middle 50% ACT: ${rd.act_25_75[0]}–${rd.act_25_75[1]}`)
                          return items.map((t, i) => (
                            <li key={i} className="flex items-start gap-2 text-foreground">
                              <span className="w-1 h-1 rounded-full bg-secondary mt-2 flex-shrink-0" />
                              {t}
                            </li>
                          ))
                        })()}
                      </ul>
                    </Card>
                  )}
                </div>
                {reqObj.source && (
                  <p className="text-[11px] text-muted-foreground/70">
                    Source:{' '}
                    {reqObj.source_url ? (
                      <a href={String(reqObj.source_url)} target="_blank" rel="noopener noreferrer" className="text-secondary hover:underline">{String(reqObj.source)}</a>
                    ) : String(reqObj.source)}
                  </p>
                )}
              </>
            )
          })()}

          {tab === 'costs' && (() => {
            const annual = effectiveTuition || 0
            const fees = cd.fees || {}
            const feeTotal = Object.values(fees).reduce((s: number, v: any) => s + (Number(v) || 0), 0)
            const intlPremium = cd.international_premium || 0
            const netPriceByIncome: Record<string, number> = cd.net_price_by_income || {}
            return (
              <>
                {/* Spec 11 §3.3a — personalized net price (highlighted block) */}
                <NetPriceEstimator estimate={netPrice} />

                {/* Tuition/yr stat omitted — the Tuition & Fees breakdown below covers it. */}
                <StatGroup
                  totalCost={cd.total_cost_attendance ?? rd.total_cost_attendance}
                  netPrice={cd.average_net_price ?? rd.avg_net_price}
                  medianDebt={cd.median_debt ?? rd.median_debt}
                  pellGrantRate={cd.pell_grant_rate ?? rd.pell_grant_rate}
                />

                <Card pad={false} className="p-5">
                  <div className="flex items-center gap-2 mb-3">
                    <DollarSign size={14} className="text-secondary" />
                    <h3 className="font-semibold text-foreground">Tuition & Fees</h3>
                  </div>
                  <dl className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <dt className="text-foreground">Annual Tuition</dt>
                      <dd className="font-medium text-foreground">{formatCurrency(annual)}</dd>
                    </div>
                    {Object.entries(fees).map(([k, v]) => (
                      <div key={k} className="flex justify-between">
                        <dt className="text-foreground capitalize">{k.replace(/_/g, ' ')}</dt>
                        <dd className="text-foreground">{formatCurrency(Number(v))}</dd>
                      </div>
                    ))}
                    {intlPremium > 0 && (
                      <div className="flex justify-between">
                        <dt className="text-foreground">International Premium</dt>
                        <dd className="text-foreground">{formatCurrency(intlPremium)}</dd>
                      </div>
                    )}
                    {feeTotal > 0 && (
                      <div className="flex justify-between border-t border-border pt-2 font-medium">
                        <dt className="text-foreground">Annual Subtotal</dt>
                        <dd className="text-foreground">{formatCurrency(annual + feeTotal)}</dd>
                      </div>
                    )}
                  </dl>

                  {/* What the cost is made up of (program-published breakdown) */}
                  {Array.isArray(cd.breakdown) && cd.breakdown.length > 0 && (
                    <div className="mt-4 pt-3 border-t border-border">
                      <p className="text-[10px] font-semibold text-foreground/70 uppercase tracking-wider mb-2">What it&rsquo;s made up of</p>
                      <dl className="space-y-1.5 text-sm">
                        {cd.breakdown.map((it: any, i: number) => (
                          <div key={i} className="flex justify-between gap-3">
                            <dt className="text-foreground" title={it.note ? String(it.note) : undefined}>
                              {String(it.label)}
                            </dt>
                            <dd className={`font-medium tabular-nums whitespace-nowrap ${Number(it.amount) < 0 ? 'text-success' : 'text-foreground'}`}>
                              {Number(it.amount) < 0 ? '−' : ''}{formatCurrency(Math.abs(Number(it.amount)))}
                            </dd>
                          </div>
                        ))}
                        {cd.total_cost_of_attendance != null && (
                          <div className="flex justify-between border-t border-border pt-2 font-semibold">
                            <dt className="text-foreground">Estimated total / year</dt>
                            <dd className="text-foreground tabular-nums whitespace-nowrap">≈ {formatCurrency(Number(cd.total_cost_of_attendance))}</dd>
                          </div>
                        )}
                      </dl>
                    </div>
                  )}
                </Card>

                {fundingSignals && (
                  <Card pad={false} className="p-5">
                    <div className="flex items-center gap-2 mb-3">
                      <DollarSign size={14} className="text-secondary" />
                      <h3 className="font-semibold text-foreground">Funding & Aid Signals</h3>
                    </div>
                    <ul className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-sm">
                      {fundingSignals.ta_funded && (
                        <li className="flex items-center gap-2 text-foreground">
                          <span className="w-1.5 h-1.5 rounded-full bg-secondary" /> TA funding available
                        </li>
                      )}
                      {fundingSignals.ra_funded && (
                        <li className="flex items-center gap-2 text-foreground">
                          <span className="w-1.5 h-1.5 rounded-full bg-secondary" /> RA funding available
                        </li>
                      )}
                      {fundingSignals.merit_scholarship_available && (
                        <li className="flex items-center gap-2 text-foreground">
                          <span className="w-1.5 h-1.5 rounded-full bg-secondary" /> Merit scholarships
                        </li>
                      )}
                      {fundingSignals.need_based_available && (
                        <li className="flex items-center gap-2 text-foreground">
                          <span className="w-1.5 h-1.5 rounded-full bg-secondary" /> Need-based aid
                        </li>
                      )}
                    </ul>
                  </Card>
                )}

                {/* Net Price by Income — what families actually pay after aid */}
                {Object.keys(netPriceByIncome).length > 0 && (() => {
                  const canonical: { key: string; label: string; range: string }[] = [
                    { key: '0-30000', label: 'Low', range: '$0 – $30K' },
                    { key: '30001-48000', label: 'Lower-middle', range: '$30K – $48K' },
                    { key: '48001-75000', label: 'Middle', range: '$48K – $75K' },
                    { key: '75001-110000', label: 'Upper-middle', range: '$75K – $110K' },
                    { key: '110001-plus', label: 'High', range: '$110K+' },
                  ]
                  const rows = canonical.filter(b => netPriceByIncome[b.key] != null)
                  if (rows.length === 0) return null
                  const maxPrice = Math.max(...rows.map(r => netPriceByIncome[r.key]))
                  return (
                    <Card pad={false} className="p-5">
                      <div className="flex items-center gap-2 mb-2">
                        <DollarSign size={14} className="text-secondary" />
                        <h3 className="font-semibold text-foreground">Net Price by Household Income</h3>
                      </div>
                      <p className="text-xs text-foreground mb-4">
                        Average price families actually pay after grants & scholarships, by household income band.
                      </p>
                      <div className="space-y-2">
                        {rows.map(r => {
                          const price = netPriceByIncome[r.key]
                          const widthPct = Math.round((price / maxPrice) * 100)
                          return (
                            <div key={r.key} className="grid grid-cols-[90px_1fr_85px] gap-3 items-center">
                              <div>
                                <p className="text-[11px] font-semibold text-foreground" title={r.range}>{r.label}</p>
                              </div>
                              <div className="relative h-2 rounded-pill bg-muted overflow-hidden">
                                <div className="h-full rounded-pill bg-secondary" style={{ width: `${widthPct}%` }} />
                              </div>
                              <p className="text-xs font-bold text-foreground text-right tabular-nums">
                                {formatCurrency(price)}
                              </p>
                            </div>
                          )
                        })}
                      </div>
                      {cd.source && (
                        <p className="text-[10px] text-foreground/50 mt-3 italic">
                          Source:{' '}
                          {cd.source_url ? (
                            <a href={cd.source_url} target="_blank" rel="noopener noreferrer" className="text-secondary not-italic hover:underline">{cd.source}</a>
                          ) : cd.source}
                          {cd.source_year ? ` · ${cd.source_year}` : ''}
                        </p>
                      )}
                      {rd.price_calculator_url && (
                        <a
                          href={rd.price_calculator_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="mt-3 inline-flex items-center gap-1.5 text-[11px] font-medium text-secondary hover:text-secondary"
                        >
                          Estimate your cost with {instName}'s calculator ↗
                        </a>
                      )}
                    </Card>
                  )
                })()}

                {/* Debt percentiles */}
                {rd.debt_percentiles && typeof rd.debt_percentiles === 'object' && (() => {
                  const dp: any = rd.debt_percentiles
                  const order = ['10th', '25th', '75th', '90th']
                  const rows = order.filter(k => dp[k] != null).map(k => ({ pct: k, value: Number(dp[k]) }))
                  if (rows.length === 0) return null
                  const max = Math.max(...rows.map(r => r.value))
                  return (
                    <Card pad={false} className="p-5">
                      <div className="flex items-center gap-2 mb-2">
                        <DollarSign size={14} className="text-secondary" />
                        <h3 className="font-semibold text-foreground">Graduate Debt Distribution</h3>
                      </div>
                      <p className="text-xs text-foreground mb-3">
                        How much graduates actually borrow. Most fall between the 25th and 75th percentiles.
                      </p>
                      <div className="space-y-2">
                        {rows.map(r => {
                          const w = Math.round((r.value / max) * 100)
                          const isMiddle = r.pct === '25th' || r.pct === '75th'
                          return (
                            <div key={r.pct} className="grid grid-cols-[70px_1fr_85px] gap-3 items-center">
                              <p className={`text-[11px] font-semibold ${isMiddle ? 'text-foreground' : 'text-foreground'}`}>
                                {r.pct} %ile
                              </p>
                              <div className="relative h-2 rounded-pill bg-muted overflow-hidden">
                                <div
                                  className={`h-full rounded-pill ${isMiddle ? 'bg-secondary' : 'bg-secondary/30'}`}
                                  style={{ width: `${w}%` }}
                                />
                              </div>
                              <p className={`text-xs font-bold tabular-nums text-right ${isMiddle ? 'text-foreground' : 'text-foreground'}`}>
                                {formatCurrency(r.value)}
                              </p>
                            </div>
                          )
                        })}
                      </div>
                      {rd.median_debt_monthly != null && (
                        <p className="text-[11px] text-foreground mt-3">
                          Median monthly payment after graduation: <span className="font-semibold text-foreground">${Math.round(rd.median_debt_monthly)}</span>
                        </p>
                      )}
                    </Card>
                  )
                })()}

              </>
            )
          })()}

          {tab === 'outcomes' && (() => {
            const od = odn
            const salary = od.median_salary ? Number(od.median_salary) : (rd.earnings_10yr_median || null)
            const salaryLow = od.salary_25th ? Number(od.salary_25th) : (salary ? Math.round(salary * 0.75) : null)
            const salaryHigh = od.salary_75th ? Number(od.salary_75th) : (salary ? Math.round(salary * 1.3) : null)
            const meanSalary = od.mean_salary ? Number(od.mean_salary) : null
            const signingBonus = od.median_signing_bonus ? Number(od.median_signing_bonus) : null
            const empRate = od.employment_rate ? Number(od.employment_rate) : null
            const empTimeframe = od.employment_timeframe || '6 months after graduation'
            const internRate = od.internship_conversion_rate ? Number(od.internship_conversion_rate) : null
            const classSize = od.class_size ? Number(od.class_size) : null
            const knowledgeRate = od.knowledge_rate != null ? Number(od.knowledge_rate) : null
            const topEmployers: string[] = od.top_employers || []
            const topIndustries: string[] = od.top_industries || []
            const conditions: string[] = Array.isArray(od.conditions) ? od.conditions : []
            const scopeNote = od.scope === 'institution'
              ? (od.scope_note || 'Institution-wide figures across all graduates — not specific to this program.')
              : null
            const hasData = !!(salary || empRate || topEmployers.length > 0 || topIndustries.length > 0)
            const fmtPct = (f: number) => {
              const v = f <= 1 ? f * 100 : f
              return Number.isInteger(v) ? `${v}%` : `${v.toFixed(1)}%`
            }
            // Shared "reference + details on conditions" footnote for each card.
            const referenceBlock = (scopeNote || conditions.length > 0 || od.source) ? (
              <div className="mt-4 pt-3 border-t border-border space-y-1.5">
                {scopeNote && <p className="text-[11px] italic text-muted-foreground">{scopeNote}</p>}
                {conditions.length > 0 && (
                  <ul className="space-y-1">
                    {conditions.map((c: string, i: number) => (
                      <li key={i} className="flex gap-1.5 text-[11px] leading-relaxed text-muted-foreground">
                        <span aria-hidden="true" className="text-foreground/30">·</span>
                        <span>{c}</span>
                      </li>
                    ))}
                  </ul>
                )}
                {od.source && (
                  <p className="text-[11px] text-muted-foreground">
                    Source:{' '}
                    {od.source_url
                      ? <a href={od.source_url} target="_blank" rel="noopener noreferrer" className="text-secondary hover:underline">{od.source}</a>
                      : od.source}.
                  </p>
                )}
              </div>
            ) : null

            if (!hasData) {
              return (
                <Card pad={false} className="p-6 text-center">
                  <TrendingUp size={32} className="text-foreground/30 mx-auto mb-3" />
                  <p className="text-sm text-foreground">Outcomes data is not yet available for this program.</p>
                  <p className="text-xs text-foreground/60 mt-1">Check back later or contact the program directly.</p>
                </Card>
              )
            }

            return (
              <>
                {/* Employment & Placement — rate, class size, industries/employers + conditions */}
                {(empRate != null || internRate != null || topIndustries.length > 0 || topEmployers.length > 0) && (
                  <Card pad={false} className="p-5">
                    <div className="flex items-center gap-2 mb-4">
                      <Briefcase size={14} className="text-secondary" />
                      <h3 className="font-semibold text-foreground">Employment &amp; Placement</h3>
                    </div>
                    <div className="flex flex-wrap gap-x-10 gap-y-4">
                      {empRate != null && (
                        <div>
                          <p className="text-3xl font-bold text-foreground leading-none">{fmtPct(empRate)}</p>
                          <p className="text-xs text-muted-foreground mt-1 max-w-[22ch]">{empTimeframe}</p>
                        </div>
                      )}
                      {classSize != null && (
                        <div>
                          <p className="text-3xl font-bold text-foreground leading-none">{classSize}</p>
                          <p className="text-xs text-muted-foreground mt-1">graduates{knowledgeRate != null ? ` · ${fmtPct(knowledgeRate)} reporting` : ''}</p>
                        </div>
                      )}
                      {internRate != null && (
                        <div>
                          <p className="text-3xl font-bold text-foreground leading-none">{fmtPct(internRate)}</p>
                          <p className="text-xs text-muted-foreground mt-1">interns → full-time offers</p>
                        </div>
                      )}
                    </div>
                    {topIndustries.length > 0 && (
                      <div className="mt-4">
                        <p className="text-[10px] font-semibold text-foreground/70 uppercase tracking-wider mb-2">Top industries</p>
                        <div className="flex flex-wrap gap-2">
                          {topIndustries.map((ind: string) => <Badge key={ind} variant="info" size="sm">{ind}</Badge>)}
                        </div>
                      </div>
                    )}
                    {topEmployers.length > 0 && (
                      <div className="mt-4">
                        <p className="text-[10px] font-semibold text-foreground/70 uppercase tracking-wider mb-2">Top employers</p>
                        <div className="flex flex-wrap gap-2">
                          {topEmployers.map((e: string) => <Badge key={e} variant="neutral" size="sm">{e}</Badge>)}
                        </div>
                      </div>
                    )}
                    {referenceBlock}
                  </Card>
                )}

                {/* Salary Distribution — median + percentiles + bonus + conditions */}
                {salary && (
                  <Card pad={false} className="p-5">
                    <div className="flex items-center gap-2 mb-4">
                      <DollarSign size={14} className="text-secondary" />
                      <h3 className="font-semibold text-foreground">Salary Distribution</h3>
                    </div>
                    {salaryBands.length > 0 ? (
                      <div className="space-y-2">
                        {salaryBands.map(b => (
                          <div key={b.band_label} className="grid grid-cols-[1fr_48px_40px] gap-3 items-center">
                            <p className="text-sm text-foreground">{b.band_label}</p>
                            <div className="relative h-2 rounded-pill bg-muted overflow-hidden">
                              <div className="h-full rounded-pill bg-secondary" style={{ width: `${Math.min(100, b.percent)}%` }} />
                            </div>
                            <p className="text-xs font-semibold text-foreground text-right tabular-nums">{b.percent}%</p>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <>
                        <div className="flex items-end justify-between mb-2">
                          <div className="text-center flex-1">
                            <p className="text-xs text-foreground/60">25th %ile</p>
                            <p className="text-sm font-medium text-foreground">{salaryLow ? formatCurrency(salaryLow) : '—'}</p>
                          </div>
                          <div className="text-center flex-1">
                            <p className="text-xs text-foreground/60">Median base</p>
                            <p className="text-2xl font-bold text-foreground">{formatCurrency(salary)}</p>
                          </div>
                          <div className="text-center flex-1">
                            <p className="text-xs text-foreground/60">75th %ile</p>
                            <p className="text-sm font-medium text-foreground">{salaryHigh ? formatCurrency(salaryHigh) : '—'}</p>
                          </div>
                        </div>
                        <div className="relative h-2 bg-muted rounded-pill mt-3">
                          <div className="absolute h-full bg-secondary/30 rounded-pill" style={{ left: '15%', width: '70%' }} />
                          <div className="absolute h-full bg-secondary rounded-pill" style={{ left: '40%', width: '20%' }} />
                        </div>
                      </>
                    )}
                    {(meanSalary || signingBonus) && (
                      <div className="flex flex-wrap gap-x-8 gap-y-2 mt-4">
                        {meanSalary != null && (
                          <div>
                            <p className="text-[11px] text-muted-foreground">Mean base</p>
                            <p className="text-sm font-semibold text-foreground">{formatCurrency(meanSalary)}</p>
                          </div>
                        )}
                        {signingBonus != null && (
                          <div>
                            <p className="text-[11px] text-muted-foreground">Median signing bonus</p>
                            <p className="text-sm font-semibold text-foreground">{formatCurrency(signingBonus)}</p>
                          </div>
                        )}
                      </div>
                    )}
                    {referenceBlock}
                  </Card>
                )}

                {/* Employer feedback now lives in the Insights tab (§3.6). */}
                {(employerData?.total_feedback ?? 0) > 0 && (
                  <button
                    onClick={() => setTab('insights')}
                    className="w-full text-left rounded-lg border border-border hover:border-secondary hover:bg-muted transition-colors p-4 flex items-center justify-between gap-3"
                  >
                    <div className="flex items-center gap-2">
                      <Briefcase size={14} className="text-secondary" />
                      <span className="text-sm text-foreground">
                        See what <span className="font-semibold">{employerData?.total_feedback}</span> employers say about graduates
                      </span>
                    </div>
                    <span className="text-xs font-semibold text-secondary">Insights →</span>
                  </button>
                )}
              </>
            )
          })()}

          {tab === 'insights' && (
            <div className="space-y-4">
              {(() => {
                const er = p.external_reviews && typeof p.external_reviews === 'object'
                  ? p.external_reviews as Record<string, any> : null
                const themes: Array<Record<string, any>> = er && Array.isArray(er.themes) ? er.themes : []
                const sources: Array<Record<string, any>> = er && Array.isArray(er.sources) ? er.sources : []
                if (!er || (!themes.length && !er.summary)) return null
                const tone = (s: string) => s === 'positive' ? 'text-success' : s === 'caution' ? 'text-warning' : 'text-foreground'
                const dot = (s: string) => s === 'positive' ? 'bg-success' : s === 'caution' ? 'bg-warning' : 'bg-secondary'
                return (
                  <Card pad={false} className="p-5">
                    <div className="flex items-center gap-2 mb-2">
                      <Star size={14} className="text-secondary" />
                      <h3 className="font-semibold text-foreground">What students say</h3>
                    </div>
                    {er.summary && <p className="text-sm text-foreground leading-relaxed mb-3">{String(er.summary)}</p>}
                    {themes.length > 0 && (
                      <ul className="space-y-2 mb-3">
                        {themes.map((t, i) => (
                          <li key={i} className="flex items-start gap-2">
                            <span className={`mt-1.5 w-1.5 h-1.5 rounded-full flex-shrink-0 ${dot(String(t.sentiment))}`} />
                            <div className="min-w-0 text-sm">
                              <span className={`font-medium ${tone(String(t.sentiment))}`}>{String(t.label)}</span>
                              {t.detail && <span className="text-foreground/80"> — {String(t.detail)}</span>}
                            </div>
                          </li>
                        ))}
                      </ul>
                    )}
                    {sources.length > 0 && (
                      <div className="pt-2 border-t border-border">
                        <p className="text-[10px] font-semibold text-foreground/60 uppercase tracking-wider mb-1.5">Sources</p>
                        <div className="flex flex-wrap gap-x-3 gap-y-1">
                          {sources.map((s, i) => (
                            <a key={i} href={String(s.url)} target="_blank" rel="noopener noreferrer" className="inline-flex items-center gap-1 text-[12px] text-secondary hover:underline">
                              <ExternalLink size={11} /> {String(s.label)}
                            </a>
                          ))}
                        </div>
                        {er.disclaimer && <p className="text-[10.5px] text-muted-foreground/70 mt-2">{String(er.disclaimer)}</p>}
                      </div>
                    )}
                  </Card>
                )
              })()}
            <InsightsPanel
              programName={p.program_name}
              reviews={reviewsData ?? null}
              employer={employerData ?? null}
              reviewerType={reviewerType}
              degree={degreeFilter}
              cohort={cohortFilter}
              minRating={minRating}
              industry={industry}
              onFilter={setFilter}
              onClear={clearFilters}
              onWriteReview={() => navigate(`/s?prefill=${encodeURIComponent(`I'd like to write a review for ${p.program_name} at ${instName}. Help me structure it.`)}`)}
              similarPrograms={similar}
              onNavigateProgram={(id) => navigate(`/s/programs/${id}`)}
            />
            </div>
          )}

          {tab === 'events' && (
            <div className="space-y-5">
              {(p as any).content_sources?.social && (
                <div>
                  <h3 className="text-[12px] font-semibold text-muted-foreground uppercase tracking-wide mb-2">Follow &amp; connect</h3>
                  <SocialLinks social={(p as any).content_sources.social} />
                </div>
              )}
              <NewsGrid
                posts={programPosts}
                events={eventsList}
                emptyText={`${p.program_name} has no events or updates yet.`}
              />
            </div>
          )}
        </div>

        {/* Sidebar */}
        <div className="lg:sticky lg:top-4 lg:self-start">
          <RelatedSidebar
            sameSchoolPrograms={sameSchool}
            similarPrograms={similar}
            discoveryBackHref={discoveryBackHref}
          />
        </div>
      </div>

      {/* ── Data sources (attribute public + proprietary data, per product decision) ── */}
      <footer className="mt-8 pt-4 border-t border-border">
        <p className="text-[11px] leading-relaxed text-muted-foreground">
          <span className="font-semibold text-foreground/70">Data sources:</span>{' '}
          U.S. Department of Education College Scorecard (admissions, cost &amp; earnings);
          institution-published admissions requirements, deadlines &amp; cost of attendance
          {(odn.outcomes_source || (reviewsData?.total_reviews ?? 0) > 0 || employerData) ?
            '; and — where shown — career-services outcomes and aggregated third-party review data' : ''}.
          {' '}Figures reflect the latest available data; verify deadlines and costs on the official program page.
        </p>
      </footer>

      {/* ── Redacted "why this match" popover (Spec 06 §3/§5.5) ── */}
      {hasMatch && rationaleOpen && programId && (
        <RationalePopover
          programId={programId}
          fitnessBreakdown={(match.fitness_breakdown as Record<string, unknown> | null) ?? null}
          confidenceBreakdown={(match.confidence_breakdown as Record<string, unknown> | null) ?? null}
          cachedRationale={match.rationale_text ?? null}
          onClose={() => setRationaleOpen(false)}
        />
      )}
    </div>
  )
}

/* ── Loading skeleton — header + tab placeholders (§6) ── */
function ProgramDetailSkeleton() {
  return (
    <div className="p-6 w-full space-y-5">
      <Skeleton className="h-40 rounded-lg" />
      <Skeleton className="h-20 rounded-lg" />
      <Skeleton className="h-24 rounded-lg" />
      <div className="flex gap-2">
        {Array.from({ length: 5 }).map((_, i) => <Skeleton key={i} className="h-9 w-28 rounded-md" />)}
      </div>
      <div className="grid grid-cols-1 lg:grid-cols-[1fr_320px] gap-6">
        <div className="space-y-4">
          {Array.from({ length: 3 }).map((_, i) => <Skeleton key={i} className="h-32 rounded-lg" />)}
        </div>
        <Skeleton className="h-64 rounded-lg" />
      </div>
    </div>
  )
}
