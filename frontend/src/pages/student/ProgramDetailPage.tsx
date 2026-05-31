import { useEffect, useState } from 'react'
import { useParams, useNavigate, useSearchParams } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  getProgram, getProgramReviews, getEmployerFeedback, getNetPrice,
  searchPrograms, semanticSearch,
} from '../../api/programs'
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
} from 'lucide-react'
import type { EventItem } from '../../types'

// Redesigned components
import DualRing from './match/DualRing'
import RationalePopover from './match/RationalePopover'
import ProbabilityBands from './match/ProbabilityBands'
import BandBadge from '../../components/ui/BandBadge'
import ProgramHeader from './program/ProgramHeader'
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
  const { data: program, isLoading } = useQuery({ queryKey: ['program', programId], queryFn: () => getProgram(programId!) })
  const { data: matchResult } = useQuery({ queryKey: ['match', programId], queryFn: () => getMatchDetail(programId!), retry: false })
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
    mutationFn: async () => {
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

  if (!program) {
    return (
      <div className="p-6 max-w-3xl mx-auto">
        <p className="text-sm text-student-text mb-3">Program details are unavailable right now.</p>
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
  const cd: any = p.cost_data || {}
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

  return (
    <div className="p-6 max-w-6xl mx-auto">
      {/* ── Archived banner (§6) ── */}
      {isArchived && (
        <div className="mb-4 flex items-center gap-2 rounded-lg border border-warning/30 bg-warning-soft px-4 py-3">
          <Archive size={16} className="text-warning flex-shrink-0" />
          <p className="text-sm text-student-ink">This program is no longer accepting applications.</p>
        </div>
      )}

      {/* ── Compact image-less header ── */}
      <ProgramHeader
        programName={p.program_name}
        degreeType={p.degree_type}
        institutionId={p.institution_id}
        institutionName={instName}
        institutionCity={p.institution_city}
        institutionCountry={p.institution_country}
        department={p.department}
        durationMonths={p.duration_months}
        deliveryFormat={p.delivery_format}
        highlights={p.highlights}
        tracks={p.tracks}
        description={p.description_text}
        isSaved={isSaved}
        isComparing={compareStore.has(p.id)}
        hasApplication={!!existingApp}
        archived={isArchived}
        onBack={() => navigate('/s/explore')}
        onSave={() => saveMut.mutate()}
        onCompare={handleCompare}
        onAskCounselor={() => askCounselor(
          `Is ${p.program_name} at ${instName} a good fit for me? Why or why not?`
        )}
        onApply={() => applyMut.mutate()}
        onViewApplication={existingApp ? () => navigate(`/s/applications/${existingApp.id}`) : undefined}
      />

      {/* ── KPI strip — adaptive: picks the 4 most distinctive numbers per program ── */}
      <KeyMetrics
        degreeType={p.degree_type}
        durationMonths={p.duration_months}
        tuition={effectiveTuition}
        tracks={p.tracks}
        highlights={p.highlights}
        descriptionText={p.description_text}
        outcomesMedianSalary={p.outcomes_data?.median_salary}
        outcomesEmploymentRate={p.outcomes_data?.employment_rate}
        outcomesInternshipConversion={p.outcomes_data?.internship_conversion_rate}
        outcomesTopEmployers={p.outcomes_data?.top_employers}
        outcomesTopIndustries={p.outcomes_data?.top_industries}
        outcomesPaybackMonths={p.outcomes_data?.payback_months}
        institutionTuition={rd.tuition_out_of_state ?? rd.tuition_in_state}
        earnings6yr={rd.earnings_6yr_median}
        earnings10yr={rd.earnings_10yr_median}
        graduationRate={rd.graduation_rate}
        retentionRate={rd.retention_rate}
      />

      {/* ── Your match — dual ring + redacted "why this match" (Spec 06 §3/§5.5) ── */}
      {hasMatch ? (
        <Card className="mb-5 p-4 flex items-center justify-between gap-4 flex-wrap">
          <div className="flex items-center gap-4">
            <DualRing
              fitness={toUnit(match.fitness_score ?? match.match_score)}
              confidence={toUnit(match.confidence_score ?? match.match_score)}
              size={84}
              onClick={() => setRationaleOpen(true)}
            />
            <div>
              <div className="flex items-center gap-2">
                <div className="text-eyebrow text-student-text">Your match</div>
                {match.band_label && <BandBadge band={match.band_label} />}
              </div>
              <p className="text-sm text-student-ink max-w-md mt-0.5">
                Fitness is how well this program matches your strategy; confidence is how sure
                we are given your profile depth.
              </p>
            </div>
          </div>
          <Button size="sm" variant="secondary" onClick={() => setRationaleOpen(true)}>
            <Sparkles size={14} className="mr-1.5" /> Why this match?
          </Button>
        </Card>
      ) : (
        /* Match not computed — gentle prompt (the public page shows a sign-in CTA). */
        <Card className="mb-5 p-4 flex items-center justify-between gap-4 flex-wrap">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 rounded-full bg-student-mist flex items-center justify-center">
              <Sparkles size={20} className="text-cobalt" />
            </div>
            <div>
              <div className="text-eyebrow text-student-text">Your match</div>
              <p className="text-sm text-student-ink mt-0.5">
                We haven't computed your match for this program yet.
              </p>
            </div>
          </div>
          <Button size="sm" variant="secondary" onClick={() => navigate('/s/explore')}>
            See my matches
          </Button>
        </Card>
      )}

      {/* ── Your realistic shot — probability bands (Spec 09 §4A) ── */}
      {hasMatch && (
        <Card className="mb-5 p-4">
          <ProbabilityBands
            bands={match.probability_bands ?? null}
            reason={match.acceptance_rate == null ? 'no_history' : 'not_match_ready'}
          />
        </Card>
      )}

      {/* ── Tabs (underline in --accent) ── */}
      <div className="border-b border-divider mb-5">
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
                    ? 'border-cobalt text-cobalt'
                    : 'border-transparent text-student-text hover:text-student-ink'
                }`}
              >
                <t.icon size={14} />
                {t.label}
                {badge && (
                  <span className={`px-1.5 py-0.5 text-[10px] rounded-full ${
                    isActive ? 'bg-student-mist text-cobalt' : 'bg-student-mist text-student-text'
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
              />

              {p.who_its_for && (
                <Card className="p-5">
                  <div className="flex items-center gap-2 mb-2">
                    <Users size={14} className="text-cobalt" />
                    <h3 className="font-semibold text-student-ink">Who It's For</h3>
                  </div>
                  <p className="text-sm text-student-text leading-relaxed">{p.who_its_for}</p>
                </Card>
              )}

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
                    <Sparkles size={14} className="text-cobalt" />
                    <h3 className="font-semibold text-student-ink">Program Highlights</h3>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {p.highlights.map((h: string, i: number) => (
                      <span key={i} className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs rounded-lg bg-cobalt/10 text-student-ink border border-cobalt/20">
                        <Sparkles size={11} className="text-cobalt" />
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
                      <Mail size={14} className="text-cobalt" />
                      <h3 className="font-semibold text-student-ink">Program Contacts</h3>
                    </div>
                    <div className="space-y-2 text-sm">
                      {rows.map((c, i) => (
                        <div key={i} className="flex justify-between items-start gap-2 border-b border-divider pb-2">
                          <div className="flex-1">
                            {c.name && <div className="font-medium text-student-ink">{c.name}</div>}
                            {c.role && <div className="text-xs text-student-text">{c.role}</div>}
                          </div>
                          {c.email && (
                            <a href={`mailto:${c.email}`} className="text-xs text-cobalt hover:underline">
                              {c.email}
                            </a>
                          )}
                        </div>
                      ))}
                      {rows[0]?.source_url && (
                        <p className="text-[10px] text-student-text/50 mt-2">
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
            const appReqs: Array<{ label: string; required?: boolean; note?: string }> = Array.isArray(p.application_requirements)
              ? p.application_requirements
              : []
            const legacyReqs = p.requirements && typeof p.requirements === 'object' ? Object.entries(p.requirements) : []
            const requiredItems = appReqs.filter(r => r.required !== false)
            const optionalItems = appReqs.filter(r => r.required === false)

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
                    <GraduationCap size={14} className="text-cobalt" />
                    <h3 className="font-semibold text-student-ink">Application Requirements</h3>
                    {appReqs.length > 0 && (
                      <span className="ml-auto text-[11px] text-student-text/60">
                        {requiredItems.length} required
                        {optionalItems.length > 0 && ` · ${optionalItems.length} optional`}
                      </span>
                    )}
                  </div>

                  {appReqs.length > 0 ? (
                    <div className="space-y-3">
                      {requiredItems.length > 0 && (
                        <div>
                          <p className="text-[10px] font-semibold text-student-text/70 uppercase tracking-wider mb-2">Required</p>
                          <ul className="grid grid-cols-1 md:grid-cols-2 gap-2">
                            {requiredItems.map((r, i) => (
                              <li key={i} className="flex items-start gap-2 px-3 py-2 rounded-lg bg-student-mist/50 border border-divider">
                                <span className="w-5 h-5 rounded-full bg-success-soft text-success flex items-center justify-center flex-shrink-0 mt-0.5">
                                  <svg width="10" height="10" viewBox="0 0 20 20" fill="currentColor"><path fillRule="evenodd" clipRule="evenodd" d="M16.7 5.3a1 1 0 010 1.4l-8 8a1 1 0 01-1.4 0l-4-4a1 1 0 011.4-1.4L8 12.6l7.3-7.3a1 1 0 011.4 0z" /></svg>
                                </span>
                                <div className="min-w-0">
                                  <p className="text-sm font-medium text-student-ink leading-tight">{r.label}</p>
                                  {r.note && <p className="text-[11px] text-student-text/70 mt-0.5">{r.note}</p>}
                                </div>
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}
                      {optionalItems.length > 0 && (
                        <div>
                          <p className="text-[10px] font-semibold text-student-text/70 uppercase tracking-wider mb-2">Optional / Flexible</p>
                          <ul className="grid grid-cols-1 md:grid-cols-2 gap-2">
                            {optionalItems.map((r, i) => (
                              <li key={i} className="flex items-start gap-2 px-3 py-2 rounded-lg bg-white border border-divider">
                                <span className="w-5 h-5 rounded-full bg-student-mist text-student-text/60 flex items-center justify-center flex-shrink-0 mt-0.5 text-[10px]">~</span>
                                <div className="min-w-0">
                                  <p className="text-sm font-medium text-student-ink leading-tight">{r.label}</p>
                                  {r.note && <p className="text-[11px] text-student-text/70 mt-0.5">{r.note}</p>}
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
                        <div key={k} className="flex justify-between border-b border-divider pb-2">
                          <dt className="text-student-text capitalize">{k.replace(/_/g, ' ')}</dt>
                          <dd className="font-medium text-student-ink">{String(v)}</dd>
                        </div>
                      ))}
                    </dl>
                  ) : (
                    <p className="text-sm text-student-text">Application requirements not yet listed. Contact the program for details.</p>
                  )}
                </Card>

                {/* Admission Timeline */}
                {admissionTimeline && (
                  <Card className="p-5">
                    <div className="flex items-center gap-2 mb-4">
                      <Clock size={14} className="text-cobalt" />
                      <h3 className="font-semibold text-student-ink">Admission Timeline</h3>
                      <span className="ml-auto text-[11px] text-student-text/60 capitalize">{admissionTimeline.term}</span>
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
                                ? 'bg-student-mist/40 border-divider opacity-60'
                                : isUrgent
                                  ? 'bg-warning-soft border-warning/30'
                                  : 'bg-white border-divider'
                            }`}
                          >
                            <div className="flex-1 min-w-0">
                              <div className="flex items-center gap-2">
                                <p className="text-sm font-semibold text-student-ink">{r.name}</p>
                                {r.binding && <Badge variant="warning" size="sm">Binding</Badge>}
                                {isUrgent && <Badge variant="warning" size="sm">{days}d left</Badge>}
                                {isPast && <Badge variant="neutral" size="sm">Closed</Badge>}
                              </div>
                              <p className="text-[11px] text-student-text/70 mt-0.5">
                                Apply by <span className="font-medium text-student-ink">{formatDate(r.deadline)}</span>
                                {r.decision_release && (
                                  <> · Decision <span className="font-medium text-student-ink">{formatDate(r.decision_release)}</span></>
                                )}
                              </p>
                            </div>
                          </div>
                        )
                      })}
                      {admissionTimeline.enrollment_deadline && (
                        <div className="flex items-center gap-3 px-3 py-2.5 rounded-lg bg-student-mist border border-cobalt/15">
                          <div className="flex-1 min-w-0">
                            <p className="text-sm font-semibold text-cobalt">Enrollment Deadline</p>
                            <p className="text-[11px] text-student-text/70 mt-0.5">
                              Commit by <span className="font-medium text-student-ink">{formatDate(admissionTimeline.enrollment_deadline)}</span>
                            </p>
                          </div>
                        </div>
                      )}
                    </div>
                  </Card>
                )}

                {/* Admissions insights */}
                <div className={`grid grid-cols-1 ${admissionTimeline ? 'md:grid-cols-1' : 'md:grid-cols-2'} gap-4`}>
                  {!admissionTimeline && (effectiveDeadline || p.program_start_date) && (
                    <Card className="p-5">
                      <div className="flex items-center gap-2 mb-3">
                        <Clock size={14} className="text-cobalt" />
                        <h3 className="font-semibold text-student-ink">Key Dates</h3>
                      </div>
                      <div className="space-y-2 text-sm">
                        {effectiveDeadline && (
                          <div className="flex justify-between">
                            <span className="text-student-text">Application Deadline</span>
                            <span className="font-medium text-student-ink">{formatDate(effectiveDeadline)}</span>
                          </div>
                        )}
                        {p.program_start_date && (
                          <div className="flex justify-between">
                            <span className="text-student-text">Program Starts</span>
                            <span className="font-medium text-student-ink">{formatDate(p.program_start_date)}</span>
                          </div>
                        )}
                      </div>
                    </Card>
                  )}

                  {(p.acceptance_rate ?? rd.acceptance_rate) != null && (
                    <Card className="p-5">
                      <div className="flex items-center gap-2 mb-3">
                        <Sparkles size={14} className="text-cobalt" />
                        <h3 className="font-semibold text-student-ink">Admissions Profile</h3>
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
                            <li key={i} className="flex items-start gap-2 text-student-text">
                              <span className="w-1 h-1 rounded-full bg-cobalt mt-2 flex-shrink-0" />
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
            const totalMid = (annual + feeTotal + living + books) * years
            const totalHigh = Math.round(totalMid * 1.15)
            const netPriceByIncome: Record<string, number> = cd.net_price_by_income || {}
            const od = p.outcomes_data || {}
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
                    <DollarSign size={14} className="text-cobalt" />
                    <h3 className="font-semibold text-student-ink">Tuition & Fees</h3>
                  </div>
                  <dl className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <dt className="text-student-text">Annual Tuition</dt>
                      <dd className="font-medium text-student-ink">{formatCurrency(annual)}</dd>
                    </div>
                    {Object.entries(fees).map(([k, v]) => (
                      <div key={k} className="flex justify-between">
                        <dt className="text-student-text capitalize">{k.replace(/_/g, ' ')}</dt>
                        <dd className="text-student-ink">{formatCurrency(Number(v))}</dd>
                      </div>
                    ))}
                    {intlPremium > 0 && (
                      <div className="flex justify-between">
                        <dt className="text-student-text">International Premium</dt>
                        <dd className="text-student-ink">{formatCurrency(intlPremium)}</dd>
                      </div>
                    )}
                    {feeTotal > 0 && (
                      <div className="flex justify-between border-t border-divider pt-2 font-medium">
                        <dt className="text-student-ink">Annual Subtotal</dt>
                        <dd className="text-student-ink">{formatCurrency(annual + feeTotal)}</dd>
                      </div>
                    )}
                  </dl>
                </Card>

                <Card className="p-5">
                  <div className="flex items-center gap-2 mb-3">
                    <GraduationCap size={14} className="text-cobalt" />
                    <h3 className="font-semibold text-student-ink">Estimated Total Cost ({years.toFixed(1)} years)</h3>
                  </div>
                  <div className="grid grid-cols-3 gap-3 text-center">
                    <div className="bg-student-mist/60 rounded-lg p-3">
                      <p className="text-xs text-student-text mb-1">Tuition Only</p>
                      <p className="text-lg font-bold text-student-ink">{formatCurrency(totalTuitionOnly)}</p>
                    </div>
                    <div className="bg-student-mist/60 rounded-lg p-3">
                      <p className="text-xs text-student-text mb-1">With Living Costs</p>
                      <p className="text-lg font-bold text-student-ink">{formatCurrency(totalMid)}</p>
                    </div>
                    <div className="bg-student-mist/60 rounded-lg p-3">
                      <p className="text-xs text-student-text mb-1">High Estimate</p>
                      <p className="text-lg font-bold text-student-ink">{formatCurrency(totalHigh)}</p>
                    </div>
                  </div>
                </Card>

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
                        <DollarSign size={14} className="text-cobalt" />
                        <h3 className="font-semibold text-student-ink">Net Price by Household Income</h3>
                      </div>
                      <p className="text-xs text-student-text mb-4">
                        Average price families actually pay after grants & scholarships, by household income band.
                      </p>
                      <div className="space-y-2">
                        {rows.map(r => {
                          const price = netPriceByIncome[r.key]
                          const widthPct = Math.round((price / maxPrice) * 100)
                          return (
                            <div key={r.key} className="grid grid-cols-[90px_1fr_85px] gap-3 items-center">
                              <div>
                                <p className="text-[11px] font-semibold text-student-ink">{r.label}</p>
                                <p className="text-[10px] text-student-text/60">{r.range}</p>
                              </div>
                              <div className="relative h-2 rounded-pill bg-student-mist overflow-hidden">
                                <div className="h-full rounded-pill bg-cobalt" style={{ width: `${widthPct}%` }} />
                              </div>
                              <p className="text-xs font-bold text-student-ink text-right tabular-nums">
                                {formatCurrency(price)}
                              </p>
                            </div>
                          )
                        })}
                      </div>
                      {cd.source && (
                        <p className="text-[10px] text-student-text/50 mt-3 italic">
                          Source: {cd.source}{cd.source_year ? ` · ${cd.source_year}` : ''}
                        </p>
                      )}
                      {rd.price_calculator_url && (
                        <a
                          href={rd.price_calculator_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="mt-3 inline-flex items-center gap-1.5 text-[11px] font-medium text-cobalt hover:text-cobalt-hover"
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
                        <DollarSign size={14} className="text-cobalt" />
                        <h3 className="font-semibold text-student-ink">Graduate Debt Distribution</h3>
                      </div>
                      <p className="text-xs text-student-text mb-3">
                        How much graduates actually borrow. Most fall between the 25th and 75th percentiles.
                      </p>
                      <div className="space-y-2">
                        {rows.map(r => {
                          const w = Math.round((r.value / max) * 100)
                          const isMiddle = r.pct === '25th' || r.pct === '75th'
                          return (
                            <div key={r.pct} className="grid grid-cols-[70px_1fr_85px] gap-3 items-center">
                              <p className={`text-[11px] font-semibold ${isMiddle ? 'text-student-ink' : 'text-student-text'}`}>
                                {r.pct} %ile
                              </p>
                              <div className="relative h-2 rounded-pill bg-student-mist overflow-hidden">
                                <div
                                  className={`h-full rounded-pill ${isMiddle ? 'bg-cobalt' : 'bg-cobalt/30'}`}
                                  style={{ width: `${w}%` }}
                                />
                              </div>
                              <p className={`text-xs font-bold tabular-nums text-right ${isMiddle ? 'text-student-ink' : 'text-student-text'}`}>
                                {formatCurrency(r.value)}
                              </p>
                            </div>
                          )
                        })}
                      </div>
                      {rd.median_debt_monthly != null && (
                        <p className="text-[11px] text-student-text mt-3">
                          Median monthly payment after graduation: <span className="font-semibold text-student-ink">${Math.round(rd.median_debt_monthly)}</span>
                        </p>
                      )}
                    </Card>
                  )
                })()}

                {(salary || empRate || payback) && (
                  <Card className="p-5">
                    <div className="flex items-center gap-2 mb-3">
                      <TrendingUp size={14} className="text-cobalt" />
                      <h3 className="font-semibold text-student-ink">ROI Snapshot</h3>
                    </div>
                    <div className="grid grid-cols-2 gap-3 text-sm">
                      {salary && <div><p className="text-student-text text-xs">Median Salary</p><p className="font-bold text-student-ink text-lg">{formatCurrency(salary)}</p></div>}
                      {empRate && <div><p className="text-student-text text-xs">Grad/Employment Rate</p><p className="font-bold text-student-ink text-lg">{(empRate * 100).toFixed(0)}%</p></div>}
                      {payback && <div><p className="text-student-text text-xs">Payback Period</p><p className="font-medium text-student-ink">{payback} months</p></div>}
                      {salary && totalMid > 0 && <div><p className="text-student-text text-xs">Salary-to-Cost</p><p className="font-medium text-student-ink">1:{(salary / totalMid).toFixed(1)}x</p></div>}
                    </div>
                  </Card>
                )}
              </>
            )
          })()}

          {tab === 'outcomes' && (() => {
            const od = p.outcomes_data || {}
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

                {!hasData ? (
                  <Card className="p-6 text-center">
                    <TrendingUp size={32} className="text-student-text/30 mx-auto mb-3" />
                    <p className="text-sm text-student-text">Outcomes data is not yet available for this program.</p>
                    <p className="text-xs text-student-text/60 mt-1">Check back later or contact the program directly.</p>
                  </Card>
                ) : (
                  <>
                    {salary && (
                      <Card className="p-5">
                        <div className="flex items-center gap-2 mb-3">
                          <DollarSign size={14} className="text-cobalt" />
                          <h3 className="font-semibold text-student-ink">Salary Distribution</h3>
                        </div>
                        <div className="flex items-end justify-between mb-2">
                          <div className="text-center flex-1">
                            <p className="text-xs text-student-text/60">25th %ile</p>
                            <p className="text-sm font-medium text-student-ink">{salaryLow ? formatCurrency(salaryLow) : '—'}</p>
                          </div>
                          <div className="text-center flex-1">
                            <p className="text-xs text-student-text/60">Median</p>
                            <p className="text-2xl font-bold text-student-ink">{formatCurrency(salary)}</p>
                          </div>
                          <div className="text-center flex-1">
                            <p className="text-xs text-student-text/60">75th %ile</p>
                            <p className="text-sm font-medium text-student-ink">{salaryHigh ? formatCurrency(salaryHigh) : '—'}</p>
                          </div>
                        </div>
                        <div className="relative h-2 bg-student-mist rounded-pill mt-3">
                          <div className="absolute h-full bg-cobalt/30 rounded-pill" style={{ left: '15%', width: '70%' }} />
                          <div className="absolute h-full bg-cobalt rounded-pill" style={{ left: '40%', width: '20%' }} />
                        </div>
                      </Card>
                    )}

                    {(empRate || internRate) && (
                      <Card className="p-5">
                        <div className="flex items-center gap-2 mb-3">
                          <Briefcase size={14} className="text-cobalt" />
                          <h3 className="font-semibold text-student-ink">Employment & Placement</h3>
                        </div>
                        <div className="grid grid-cols-2 gap-4">
                          {empRate != null && (
                            <div>
                              <p className="text-xs text-student-text">Employment Rate</p>
                              <p className="text-2xl font-bold text-student-ink">{(empRate * 100).toFixed(0)}%</p>
                              <p className="text-[10px] text-student-text/60">Within {empTimeframe}</p>
                            </div>
                          )}
                          {internRate != null && (
                            <div>
                              <p className="text-xs text-student-text">Internship Conversion</p>
                              <p className="text-2xl font-bold text-student-ink">{(internRate * 100).toFixed(0)}%</p>
                              <p className="text-[10px] text-student-text/60">Interns → full-time offers</p>
                            </div>
                          )}
                        </div>
                      </Card>
                    )}

                    {topEmployers.length > 0 && (
                      <Card className="p-5">
                        <div className="flex items-center gap-2 mb-3">
                          <Building2 size={14} className="text-cobalt" />
                          <h3 className="font-semibold text-student-ink">Top Employers</h3>
                        </div>
                        <div className="flex flex-wrap gap-2">
                          {topEmployers.map((e: string) => <Badge key={e} variant="neutral" size="sm">{e}</Badge>)}
                        </div>
                      </Card>
                    )}

                    {topIndustries.length > 0 && (
                      <Card className="p-5">
                        <div className="flex items-center gap-2 mb-3">
                          <Users size={14} className="text-cobalt" />
                          <h3 className="font-semibold text-student-ink">Industry Placement</h3>
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
                        className="w-full text-left rounded-lg border border-divider hover:border-cobalt hover:bg-student-mist transition-colors p-4 flex items-center justify-between gap-3"
                      >
                        <div className="flex items-center gap-2">
                          <Briefcase size={14} className="text-cobalt" />
                          <span className="text-sm text-student-ink">
                            See what <span className="font-semibold">{employerData?.total_feedback}</span> employers say about graduates
                          </span>
                        </div>
                        <span className="text-xs font-semibold text-cobalt">Insights →</span>
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
            netPrice={netPrice}
            discoveryBackHref={discoveryBackHref}
          />
        </div>
      </div>

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
    <div className="p-6 max-w-6xl mx-auto space-y-5">
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
