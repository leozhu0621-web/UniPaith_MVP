import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { getProgram, getProgramReviews, getEmployerFeedback, searchPrograms, semanticSearch } from '../../api/programs'
import { getMatchDetail, logEngagement } from '../../api/matching'
import { listEvents, rsvpEvent, getMyRsvps } from '../../api/events'
import { listMyApplications, createApplication } from '../../api/applications'
import { saveProgram, unsaveProgram, listSaved } from '../../api/saved-lists'
import { useCompareStore } from '../../stores/compare-store'
import Card from '../../components/ui/Card'
import Badge from '../../components/ui/Badge'
import Button from '../../components/ui/Button'
import Skeleton from '../../components/ui/Skeleton'
import ProgressBar from '../../components/ui/ProgressBar'
import Modal from '../../components/ui/Modal'
import { showToast } from '../../stores/toast-store'
import { formatCurrency, formatDate, formatScore } from '../../utils/format'
import {
  BookOpen, GraduationCap, DollarSign, TrendingUp, MessageSquare,
  Star, Quote, BarChart3, Briefcase, Building2, Users, Clock,
  Sparkles,
} from 'lucide-react'
import type { MatchResult, EventItem } from '../../types'

// Redesigned components
import MatchRing from './program/MatchRing'
import ProgramHeader from './program/ProgramHeader'
import KeyMetrics from './program/KeyMetrics'
import StatGroup from './program/StatGroup'
import AboutCard from './program/AboutCard'
import NextStepsCard from './program/NextStepsCard'
import RelatedSidebar from './program/RelatedSidebar'

// Local logos (no campus images on program detail — that content belongs on the university page)
const LOCAL_LOGOS: Record<string, string> = {
  'new york university': '/school-images/nyu-logo.jpg',
  'stanford university': '/school-images/stanford-logo.jpg',
}

type Tab = 'overview' | 'admissions' | 'costs' | 'outcomes' | 'reviews'

const TABS: { id: Tab; label: string; icon: typeof BookOpen }[] = [
  { id: 'overview', label: 'Overview', icon: BookOpen },
  { id: 'admissions', label: 'Admissions', icon: GraduationCap },
  { id: 'costs', label: 'Costs & Aid', icon: DollarSign },
  { id: 'outcomes', label: 'Outcomes', icon: TrendingUp },
  { id: 'reviews', label: 'Reviews', icon: Star },
]

