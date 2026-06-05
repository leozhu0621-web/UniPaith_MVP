import { Fragment, useState } from 'react'
import { useParams, Link, useSearchParams } from 'react-router-dom'
import { useQuery, useMutation } from '@tanstack/react-query'
import {
  GraduationCap, DollarSign, CalendarDays,
  Globe, ExternalLink, BookOpen, CheckCircle2, Sparkles,
  Briefcase, TrendingUp, Trophy, Bookmark, Send,
} from 'lucide-react'
import { getProgram } from '../../api/programs'
import { getPublicInstitution, submitInquiry } from '../../api/institutions'
import { listEvents } from '../../api/events'
import Card from '../../components/ui/Card'
import Badge from '../../components/ui/Badge'
import Button from '../../components/ui/Button'
import Modal from '../../components/ui/Modal'
import Input from '../../components/ui/Input'
import Textarea from '../../components/ui/Textarea'
import Tabs from '../../components/ui/Tabs'
import Skeleton from '../../components/ui/Skeleton'
import EmptyState from '../../components/ui/EmptyState'
import QueryError from '../../components/ui/QueryError'
import { showToast } from '../../stores/toast-store'
import { useAuthStore } from '../../stores/auth-store'
import { formatCurrency, formatDate, formatPercent } from '../../utils/format'
import { DEGREE_LABELS, DELIVERY_FORMAT_LABELS, CAMPUS_SETTING_LABELS } from '../../utils/constants'
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
import type { Program, Institution, EventItem } from '../../types'

