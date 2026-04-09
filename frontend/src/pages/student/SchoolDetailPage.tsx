import { useState, useEffect } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { getProgram, getProgramReviews, getEmployerFeedback, searchPrograms, semanticSearch } from '../../api/programs'
import { getMatchDetail, logEngagement } from '../../api/matching'
import { listEvents, rsvpEvent } from '../../api/events'
import { listMyApplications, createApplication } from '../../api/applications'
import { saveProgram, unsaveProgram, listSaved } from '../../api/saved-lists'
import Card from '../../components/ui/Card'
import Badge from '../../components/ui/Badge'
import Button from '../../components/ui/Button'
import Tabs from '../../components/ui/Tabs'
import ProgressBar from '../../components/ui/ProgressBar'
import Skeleton from '../../components/ui/Skeleton'
import { showToast } from '../../stores/toast-store'
import { formatCurrency, formatDate, formatPercent, formatScore } from '../../utils/format'
import { DEGREE_LABELS, TIER_LABELS } from '../../utils/constants'
import { ArrowLeft, Heart, HeartOff, MessageSquare, DollarSign, TrendingUp, Clock, GraduationCap, Briefcase, Building2, BarChart3, Users, Star, Quote } from 'lucide-react'
import type { Program, MatchResult, EventItem } from '../../types'