export default function SchoolDetailPage() {
  const { programId } = useParams<{ programId: string }>()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const compareStore = useCompareStore()
  const [tab, setTab] = useState<Tab>('overview')
  const [matchModalOpen, setMatchModalOpen] = useState(false)

  // Review/employer filters
  const [reviewDegree, setReviewDegree] = useState('')
  const [reviewYear, setReviewYear] = useState('')
  const [reviewMinRating, setReviewMinRating] = useState('')
  const [empIndustry, setEmpIndustry] = useState('')
  const [empYear, setEmpYear] = useState('')
  const [empSentiment, setEmpSentiment] = useState('')

  // Data
  const { data: program, isLoading } = useQuery({ queryKey: ['program', programId], queryFn: () => getProgram(programId!) })
  const { data: matchResult } = useQuery({ queryKey: ['match', programId], queryFn: () => getMatchDetail(programId!), retry: false })
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
    mutationFn: () => isSaved ? unsaveProgram(programId!) : saveProgram(programId!),
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

  if (isLoading) {
    return <div className="p-6 max-w-6xl mx-auto space-y-4">{Array.from({ length: 4 }).map((_, i) => <Skeleton key={i} className="h-24" />)}</div>
  }
  if (!program) {
    return (
      <div className="p-6 max-w-3xl mx-auto">
        <p className="text-sm text-gray-600 mb-3">Program details are unavailable right now.</p>
        <Button size="sm" variant="secondary" onClick={() => navigate('/s/explore')}>Back to Explore</Button>
      </div>
    )
  }

  const p: any = program
  const match: MatchResult | null = matchResult ?? null
  const rd: any = p.ranking_data || {}
  const instName = p.institution_name || ''

  // Logo only — no campus image on this page (that belongs on the university page)
  const instLogo = LOCAL_LOGOS[instName.toLowerCase()] || p.institution_logo_url

  const upcomingEvent = eventsList
    .filter((e: any) => new Date(e.event_datetime || e.starts_at || Date.now()) > new Date())
    .sort((a: any, b: any) => new Date(a.event_datetime || a.starts_at).getTime() - new Date(b.event_datetime || b.starts_at).getTime())[0]

  const handleCompare = () => {
    if (compareStore.has(p.id)) compareStore.remove(p.id)
    else compareStore.add({ program_id: p.id, program_name: p.program_name, institution_name: instName, degree_type: p.degree_type })
  }

  const sameSchool = (sameSchoolData?.items ?? []).filter((sp: any) => sp.id !== programId).slice(0, 5)
  const similar = (Array.isArray(similarData) ? similarData : []).filter((sp: any) => sp.id !== programId).slice(0, 5)

  return (
    <div className="p-6 max-w-6xl mx-auto">
      {/* ── Compact image-less header ── */}
      <ProgramHeader
        programName={p.program_name}
        degreeType={p.degree_type}
        institutionId={p.institution_id}
        institutionName={instName}
        institutionCity={p.institution_city}
        institutionCountry={p.institution_country}
        institutionLogoUrl={instLogo}
        department={p.department}
        usNewsRank={rd.us_news_2025}
        durationMonths={p.duration_months}
        deliveryFormat={p.delivery_format}
        campusSetting={p.campus_setting || p.institution_campus_setting}
        studentBodySize={p.institution_student_body_size}
        applicationDeadline={p.application_deadline}
        matchScore={match?.match_score}
        matchTier={match?.match_tier}
        onMatchClick={() => setMatchModalOpen(true)}
        isSaved={isSaved}
        isComparing={compareStore.has(p.id)}
        hasApplication={!!existingApp}
        onBack={() => navigate('/s/explore')}
        onSave={() => saveMut.mutate()}
        onCompare={handleCompare}
        onAskCounselor={() => navigate(`/s?prefill=${encodeURIComponent(`Tell me about ${p.program_name} at ${instName}. Is it a good fit?`)}`)}
        onApply={() => applyMut.mutate()}
        onViewApplication={existingApp ? () => navigate(`/s/applications/${existingApp.id}`) : undefined}
      />

      {/* ── Hero KPI strip — only the stats that matter most ── */}
      <KeyMetrics
        acceptanceRate={p.acceptance_rate ?? rd.acceptance_rate}
        medianSalary={p.outcomes_data?.median_salary ?? rd.earnings_10yr_median}
        tuition={p.tuition}
        graduationRate={rd.graduation_rate}
        employmentRate={p.outcomes_data?.employment_rate}
      />

      {/* ── Tabs ── */}
      <div className="border-b border-divider mb-5">
        <div className="flex gap-1 overflow-x-auto">
          {TABS.map(t => {
            const isActive = tab === t.id
            let badge: string | null = null
            if (t.id === 'reviews' && reviewsData?.total_reviews) badge = String(reviewsData.total_reviews)
            return (
              <button
                key={t.id}
                onClick={() => setTab(t.id)}
                className={`flex items-center gap-1.5 px-4 py-2.5 text-sm font-medium border-b-2 transition-colors whitespace-nowrap ${
                  isActive
                    ? 'border-student text-student'
                    : 'border-transparent text-student-text hover:text-student-ink'
                }`}
              >
                <t.icon size={14} />
                {t.label}
                {badge && (
                  <span className={`px-1.5 py-0.5 text-[10px] rounded-full ${
                    isActive ? 'bg-student-mist text-student' : 'bg-slate-100 text-student-text'
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
              <AboutCard description={p.description_text || p.institution_description || ''} />

              {p.who_its_for && (
                <Card className="p-5">
                  <div className="flex items-center gap-2 mb-2">
                    <Users size={14} className="text-student" />
                    <h3 className="font-semibold text-student-ink">Who It's For</h3>
                  </div>
                  <p className="text-sm text-student-text leading-relaxed">{p.who_its_for}</p>
                </Card>
              )}

              <NextStepsCard
                applicationDeadline={p.application_deadline}
                upcomingEvent={upcomingEvent ? {
                  title: upcomingEvent.title || (upcomingEvent as any).event_name,
                  event_datetime: (upcomingEvent as any).event_datetime || (upcomingEvent as any).starts_at,
                  onClick: () => rsvpMut.mutate(upcomingEvent.id),
                } : null}
                hasApplication={!!existingApp}
                onApply={() => applyMut.mutate()}
                onViewApplication={existingApp ? () => navigate(`/s/applications/${existingApp.id}`) : undefined}
                onAskCounselor={() => navigate(`/s?prefill=${encodeURIComponent(`Tell me more about ${p.program_name}. What should I know?`)}`)}
              />

              {/* Highlights as visual chips */}
              {Array.isArray(p.highlights) && p.highlights.length > 0 && (
                <Card className="p-5">
                  <div className="flex items-center gap-2 mb-3">
                    <Sparkles size={14} className="text-gold" />
                    <h3 className="font-semibold text-student-ink">Program Highlights</h3>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {p.highlights.map((h: string, i: number) => (
                      <span key={i} className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs rounded-lg bg-gold-soft/50 text-student-ink border border-gold/20">
                        <Sparkles size={11} className="text-gold" />
                        {h}
                      </span>
                    ))}
                  </div>
                </Card>
              )}
            </>
          )}

          {tab === 'admissions' && (() => {
            // application_requirements is a list of { label, required, note? }
            // (the legacy `requirements` freeform dict is usually empty — fall back to it only if the list isn't present)
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
                  applicationDeadline={p.application_deadline}
                />

                {/* Application Requirements — structured list */}
                <Card className="p-5">
                  <div className="flex items-center gap-2 mb-3">
                    <GraduationCap size={14} className="text-student" />
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
                              <li key={i} className="flex items-start gap-2 px-3 py-2 rounded-lg bg-slate-50 border border-slate-100">
                                <span className="w-5 h-5 rounded-full bg-emerald-100 text-emerald-700 flex items-center justify-center flex-shrink-0 mt-0.5">
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
                              <li key={i} className="flex items-start gap-2 px-3 py-2 rounded-lg bg-white border border-slate-200">
                                <span className="w-5 h-5 rounded-full bg-slate-100 text-slate-500 flex items-center justify-center flex-shrink-0 mt-0.5 text-[10px]">~</span>
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
                        <div key={k} className="flex justify-between border-b border-gray-100 pb-2">
                          <dt className="text-student-text capitalize">{k.replace(/_/g, ' ')}</dt>
                          <dd className="font-medium text-student-ink">{String(v)}</dd>
                        </div>
                      ))}
                    </dl>
                  ) : (
                    <p className="text-sm text-student-text">Application requirements not yet listed. Contact the program for details.</p>
                  )}
                </Card>

                {/* Key dates + admissions insights — 2 columns */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {(p.application_deadline || p.program_start_date) && (
                    <Card className="p-5">
                      <div className="flex items-center gap-2 mb-3">
                        <Clock size={14} className="text-amber-600" />
                        <h3 className="font-semibold text-student-ink">Key Dates</h3>
                      </div>
                      <div className="space-y-2 text-sm">
                        {p.application_deadline && (
                          <div className="flex justify-between">
                            <span className="text-student-text">Application Deadline</span>
                            <span className="font-medium text-student-ink">{formatDate(p.application_deadline)}</span>
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

                  {/* Admissions insights card — derived from acceptance rate + SAT */}
                  {(p.acceptance_rate ?? rd.acceptance_rate) != null && (
                    <Card className="p-5">
                      <div className="flex items-center gap-2 mb-3">
                        <Sparkles size={14} className="text-student" />
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
                              <span className="w-1 h-1 rounded-full bg-student mt-2 flex-shrink-0" />
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
            const cd = p.cost_data || {}
            const years = (p.duration_months || (p.degree_type === 'bachelors' ? 48 : 24)) / 12
            const annual = p.tuition || 0
            const fees = cd.fees || {}
            const feeTotal = Object.values(fees).reduce((s: number, v: any) => s + (Number(v) || 0), 0)
            const living = cd.estimated_living_cost || 15000
            const books = cd.book_supplies || 1200
            const intlPremium = cd.international_premium || 0
            const totalTuitionOnly = annual * years
            const totalMid = (annual + feeTotal + living + books) * years
            const totalHigh = Math.round(totalMid * 1.15)
            const od = p.outcomes_data || {}
            const salary = od.median_salary ? Number(od.median_salary) : (rd.earnings_10yr_median || null)
            const empRate = od.employment_rate ? Number(od.employment_rate) : (rd.graduation_rate || null)
            const payback = od.payback_months ? Number(od.payback_months) : null
            return (
              <>
                <StatGroup
                  tuition={p.tuition}
                  totalCost={rd.total_cost_attendance}
                  netPrice={rd.avg_net_price}
                  medianDebt={rd.median_debt}
                  pellGrantRate={rd.pell_grant_rate}
                />

                <Card className="p-5">
                  <div className="flex items-center gap-2 mb-3">
                    <DollarSign size={14} className="text-rose-600" />
                    <h3 className="font-semibold text-student-ink">Tuition & Fees</h3>
                  </div>
                  <dl className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <dt className="text-student-text">Annual Tuition</dt>
                      <dd className="font-medium">{formatCurrency(annual)}</dd>
                    </div>
                    {Object.entries(fees).map(([k, v]) => (
                      <div key={k} className="flex justify-between">
                        <dt className="text-student-text capitalize">{k.replace(/_/g, ' ')}</dt>
                        <dd>{formatCurrency(Number(v))}</dd>
                      </div>
                    ))}
                    {intlPremium > 0 && (
                      <div className="flex justify-between">
                        <dt className="text-student-text">International Premium</dt>
                        <dd>{formatCurrency(intlPremium)}</dd>
                      </div>
                    )}
                    {feeTotal > 0 && (
                      <div className="flex justify-between border-t pt-2 font-medium">
                        <dt>Annual Subtotal</dt>
                        <dd>{formatCurrency(annual + feeTotal)}</dd>
                      </div>
                    )}
                  </dl>
                </Card>

                <Card className="p-5">
                  <div className="flex items-center gap-2 mb-3">
                    <GraduationCap size={14} className="text-student" />
                    <h3 className="font-semibold text-student-ink">Estimated Total Cost ({years.toFixed(1)} years)</h3>
                  </div>
                  <div className="grid grid-cols-3 gap-3 text-center">
                    <div className="bg-emerald-50 rounded-lg p-3">
                      <p className="text-xs text-student-text mb-1">Tuition Only</p>
                      <p className="text-lg font-bold text-emerald-700">{formatCurrency(totalTuitionOnly)}</p>
                    </div>
                    <div className="bg-slate-50 rounded-lg p-3">
                      <p className="text-xs text-student-text mb-1">With Living Costs</p>
                      <p className="text-lg font-bold text-student-ink">{formatCurrency(totalMid)}</p>
                    </div>
                    <div className="bg-amber-50 rounded-lg p-3">
                      <p className="text-xs text-student-text mb-1">High Estimate</p>
                      <p className="text-lg font-bold text-amber-700">{formatCurrency(totalHigh)}</p>
                    </div>
                  </div>
                </Card>

                {(salary || empRate || payback) && (
                  <Card className="p-5">
                    <div className="flex items-center gap-2 mb-3">
                      <TrendingUp size={14} className="text-emerald-600" />
                      <h3 className="font-semibold text-student-ink">ROI Snapshot</h3>
                    </div>
                    <div className="grid grid-cols-2 gap-3 text-sm">
                      {salary && <div><p className="text-student-text text-xs">Median Salary</p><p className="font-bold text-emerald-700 text-lg">{formatCurrency(salary)}</p></div>}
                      {empRate && <div><p className="text-student-text text-xs">Grad/Employment Rate</p><p className="font-bold text-student-ink text-lg">{(empRate * 100).toFixed(0)}%</p></div>}
                      {payback && <div><p className="text-student-text text-xs">Payback Period</p><p className="font-medium">{payback} months</p></div>}
                      {salary && totalMid > 0 && <div><p className="text-student-text text-xs">Salary-to-Cost</p><p className="font-medium">1:{(salary / totalMid).toFixed(1)}x</p></div>}
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

            // Employer feedback data
            const ed = employerData || { total_feedback: 0, feedback: [], sentiment_counts: {} }
            const allFeedback: any[] = ed.feedback || []
            const sentiments = ed.sentiment_counts || {}
            const totalSent = Object.values(sentiments).reduce((s: number, v: any) => s + (Number(v) || 0), 0)
            const dims: { key: string; label: string }[] = [
              { key: 'avg_technical', label: 'Technical Skills' },
              { key: 'avg_practical', label: 'Practical Experience' },
              { key: 'avg_communication', label: 'Communication' },
              { key: 'avg_overall', label: 'Overall Readiness' },
            ]
            const industryOptions = [...new Set(allFeedback.map(f => f.industry).filter(Boolean))]
            const empYearOptions = [...new Set(allFeedback.map(f => f.feedback_year).filter(Boolean))].sort()
            const filteredFb = allFeedback.filter(f => {
              if (empIndustry && f.industry !== empIndustry) return false
              if (empYear && String(f.feedback_year) !== empYear) return false
              if (empSentiment && f.job_readiness_sentiment !== empSentiment) return false
              return true
            })

            return (
              <>
                <StatGroup
                  earnings6yr={rd.earnings_6yr_median}
                  earnings10yr={rd.earnings_10yr_median}
                  graduationRate={rd.graduation_rate}
                  retentionRate={rd.retention_rate}
                  employmentRate={od.employment_rate}
                />

                {!hasData && ed.total_feedback === 0 ? (
                  <Card className="p-6 text-center">
                    <BarChart3 size={32} className="text-student-text/30 mx-auto mb-3" />
                    <p className="text-sm text-student-text">Outcomes data is not yet available for this program.</p>
                    <p className="text-xs text-student-text/60 mt-1">Check back later or contact the program directly.</p>
                  </Card>
                ) : (
                  <>
                    {salary && (
                      <Card className="p-5">
                        <div className="flex items-center gap-2 mb-3">
                          <DollarSign size={14} className="text-emerald-600" />
                          <h3 className="font-semibold text-student-ink">Salary Distribution</h3>
                        </div>
                        <div className="flex items-end justify-between mb-2">
                          <div className="text-center flex-1">
                            <p className="text-xs text-student-text/60">25th %ile</p>
                            <p className="text-sm font-medium text-student-ink">{salaryLow ? formatCurrency(salaryLow) : '—'}</p>
                          </div>
                          <div className="text-center flex-1">
                            <p className="text-xs text-student-text/60">Median</p>
                            <p className="text-2xl font-bold text-emerald-700">{formatCurrency(salary)}</p>
                          </div>
                          <div className="text-center flex-1">
                            <p className="text-xs text-student-text/60">75th %ile</p>
                            <p className="text-sm font-medium text-student-ink">{salaryHigh ? formatCurrency(salaryHigh) : '—'}</p>
                          </div>
                        </div>
                        <div className="relative h-2 bg-slate-100 rounded-full mt-3">
                          <div className="absolute h-full bg-emerald-200 rounded-full" style={{ left: '15%', width: '70%' }} />
                          <div className="absolute h-full bg-emerald-500 rounded-full" style={{ left: '40%', width: '20%' }} />
                        </div>
                      </Card>
                    )}

                    {(empRate || internRate) && (
                      <Card className="p-5">
                        <div className="flex items-center gap-2 mb-3">
                          <Briefcase size={14} className="text-student" />
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
                          <Building2 size={14} className="text-student" />
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
                          <Users size={14} className="text-student" />
                          <h3 className="font-semibold text-student-ink">Industry Placement</h3>
                        </div>
                        <div className="flex flex-wrap gap-2">
                          {topIndustries.map((ind: string) => <Badge key={ind} variant="info" size="sm">{ind}</Badge>)}
                        </div>
                      </Card>
                    )}

                    {/* Employer feedback section (merged from old Employer Insights tab) */}
                    {ed.total_feedback > 0 && (
                      <>
                        <div className="border-t border-divider pt-4 mt-2">
                          <h3 className="text-sm font-semibold text-student-ink mb-3">Employer Feedback ({ed.total_feedback})</h3>
                          <div className="flex flex-wrap gap-2 mb-3">
                            <select value={empIndustry} onChange={e => setEmpIndustry(e.target.value)} className="text-xs border border-stone rounded-lg px-2 py-1.5 bg-white">
                              <option value="">All Industries</option>
                              {industryOptions.map(i => <option key={i} value={i}>{i}</option>)}
                            </select>
                            <select value={empYear} onChange={e => setEmpYear(e.target.value)} className="text-xs border border-stone rounded-lg px-2 py-1.5 bg-white">
                              <option value="">All Years</option>
                              {empYearOptions.map(y => <option key={y} value={String(y)}>{y}</option>)}
                            </select>
                            <select value={empSentiment} onChange={e => setEmpSentiment(e.target.value)} className="text-xs border border-stone rounded-lg px-2 py-1.5 bg-white">
                              <option value="">All Sentiments</option>
                              <option value="positive">Positive</option>
                              <option value="neutral">Neutral</option>
                              <option value="negative">Negative</option>
                            </select>
                          </div>
                        </div>

                        {totalSent > 0 && (
                          <Card className="p-5">
                            <div className="flex items-center gap-2 mb-3">
                              <TrendingUp size={14} className="text-student" />
                              <h3 className="font-semibold text-student-ink">Job Readiness Sentiment</h3>
                            </div>
                            <div className="flex gap-3">
                              {['positive', 'neutral', 'negative'].map(s => {
                                const count = sentiments[s] || 0
                                const pct = totalSent > 0 ? Math.round((count / totalSent) * 100) : 0
                                const color = s === 'positive' ? 'bg-emerald-400' : s === 'neutral' ? 'bg-amber-400' : 'bg-red-400'
                                return (
                                  <div key={s} className="flex-1 text-center">
                                    <div className="h-20 bg-slate-100 rounded-lg flex items-end overflow-hidden">
                                      <div className={`w-full ${color} rounded-lg transition-all`} style={{ height: `${Math.max(pct, 5)}%` }} />
                                    </div>
                                    <p className="text-xs font-medium mt-1 capitalize">{s}</p>
                                    <p className="text-[10px] text-student-text/60">{pct}% ({count})</p>
                                  </div>
                                )
                              })}
                            </div>
                          </Card>
                        )}

                        <Card className="p-5">
                          <div className="flex items-center gap-2 mb-3">
                            <BarChart3 size={14} className="text-student" />
                            <h3 className="font-semibold text-student-ink">Skills Assessment</h3>
                          </div>
                          <div className="space-y-2">
                            {dims.map(d => {
                              const val: number | null = (ed as any)[d.key]
                              if (val == null) return null
                              return (
                                <div key={d.key} className="flex items-center gap-3">
                                  <span className="text-xs text-student-text w-32">{d.label}</span>
                                  <div className="flex-1 h-2 bg-slate-100 rounded-full overflow-hidden">
                                    <div className="h-full bg-student rounded-full" style={{ width: `${(val / 5) * 100}%` }} />
                                  </div>
                                  <span className="text-xs font-medium text-student-ink w-8 text-right">{val.toFixed(1)}</span>
                                </div>
                              )
                            })}
                          </div>
                        </Card>

                        <div className="space-y-3">
                          {filteredFb.map((fb: any) => (
                            <Card key={fb.id} className="p-4">
                              <div className="flex items-center justify-between mb-2">
                                <div>
                                  <p className="text-sm font-medium text-student-ink">{fb.employer_name}</p>
                                  <div className="flex items-center gap-2 mt-0.5">
                                    {fb.industry && <Badge variant="info" size="sm">{fb.industry}</Badge>}
                                    {fb.feedback_year && <span className="text-[10px] text-student-text/60">{fb.feedback_year}</span>}
                                  </div>
                                </div>
                                {fb.job_readiness_sentiment && (
                                  <Badge
                                    variant={fb.job_readiness_sentiment === 'positive' ? 'success' : fb.job_readiness_sentiment === 'negative' ? 'danger' : 'warning'}
                                    size="sm"
                                  >
                                    {fb.job_readiness_sentiment}
                                  </Badge>
                                )}
                              </div>
                              {fb.feedback_text && <p className="text-sm text-student-text mt-2">{fb.feedback_text}</p>}
                              {fb.hiring_pattern && (
                                <p className="text-xs text-student/70 mt-2 bg-student-mist rounded px-2 py-1">
                                  <Briefcase size={10} className="inline mr-1" />{fb.hiring_pattern}
                                </p>
                              )}
                            </Card>
                          ))}
                        </div>
                      </>
                    )}
                  </>
                )}
              </>
            )
          })()}

          {tab === 'reviews' && (() => {
            const reviewData = reviewsData || { total_reviews: 0, reviews: [] }
            const allReviews: any[] = reviewData.reviews || []
            const dims: { key: string; label: string }[] = [
              { key: 'avg_teaching', label: 'Teaching Quality' },
              { key: 'avg_workload', label: 'Workload' },
              { key: 'avg_career_support', label: 'Career Support' },
              { key: 'avg_roi', label: 'Return on Investment' },
              { key: 'avg_overall', label: 'Overall' },
            ]
            const degreeOptions = [...new Set(allReviews.map(r => r.reviewer_context?.degree).filter(Boolean))]
            const yearOptions = [...new Set(allReviews.map(r => r.reviewer_context?.graduation_year || r.reviewer_context?.cohort_year).filter(Boolean))].sort()
            const filtered = allReviews.filter(r => {
              if (reviewDegree && r.reviewer_context?.degree !== reviewDegree) return false
              const ry = r.reviewer_context?.graduation_year || r.reviewer_context?.cohort_year
              if (reviewYear && String(ry) !== reviewYear) return false
              if (reviewMinRating && (r.rating_overall || 0) < Number(reviewMinRating)) return false
              return true
            })

            return (
              <>
                {allReviews.length > 0 && (
                  <div className="flex flex-wrap gap-2 mb-2">
                    <select value={reviewDegree} onChange={e => setReviewDegree(e.target.value)} className="text-xs border border-stone rounded-lg px-2 py-1.5 bg-white">
                      <option value="">All Degrees</option>
                      {degreeOptions.map(d => <option key={d} value={d}>{d}</option>)}
                    </select>
                    <select value={reviewYear} onChange={e => setReviewYear(e.target.value)} className="text-xs border border-stone rounded-lg px-2 py-1.5 bg-white">
                      <option value="">All Cohorts</option>
                      {yearOptions.map(y => <option key={y} value={String(y)}>{y}</option>)}
                    </select>
                    <select value={reviewMinRating} onChange={e => setReviewMinRating(e.target.value)} className="text-xs border border-stone rounded-lg px-2 py-1.5 bg-white">
                      <option value="">Any Rating</option>
                      <option value="4">4+ Stars</option>
                      <option value="3">3+ Stars</option>
                      <option value="2">2+ Stars</option>
                    </select>
                    {(reviewDegree || reviewYear || reviewMinRating) && (
                      <button onClick={() => { setReviewDegree(''); setReviewYear(''); setReviewMinRating('') }} className="text-xs text-student-text/60 hover:text-student-ink">Clear</button>
                    )}
                  </div>
                )}

                {reviewData.total_reviews > 0 && (
                  <Card className="p-5">
                    <div className="flex items-center gap-2 mb-3">
                      <Star size={14} className="text-amber-500 fill-amber-500" />
                      <h3 className="font-semibold text-student-ink">Rating Summary</h3>
                      <span className="text-xs text-student-text/60">{reviewData.total_reviews} review{reviewData.total_reviews !== 1 ? 's' : ''}</span>
                    </div>
                    <div className="space-y-2">
                      {dims.map(d => {
                        const val: number | null = (reviewData as any)[d.key]
                        if (val == null) return null
                        return (
                          <div key={d.key} className="flex items-center gap-3">
                            <span className="text-xs text-student-text w-28">{d.label}</span>
                            <div className="flex-1 h-2 bg-slate-100 rounded-full overflow-hidden">
                              <div className="h-full bg-amber-400 rounded-full" style={{ width: `${(val / 5) * 100}%` }} />
                            </div>
                            <span className="text-xs font-medium text-student-ink w-8 text-right">{val.toFixed(1)}</span>
                          </div>
                        )
                      })}
                    </div>
                  </Card>
                )}

                {filtered.length > 0 ? (
                  <div className="space-y-3">
                    {filtered.map((r: any) => (
                      <Card key={r.id} className="p-4">
                        <div className="flex items-center justify-between mb-2">
                          <div className="flex items-center gap-2">
                            {r.rating_overall && (
                              <div className="flex items-center gap-0.5">
                                {Array.from({ length: 5 }).map((_, i) => (
                                  <Star key={i} size={12} className={i < r.rating_overall ? 'text-amber-400 fill-amber-400' : 'text-slate-200'} />
                                ))}
                              </div>
                            )}
                            {r.is_verified && <Badge variant="success" size="sm">Verified</Badge>}
                          </div>
                          <span className="text-[10px] text-student-text/60">{formatDate(r.created_at)}</span>
                        </div>
                        {r.reviewer_context && (
                          <div className="flex flex-wrap gap-1.5 mb-2">
                            {Object.entries(r.reviewer_context).map(([k, v]) => (
                              <Badge key={k} variant="neutral" size="sm">{String(v)}</Badge>
                            ))}
                          </div>
                        )}
                        {r.review_text && <p className="text-sm text-student-text mb-2">{r.review_text}</p>}
                        {r.who_thrives_here && (
                          <div className="bg-student-mist rounded-lg p-3 mt-2">
                            <div className="flex items-center gap-1.5 mb-1">
                              <Quote size={12} className="text-student" />
                              <span className="text-xs font-medium text-student">Who thrives here</span>
                            </div>
                            <p className="text-xs text-student-text">{r.who_thrives_here}</p>
                          </div>
                        )}
                      </Card>
                    ))}
                  </div>
                ) : (
                  <>
                    {/* Compact empty state with a CTA */}
                    <Card className="p-5">
                      <div className="flex items-start gap-3">
                        <div className="w-10 h-10 rounded-lg bg-amber-50 flex items-center justify-center flex-shrink-0">
                          <Star size={18} className="text-amber-500" />
                        </div>
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-semibold text-student-ink">Be the first to review {p.program_name}</p>
                          <p className="text-xs text-student-text mt-0.5">
                            Help future students — share what it's like to study here. Reviews stay anonymous unless you opt in.
                          </p>
                        </div>
                        <button
                          onClick={() => navigate(`/s?prefill=${encodeURIComponent(`I'd like to write a review for ${p.program_name} at ${instName}. Help me structure it.`)}`)}
                          className="flex-shrink-0 px-3 py-1.5 text-xs font-semibold bg-student text-white rounded-lg hover:bg-student-hover transition-colors"
                        >
                          Write a review
                        </button>
                      </div>
                    </Card>

                    {/* In the meantime: show outcomes + employer signals as proxy "quality signals" */}
                    {(p.outcomes_data?.median_salary || p.outcomes_data?.employment_rate || rd.graduation_rate) && (
                      <Card className="p-5">
                        <div className="flex items-center gap-2 mb-3">
                          <BarChart3 size={14} className="text-student" />
                          <h3 className="font-semibold text-student-ink">Quality Signals</h3>
                          <span className="text-[11px] text-student-text/60">in lieu of reviews</span>
                        </div>
                        <p className="text-xs text-student-text mb-3">
                          Until students share firsthand, these outcome signals give a sense of the program's track record.
                        </p>
                        <ul className="space-y-2 text-sm text-student-text">
                          {rd.graduation_rate && (
                            <li className="flex items-start gap-2">
                              <span className="w-1 h-1 rounded-full bg-student mt-2 flex-shrink-0" />
                              <span><strong className="text-student-ink">{Math.round(rd.graduation_rate * 100)}%</strong> of students complete their degree — {rd.graduation_rate > 0.85 ? 'well above' : rd.graduation_rate > 0.7 ? 'in line with' : 'below'} the national average.</span>
                            </li>
                          )}
                          {rd.retention_rate && (
                            <li className="flex items-start gap-2">
                              <span className="w-1 h-1 rounded-full bg-student mt-2 flex-shrink-0" />
                              <span><strong className="text-student-ink">{Math.round(rd.retention_rate * 100)}%</strong> first-year retention — students return for sophomore year.</span>
                            </li>
                          )}
                          {rd.earnings_10yr_median && (
                            <li className="flex items-start gap-2">
                              <span className="w-1 h-1 rounded-full bg-student mt-2 flex-shrink-0" />
                              <span>Graduates earn a median <strong className="text-student-ink">{formatCurrency(rd.earnings_10yr_median)}</strong> 10 years after enrollment.</span>
                            </li>
                          )}
                        </ul>
                      </Card>
                    )}

                    {/* Similar programs — let students explore alternatives that may have reviews */}
                    {similar.length > 0 && (
                      <Card className="p-5">
                        <div className="flex items-center gap-2 mb-3">
                          <Sparkles size={14} className="text-gold" />
                          <h3 className="font-semibold text-student-ink">See reviews for similar programs</h3>
                        </div>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                          {similar.slice(0, 4).map((sp: any) => (
                            <button
                              key={sp.id}
                              onClick={() => navigate(`/s/programs/${sp.id}`)}
                              className="flex items-center justify-between gap-2 px-3 py-2.5 rounded-lg border border-divider hover:border-student hover:bg-student-mist transition-colors text-left"
                            >
                              <div className="min-w-0">
                                <p className="text-sm font-medium text-student-ink truncate">{sp.program_name}</p>
                                <p className="text-[11px] text-student-text/70 truncate">{sp.institution_name}</p>
                              </div>
                              <Star size={12} className="text-student-text/40 flex-shrink-0" />
                            </button>
                          ))}
                        </div>
                      </Card>
                    )}
                  </>
                )}
              </>
            )
          })()}
        </div>

        {/* Sidebar */}
        <div className="lg:sticky lg:top-4 lg:self-start">
          <RelatedSidebar
            events={eventsList}
            sameSchoolPrograms={sameSchool}
            similarPrograms={similar}
            onRsvp={(id) => rsvpMut.mutate(id)}
            rsvpedIds={rsvpSet}
          />
        </div>
      </div>

      {/* ── Match modal ── */}
      {match && matchModalOpen && (
        <Modal isOpen={matchModalOpen} onClose={() => setMatchModalOpen(false)} title="Match Analysis">
          <div className="space-y-4">
            <MatchRing score={match.match_score} tier={match.match_tier} size={100} />
            {match.score_breakdown && Object.entries(match.score_breakdown).map(([k, v]) => (
              <div key={k}>
                <div className="flex justify-between text-sm mb-1">
                  <span className="capitalize text-student-ink">{k.replace(/_/g, ' ')}</span>
                  <span className="font-medium">{formatScore(v as number)}</span>
                </div>
                <ProgressBar value={(v as number) * 100} />
              </div>
            ))}
            {match.reasoning_text && (
              <div>
                <h3 className="font-medium text-sm mb-2">Why this match?</h3>
                <p className="text-sm text-student-text whitespace-pre-wrap">{match.reasoning_text}</p>
              </div>
            )}
            <div className="border-t pt-3 flex justify-end">
              <Button size="sm" variant="secondary" onClick={() => { setMatchModalOpen(false); navigate('/s?prefill=' + encodeURIComponent(`Help me understand my match with ${p.program_name}`)) }}>
                <MessageSquare size={14} className="mr-1" /> Ask Counselor
              </Button>
            </div>
          </div>
        </Modal>
      )}
    </div>
  )
}
