import { Fragment, useEffect, useState } from 'react'
import QueryError from '../../components/ui/QueryError'
import { useParams, useNavigate, useSearchParams, Link } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  getProgram, getProgramReviews, getEmployerFeedback, getNetPrice,
  searchPrograms, semanticSearch,
} from '../../api/programs'
import { getPublicInstitution } from '../../api/institutions'
import { pushRecentProgram } from '../../lib/recentPrograms'
import { getMatchDetail, logEngagement } from '../../api/matching'
import { listEvents, rsvpEvent, getMyRsvps } from '../../api/events'
import { listMyApplications, createApplication } from '../../api/applications'
import { saveProgram, unsaveProgram, listSaved } from '../../api/saved-lists'
import { useCompareStore } from '../../stores/compare-store'
import { useCounselorStore } from '../../stores/counselor-store'
import Card from '../../components/ui/Card'
import Badge from '../../components/ui/Badge'
import Button from '../../components/ui/Button'
import Skeleton from '../../components/ui/Skeleton'
import { showToast } from '../../stores/toast-store'
import { formatCurrency, formatDate } from '../../utils/format'
import { differenceInDays } from 'date-fns'
import {
  BookOpen, GraduationCap, DollarSign, TrendingUp, MessageSquare,
  Briefcase, Building2, Users, Clock, Sparkles, Mail, Archive,
  Bookmark, BookmarkCheck, FileText, Send, ArrowRightLeft, ChevronRight, ArrowLeft,
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
  extractTestPolicy,
  extractRecommendations,
  extractFundingSignals,
  extractSalaryBands,
} from '../../utils/programNormalize'

// Redesigned components
import DualRing from './match/DualRing'
import RationalePopover from './match/RationalePopover'
import ProbabilityBands from './match/ProbabilityBands'
import BandBadge from '../../components/ui/BandBadge'
import KeyMetrics from './program/KeyMetrics'
import StatGroup from './program/StatGroup'
import AboutCard from './program/AboutCard'
import NextStepsCard from './program/NextStepsCard'
import RelatedSidebar from './program/RelatedSidebar'
import InsightsPanel from './program/InsightsPanel'
import NetPriceEstimator from './program/NetPriceEstimator'

// Spec 11 §3 — five tabs; Insights merges student reviews + employer feedback (§3.6).
type Tab = 'overview' | 'admissions' | 'costs' | 'outcomes' | 'insights'
const TAB_IDS: Tab[] = ['overview', 'admissions', 'costs', 'outcomes', 'insights']