export default function SchoolDetailPage() {
  const { programId } = useParams<{ programId: string }>()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [tab, setTab] = useState('overview')

  // Insight filters
  const [reviewDegree, setReviewDegree] = useState('')
  const [reviewYear, setReviewYear] = useState('')
  const [reviewMinRating, setReviewMinRating] = useState('')
  const [empIndustry, setEmpIndustry] = useState('')
  const [empYear, setEmpYear] = useState('')
  const [empSentiment, setEmpSentiment] = useState('')

  const { data: program, isLoading } = useQuery({
    queryKey: ['program', programId],
    queryFn: () => getProgram(programId!),
  })

  const { data: matchResult } = useQuery({
    queryKey: ['match', programId],
    queryFn: () => getMatchDetail(programId!),
    retry: false,
  })

  const { data: events } = useQuery({
    queryKey: ['events', { program_id: programId }],
    queryFn: () => listEvents({ program_id: programId, limit: 5 }),
  })

  const { data: saved } = useQuery({ queryKey: ['saved'], queryFn: listSaved })
  const savedList: any[] = Array.isArray(saved) ? saved : []
  const isSaved = savedList.some((s: any) => s.program_id === programId)

  const { data: applications } = useQuery({ queryKey: ['my-applications'], queryFn: listMyApplications })
  const applicationsList: any[] = Array.isArray(applications) ? applications : []
  const existingApp = applicationsList.find((a: any) => a.program_id === programId)
  const eventsList: EventItem[] = Array.isArray(events) ? events : []

  const { data: reviewsData } = useQuery({
    queryKey: ['program-reviews', programId],
    queryFn: () => getProgramReviews(programId!),
    retry: false,
  })

  const { data: employerData } = useQuery({
    queryKey: ['employer-feedback', programId],
    queryFn: () => getEmployerFeedback(programId!),
    retry: false,
  })

  const { data: sameSchoolData } = useQuery({
    queryKey: ['same-school-programs', program?.institution_id],
    queryFn: () => searchPrograms({
      institution_id: program?.institution_id,
      page_size: 7,
    }),
    enabled: !!program?.institution_id,
    retry: false,
  })
  const sameSchoolPrograms = (sameSchoolData?.items ?? [])
    .filter((sp: any) => sp.id !== programId)
    .slice(0, 6)

  const { data: similarData } = useQuery({
    queryKey: ['similar-programs', program?.program_name],
    queryFn: () => semanticSearch(program!.program_name, 7),
    enabled: !!program?.program_name,
    retry: false,
  })
  const similarPrograms = (Array.isArray(similarData) ? similarData : [])
    .filter((sp: any) => sp.id !== programId)
    .slice(0, 6)

  useEffect(() => {
    if (programId) logEngagement(programId, 'viewed_program', 1).catch(() => {})
    const start = Date.now()
    return () => {
      const secs = Math.round((Date.now() - start) / 1000)
      if (programId && secs > 5) logEngagement(programId, 'time_spent', secs).catch(() => {})
    }
  }, [programId])

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
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['events'] }); showToast('RSVP confirmed', 'success') },
  })
  if (isLoading) return <div className="p-6 space-y-4">{Array.from({ length: 3 }).map((_, i) => <Skeleton key={i} className="h-24" />)}</div>
  if (!program) {
    return (
      <div className="p-6 max-w-3xl mx-auto">
        <p className="text-sm text-gray-600 mb-3">Program details are unavailable right now.</p>
        <Button size="sm" variant="secondary" onClick={() => navigate('/s/discover')}>
          Back to Discover
        </Button>
      </div>
    )
  }

  const p: Program = program
  const match: MatchResult | null = matchResult ?? null
  const tierInfo = match ? TIER_LABELS[match.match_tier] : null

  return (
    <div className="p-6 max-w-3xl mx-auto">
      <button onClick={() => navigate('/s/discover')} className="flex items-center gap-1 text-sm text-gray-500 hover:text-brand-slate-600 mb-4">
        <ArrowLeft size={16} /> Back to Discover
      </button>

      <div className="flex justify-between items-start mb-6">
        <div>
          <h1 className="text-2xl font-bold">{p.program_name}</h1>
          <Link to={`/school/${p.institution_id}`} className="text-sm text-brand-slate-600 hover:underline">View Institution Profile</Link>
          <p className="text-gray-500">{p.department || ''}</p>
          {match && tierInfo && (
            <div className="flex items-center gap-2 mt-2">
              <Badge variant={tierInfo.color as any}>{tierInfo.label}</Badge>
              <span className="text-lg font-bold">{formatScore(match.match_score)} fit</span>
            </div>
          )}
        </div>
        <div className="flex gap-2">
          <Button variant="secondary" onClick={() => saveMut.mutate()} loading={saveMut.isPending}>
            {isSaved ? <><HeartOff size={14} className="mr-1" /> Unsave</> : <><Heart size={14} className="mr-1" /> Save</>}
          </Button>
          {existingApp ? (
            <Button onClick={() => navigate(`/s/applications/${existingApp.id}`)}>View Application</Button>
          ) : (
            <Button onClick={() => applyMut.mutate()} loading={applyMut.isPending}>Apply</Button>
          )}
        </div>
      </div>

      <Tabs
        tabs={[
          { id: 'overview', label: 'Overview' },
          { id: 'requirements', label: 'Requirements' },
          { id: 'costs', label: 'Costs & Aid' },
          { id: 'outcomes', label: 'Outcomes' },
          { id: 'reviews', label: `Reviews${reviewsData?.total_reviews ? ` (${reviewsData.total_reviews})` : ''}` },
          { id: 'employers', label: `Employer Insights${employerData?.total_feedback ? ` (${employerData.total_feedback})` : ''}` },
          { id: 'match', label: 'Match Analysis' },
        ]}
        activeTab={tab}
        onChange={setTab}
      />

      <div className="mt-6">
        {tab === 'overview' && (
          <div className="space-y-4">
            {p.description_text && <p className="text-sm text-brand-slate-600">{p.description_text}</p>}
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div><span className="text-gray-500">Degree:</span> {DEGREE_LABELS[p.degree_type] || p.degree_type}</div>
              <div><span className="text-gray-500">Duration:</span> {p.duration_months ? `${p.duration_months} months` : '—'}</div>
              <div><span className="text-gray-500">Tuition:</span> {formatCurrency(p.tuition)}</div>
              <div><span className="text-gray-500">Acceptance Rate:</span> {formatPercent(p.acceptance_rate, 1)}</div>
              <div><span className="text-gray-500">Deadline:</span> {formatDate(p.application_deadline)}</div>
              <div><span className="text-gray-500">Start:</span> {formatDate(p.program_start_date)}</div>
            </div>
            {p.highlights?.length ? (
              <div>
                <h3 className="font-medium text-sm mb-2">Highlights</h3>
                <ul className="list-disc list-inside text-sm text-gray-600 space-y-1">
                  {p.highlights.map((h, i) => <li key={i}>{h}</li>)}
                </ul>
              </div>
            ) : null}
          </div>
        )}

        {tab === 'requirements' && (
          <div>
            {p.requirements && Object.keys(p.requirements).length > 0 ? (
              <dl className="space-y-2 text-sm">
                {Object.entries(p.requirements).map(([k, v]) => (
                  <div key={k} className="flex justify-between border-b border-gray-100 pb-2">
                    <dt className="text-gray-500 capitalize">{k.replace(/_/g, ' ')}</dt>
                    <dd className="font-medium">{String(v)}</dd>
                  </div>
                ))}
              </dl>
            ) : (
              <p className="text-sm text-gray-500">No specific requirements listed.</p>
            )}
          </div>
        )}

        {tab === 'costs' && (() => {
          const cd = p.cost_data || {}
          const years = (p.duration_months || 24) / 12
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
          const salary = od.median_salary ? Number(od.median_salary) : null
          const empRate = od.employment_rate ? Number(od.employment_rate) : null
          const payback = od.payback_months ? Number(od.payback_months) : null

          return (
            <div className="space-y-4">
              <Card className="p-4">
                <div className="flex items-center gap-2 mb-3">
                  <DollarSign size={16} className="text-stone-600" />
                  <h3 className="font-medium text-sm text-stone-700">Tuition & Fees</h3>
                </div>
                <dl className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <dt className="text-gray-500">Annual Tuition</dt>
                    <dd className="font-medium">{formatCurrency(annual)}</dd>
                  </div>
                  {Object.entries(fees).map(([k, v]) => (
                    <div key={k} className="flex justify-between">
                      <dt className="text-gray-500 capitalize">{k.replace(/_/g, ' ')}</dt>
                      <dd>{formatCurrency(Number(v))}</dd>
                    </div>
                  ))}
                  {intlPremium > 0 && (
                    <div className="flex justify-between">
                      <dt className="text-gray-500">International Premium</dt>
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

              <Card className="p-4">
                <div className="flex items-center gap-2 mb-3">
                  <GraduationCap size={16} className="text-stone-600" />
                  <h3 className="font-medium text-sm text-stone-700">Estimated Total Cost ({years.toFixed(1)} years)</h3>
                </div>
                <div className="grid grid-cols-3 gap-3 text-center">
                  <div className="bg-emerald-50 rounded-lg p-3">
                    <p className="text-xs text-gray-500 mb-1">Tuition Only</p>
                    <p className="text-lg font-bold text-emerald-700">{formatCurrency(totalTuitionOnly)}</p>
                  </div>
                  <div className="bg-stone-50 rounded-lg p-3">
                    <p className="text-xs text-gray-500 mb-1">With Living Costs</p>
                    <p className="text-lg font-bold text-stone-700">{formatCurrency(totalMid)}</p>
                  </div>
                  <div className="bg-amber-50 rounded-lg p-3">
                    <p className="text-xs text-gray-500 mb-1">High Estimate</p>
                    <p className="text-lg font-bold text-amber-700">{formatCurrency(totalHigh)}</p>
                  </div>
                </div>
              </Card>

              <Card className="p-4">
                <div className="flex items-center gap-2 mb-3">
                  <DollarSign size={16} className="text-stone-600" />
                  <h3 className="font-medium text-sm text-stone-700">Financial Aid</h3>
                </div>
                {cd.financial_aid_available ? (
                  <div className="space-y-2">
                    <Badge variant="success" size="sm">Aid Available</Badge>
                    {cd.aid_types?.length > 0 && (
                      <div className="flex flex-wrap gap-1.5 mt-2">
                        {cd.aid_types.map((t: string) => (
                          <Badge key={t} variant="info" size="sm">{t.replace(/_/g, ' ')}</Badge>
                        ))}
                      </div>
                    )}
                    {cd.avg_aid_amount && (
                      <p className="text-sm text-gray-600 mt-2">Average aid: {formatCurrency(cd.avg_aid_amount)}</p>
                    )}
                  </div>
                ) : (
                  <p className="text-sm text-gray-500">Contact the program for financial aid details.</p>
                )}
              </Card>

              <Card className="p-4">
                <div className="flex items-center gap-2 mb-3">
                  <TrendingUp size={16} className="text-stone-600" />
                  <h3 className="font-medium text-sm text-stone-700">ROI Snapshot</h3>
                </div>
                {salary || empRate || payback ? (
                  <div className="grid grid-cols-2 gap-3 text-sm">
                    {salary && (
                      <div>
                        <p className="text-gray-500 text-xs">Median Starting Salary</p>
                        <p className="font-bold text-emerald-700 text-lg">{formatCurrency(salary)}</p>
                      </div>
                    )}
                    {empRate && (
                      <div>
                        <p className="text-gray-500 text-xs">Employment Rate</p>
                        <p className="font-bold text-stone-700 text-lg">{(empRate * 100).toFixed(0)}%</p>
                      </div>
                    )}
                    {payback && (
                      <div className="flex items-center gap-2">
                        <Clock size={14} className="text-gray-400" />
                        <div>
                          <p className="text-gray-500 text-xs">Payback Period</p>
                          <p className="font-medium">{payback} months</p>
                        </div>
                      </div>
                    )}
                    {salary && totalMid > 0 && (
                      <div>
                        <p className="text-gray-500 text-xs">Cost-to-Salary Ratio</p>
                        <p className="font-medium">1:{(salary / totalMid).toFixed(1)}x</p>
                      </div>
                    )}
                  </div>
                ) : (
                  <p className="text-sm text-gray-500">Outcomes data not yet available for this program.</p>
                )}
              </Card>
            </div>
          )
        })()}

        {tab === 'outcomes' && (() => {
          const od = p.outcomes_data || {}
          const salary = od.median_salary ? Number(od.median_salary) : null
          const salaryLow = od.salary_25th ? Number(od.salary_25th) : (salary ? Math.round(salary * 0.75) : null)
          const salaryHigh = od.salary_75th ? Number(od.salary_75th) : (salary ? Math.round(salary * 1.3) : null)
          const empRate = od.employment_rate ? Number(od.employment_rate) : null
          const empTimeframe = od.employment_timeframe || '6 months after graduation'
          const internRate = od.internship_conversion_rate ? Number(od.internship_conversion_rate) : null
          const topEmployers: string[] = od.top_employers || []
          const topIndustries: string[] = od.top_industries || []
          const hasData = salary || empRate || topEmployers.length > 0

          return (
            <div className="space-y-4">
              {!hasData ? (
                <Card className="p-6 text-center">
                  <BarChart3 size={32} className="text-gray-300 mx-auto mb-3" />
                  <p className="text-sm text-gray-500">Outcomes data is not yet available for this program.</p>
                  <p className="text-xs text-gray-400 mt-1">Check back later or contact the program directly.</p>
                </Card>
              ) : (
                <>
                  <Card className="p-4">
                    <div className="flex items-center gap-2 mb-3">
                      <DollarSign size={16} className="text-stone-600" />
                      <h3 className="font-medium text-sm text-stone-700">Salary Distribution</h3>
                    </div>
                    {salary ? (
                      <div>
                        <div className="flex items-end justify-between mb-2">
                          <div className="text-center flex-1">
                            <p className="text-xs text-gray-400">25th %ile</p>
                            <p className="text-sm font-medium text-gray-600">{salaryLow ? formatCurrency(salaryLow) : '—'}</p>
                          </div>
                          <div className="text-center flex-1">
                            <p className="text-xs text-gray-400">Median</p>
                            <p className="text-2xl font-bold text-emerald-700">{formatCurrency(salary)}</p>
                          </div>
                          <div className="text-center flex-1">
                            <p className="text-xs text-gray-400">75th %ile</p>
                            <p className="text-sm font-medium text-gray-600">{salaryHigh ? formatCurrency(salaryHigh) : '—'}</p>
                          </div>
                        </div>
                        <div className="relative h-2 bg-gray-100 rounded-full mt-3">
                          <div
                            className="absolute h-full bg-emerald-200 rounded-full"
                            style={{ left: '15%', width: '70%' }}
                          />
                          <div
                            className="absolute h-full bg-emerald-500 rounded-full"
                            style={{ left: '40%', width: '20%' }}
                          />
                        </div>
                        <p className="text-[10px] text-gray-400 mt-1 text-center">Starting salary range</p>
                      </div>
                    ) : (
                      <p className="text-sm text-gray-500">Salary data not available.</p>
                    )}
                  </Card>

                  <Card className="p-4">
                    <div className="flex items-center gap-2 mb-3">
                      <Briefcase size={16} className="text-stone-600" />
                      <h3 className="font-medium text-sm text-stone-700">Employment & Placement</h3>
                    </div>
                    <div className="grid grid-cols-2 gap-4">
                      {empRate != null && (
                        <div>
                          <p className="text-xs text-gray-500">Employment Rate</p>
                          <p className="text-2xl font-bold text-stone-700">{(empRate * 100).toFixed(0)}%</p>
                          <p className="text-[10px] text-gray-400">Within {empTimeframe}</p>
                        </div>
                      )}
                      {internRate != null && (
                        <div>
                          <p className="text-xs text-gray-500">Internship Conversion</p>
                          <p className="text-2xl font-bold text-stone-700">{(internRate * 100).toFixed(0)}%</p>
                          <p className="text-[10px] text-gray-400">Interns receiving full-time offers</p>
                        </div>
                      )}
                    </div>
                  </Card>

                  {topEmployers.length > 0 && (
                    <Card className="p-4">
                      <div className="flex items-center gap-2 mb-3">
                        <Building2 size={16} className="text-stone-600" />
                        <h3 className="font-medium text-sm text-stone-700">Top Employers</h3>
                      </div>
                      <div className="flex flex-wrap gap-2">
                        {topEmployers.map((e: string) => (
                          <Badge key={e} variant="neutral" size="sm">{e}</Badge>
                        ))}
                      </div>
                    </Card>
                  )}

                  {topIndustries.length > 0 && (
                    <Card className="p-4">
                      <div className="flex items-center gap-2 mb-3">
                        <Users size={16} className="text-stone-600" />
                        <h3 className="font-medium text-sm text-stone-700">Industry Placement</h3>
                      </div>
                      <div className="flex flex-wrap gap-2">
                        {topIndustries.map((ind: string) => (
                          <Badge key={ind} variant="info" size="sm">{ind}</Badge>
                        ))}
                      </div>
                    </Card>
                  )}
                </>
              )}
            </div>
          )
        })()}

        {tab === 'reviews' && (() => {
          const rd = reviewsData || { total_reviews: 0, reviews: [] }
          const allReviews: any[] = rd.reviews || []
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
            <div className="space-y-4">
              {allReviews.length > 0 && (
                <div className="flex flex-wrap gap-2">
                  <select value={reviewDegree} onChange={e => setReviewDegree(e.target.value)} className="text-xs border border-gray-300 rounded-lg px-2 py-1.5 bg-white">
                    <option value="">All Degrees</option>
                    {degreeOptions.map(d => <option key={d} value={d}>{d}</option>)}
                  </select>
                  <select value={reviewYear} onChange={e => setReviewYear(e.target.value)} className="text-xs border border-gray-300 rounded-lg px-2 py-1.5 bg-white">
                    <option value="">All Cohorts</option>
                    {yearOptions.map(y => <option key={y} value={String(y)}>{y}</option>)}
                  </select>
                  <select value={reviewMinRating} onChange={e => setReviewMinRating(e.target.value)} className="text-xs border border-gray-300 rounded-lg px-2 py-1.5 bg-white">
                    <option value="">Any Rating</option>
                    <option value="4">4+ Stars</option>
                    <option value="3">3+ Stars</option>
                    <option value="2">2+ Stars</option>
                  </select>
                  {(reviewDegree || reviewYear || reviewMinRating) && (
                    <button onClick={() => { setReviewDegree(''); setReviewYear(''); setReviewMinRating('') }} className="text-xs text-gray-500 hover:text-stone-700">Clear</button>
                  )}
                </div>
              )}

              {rd.total_reviews > 0 && (
                <Card className="p-4">
                  <div className="flex items-center gap-2 mb-3">
                    <Star size={16} className="text-amber-500" />
                    <h3 className="font-medium text-sm text-stone-700">Rating Summary</h3>
                    <span className="text-xs text-gray-400">{rd.total_reviews} review{rd.total_reviews !== 1 ? 's' : ''}</span>
                  </div>
                  <div className="space-y-2">
                    {dims.map(d => {
                      const val: number | null = (rd as any)[d.key]
                      if (val == null) return null
                      return (
                        <div key={d.key} className="flex items-center gap-3">
                          <span className="text-xs text-gray-500 w-28">{d.label}</span>
                          <div className="flex-1 h-2 bg-gray-100 rounded-full overflow-hidden">
                            <div className="h-full bg-amber-400 rounded-full" style={{ width: `${(val / 5) * 100}%` }} />
                          </div>
                          <span className="text-xs font-medium text-stone-700 w-8 text-right">{val.toFixed(1)}</span>
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
                                <Star key={i} size={12} className={i < r.rating_overall ? 'text-amber-400 fill-amber-400' : 'text-gray-200'} />
                              ))}
                            </div>
                          )}
                          {r.is_verified && <Badge variant="success" size="sm">Verified</Badge>}
                        </div>
                        <span className="text-[10px] text-gray-400">{formatDate(r.created_at)}</span>
                      </div>
                      {r.reviewer_context && (
                        <div className="flex flex-wrap gap-1.5 mb-2">
                          {Object.entries(r.reviewer_context).map(([k, v]) => (
                            <Badge key={k} variant="neutral" size="sm">{String(v)}</Badge>
                          ))}
                        </div>
                      )}
                      {r.review_text && <p className="text-sm text-gray-700 mb-2">{r.review_text}</p>}
                      {r.who_thrives_here && (
                        <div className="bg-stone-50 rounded-lg p-3 mt-2">
                          <div className="flex items-center gap-1.5 mb-1">
                            <Quote size={12} className="text-stone-400" />
                            <span className="text-xs font-medium text-stone-600">Who thrives here</span>
                          </div>
                          <p className="text-xs text-stone-600">{r.who_thrives_here}</p>
                        </div>
                      )}
                    </Card>
                  ))}
                </div>
              ) : (
                <Card className="p-6 text-center">
                  <Star size={32} className="text-gray-300 mx-auto mb-3" />
                  <p className="text-sm text-gray-500">No reviews yet for this program.</p>
                  <p className="text-xs text-gray-400 mt-1">Be the first to share your experience.</p>
                </Card>
              )}
            </div>
          )
        })()}

        {tab === 'employers' && (() => {
          const ed = employerData || { total_feedback: 0, feedback: [], sentiment_counts: {} }
          const allFeedback: any[] = ed.feedback || []
          const dims: { key: string; label: string }[] = [
            { key: 'avg_technical', label: 'Technical Skills' },
            { key: 'avg_practical', label: 'Practical Experience' },
            { key: 'avg_communication', label: 'Communication' },
            { key: 'avg_overall', label: 'Overall Readiness' },
          ]
          const sentiments = ed.sentiment_counts || {}
          const totalSent = Object.values(sentiments).reduce((s: number, v: any) => s + (Number(v) || 0), 0)

          const industryOptions = [...new Set(allFeedback.map(f => f.industry).filter(Boolean))]
          const empYearOptions = [...new Set(allFeedback.map(f => f.feedback_year).filter(Boolean))].sort()

          const filteredFb = allFeedback.filter(f => {
            if (empIndustry && f.industry !== empIndustry) return false
            if (empYear && String(f.feedback_year) !== empYear) return false
            if (empSentiment && f.job_readiness_sentiment !== empSentiment) return false
            return true
          })

          return (
            <div className="space-y-4">
              {allFeedback.length > 0 && (
                <div className="flex flex-wrap gap-2">
                  <select value={empIndustry} onChange={e => setEmpIndustry(e.target.value)} className="text-xs border border-gray-300 rounded-lg px-2 py-1.5 bg-white">
                    <option value="">All Industries</option>
                    {industryOptions.map(i => <option key={i} value={i}>{i}</option>)}
                  </select>
                  <select value={empYear} onChange={e => setEmpYear(e.target.value)} className="text-xs border border-gray-300 rounded-lg px-2 py-1.5 bg-white">
                    <option value="">All Years</option>
                    {empYearOptions.map(y => <option key={y} value={String(y)}>{y}</option>)}
                  </select>
                  <select value={empSentiment} onChange={e => setEmpSentiment(e.target.value)} className="text-xs border border-gray-300 rounded-lg px-2 py-1.5 bg-white">
                    <option value="">All Sentiments</option>
                    <option value="positive">Positive</option>
                    <option value="neutral">Neutral</option>
                    <option value="negative">Negative</option>
                  </select>
                  {(empIndustry || empYear || empSentiment) && (
                    <button onClick={() => { setEmpIndustry(''); setEmpYear(''); setEmpSentiment('') }} className="text-xs text-gray-500 hover:text-stone-700">Clear</button>
                  )}
                </div>
              )}

              {ed.total_feedback === 0 ? (
                <Card className="p-6 text-center">
                  <Building2 size={32} className="text-gray-300 mx-auto mb-3" />
                  <p className="text-sm text-gray-500">No employer feedback yet for this program.</p>
                </Card>
              ) : (
                <>
                  {totalSent > 0 && (
                    <Card className="p-4">
                      <div className="flex items-center gap-2 mb-3">
                        <TrendingUp size={16} className="text-stone-600" />
                        <h3 className="font-medium text-sm text-stone-700">Job Readiness Sentiment</h3>
                      </div>
                      <div className="flex gap-3">
                        {['positive', 'neutral', 'negative'].map(s => {
                          const count = sentiments[s] || 0
                          const pct = totalSent > 0 ? Math.round((count / totalSent) * 100) : 0
                          const color = s === 'positive' ? 'bg-emerald-400' : s === 'neutral' ? 'bg-amber-400' : 'bg-red-400'
                          return (
                            <div key={s} className="flex-1 text-center">
                              <div className="h-20 bg-gray-100 rounded-lg flex items-end overflow-hidden">
                                <div className={`w-full ${color} rounded-lg transition-all`} style={{ height: `${Math.max(pct, 5)}%` }} />
                              </div>
                              <p className="text-xs font-medium mt-1 capitalize">{s}</p>
                              <p className="text-[10px] text-gray-400">{pct}% ({count})</p>
                            </div>
                          )
                        })}
                      </div>
                    </Card>
                  )}

                  <Card className="p-4">
                    <div className="flex items-center gap-2 mb-3">
                      <BarChart3 size={16} className="text-stone-600" />
                      <h3 className="font-medium text-sm text-stone-700">Skills Assessment</h3>
                    </div>
                    <div className="space-y-2">
                      {dims.map(d => {
                        const val: number | null = (ed as any)[d.key]
                        if (val == null) return null
                        return (
                          <div key={d.key} className="flex items-center gap-3">
                            <span className="text-xs text-gray-500 w-32">{d.label}</span>
                            <div className="flex-1 h-2 bg-gray-100 rounded-full overflow-hidden">
                              <div className="h-full bg-stone-500 rounded-full" style={{ width: `${(val / 5) * 100}%` }} />
                            </div>
                            <span className="text-xs font-medium text-stone-700 w-8 text-right">{val.toFixed(1)}</span>
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
                            <p className="text-sm font-medium text-stone-700">{fb.employer_name}</p>
                            <div className="flex items-center gap-2 mt-0.5">
                              {fb.industry && <Badge variant="info" size="sm">{fb.industry}</Badge>}
                              {fb.feedback_year && <span className="text-[10px] text-gray-400">{fb.feedback_year}</span>}
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
                        {fb.feedback_text && <p className="text-sm text-gray-600 mt-2">{fb.feedback_text}</p>}
                        {fb.hiring_pattern && (
                          <p className="text-xs text-stone-500 mt-2 bg-stone-50 rounded px-2 py-1">
                            <Briefcase size={10} className="inline mr-1" />{fb.hiring_pattern}
                          </p>
                        )}
                      </Card>
                    ))}
                  </div>
                </>
              )}
            </div>
          )
        })()}

        {tab === 'match' && (
          <div>
            {match ? (
              <div className="space-y-4">
                {match.score_breakdown && Object.entries(match.score_breakdown).map(([k, v]) => (
                  <div key={k}>
                    <div className="flex justify-between text-sm mb-1">
                      <span className="capitalize">{k.replace(/_/g, ' ')}</span>
                      <span>{formatScore(v)}</span>
                    </div>
                    <ProgressBar value={v * 100} />
                  </div>
                ))}
                {match.reasoning_text && (
                  <div className="mt-4">
                    <h3 className="font-medium text-sm mb-2">AI Explanation</h3>
                    <p className="text-sm text-gray-600 whitespace-pre-wrap">{match.reasoning_text}</p>
                  </div>
                )}
                <div className="mt-4 border-t pt-4">
                  <div className="flex items-center justify-between">
                    <p className="text-sm text-gray-500">Want to understand this match better?</p>
                    <Button size="sm" variant="secondary" onClick={() => navigate('/s/chat')}>
                      <MessageSquare size={14} className="mr-1" /> Ask Counselor
                    </Button>
                  </div>
                </div>
              </div>
            ) : (
              <p className="text-sm text-gray-500">No match analysis available. Complete your profile to see how you fit.</p>
            )}
          </div>
        )}
      </div>

      {/* Events */}
      {eventsList.length > 0 && (
        <div className="mt-8">
          <h3 className="font-medium text-sm mb-3">Upcoming Events</h3>
          <div className="space-y-2">
            {eventsList.map((e: EventItem) => (
              <Card key={e.id} className="p-3 flex justify-between items-center">
                <div>
                  <p className="text-sm font-medium">{e.event_name}</p>
                  <p className="text-xs text-gray-500">{formatDate(e.start_time)}</p>
                </div>
                <Button size="sm" variant="secondary" onClick={() => rsvpMut.mutate(e.id)}>RSVP</Button>
              </Card>
            ))}
          </div>
        </div>
      )}

      {/* Other Programs at This School */}
      {sameSchoolPrograms.length > 0 && (
        <div className="mt-8">
          <div className="flex items-center justify-between mb-3">
            <h3 className="font-medium text-sm">Other Programs at This School</h3>
            <Link to={`/school/${p.institution_id}?tab=programs`} className="text-xs text-stone-500 hover:text-stone-700">
              View all
            </Link>
          </div>
          <div className="flex gap-3 overflow-x-auto pb-2">
            {sameSchoolPrograms.map((sp: any) => (
              <Card
                key={sp.id}
                onClick={() => navigate(`/s/programs/${sp.id}`)}
                className="flex-shrink-0 w-56 p-3"
              >
                <p className="text-sm font-semibold text-stone-700 truncate">{sp.program_name}</p>
                <div className="flex items-center gap-2 mt-1.5">
                  <Badge variant="info" size="sm">{DEGREE_LABELS[sp.degree_type] || sp.degree_type}</Badge>
                  {sp.tuition != null && <span className="text-xs text-gray-500">{formatCurrency(sp.tuition)}</span>}
                </div>
              </Card>
            ))}
          </div>
        </div>
      )}

      {/* Similar Programs */}
      {similarPrograms.length > 0 && (
        <div className="mt-8">
          <h3 className="font-medium text-sm mb-3">Similar Programs</h3>
          <div className="flex gap-3 overflow-x-auto pb-2">
            {similarPrograms.map((sp: any) => (
              <Card
                key={sp.id}
                onClick={() => navigate(`/s/programs/${sp.id}`)}
                className="flex-shrink-0 w-56 p-3 border border-purple-100"
              >
                <p className="text-sm font-semibold text-stone-700 truncate">{sp.program_name}</p>
                <p className="text-xs text-gray-500 truncate mt-0.5">{sp.institution_name}</p>
                <div className="flex items-center gap-2 mt-1.5">
                  <Badge variant="info" size="sm">{DEGREE_LABELS[sp.degree_type] || sp.degree_type}</Badge>
                  {sp.tuition != null && <span className="text-xs text-gray-500">{formatCurrency(sp.tuition)}</span>}
                </div>
              </Card>
            ))}
          </div>
        </div>
      )}

      {/* Back to Discovery */}
      <div className="mt-8 pt-6 border-t border-gray-100 flex items-center justify-between">
        <p className="text-sm text-gray-500">Want to explore more options?</p>
        <Button size="sm" variant="secondary" onClick={() => navigate('/s/discover')}>
          Back to Discovery
        </Button>
      </div>
    </div>
  )
}
