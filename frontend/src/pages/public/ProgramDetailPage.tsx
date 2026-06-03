import { useState } from 'react'
import { useParams, Link, useSearchParams } from 'react-router-dom'
import { useQuery, useMutation } from '@tanstack/react-query'
import {
  GraduationCap, MapPin, Clock, DollarSign, CalendarDays,
  Users, Globe, ExternalLink, BookOpen, CheckCircle2, ArrowLeft, MessageSquare, Sparkles,
  Briefcase, TrendingUp,
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
import { showToast } from '../../stores/toast-store'
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
      <div className="max-w-5xl mx-auto px-6 py-10 space-y-6">
        <Skeleton className="h-10 w-96" />
        <Skeleton className="h-6 w-64" />
        <div className="grid grid-cols-3 gap-4">{Array.from({ length: 3 }).map((_, i) => <Skeleton key={i} className="h-24" />)}</div>
      </div>
    )
  }

  if (!p) {
    return (
      <div className="max-w-5xl mx-auto px-6 py-16 text-center">
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

  return (
    <>
      <div className="max-w-5xl mx-auto px-6 py-8">
        {inst && (
          <Link to={`/school/${p.institution_id}`} className="inline-flex items-center gap-1 text-sm text-foreground/70 hover:text-foreground mb-4">
            <ArrowLeft size={14} /> {inst.name}
          </Link>
        )}

        <div className="bg-card rounded-lg border border-border p-6 mb-6">
          <div className="flex items-start justify-between gap-6">
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-3 mb-1">
                <h1 className="text-2xl font-bold text-foreground">{p.program_name}</h1>
                <Badge variant="info">{DEGREE_LABELS[p.degree_type] || p.degree_type}</Badge>
              </div>
              {p.department && <p className="text-foreground/70 mb-1">{p.department}</p>}
              {inst && (
                <Link to={`/school/${p.institution_id}`} className="text-sm text-secondary hover:underline">
                  {inst.name}
                </Link>
              )}

              <div className="flex flex-wrap gap-4 mt-4 text-sm text-foreground">
                {effectiveTuition != null && (
                  <span className="flex items-center gap-1.5"><DollarSign size={14} /> {formatCurrency(effectiveTuition)}</span>
                )}
                {p.duration_months != null && (
                  <span className="flex items-center gap-1.5"><Clock size={14} /> {p.duration_months} months</span>
                )}
                {p.acceptance_rate != null && (
                  <span className="flex items-center gap-1.5"><Users size={14} /> {formatPercent(p.acceptance_rate, 1)} acceptance</span>
                )}
                {p.delivery_format && (
                  <span className="flex items-center gap-1.5"><Globe size={14} /> {DELIVERY_FORMAT_LABELS[p.delivery_format] ?? p.delivery_format}</span>
                )}
                {p.campus_setting && (
                  <span className="flex items-center gap-1.5"><MapPin size={14} /> {CAMPUS_SETTING_LABELS[p.campus_setting] ?? p.campus_setting}</span>
                )}
              </div>

              {effectiveDeadline && (
                <div className="flex items-center gap-2 mt-3 text-sm">
                  <CalendarDays size={14} className="text-warning" />
                  <span className="text-warning font-medium">Application deadline: {formatDate(effectiveDeadline)}</span>
                </div>
              )}

              <Link
                to="/login"
                className="inline-flex items-center gap-2 mt-4 px-3 py-2 rounded-lg border border-secondary/30 bg-secondary/5 text-secondary text-sm font-semibold hover:bg-secondary/10 transition-colors"
              >
                <Sparkles size={14} /> Sign in to see your match
              </Link>
            </div>

            <div className="flex flex-col gap-2 shrink-0">
              <Link to="/signup?role=student">
                <Button className="w-full">Apply Now</Button>
              </Link>
              <Link to="/login">
                <Button variant="secondary" className="w-full">Save Program</Button>
              </Link>
              <Button variant="secondary" onClick={() => setShowInquiryModal(true)} className="w-full flex items-center gap-2">
                <MessageSquare size={14} /> Request Info
              </Button>
              {inst?.website_url && (
                <a href={inst.website_url} target="_blank" rel="noopener noreferrer">
                  <Button variant="ghost" className="w-full flex items-center gap-2">
                    <Globe size={14} /> Website <ExternalLink size={12} />
                  </Button>
                </a>
              )}
            </div>
          </div>
        </div>

        <Tabs tabs={tabs} activeTab={tab} onChange={setTab} />

        <div className="mt-6">
          {tab === 'overview' && (
            <div className="space-y-6">
              {p.description_text && (
                <Card className="p-5">
                  <h3 className="text-sm font-semibold text-foreground mb-2">About this program</h3>
                  <p className="text-sm text-foreground whitespace-pre-wrap">{p.description_text}</p>
                </Card>
              )}

              {p.who_its_for && (
                <Card className="p-5">
                  <h3 className="text-sm font-semibold text-foreground mb-2">Who it&apos;s for</h3>
                  <p className="text-sm text-foreground whitespace-pre-wrap">{p.who_its_for}</p>
                </Card>
              )}

              {(tracksMeta.concentrations.length > 0 || tracksMeta.note || tracksMeta.learning_format) && (
                <Card className="p-5">
                  <h3 className="text-sm font-semibold text-foreground mb-3">Tracks & Structure</h3>
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
                  <h3 className="text-sm font-semibold text-foreground mb-3">Highlights</h3>
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
                  <h3 className="text-sm font-semibold text-foreground mb-3">Faculty Contacts</h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    {faculty.map((f, i) => (
                      <div key={i} className="flex items-center gap-3 p-3 rounded-lg bg-muted/50">
                        <div className="w-9 h-9 rounded-full bg-secondary/10 flex items-center justify-center text-sm font-medium text-secondary">
                          {(f.name || '?')[0].toUpperCase()}
                        </div>
                        <div className="min-w-0">
                          <p className="text-sm font-medium text-foreground truncate">{f.name}</p>
                          {f.role && <p className="text-xs text-foreground/70">{f.role}</p>}
                          {f.email && <p className="text-xs text-foreground/50">{f.email}</p>}
                        </div>
                      </div>
                    ))}
                  </div>
                </Card>
              )}

              <Card className="p-5">
                <h3 className="text-sm font-semibold text-foreground mb-3">Quick Facts</h3>
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
                  <h3 className="text-sm font-semibold text-foreground mb-3">Key Dates</h3>
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
                  <h3 className="text-sm font-semibold text-foreground mb-3">Application Materials</h3>
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
                  <h3 className="text-sm font-semibold text-foreground mb-3">Prerequisites</h3>
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
                    <h3 className="text-sm font-semibold text-foreground">Test Policy</h3>
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
                  <h3 className="text-sm font-semibold text-foreground mb-2">Recommendations</h3>
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
                  <h3 className="text-sm font-semibold text-foreground mb-3">Intake Rounds — {admissionTimeline.term}</h3>
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
                  <h3 className="text-sm font-semibold text-foreground mb-3">Other Requirements</h3>
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
                <h3 className="text-sm font-semibold text-foreground mb-3">Tuition & Fees</h3>
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
                  <h3 className="text-sm font-semibold text-foreground mb-2">Estimated Total Cost</h3>
                  <p className="text-lg font-semibold text-foreground">
                    {costBandMin != null && costBandMax != null
                      ? `${formatCurrency(costBandMin)} – ${formatCurrency(costBandMax)}`
                      : formatCurrency(costBandMax ?? costBandMin ?? 0)}
                  </p>
                </Card>
              )}

              {fundingSignals && (
                <Card className="p-5">
                  <h3 className="text-sm font-semibold text-foreground mb-3">Funding & Aid Signals</h3>
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
                        <h3 className="text-sm font-semibold text-foreground">Salary</h3>
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
                        <h3 className="text-sm font-semibold text-foreground">Employment & Placement</h3>
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
                      <h3 className="text-sm font-semibold text-foreground mb-3">Top Employers</h3>
                      <div className="flex flex-wrap gap-2">
                        {odn.top_employers.map((e: string) => <Badge key={e} variant="neutral" size="sm">{e}</Badge>)}
                      </div>
                    </Card>
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
          <Input label="Subject" value={inquirySubject} onChange={e => setInquirySubject(e.target.value)} placeholder="What would you like to know about this program?" />
          <Textarea label="Message" value={inquiryMessage} onChange={e => setInquiryMessage(e.target.value)} rows={4} placeholder="Tell us about your interests, questions about admissions, curriculum, financial aid..." />
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