export default function ProgramDetailPage() {
  const { programId } = useParams<{ programId: string }>()
  const [searchParams] = useSearchParams()
  // When a logged-in student lands on this public page, point Apply/Save at the
  // real in-app program page (where the actual save/apply actions live) rather
  // than the signup/login CTAs meant for anonymous visitors.
  const isStudent = useAuthStore(s => s.isAuthenticated && s.user?.role === 'student')
  const [tab, setTab] = useState('overview')
  const [showInquiryModal, setShowInquiryModal] = useState(false)
  const [inquirySubject, setInquirySubject] = useState('')
  const [inquiryMessage, setInquiryMessage] = useState('')

  const inquiryMut = useMutation({
    mutationFn: (payload: { institution_id: string; program_id?: string; subject: string; message: string; campaign_id?: string }) =>
      submitInquiry(payload),
    onSuccess: () => {
      showToast('Inquiry sent! The institution will respond soon.', 'success')
      setShowInquiryModal(false)
      setInquirySubject('')
      setInquiryMessage('')
    },
    onError: () => showToast('Please sign in as a student to send inquiries.', 'warning'),
  })

  const programQ = useQuery({
    queryKey: ['public-program', programId],
    queryFn: () => getProgram(programId!),
    enabled: !!programId,
  })

  const p: Program | undefined = programQ.data

  const instQ = useQuery({
    queryKey: ['public-institution', p?.institution_id],
    queryFn: () => getPublicInstitution(p!.institution_id),
    enabled: !!p?.institution_id,
  })

  const eventsQ = useQuery({
    queryKey: ['public-program-events', programId],
    queryFn: () => listEvents({ program_id: programId, limit: 10 }),
    enabled: !!programId,
  })

  const inst: Institution | undefined = instQ.data
  const events: EventItem[] = Array.isArray(eventsQ.data) ? eventsQ.data : []

  // Spec 23 → Spec 11 bridge (same helpers as the authenticated student page).
  const cd = normalizeCostData(p?.cost_data)
  const odn = normalizeOutcomes(p?.outcomes_data)
  const tracksMeta = extractTracksMeta(p?.tracks)
  const appMaterials = normalizeRequirements(p?.application_requirements)
  const prerequisites = extractPrerequisites(p?.application_requirements)
  const testPolicy = extractTestPolicy(p?.application_requirements)
  const recommendations = extractRecommendations(p?.application_requirements)
  const fundingSignals = extractFundingSignals(p?.cost_data)
  const salaryBands = extractSalaryBands(p?.outcomes_data)
  const admissionTimeline = intakeTimelineFromArray(p?.intake_rounds)
  const effectiveDeadline = p?.application_deadline ?? intakeDeadlineFromArray(p?.intake_rounds)
  const effectiveTuition = p?.tuition ?? cd.tuition_annual ?? null
  const highlights: string[] = Array.isArray(p?.highlights) ? p.highlights : []
  const faculty: Record<string, any>[] = Array.isArray(p?.faculty_contacts) ? p.faculty_contacts : []
  const costBandMin = cd.estimated_total_cost_band?.min != null ? Number(cd.estimated_total_cost_band.min) : null
  const costBandMax = cd.estimated_total_cost_band?.max != null ? Number(cd.estimated_total_cost_band.max) : cd.total_cost_attendance != null ? Number(cd.total_cost_attendance) : null

  const tabs = [
    { id: 'overview', label: 'Overview' },
    { id: 'admissions', label: 'Admissions' },
    { id: 'costs', label: 'Costs & Aid' },
    { id: 'outcomes', label: 'Outcomes' },
    ...(events.length > 0 ? [{ id: 'events', label: `Events (${events.length})` }] : []),
  ]

  if (programQ.isLoading) {
    return (
      <div className="max-w-5xl w-full mx-auto px-6 py-10 space-y-6">
        <Skeleton className="h-10 w-96" />
        <Skeleton className="h-6 w-64" />
        <div className="grid grid-cols-3 gap-4">{Array.from({ length: 3 }).map((_, i) => <Skeleton key={i} className="h-24" />)}</div>
      </div>
    )
  }

  // A failed fetch (network / 5xx) is distinct from a genuine 404 — offer a retry
  // instead of telling the visitor the program doesn't exist.
  if (programQ.isError) {
    return (
      <div className="max-w-5xl w-full mx-auto px-6 py-16">
        <QueryError detail="We couldn't load this program." onRetry={() => programQ.refetch()} />
        <div className="text-center mt-4">
          <Link to="/browse" className="text-secondary hover:underline">Browse programs</Link>
        </div>
      </div>
    )
  }

  if (!p) {
    return (
      <div className="max-w-5xl w-full mx-auto px-6 py-16 text-center">
        <GraduationCap size={48} className="mx-auto text-foreground/30 mb-4" />
        <h2 className="text-xl font-semibold text-foreground mb-2">Program not found</h2>
        <p className="text-foreground/70 mb-6">This program may not be published or the link is incorrect.</p>
        <Link to="/browse" className="text-secondary hover:underline">Browse programs</Link>
      </div>
    )
  }

  const hasAdmissions =
    appMaterials.length > 0 ||
    prerequisites.length > 0 ||
    !!testPolicy ||
    !!recommendations ||
    !!admissionTimeline ||
    !!effectiveDeadline ||
    (p.requirements && Object.keys(p.requirements).length > 0)

  const hasOutcomes =
    odn.median_salary != null ||
    odn.employment_rate != null ||
    odn.internship_conversion_rate != null ||
    (odn.top_employers?.length ?? 0) > 0 ||
    (odn.top_industries?.length ?? 0) > 0 ||
    salaryBands.length > 0

  // ── Hero (mirrors InstitutionDetail / SchoolSubunitPage) ──────────────────
  // A program has no photo of its own — inherit the parent institution's campus
  // photo (first raster image in the gallery; logos are SVG → skipped). Falls
  // back to a clean gradient. No logo, no geo.
  const heroPhoto = (inst?.media_gallery ?? []).find(u => /\.(jpe?g|png|webp|avif)(\?|$)/i.test(u)) ?? null
  // Eyebrow: a full degree label ("Master's program"), else the institution name.
  const degreeEyebrow = DEGREE_EYEBROW[p.degree_type] ?? (inst?.name ? inst.name : null)
  // Median earnings: prefer a 10-yr earnings figure if the program published one,
  // else fall back to the normalized median (starting) salary.
  const rawOutcomes = (p.outcomes_data && typeof p.outcomes_data === 'object' ? p.outcomes_data : {}) as Record<string, any>
  const medianEarnings =
    num(rawOutcomes.median_earnings_10yr) ??
    num(rawOutcomes.median_earnings) ??
    (odn.median_salary != null ? Number(odn.median_salary) : null)
  // A single program ranking, if one is published in cost/outcomes blobs.
  const programRanking = extractRanking(rawOutcomes) ?? extractRanking(cd)
  // The source string the institution attached to its outcomes blob (cited, never invented).
  const outcomesSource: string | null =
    typeof rawOutcomes.source === 'string' && rawOutcomes.source.trim()
      ? rawOutcomes.source.trim()
      : typeof rawOutcomes.data_source === 'string' && rawOutcomes.data_source.trim()
        ? rawOutcomes.data_source.trim()
        : null

  // Headline stat strip — REAL fields only, no geo. The institution name is a
  // separate clickable link rendered after the strip.
  const heroStats: { value: string; label: string }[] = []
  if (p.acceptance_rate != null) heroStats.push({ value: formatPercent(p.acceptance_rate, p.acceptance_rate < 0.1 ? 1 : 0), label: 'acceptance' })
  if (effectiveTuition != null) heroStats.push({ value: formatCurrency(effectiveTuition), label: 'tuition' })
  if (medianEarnings != null) heroStats.push({ value: formatCurrency(medianEarnings), label: 'median earnings' })
  if (p.duration_months != null) heroStats.push({ value: `${p.duration_months} mo`, label: 'duration' })

  // Report-card "at a glance" row for the Overview tab — same shape as InstitutionDetail.
  const keyStats: { value: string; label: string; hint?: string }[] = []
  if (p.acceptance_rate != null) keyStats.push({ value: formatPercent(p.acceptance_rate, p.acceptance_rate < 0.1 ? 1 : 0), label: 'Acceptance rate' })
  if (effectiveTuition != null) keyStats.push({ value: formatCurrency(effectiveTuition), label: 'Tuition', hint: 'per year' })
  if (medianEarnings != null) keyStats.push({ value: formatCurrency(medianEarnings), label: 'Median earnings', hint: rawOutcomes.median_earnings_10yr != null ? '10 yrs after entry' : 'starting salary' })
  if (odn.employment_rate != null) keyStats.push({ value: formatPercent(Number(odn.employment_rate), 0), label: 'Employment rate' })

  // Primary/secondary action targets — students go to the real in-app program page.
  const primaryHref = isStudent ? `/s/programs/${p.id}` : '/signup?role=student'
  const saveHref = isStudent ? `/s/programs/${p.id}` : '/login'

  return (
    <>
      <div className="max-w-5xl w-full mx-auto px-6 py-8">
        {/* Breadcrumb — text-driven, no back-arrow (mirrors the school pages). */}
        <nav className="flex items-center gap-1.5 text-[13px] text-muted-foreground mb-4 flex-wrap" aria-label="Breadcrumb">
          <Link to="/" className="hover:text-secondary transition-colors">Home</Link>
          <span className="text-border" aria-hidden="true">·</span>
          <Link to="/browse" className="hover:text-secondary transition-colors">Browse</Link>
          {inst && (
            <>
              <span className="text-border" aria-hidden="true">·</span>
              <Link to={`/school/${p.institution_id}`} className="hover:text-secondary transition-colors truncate max-w-[24ch]">{inst.name}</Link>
            </>
          )}
          <span className="text-border" aria-hidden="true">·</span>
          <span className="text-foreground font-medium truncate max-w-[32ch]" aria-current="page">{p.program_name}</span>
        </nav>

        {/* Hero — parent campus photo fading into the cream page background. No logo, no geo. */}
        <div className="relative rounded-xl overflow-hidden border border-border mb-5 bg-background">
          {/* Photo banner */}
          <div className="relative h-44 sm:h-56 md:h-64">
            {heroPhoto ? (
              <img src={heroPhoto} alt="" aria-hidden="true" className="absolute inset-0 h-full w-full object-cover" />
            ) : (
              <div className="absolute inset-0 bg-gradient-to-br from-secondary/15 via-muted to-background" />
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
          <div className="relative -mt-16 px-5 sm:px-7 pb-6">
            {degreeEyebrow && <p className="text-eyebrow uppercase text-secondary mb-1.5">{degreeEyebrow}</p>}
            <h1 className="text-2xl sm:text-3xl md:text-[2.5rem] font-bold text-foreground leading-[1.08] tracking-tight max-w-[24ch]">
              {p.program_name}
            </h1>
            {p.department && <p className="text-[13px] text-muted-foreground mt-1">{p.department}</p>}

            {/* Headline stats — no location, per the page spec. */}
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

            {/* Parent institution link + website (Spec 22 §3). */}
            {(inst || effectiveDeadline) && (
              <div className="flex items-center gap-4 mt-2.5 text-[12px] flex-wrap">
                {inst && (
                  <Link to={`/school/${p.institution_id}`} className="inline-flex items-center gap-1 text-secondary hover:underline">
                    <GraduationCap size={12} /> {inst.name}
                  </Link>
                )}
                {inst?.website_url && (
                  <a href={inst.website_url} target="_blank" rel="noopener noreferrer" className="inline-flex items-center gap-1 text-secondary hover:underline">
                    <Globe size={12} /> Website <ExternalLink size={11} />
                  </a>
                )}
                {effectiveDeadline && (
                  <span className="inline-flex items-center gap-1 text-warning font-medium">
                    <CalendarDays size={12} /> Deadline {formatDate(effectiveDeadline)}
                  </span>
                )}
              </div>
            )}

            {/* Actions — primary Apply, then Save / Request info / See-your-match. */}
            <div className="flex flex-wrap items-center gap-2 mt-4">
              <Link to={primaryHref}>
                <Button size="sm">{isStudent ? 'Apply now' : 'Apply now'}</Button>
              </Link>
              <Link to={saveHref}>
                <Button size="sm" variant="tertiary">
                  <Bookmark size={14} className="mr-1.5" /> {isStudent ? 'Save program' : 'Sign in to save'}
                </Button>
              </Link>
              <Button size="sm" variant="tertiary" onClick={() => setShowInquiryModal(true)}>
                <Send size={14} className="mr-1.5" /> Request info
              </Button>
              <Link to={isStudent ? `/s/programs/${p.id}` : '/login'}>
                <Button size="sm" variant="ghost">
                  <Sparkles size={14} className="mr-1.5" /> {isStudent ? 'See your match' : 'Sign in to see your match'}
                </Button>
              </Link>
            </div>
          </div>
        </div>

        <Tabs tabs={tabs} activeTab={tab} onChange={setTab} />

        <div className="mt-6">
          {tab === 'overview' && (
            <div className="space-y-6">
              {/* Report card — the Niche-style "at a glance" stats, real data only. */}
              {keyStats.length > 0 && (
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                  {keyStats.map(s => (
                    <Card key={s.label} className="p-4">
                      <p className="text-[1.9rem] leading-none font-bold text-foreground tracking-tight tabular-nums">{s.value}</p>
                      <p className="text-[12px] font-medium text-foreground/80 mt-2">{s.label}</p>
                      {s.hint && <p className="text-[10.5px] text-muted-foreground/70 mt-0.5">{s.hint}</p>}
                    </Card>
                  ))}
                </div>
              )}

              {programRanking && (
                <Card className="p-5">
                  <h2 className="font-semibold text-foreground mb-3 flex items-center gap-2"><Trophy size={15} className="text-secondary" /> Ranking</h2>
                  <div className="flex items-baseline gap-3">
                    <span className="text-2xl font-bold text-foreground tabular-nums leading-none">#{programRanking.rank}</span>
                    <span className="text-sm text-muted-foreground">{programRanking.label}{programRanking.year ? ` · ${programRanking.year}` : ''}</span>
                  </div>
                </Card>
              )}

              {p.description_text && (
                <Card className="p-5">
                  <h2 className="font-semibold text-foreground mb-2">About this program</h2>
                  <p className="text-sm text-muted-foreground leading-relaxed whitespace-pre-wrap">{p.description_text}</p>
                </Card>
              )}

              {p.who_its_for && (
                <Card className="p-5">
                  <h2 className="font-semibold text-foreground mb-2">Who it&apos;s for</h2>
                  <p className="text-sm text-foreground whitespace-pre-wrap">{p.who_its_for}</p>
                </Card>
              )}

              {(tracksMeta.concentrations.length > 0 || tracksMeta.note || tracksMeta.learning_format) && (
                <Card className="p-5">
                  <h2 className="font-semibold text-foreground mb-3">Tracks & Structure</h2>
                  {tracksMeta.concentrations.length > 0 && (
                    <div className="flex flex-wrap gap-2 mb-3">
                      {tracksMeta.concentrations.map((t, i) => (
                        <Badge key={i} variant="info">{t}</Badge>
                      ))}
                    </div>
                  )}
                  {tracksMeta.note && <p className="text-sm text-foreground mb-2">{tracksMeta.note}</p>}
                  {tracksMeta.learning_format && (
                    <p className="text-sm text-foreground"><span className="font-semibold text-foreground">Learning format:</span> {tracksMeta.learning_format}</p>
                  )}
                </Card>
              )}

              {highlights.length > 0 && (
                <Card className="p-5">
                  <h2 className="font-semibold text-foreground mb-3">Highlights</h2>
                  <ul className="space-y-2">
                    {highlights.map((h, i) => (
                      <li key={i} className="flex items-start gap-2 text-sm text-foreground">
                        <CheckCircle2 size={16} className="text-secondary mt-0.5 shrink-0" />
                        {h}
                      </li>
                    ))}
                  </ul>
                </Card>
              )}

              {faculty.length > 0 && (
                <Card className="p-5">
                  <h2 className="font-semibold text-foreground mb-3">Faculty Contacts</h2>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    {faculty.map((f, i) => (
                      <div key={i} className="flex items-center gap-3 p-3 rounded-lg bg-muted/50">
                        <div className="w-9 h-9 rounded-full bg-secondary/10 flex items-center justify-center text-sm font-medium text-secondary">
                          {String(f.name ?? '?').trim()[0]?.toUpperCase() ?? '?'}
                        </div>
                        <div className="min-w-0">
                          <p className="text-sm font-medium text-foreground truncate">{f.name}</p>
                          {f.role && <p className="text-xs text-foreground/70">{f.role}</p>}
                        </div>
                      </div>
                    ))}
                  </div>
                </Card>
              )}

              <Card className="p-5">
                <h2 className="font-semibold text-foreground mb-3">Quick Facts</h2>
                <div className="grid grid-cols-2 md:grid-cols-3 gap-4 text-sm">
                  <div><span className="text-foreground/70">Degree:</span> <span className="font-medium">{DEGREE_LABELS[p.degree_type] || p.degree_type}</span></div>
                  {p.duration_months && <div><span className="text-foreground/70">Duration:</span> <span className="font-medium">{p.duration_months} months</span></div>}
                  {p.delivery_format && <div><span className="text-foreground/70">Format:</span> <span className="font-medium">{DELIVERY_FORMAT_LABELS[p.delivery_format] ?? p.delivery_format}</span></div>}
                  {p.campus_setting && <div><span className="text-foreground/70">Setting:</span> <span className="font-medium">{CAMPUS_SETTING_LABELS[p.campus_setting] ?? p.campus_setting}</span></div>}
                  {p.program_start_date && <div><span className="text-foreground/70">Start Date:</span> <span className="font-medium">{formatDate(p.program_start_date)}</span></div>}
                  {effectiveDeadline && <div><span className="text-foreground/70">Deadline:</span> <span className="font-medium">{formatDate(effectiveDeadline)}</span></div>}
                </div>
              </Card>
            </div>
          )}

          {tab === 'admissions' && (
            <div className="space-y-6">
              {(effectiveDeadline || p.program_start_date) && (
                <Card className="p-5">
                  <h2 className="font-semibold text-foreground mb-3">Key Dates</h2>
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    {effectiveDeadline && (
                      <div className="flex items-center gap-2">
                        <CalendarDays size={16} className="text-warning" />
                        <div><span className="text-foreground/70">Deadline:</span> <span className="font-medium">{formatDate(effectiveDeadline)}</span></div>
                      </div>
                    )}
                    {p.program_start_date && (
                      <div className="flex items-center gap-2">
                        <CalendarDays size={16} className="text-secondary" />
                        <div><span className="text-foreground/70">Start Date:</span> <span className="font-medium">{formatDate(p.program_start_date)}</span></div>
                      </div>
                    )}
                  </div>
                </Card>
              )}

              {appMaterials.length > 0 && (
                <Card className="p-5">
                  <h2 className="font-semibold text-foreground mb-3">Application Materials</h2>
                  <ul className="space-y-2">
                    {appMaterials.map((req, i) => (
                      <li key={i} className="flex items-start gap-2 text-sm">
                        <CheckCircle2 size={16} className={`mt-0.5 shrink-0 ${req.required !== false ? 'text-secondary' : 'text-foreground/30'}`} />
                        <div>
                          <span className="text-foreground">{req.label}</span>
                          {req.required !== false && <Badge variant="warning" className="ml-2 text-[10px]">Required</Badge>}
                          {req.note && <p className="text-xs text-foreground/60 mt-0.5">{req.note}</p>}
                        </div>
                      </li>
                    ))}
                  </ul>
                </Card>
              )}

              {prerequisites.length > 0 && (
                <Card className="p-5">
                  <h2 className="font-semibold text-foreground mb-3">Prerequisites</h2>
                  <ul className="space-y-2 text-sm">
                    {prerequisites.map((pr, i) => (
                      <li key={i} className="rounded-lg border border-border px-3 py-2">
                        <div className="flex items-center justify-between gap-2">
                          <span className="font-medium text-foreground">{pr.name}</span>
                          <Badge variant={pr.required ? 'warning' : 'neutral'} size="sm">{pr.required ? 'Required' : 'Recommended'}</Badge>
                        </div>
                        {pr.allowed_substitutes.length > 0 && (
                          <p className="text-xs text-foreground/60 mt-1">Substitutes: {pr.allowed_substitutes.join(', ')}</p>
                        )}
                      </li>
                    ))}
                  </ul>
                </Card>
              )}

              {testPolicy && (
                <Card className="p-5">
                  <div className="flex items-center gap-2 mb-3">
                    <h2 className="font-semibold text-foreground">Test Policy</h2>
                    {testPolicy.stance_label && <Badge variant="info" size="sm">{testPolicy.stance_label}</Badge>}
                  </div>
                  <div className="space-y-2 text-sm">
                    {testPolicy.required.length > 0 && (
                      <p><span className="text-foreground/70">Required:</span> {testPolicy.required.join(', ')}</p>
                    )}
                    {testPolicy.optional.length > 0 && (
                      <p><span className="text-foreground/70">Optional:</span> {testPolicy.optional.join(', ')}</p>
                    )}
                    {testPolicy.typical_ranges.length > 0 && (
                      <div>
                        <p className="text-foreground/70 mb-1">Typical ranges:</p>
                        {testPolicy.typical_ranges.map(r => (
                          <p key={r.test} className="text-foreground">{r.test}: {r.low}–{r.high}</p>
                        ))}
                      </div>
                    )}
                    {testPolicy.waived_rules && <p className="text-foreground">{testPolicy.waived_rules}</p>}
                  </div>
                </Card>
              )}

              {recommendations && (
                <Card className="p-5">
                  <h2 className="font-semibold text-foreground mb-2">Recommendations</h2>
                  <p className="text-sm text-foreground">
                    {recommendations.required_count > 0
                      ? `${recommendations.required_count} letter${recommendations.required_count === 1 ? '' : 's'} required`
                      : 'Recommendations may be requested'}
                    {recommendations.types.length > 0 && ` · ${recommendations.types.join(', ')}`}
                  </p>
                </Card>
              )}

              {admissionTimeline && (
                <Card className="p-5">
                  <h2 className="font-semibold text-foreground mb-3">Intake Rounds — {admissionTimeline.term}</h2>
                  <div className="space-y-2">
                    {admissionTimeline.rounds.map((round: any, i: number) => (
                      <div key={i} className="p-3 rounded-lg bg-muted/50 border border-border text-sm">
                        <p className="font-medium text-foreground">{round.name}</p>
                        <p className="text-xs text-foreground/70 mt-1">
                          Deadline: {formatDate(round.deadline)}
                          {round.decision_release && ` · Decision: ${formatDate(round.decision_release)}`}
                        </p>
                      </div>
                    ))}
                  </div>
                </Card>
              )}

              {p.requirements && Object.keys(p.requirements).length > 0 && (
                <Card className="p-5">
                  <h2 className="font-semibold text-foreground mb-3">Other Requirements</h2>
                  <dl className="space-y-2 text-sm">
                    {Object.entries(p.requirements).map(([k, v]) => (
                      <div key={k} className="flex justify-between border-b border-border pb-2">
                        <dt className="text-foreground/70 capitalize">{k.replace(/_/g, ' ')}</dt>
                        <dd className="font-medium text-foreground">{String(v)}</dd>
                      </div>
                    ))}
                  </dl>
                </Card>
              )}

              {!hasAdmissions && (
                <EmptyState icon={<BookOpen size={40} />} title="No admissions details" description="This program has not published admissions requirements yet." />
              )}
            </div>
          )}

          {tab === 'costs' && (
            <div className="space-y-6">
              <Card className="p-5">
                <h2 className="font-semibold text-foreground mb-3">Tuition & Fees</h2>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-foreground/70">Tuition</span>
                    <span className="font-medium text-foreground">{effectiveTuition != null ? formatCurrency(effectiveTuition) : 'Not published'}</span>
                  </div>
                  {Object.entries(cd.fees || {}).map(([name, amount]) => (
                    <div key={name} className="flex justify-between">
                      <span className="text-foreground/70">{name}</span>
                      <span className="text-foreground">{formatCurrency(Number(amount))}</span>
                    </div>
                  ))}
                </div>
              </Card>

              {(costBandMin != null || costBandMax != null) && (
                <Card className="p-5">
                  <h2 className="font-semibold text-foreground mb-2">Estimated Total Cost</h2>
                  <p className="text-lg font-semibold text-foreground">
                    {costBandMin != null && costBandMax != null
                      ? `${formatCurrency(costBandMin)} – ${formatCurrency(costBandMax)}`
                      : formatCurrency(costBandMax ?? costBandMin ?? 0)}
                  </p>
                </Card>
              )}

              {fundingSignals && (
                <Card className="p-5">
                  <h2 className="font-semibold text-foreground mb-3">Funding & Aid Signals</h2>
                  <ul className="space-y-1.5 text-sm text-foreground">
                    {fundingSignals.ta_funded && <li>TA funding available</li>}
                    {fundingSignals.ra_funded && <li>RA funding available</li>}
                    {fundingSignals.merit_scholarship_available && <li>Merit scholarships</li>}
                    {fundingSignals.need_based_available && <li>Need-based aid</li>}
                  </ul>
                </Card>
              )}

              {effectiveTuition == null && !costBandMin && !fundingSignals && (
                <Card className="p-5 text-center">
                  <p className="text-sm text-foreground/70">Cost data has not been published for this program yet.</p>
                </Card>
              )}
            </div>
          )}

          {tab === 'outcomes' && (
            <div className="space-y-6">
              {!hasOutcomes ? (
                <Card className="p-5 text-center">
                  <TrendingUp size={32} className="text-foreground/30 mx-auto mb-3" />
                  <p className="text-sm text-foreground/70">Outcomes data has not been published for this program yet.</p>
                </Card>
              ) : (
                <>
                  {(odn.median_salary != null || salaryBands.length > 0) && (
                    <Card className="p-5">
                      <div className="flex items-center gap-2 mb-3">
                        <DollarSign size={14} className="text-secondary" />
                        <h2 className="font-semibold text-foreground">Salary</h2>
                      </div>
                      {salaryBands.length > 0 ? (
                        <div className="space-y-2">
                          {salaryBands.map(b => (
                            <div key={b.band_label} className="flex justify-between text-sm">
                              <span className="text-foreground">{b.band_label}</span>
                              <span className="font-medium text-foreground">{b.percent}%</span>
                            </div>
                          ))}
                        </div>
                      ) : odn.median_salary != null ? (
                        <p className="text-2xl font-bold text-foreground">{formatCurrency(Number(odn.median_salary))}</p>
                      ) : null}
                    </Card>
                  )}

                  {(odn.employment_rate != null || odn.internship_conversion_rate != null) && (
                    <Card className="p-5">
                      <div className="flex items-center gap-2 mb-3">
                        <Briefcase size={14} className="text-secondary" />
                        <h2 className="font-semibold text-foreground">Employment & Placement</h2>
                      </div>
                      <div className="grid grid-cols-2 gap-4 text-sm">
                        {odn.employment_rate != null && (
                          <div>
                            <p className="text-foreground/70">Employment rate</p>
                            <p className="text-xl font-bold text-foreground">{(Number(odn.employment_rate) * 100).toFixed(0)}%</p>
                            {odn.employment_timeframe && <p className="text-xs text-foreground/60">Within {odn.employment_timeframe}</p>}
                          </div>
                        )}
                        {odn.internship_conversion_rate != null && (
                          <div>
                            <p className="text-foreground/70">Internship conversion</p>
                            <p className="text-xl font-bold text-foreground">{(Number(odn.internship_conversion_rate) * 100).toFixed(0)}%</p>
                          </div>
                        )}
                      </div>
                    </Card>
                  )}

                  {(odn.top_employers?.length ?? 0) > 0 && (
                    <Card className="p-5">
                      <h2 className="font-semibold text-foreground mb-3">Top employers</h2>
                      <div className="flex flex-wrap gap-2">
                        {odn.top_employers.map((e: string) => <Badge key={e} variant="neutral" size="sm">{e}</Badge>)}
                      </div>
                    </Card>
                  )}

                  {/* Cite the source the institution attached — never invented. */}
                  {(outcomesSource || odn.employment_timeframe) && (
                    <p className="text-[11px] leading-relaxed text-muted-foreground pt-1">
                      <span className="font-semibold text-foreground/70">Source:</span>{' '}
                      {outcomesSource ?? 'Institution-reported outcomes'}
                      {odn.employment_timeframe ? ` · reported within ${odn.employment_timeframe}` : ''}.
                    </p>
                  )}
                </>
              )}
            </div>
          )}

          {tab === 'events' && (
            <div className="space-y-3">
              {events.length === 0 ? (
                <EmptyState icon={<CalendarDays size={40} />} title="No upcoming events" description="Check back later for program-specific events." />
              ) : (
                events.map(e => (
                  <Card key={e.id} className="p-4 flex items-center justify-between">
                    <div>
                      <h4 className="font-medium text-foreground">{e.event_name}</h4>
                      <p className="text-sm text-foreground/70">{formatDate(e.start_time)}{e.location ? ` · ${e.location}` : ''}</p>
                      {e.event_type && <Badge variant="neutral" className="mt-1">{e.event_type}</Badge>}
                    </div>
                    {e.capacity != null && (
                      <span className="text-xs text-foreground/50">{e.rsvp_count}/{e.capacity} spots</span>
                    )}
                  </Card>
                ))
              )}
            </div>
          )}
        </div>
      </div>

      <Modal isOpen={showInquiryModal} onClose={() => setShowInquiryModal(false)} title={`Request Info — ${p?.program_name ?? ''}`}>
        <div className="space-y-4">
          <Input label="Subject" value={inquirySubject} onChange={e => setInquirySubject(e.target.value)} maxLength={200} placeholder="What would you like to know about this program?" />
          <Textarea label="Message" value={inquiryMessage} onChange={e => setInquiryMessage(e.target.value)} rows={4} maxLength={2000} showCount placeholder="Tell us about your interests, questions about admissions, curriculum, financial aid..." />
          <div className="flex justify-end gap-2">
            <Button variant="ghost" onClick={() => setShowInquiryModal(false)}>Cancel</Button>
            <Button
              onClick={() => p && inquiryMut.mutate({
                institution_id: p.institution_id,
                program_id: p.id,
                subject: inquirySubject,
                message: inquiryMessage,
                campaign_id: searchParams.get('cid') || undefined,
              })}
              disabled={inquiryMut.isPending || !inquirySubject.trim() || !inquiryMessage.trim()}
            >
              {inquiryMut.isPending ? 'Sending...' : 'Send Inquiry'}
            </Button>
          </div>
        </div>
      </Modal>
    </>
  )
}

/* ── helpers ─────────────────────────────────────────────────────────────── */

// Full degree label for the hero eyebrow (the constants map gives short forms
// like "M.S."; the eyebrow wants "Master's program").
const DEGREE_EYEBROW: Record<string, string> = {
  bachelors: "Bachelor's program",
  masters: "Master's program",
  phd: 'Doctoral program',
  doctorate: 'Doctoral program',
  certificate: 'Certificate program',
  diploma: 'Diploma program',
  associate: 'Associate program',
}

function num(v: unknown): number | null {
  if (v == null || v === '') return null
  const n = Number(v)
  return Number.isNaN(n) ? null : n
}

// Pull a single {rank,label,year} from a JSONB blob, if a real ranking is
// present. Supports either a top-level `rank`/`ranking` number or a nested
// `{ <provider>: { rank, year } }` shape. Returns null when nothing is published
// (never fabricates a ranking).
function extractRanking(blob: Record<string, any> | null | undefined): { rank: number; label: string; year?: number } | null {
  if (!blob || typeof blob !== 'object') return null
  const topRank = num(blob.rank ?? blob.ranking)
  if (topRank != null) {
    const label = typeof blob.ranking_label === 'string' ? blob.ranking_label : typeof blob.ranking_source === 'string' ? blob.ranking_source : 'Program ranking'
    return { rank: topRank, label, year: num(blob.ranking_year ?? blob.year) ?? undefined }
  }
  for (const [key, v] of Object.entries(blob)) {
    if (v && typeof v === 'object' && typeof (v as any).rank === 'number') {
      return {
        rank: (v as any).rank,
        label: key.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase()),
        year: num((v as any).year) ?? undefined,
      }
    }
  }
  return null
}