const TABS: { id: Tab; label: string; icon: typeof BookOpen }[] = [
  { id: 'overview', label: 'Overview', icon: BookOpen },
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

// Match scores arrive as Decimal/number in either 0..1 or 0..100; the rings
// want 0..1. Coerce defensively so the UI is robust to either convention.
function toUnit(v: number | string | null | undefined): number {
  const n = typeof v === 'string' ? parseFloat(v) : (v ?? 0)
  if (!Number.isFinite(n)) return 0
  const unit = n > 1 ? n / 100 : n
  return Math.max(0, Math.min(1, unit))
}

export default function ProgramDetailPage() {
  const { programId } = useParams<{ programId: string }>()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const compareStore = useCompareStore()
  const askCounselor = useCounselorStore(s => s.askQuestion)

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
  // Track the visit for the global command palette's "Recently viewed".
  useEffect(() => { if (program) pushRecentProgram(program) }, [program])
  const { data: matchResult } = useQuery({ queryKey: ['match', programId], queryFn: () => getMatchDetail(programId!), retry: false })
  // Parent institution — a program has no photo of its own, so the hero inherits
  // the institution's campus photo (gradient fallback). Mirrors the school pages.
  const { data: institution } = useQuery({
    queryKey: ['institution', (program as any)?.institution_id],
    queryFn: () => getPublicInstitution((program as any).institution_id),
    enabled: !!(program as any)?.institution_id,
    retry: false,
  })
  const { data: netPrice } = useQuery({ queryKey: ['net-price', programId], queryFn: () => getNetPrice(programId!), enabled: !!programId, retry: false })
  const { data: events } = useQuery({ queryKey: ['events', { program_id: programId }], queryFn: () => listEvents({ program_id: programId, limit: 5 }) })
  const { data: rsvps } = useQuery({ queryKey: ['my-rsvps'], queryFn: getMyRsvps, retry: false })
  const { data: saved } = useQuery({ queryKey: ['saved'], queryFn: listSaved })
  const { data: applications } = useQuery({ queryKey: ['my-applications'], queryFn: listMyApplications })
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
  const applicationsList: any[] = Array.isArray(applications) ? applications : []
  const existingApp = applicationsList.find((a: any) => a.program_id === programId)
  const eventsList: EventItem[] = Array.isArray(events) ? events : []
  const rsvpSet = new Set((rsvps as any[] ?? []).map((r: any) => r.event_id))

  const saveMut = useMutation({
    mutationFn: async (): Promise<void> => {
      if (isSaved) await unsaveProgram(programId!)
      else await saveProgram(programId!)
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['saved'] }),
  })
  const applyMut = useMutation({
    mutationFn: () => createApplication(programId!),
    onSuccess: (app) => { showToast('Application created', 'success'); navigate(`/s/applications/${app.id}`) },
  })
  const rsvpMut = useMutation({
    mutationFn: rsvpEvent,
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['events'] }); queryClient.invalidateQueries({ queryKey: ['my-rsvps'] }); showToast('RSVP confirmed', 'success') },
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
  const testPolicy = extractTestPolicy(p.application_requirements)
  const recommendations = extractRecommendations(p.application_requirements)
  const fundingSignals = extractFundingSignals(p.cost_data)
  const salaryBands = extractSalaryBands(p.outcomes_data)
  const costBandMin =
    cd.estimated_total_cost_band?.min != null && !Number.isNaN(Number(cd.estimated_total_cost_band.min))
      ? Number(cd.estimated_total_cost_band.min)
      : null
  const costBandMax =
    cd.estimated_total_cost_band?.max != null && !Number.isNaN(Number(cd.estimated_total_cost_band.max))
      ? Number(cd.estimated_total_cost_band.max)
      : cd.total_cost_attendance != null && !Number.isNaN(Number(cd.total_cost_attendance))
        ? Number(cd.total_cost_attendance)
        : null
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

  const upcomingEvent = eventsList
    .filter((e: any) => new Date(e.event_datetime || e.starts_at || Date.now()) > new Date())
    .sort((a: any, b: any) => new Date(a.event_datetime || a.starts_at).getTime() - new Date(b.event_datetime || b.starts_at).getTime())[0]

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

  /* ── Hero (campus-photo, no logo/geo) — mirrors the institution/school pages.
     The program owns no photo; inherit the parent institution's campus photo
     (first raster image in its gallery; logos are SVG → skipped). Fall back to a
     clean gradient when the school has no photo. ── */
  const inst: any = institution ?? null
  const heroPhoto: string | null =
    (inst?.media_gallery ?? []).find((u: string) => /\.(jpe?g|png|webp|avif)(\?|$)/i.test(u)) ?? null
  const degreeLabel = DEGREE_LABELS[p.degree_type] || p.degree_type || ''
  // Eyebrow = degree label when we have one, else the institution name.
  const heroEyebrow = degreeLabel || instName || null

  // Stat strip — real fields only, NO location. Omit anything absent.
  const heroStats: { value: string; label: string }[] = []
  if (hasMatch) {
    const fit = toUnit(match.fitness_score ?? match.match_score)
    if (fit > 0) heroStats.push({ value: `${Math.round(fit * 100)}%`, label: 'fitness' })
  }
  const heroAcceptance = p.acceptance_rate ?? rd.acceptance_rate
  if (heroAcceptance != null && Number.isFinite(Number(heroAcceptance))) {
    const ar = Number(heroAcceptance)
    heroStats.push({ value: `${(ar * 100).toFixed(ar < 0.1 ? 1 : 0)}%`, label: 'acceptance' })
  }
  if (effectiveTuition != null && Number.isFinite(Number(effectiveTuition)) && Number(effectiveTuition) > 0) {
    heroStats.push({ value: formatCurrency(Number(effectiveTuition)), label: 'tuition / yr' })
  }
  const heroEarnings =
    odn.median_salary != null && Number.isFinite(Number(odn.median_salary))
      ? Number(odn.median_salary)
      : (rd.earnings_10yr_median != null && Number.isFinite(Number(rd.earnings_10yr_median))
        ? Number(rd.earnings_10yr_median)
        : null)
  if (heroEarnings != null && heroEarnings > 0) {
    heroStats.push({ value: formatCurrency(heroEarnings), label: 'median earnings' })
  }

  return (
    <div className="p-6 max-w-5xl w-full mx-auto">
      {/* ── Archived banner (§6) ── */}
      {isArchived && (
        <div className="mb-4 flex items-center gap-2 rounded-lg border border-warning/30 bg-warning-soft px-4 py-3">
          <Archive size={16} className="text-warning flex-shrink-0" />
          <p className="text-sm text-foreground">This program is no longer accepting applications.</p>
        </div>
      )}

      {/* ── Back to the last level ── */}
      <button
        onClick={() => navigate(-1)}
        className="inline-flex items-center gap-1.5 text-[13px] font-medium text-secondary hover:underline mb-3"
      >
        <ArrowLeft size={15} /> Back
      </button>

      {/* ── Breadcrumb (mirrors the school pages) ── */}
      <nav className="flex items-center gap-1.5 text-[13px] text-muted-foreground mb-4 flex-wrap" aria-label="Breadcrumb">
        <button onClick={() => navigate('/s/explore')} className="hover:text-secondary transition-colors">Match</button>
        <span className="text-muted-foreground" aria-hidden="true">·</span>
        <Link to={`/s/institutions/${p.institution_id}`} className="hover:text-secondary transition-colors truncate max-w-[28ch]">
          {instName || 'School'}
        </Link>
        <span className="text-muted-foreground" aria-hidden="true">·</span>
        <span className="text-foreground font-medium truncate max-w-[40ch]" aria-current="page">{p.program_name}</span>
      </nav>

      {/* ── Hero — campus photo (inherited from the parent institution) fading
            into the cream page background. No logo, no geo. ── */}
      <div className="relative rounded-xl overflow-hidden border border-border mb-5 bg-background">
        {/* Photo banner (raster image) or gradient fallback */}
        <div className="relative h-52 sm:h-64 md:h-72">
          {heroPhoto ? (
            <img src={heroPhoto} alt="" aria-hidden="true" className="absolute inset-0 h-full w-full object-cover" />
          ) : (
            <div className="absolute inset-0 bg-gradient-to-br from-secondary/10 to-background" />
          )}
          {/* Fade to the cream page background at the bottom; soft top scrim for glare. */}
          <div
            className="absolute inset-0"
            style={{
              background:
                'linear-gradient(to bottom, rgba(10,18,36,0.30) 0%, rgba(10,18,36,0.04) 24%, rgba(10,18,36,0) 44%, hsl(var(--background)) 97%)',
            }}
          />
        </div>

        {/* Identity — overlaps onto the cream gradient base; dark text reads cleanly. */}
        <div className="relative -mt-20 px-5 sm:px-7 pb-6">
          {heroEyebrow && <p className="text-eyebrow uppercase text-secondary mb-1.5">{heroEyebrow}</p>}

          <div className="flex flex-wrap items-end justify-between gap-4">
            <div className="min-w-0">
              <h1 className="text-2xl sm:text-3xl md:text-[2.5rem] font-bold text-foreground leading-[1.08] tracking-tight max-w-[24ch]">
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

            {/* Match ring — integrated beside the title (the sole gold accent, §2). */}
            {hasMatch ? (
              <div
                className="flex items-center gap-2.5 flex-shrink-0"
                title="Fitness is how well this program matches your strategy; confidence is how sure we are given your profile depth."
              >
                <DualRing
                  fitness={toUnit(match.fitness_score ?? match.match_score)}
                  confidence={toUnit(match.confidence_score ?? match.match_score)}
                  size={64}
                  onClick={() => setRationaleOpen(true)}
                />
                <div className="flex flex-col items-start gap-1">
                  {match.band_label && <BandBadge band={match.band_label} />}
                  <button
                    onClick={() => setRationaleOpen(true)}
                    className="inline-flex items-center gap-1 text-[11px] font-medium text-secondary hover:underline"
                  >
                    <Sparkles size={11} /> Why this match?
                  </button>
                </div>
              </div>
            ) : (
              <button
                onClick={() => navigate('/s/explore')}
                className="flex items-center gap-2 text-left flex-shrink-0"
                title="We haven't computed your match for this program yet."
              >
                <div className="w-11 h-11 rounded-full bg-muted flex items-center justify-center flex-shrink-0">
                  <Sparkles size={16} className="text-secondary" />
                </div>
                <div className="leading-tight">
                  <p className="text-[9px] uppercase tracking-wider font-semibold text-muted-foreground/60">Your match</p>
                  <p className="text-[12px] font-medium text-secondary hover:underline">See my matches</p>
                </div>
              </button>
            )}
          </div>

          {/* Actions — primary application CTA + Save + Ask counselor + Compare. */}
          <div className="flex flex-wrap items-center gap-2 mt-5">
            {existingApp ? (
              <Button size="sm" variant="secondary" onClick={() => navigate(`/s/applications/${existingApp.id}`)}>
                <FileText size={14} className="mr-1.5" /> My application
              </Button>
            ) : (
              <Button size="sm" variant="secondary" onClick={() => applyMut.mutate()} disabled={isArchived || applyMut.isPending}>
                <Send size={14} className="mr-1.5" /> Start application
              </Button>
            )}
            <Button
              size="sm"
              variant={isSaved ? 'secondary' : 'tertiary'}
              onClick={() => saveMut.mutate()}
              disabled={isArchived || saveMut.isPending}
              aria-pressed={isSaved}
            >
              {isSaved ? <BookmarkCheck size={14} className="mr-1.5" /> : <Bookmark size={14} className="mr-1.5" />}
              {isSaved ? 'Saved' : 'Save'}
            </Button>
            <Button
              size="sm"
              variant="tertiary"
              onClick={() => askCounselor(`Is ${p.program_name} at ${instName} a good fit for me? Why or why not?`)}
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
      </div>

      {/* ── KPI strip — adaptive: picks the 4 most distinctive numbers per program ── */}
      <KeyMetrics
        degreeType={p.degree_type}
        durationMonths={p.duration_months}
        tuition={effectiveTuition}
        tracks={p.tracks}
        highlights={p.highlights}
        descriptionText={p.description_text}
        outcomesMedianSalary={odn.median_salary}
        outcomesEmploymentRate={odn.employment_rate}
        outcomesInternshipConversion={odn.internship_conversion_rate}
        outcomesTopEmployers={odn.top_employers}
        outcomesTopIndustries={odn.top_industries}
        outcomesPaybackMonths={odn.payback_months}
        institutionTuition={rd.tuition_out_of_state ?? rd.tuition_in_state}
        earnings6yr={rd.earnings_6yr_median}
        earnings10yr={rd.earnings_10yr_median}
        graduationRate={rd.graduation_rate}
        retentionRate={rd.retention_rate}
      />

      {/* ── Your realistic shot — probability bands (Spec 09 §4A).
            The DualRing + redacted "why this match" now lead the fact strip (§2). ── */}
      {hasMatch && (
        <Card className="mb-5 p-4">
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

              {(tracksMeta.concentrations.length > 0 || tracksMeta.note || tracksMeta.learning_format || tracksMeta.curriculum.length > 0) && (
                <Card className="p-5">
                  <div className="flex items-center gap-2 mb-3">
                    <BookOpen size={14} className="text-secondary" />
                    <h3 className="font-semibold text-foreground">Curriculum & Structure</h3>
                  </div>
                  {tracksMeta.note && (
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
                  {tracksMeta.curriculum.length > 0 && (
                    <div className="space-y-3">
                      {tracksMeta.curriculum.map((term, i) => (
                        <div key={i} className="rounded-lg border border-border bg-muted/40 px-3 py-2.5">
                          <p className="text-[10px] font-semibold text-secondary uppercase tracking-wider mb-1.5">{term.term}</p>
                          <div className="flex flex-wrap gap-1.5">
                            {term.courses.map((c, j) => (
                              <span key={j} className="px-2 py-0.5 text-[11px] rounded-md bg-card text-foreground border border-border/60">{c}</span>
                            ))}
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
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
                  <Card className="p-5">
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
                    {cp.source && (
                      <p className="mt-3 text-[11px] text-muted-foreground/70">Source: {String(cp.source)}</p>
                    )}
                  </Card>
                )
              })()}

              <NextStepsCard
                applicationDeadline={effectiveDeadline}
                upcomingEvent={upcomingEvent ? {
                  title: (upcomingEvent as any).title || (upcomingEvent as any).event_name,
                  event_datetime: (upcomingEvent as any).event_datetime || (upcomingEvent as any).starts_at || (upcomingEvent as any).start_time,
                  onClick: () => rsvpMut.mutate(upcomingEvent.id),
                } : null}
                hasApplication={!!existingApp}
                onApply={() => applyMut.mutate()}
                onViewApplication={existingApp ? () => navigate(`/s/applications/${existingApp.id}`) : undefined}
                onAskCounselor={() => navigate(`/s?prefill=${encodeURIComponent(`Tell me more about ${p.program_name}. What should I know?`)}`)}
              />

              {/* Highlights as editorial chips */}
              {Array.isArray(p.highlights) && p.highlights.length > 0 && (
                <Card className="p-5">
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
                  <Card className="p-5">
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
            // Enriched admissions detail (rounds, fee, how-you're-evaluated).
            const reqObj = (p.application_requirements && !Array.isArray(p.application_requirements)
              ? p.application_requirements : {}) as Record<string, any>
            const evaluation = typeof reqObj.evaluation === 'string' ? reqObj.evaluation : null
            const appFee = reqObj.application_fee && typeof reqObj.application_fee === 'object'
              ? reqObj.application_fee as { amount_usd?: number; waiver_available?: boolean; note?: string }
              : null
            const deadlineRounds: Array<{ round: string; date: string }> = Array.isArray(reqObj.deadlines)
              ? reqObj.deadlines.filter((d: any) => d && d.round && d.date)
                .map((d: any) => ({ round: String(d.round), date: String(d.date) }))
              : []

            return (
              <>
                <StatGroup
                  acceptanceRate={p.acceptance_rate ?? rd.acceptance_rate}
                  satAvg={rd.sat_avg}
                  actMidpoint={rd.act_midpoint}
                  applicationDeadline={effectiveDeadline}
                />

                {/* Application Requirements */}
                <Card className="p-5">
                  <div className="flex items-center gap-2 mb-3">
                    <GraduationCap size={14} className="text-secondary" />
                    <h3 className="font-semibold text-foreground">Application Requirements</h3>
                    {appReqs.length > 0 && (
                      <span className="ml-auto text-[11px] text-foreground/60">
                        {requiredItems.length} required
                        {optionalItems.length > 0 && ` · ${optionalItems.length} optional`}
                      </span>
                    )}
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
                  <Card className="p-5">
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

                {testPolicy && (
                  <Card className="p-5">
                    <div className="flex items-center gap-2 mb-3">
                      <BookOpen size={14} className="text-secondary" />
                      <h3 className="font-semibold text-foreground">Test Policy</h3>
                      {testPolicy.stance_label && (
                        <Badge variant="info" size="sm">{testPolicy.stance_label}</Badge>
                      )}
                    </div>
                    <div className="space-y-3 text-sm">
                      {testPolicy.required.length > 0 && (
                        <div>
                          <p className="text-[10px] font-semibold text-foreground/70 uppercase tracking-wider mb-1">Required</p>
                          <div className="flex flex-wrap gap-1.5">
                            {testPolicy.required.map(t => <Badge key={t} variant="neutral" size="sm">{t}</Badge>)}
                          </div>
                        </div>
                      )}
                      {testPolicy.optional.length > 0 && (
                        <div>
                          <p className="text-[10px] font-semibold text-foreground/70 uppercase tracking-wider mb-1">Optional</p>
                          <div className="flex flex-wrap gap-1.5">
                            {testPolicy.optional.map(t => <Badge key={t} variant="neutral" size="sm">{t}</Badge>)}
                          </div>
                        </div>
                      )}
                      {testPolicy.accepted_tests.length > 0 && (
                        <div>
                          <p className="text-[10px] font-semibold text-foreground/70 uppercase tracking-wider mb-1">Accepted</p>
                          <div className="flex flex-wrap gap-1.5">
                            {testPolicy.accepted_tests.map(t => <Badge key={t} variant="neutral" size="sm">{t}</Badge>)}
                          </div>
                        </div>
                      )}
                      {testPolicy.typical_ranges.length > 0 && (
                        <div>
                          <p className="text-[10px] font-semibold text-foreground/70 uppercase tracking-wider mb-1">Typical score ranges</p>
                          <dl className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                            {testPolicy.typical_ranges.map(r => (
                              <div key={r.test} className="flex justify-between border-b border-border pb-1">
                                <dt className="text-foreground">{r.test}</dt>
                                <dd className="font-medium text-foreground tabular-nums">{r.low}–{r.high}</dd>
                              </div>
                            ))}
                          </dl>
                        </div>
                      )}
                      {testPolicy.superscore_enabled && (
                        <p className="text-xs text-foreground">Superscore across attempts is accepted.</p>
                      )}
                      {testPolicy.waived_rules && (
                        <p className="text-xs text-foreground"><span className="font-semibold text-foreground">Waiver rules:</span> {testPolicy.waived_rules}</p>
                      )}
                    </div>
                  </Card>
                )}

                {recommendations && (
                  <Card className="p-5">
                    <div className="flex items-center gap-2 mb-2">
                      <Mail size={14} className="text-secondary" />
                      <h3 className="font-semibold text-foreground">Recommendations</h3>
                    </div>
                    <p className="text-sm text-foreground">
                      {recommendations.required_count > 0
                        ? `${recommendations.required_count} letter${recommendations.required_count === 1 ? '' : 's'} required`
                        : 'Recommendations may be requested'}
                      {recommendations.types.length > 0 && (
                        <> · {recommendations.types.map(t => t.replace(/_/g, ' ')).join(', ')}</>
                      )}
                    </p>
                  </Card>
                )}

                {/* Admission Timeline */}
                {admissionTimeline && (
                  <Card className="p-5">
                    <div className="flex items-center gap-2 mb-4">
                      <Clock size={14} className="text-secondary" />
                      <h3 className="font-semibold text-foreground">Admission Timeline</h3>
                      <span className="ml-auto text-[11px] text-foreground/60 capitalize">{admissionTimeline.term}</span>
                    </div>
                    <div className="space-y-2">
                      {admissionTimeline.rounds.map((r: any, i: number) => {
                        const days = differenceInDays(new Date(r.deadline), new Date())
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

                {/* Application rounds (Early Action / Regular / R1–R3 etc.) */}
                {deadlineRounds.length > 0 && (
                  <Card className="p-5">
                    <div className="flex items-center gap-2 mb-3">
                      <Clock size={14} className="text-secondary" />
                      <h3 className="font-semibold text-foreground">Application Rounds</h3>
                    </div>
                    <ul className="space-y-2 text-sm">
                      {deadlineRounds.map((d, i) => (
                        <li key={i} className="flex justify-between border-b border-border pb-2 last:border-0 last:pb-0">
                          <span className="text-foreground">{d.round}</span>
                          <span className="font-medium text-foreground">{d.date}</span>
                        </li>
                      ))}
                    </ul>
                  </Card>
                )}

                {/* How you're evaluated + application fee */}
                {(evaluation || appFee) && (
                  <Card className="p-5">
                    <div className="flex items-center gap-2 mb-3">
                      <Sparkles size={14} className="text-secondary" />
                      <h3 className="font-semibold text-foreground">How You&rsquo;re Evaluated</h3>
                    </div>
                    {evaluation && <p className="text-sm text-foreground leading-relaxed">{evaluation}</p>}
                    {appFee && (
                      <div className="mt-3 flex items-start gap-2 text-sm rounded-lg bg-muted/50 border border-border px-3 py-2">
                        <DollarSign size={14} className="text-secondary flex-shrink-0 mt-0.5" />
                        <span className="text-foreground">
                          Application fee: <span className="font-semibold">${appFee.amount_usd}</span>
                          {appFee.waiver_available && (
                            <span className="text-foreground/70"> · fee waivers available</span>
                          )}
                          {appFee.note && <span className="block text-[11px] text-foreground/60 mt-0.5">{appFee.note}</span>}
                        </span>
                      </div>
                    )}
                  </Card>
                )}

                {/* Admissions insights */}
                <div className={`grid grid-cols-1 ${admissionTimeline ? 'md:grid-cols-1' : 'md:grid-cols-2'} gap-4`}>
                  {!admissionTimeline && (effectiveDeadline || p.program_start_date) && (
                    <Card className="p-5">
                      <div className="flex items-center gap-2 mb-3">
                        <Clock size={14} className="text-secondary" />
                        <h3 className="font-semibold text-foreground">Key Dates</h3>
                      </div>
                      <div className="space-y-2 text-sm">
                        {effectiveDeadline && (
                          <div className="flex justify-between">
                            <span className="text-foreground">Application Deadline</span>
                            <span className="font-medium text-foreground">{formatDate(effectiveDeadline)}</span>
                          </div>
                        )}
                        {p.program_start_date && (
                          <div className="flex justify-between">
                            <span className="text-foreground">Program Starts</span>
                            <span className="font-medium text-foreground">{formatDate(p.program_start_date)}</span>
                          </div>
                        )}
                      </div>
                    </Card>
                  )}

                  {(p.acceptance_rate ?? rd.acceptance_rate) != null && (
                    <Card className="p-5">
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
              </>
            )
          })()}

          {tab === 'costs' && (() => {
            const years = (p.duration_months || (p.degree_type === 'bachelors' ? 48 : 24)) / 12
            const annual = effectiveTuition || 0
            const fees = cd.fees || {}
            const feeTotal = Object.values(fees).reduce((s: number, v: any) => s + (Number(v) || 0), 0)
            const living = cd.estimated_living_cost || 15000
            const books = cd.book_supplies || 1200
            const intlPremium = cd.international_premium || 0
            const totalTuitionOnly = annual * years
            const totalMid = costBandMin != null && costBandMax != null
              ? Math.round((costBandMin + costBandMax) / 2)
              : (annual + feeTotal + living + books) * years
            const totalHigh = costBandMax ?? Math.round(totalMid * 1.15)
            const netPriceByIncome: Record<string, number> = cd.net_price_by_income || {}
            const od = odn
            const salary = od.median_salary ? Number(od.median_salary) : (rd.earnings_10yr_median || null)
            const empRate = od.employment_rate ? Number(od.employment_rate) : (rd.graduation_rate || null)
            const payback = od.payback_months ? Number(od.payback_months) : null
            return (
              <>
                {/* Spec 11 §3.3a — personalized net price (highlighted block) */}
                <NetPriceEstimator estimate={netPrice} />

                <StatGroup
                  tuition={effectiveTuition}
                  totalCost={cd.total_cost_attendance ?? rd.total_cost_attendance}
                  netPrice={cd.average_net_price ?? rd.avg_net_price}
                  medianDebt={cd.median_debt ?? rd.median_debt}
                  pellGrantRate={cd.pell_grant_rate ?? rd.pell_grant_rate}
                />

                <Card className="p-5">
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
                </Card>

                <Card className="p-5">
                  <div className="flex items-center gap-2 mb-3">
                    <GraduationCap size={14} className="text-secondary" />
                    <h3 className="font-semibold text-foreground">Estimated Total Cost ({years.toFixed(1)} years)</h3>
                  </div>
                  <div className="grid grid-cols-3 gap-3 text-center">
                    <div className="bg-muted/60 rounded-lg p-3">
                      <p className="text-xs text-foreground mb-1">{costBandMin != null ? 'Low estimate' : 'Tuition Only'}</p>
                      <p className="text-lg font-bold text-foreground">{formatCurrency(costBandMin ?? totalTuitionOnly)}</p>
                    </div>
                    <div className="bg-muted/60 rounded-lg p-3">
                      <p className="text-xs text-foreground mb-1">{costBandMax != null ? 'Expected range' : 'With Living Costs'}</p>
                      <p className="text-lg font-bold text-foreground">
                        {costBandMin != null && costBandMax != null
                          ? `${formatCurrency(costBandMin)} – ${formatCurrency(costBandMax)}`
                          : formatCurrency(totalMid)}
                      </p>
                    </div>
                    <div className="bg-muted/60 rounded-lg p-3">
                      <p className="text-xs text-foreground mb-1">{costBandMax != null ? 'High estimate' : 'High Estimate'}</p>
                      <p className="text-lg font-bold text-foreground">{formatCurrency(totalHigh)}</p>
                    </div>
                  </div>
                </Card>

                {fundingSignals && (
                  <Card className="p-5">
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
                    <Card className="p-5">
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
                                <p className="text-[11px] font-semibold text-foreground">{r.label}</p>
                                <p className="text-[10px] text-foreground/60">{r.range}</p>
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
                          Source: {cd.source}{cd.source_year ? ` · ${cd.source_year}` : ''}
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
                    <Card className="p-5">
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

                {(salary || empRate || payback) && (
                  <Card className="p-5">
                    <div className="flex items-center gap-2 mb-3">
                      <TrendingUp size={14} className="text-secondary" />
                      <h3 className="font-semibold text-foreground">ROI Snapshot</h3>
                    </div>
                    <div className="grid grid-cols-2 gap-3 text-sm">
                      {salary && <div><p className="text-foreground text-xs">Median Salary</p><p className="font-bold text-foreground text-lg">{formatCurrency(salary)}</p></div>}
                      {empRate && <div><p className="text-foreground text-xs">Grad/Employment Rate</p><p className="font-bold text-foreground text-lg">{(empRate * 100).toFixed(0)}%</p></div>}
                      {payback && <div><p className="text-foreground text-xs">Payback Period</p><p className="font-medium text-foreground">{payback} months</p></div>}
                      {salary && totalMid > 0 && <div><p className="text-foreground text-xs">Salary-to-Cost</p><p className="font-medium text-foreground">1:{(salary / totalMid).toFixed(1)}x</p></div>}
                    </div>
                  </Card>
                )}
              </>
            )
          })()}

          {tab === 'outcomes' && (() => {
            const od = odn
            const salary = od.median_salary ? Number(od.median_salary) : (rd.earnings_10yr_median || null)
            const salaryLow = od.salary_25th ? Number(od.salary_25th) : (salary ? Math.round(salary * 0.75) : null)
            const salaryHigh = od.salary_75th ? Number(od.salary_75th) : (salary ? Math.round(salary * 1.3) : null)
            const empRate = od.employment_rate ? Number(od.employment_rate) : null
            const empTimeframe = od.employment_timeframe || '6 months after graduation'
            const internRate = od.internship_conversion_rate ? Number(od.internship_conversion_rate) : null
            const topEmployers: string[] = od.top_employers || []
            const topIndustries: string[] = od.top_industries || []
            const hasData = salary || empRate || topEmployers.length > 0

            return (
              <>
                <StatGroup
                  earnings6yr={rd.earnings_6yr_median}
                  earnings10yr={rd.earnings_10yr_median}
                  graduationRate={rd.graduation_rate}
                  retentionRate={rd.retention_rate}
                  employmentRate={od.employment_rate}
                />

                {(salary || empRate) && (od.scope || od.source) && (
                  <Card className="p-3 border-secondary/30 bg-secondary/[0.05]">
                    <p className="text-[12px] text-muted-foreground">
                      {od.scope === 'institution'
                        ? (od.scope_note || 'Institution-wide figures across all graduates — not specific to this program.')
                        : 'Program-level median earnings (College Scorecard, Field of Study).'}
                      {od.source ? ` Source: ${od.source}.` : ''}
                    </p>
                  </Card>
                )}

                {!hasData ? (
                  <Card className="p-6 text-center">
                    <TrendingUp size={32} className="text-foreground/30 mx-auto mb-3" />
                    <p className="text-sm text-foreground">Outcomes data is not yet available for this program.</p>
                    <p className="text-xs text-foreground/60 mt-1">Check back later or contact the program directly.</p>
                  </Card>
                ) : (
                  <>
                    {salary && (
                      <Card className="p-5">
                        <div className="flex items-center gap-2 mb-3">
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
                            {odn.outcome_reporting_window && (
                              <p className="text-[10px] text-foreground/60 mt-2">{odn.outcome_reporting_window}</p>
                            )}
                          </div>
                        ) : (
                          <>
                            <div className="flex items-end justify-between mb-2">
                              <div className="text-center flex-1">
                                <p className="text-xs text-foreground/60">25th %ile</p>
                                <p className="text-sm font-medium text-foreground">{salaryLow ? formatCurrency(salaryLow) : '—'}</p>
                              </div>
                              <div className="text-center flex-1">
                                <p className="text-xs text-foreground/60">Median</p>
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
                      </Card>
                    )}

                    {(empRate || internRate) && (
                      <Card className="p-5">
                        <div className="flex items-center gap-2 mb-3">
                          <Briefcase size={14} className="text-secondary" />
                          <h3 className="font-semibold text-foreground">Employment & Placement</h3>
                        </div>
                        <div className="grid grid-cols-2 gap-4">
                          {empRate != null && (
                            <div>
                              <p className="text-xs text-foreground">Employment Rate</p>
                              <p className="text-2xl font-bold text-foreground">{(empRate * 100).toFixed(0)}%</p>
                              <p className="text-[10px] text-foreground/60">Within {empTimeframe}</p>
                            </div>
                          )}
                          {internRate != null && (
                            <div>
                              <p className="text-xs text-foreground">Internship Conversion</p>
                              <p className="text-2xl font-bold text-foreground">{(internRate * 100).toFixed(0)}%</p>
                              <p className="text-[10px] text-foreground/60">Interns → full-time offers</p>
                            </div>
                          )}
                        </div>
                      </Card>
                    )}

                    {topEmployers.length > 0 && (
                      <Card className="p-5">
                        <div className="flex items-center gap-2 mb-3">
                          <Building2 size={14} className="text-secondary" />
                          <h3 className="font-semibold text-foreground">Top Employers</h3>
                        </div>
                        <div className="flex flex-wrap gap-2">
                          {topEmployers.map((e: string) => <Badge key={e} variant="neutral" size="sm">{e}</Badge>)}
                        </div>
                      </Card>
                    )}

                    {topIndustries.length > 0 && (
                      <Card className="p-5">
                        <div className="flex items-center gap-2 mb-3">
                          <Users size={14} className="text-secondary" />
                          <h3 className="font-semibold text-foreground">Industry Placement</h3>
                        </div>
                        <div className="flex flex-wrap gap-2">
                          {topIndustries.map((ind: string) => <Badge key={ind} variant="info" size="sm">{ind}</Badge>)}
                        </div>
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
                )}
              </>
            )
          })()}

          {tab === 'insights' && (
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
          )}
        </div>

        {/* Sidebar */}
        <div className="lg:sticky lg:top-4 lg:self-start">
          <RelatedSidebar
            events={eventsList}
            sameSchoolPrograms={sameSchool}
            similarPrograms={similar}
            onRsvp={(id) => rsvpMut.mutate(id)}
            rsvpedIds={rsvpSet}
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
    <div className="p-6 max-w-5xl w-full mx-auto space-y-5">
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
