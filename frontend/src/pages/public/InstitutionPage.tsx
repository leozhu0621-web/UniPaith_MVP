import { useState, useEffect } from 'react'
import { useParams, Link, useSearchParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { useMutation } from '@tanstack/react-query'
import {
  Building2, MapPin, Users, Globe, Mail, ExternalLink,
  BookOpen, CalendarDays, FileText, Pin, MessageSquare,
  Shield, HeartHandshake, Plane, TrendingUp, Briefcase,
} from 'lucide-react'
import { getPublicInstitution, getPublicPosts, recordCampaignAction, submitInquiry } from '../../api/institutions'
import { searchPrograms } from '../../api/programs'
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
import { formatCurrency, formatDate } from '../../utils/format'
import { DEGREE_LABELS } from '../../utils/constants'
import type { Institution, InstitutionPost, ProgramSummary, PaginatedResponse, EventItem } from '../../types'

export default function InstitutionPage() {
  const { institutionId } = useParams<{ institutionId: string }>()
  const [searchParams] = useSearchParams()
  const [tab, setTab] = useState(searchParams.get('tab') || 'overview')

  // Campaign attribution tracking
  useEffect(() => {
    const cid = searchParams.get('cid')
    if (cid && institutionId) {
      recordCampaignAction({
        campaign_id: cid,
        action_type: 'view',
        target_id: institutionId,
      }).catch(() => {})  // silently ignore auth errors for anonymous visitors
    }
  }, [searchParams, institutionId])
  const [programPage, setProgPage] = useState(1)
  const [degreeFilter, setDegreeFilter] = useState('')
  const [showInquiryModal, setShowInquiryModal] = useState(false)
  const [inquirySubject, setInquirySubject] = useState('')
  const [inquiryMessage, setInquiryMessage] = useState('')

  const inquiryMut = useMutation({
    mutationFn: (p: { institution_id: string; subject: string; message: string; campaign_id?: string }) =>
      submitInquiry(p),
    onSuccess: () => {
      showToast('Inquiry sent! The institution will respond soon.', 'success')
      setShowInquiryModal(false)
      setInquirySubject('')
      setInquiryMessage('')
    },
    onError: () => showToast('Please sign in as a student to send inquiries.', 'warning'),
  })

  const instQ = useQuery({
    queryKey: ['public-institution', institutionId],
    queryFn: () => getPublicInstitution(institutionId!),
    enabled: !!institutionId,
  })

  const programsQ = useQuery({
    queryKey: ['public-inst-programs', institutionId, programPage, degreeFilter],
    queryFn: () => searchPrograms({
      institution_id: institutionId,
      degree_type: degreeFilter || undefined,
      page: programPage,
      page_size: 12,
    }),
    enabled: !!institutionId,
  })

  const eventsQ = useQuery({
    queryKey: ['public-inst-events', institutionId],
    queryFn: () => listEvents({ institution_id: institutionId, limit: 10 }),
    enabled: !!institutionId,
  })

  const postsQ = useQuery({
    queryKey: ['public-inst-posts', institutionId],
    queryFn: () => getPublicPosts(institutionId!),
    enabled: !!institutionId,
  })

  const inst: Institution | undefined = instQ.data
  const programs: ProgramSummary[] = (programsQ.data as PaginatedResponse<ProgramSummary>)?.items ?? []
  const totalProgramPages = (programsQ.data as PaginatedResponse<ProgramSummary>)?.total_pages ?? 1
  const events: EventItem[] = Array.isArray(eventsQ.data) ? eventsQ.data : []
  const publicPosts: InstitutionPost[] = postsQ.data ?? []
  const gallery: string[] = Array.isArray(inst?.media_gallery) ? inst.media_gallery : []

  const tabs = [
    { id: 'overview', label: 'Overview' },
    { id: 'programs', label: `Programs${inst?.program_count != null ? ` (${inst.program_count})` : ''}` },
    { id: 'services', label: 'Services' },
    { id: 'international', label: 'International' },
    { id: 'outcomes', label: 'Outcomes' },
    { id: 'events', label: `Events${events.length ? ` (${events.length})` : ''}` },
    ...(publicPosts.length > 0 ? [{ id: 'posts', label: `Posts (${publicPosts.length})` }] : []),
    ...(gallery.length > 0 ? [{ id: 'gallery', label: 'Gallery' }] : []),
  ]

  const SETTING_LABELS: Record<string, string> = { urban: 'Urban', suburban: 'Suburban', rural: 'Rural' }

  if (instQ.isLoading) {
    return (
      <div className="min-h-screen bg-gray-50">
        <header className="bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between">
          <Link to="/" className="text-lg font-bold">UniPaith</Link>
          <div className="flex gap-3">
            <Link to="/login" className="text-sm text-gray-600 hover:text-gray-900">Log in</Link>
            <Link to="/signup" className="text-sm bg-gray-900 text-white px-3 py-1 rounded hover:bg-gray-800">Sign up</Link>
          </div>
        </header>
        <div className="max-w-5xl mx-auto px-6 py-10 space-y-6">
          <Skeleton className="h-10 w-72" />
          <Skeleton className="h-6 w-48" />
          <div className="grid grid-cols-3 gap-4">{Array.from({ length: 3 }).map((_, i) => <Skeleton key={i} className="h-24" />)}</div>
        </div>
      </div>
    )
  }

  if (!inst) {
    return (
      <div className="min-h-screen bg-gray-50">
        <header className="bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between">
          <Link to="/" className="text-lg font-bold">UniPaith</Link>
          <div className="flex gap-3">
            <Link to="/login" className="text-sm text-gray-600 hover:text-gray-900">Log in</Link>
            <Link to="/signup" className="text-sm bg-gray-900 text-white px-3 py-1 rounded hover:bg-gray-800">Sign up</Link>
          </div>
        </header>
        <div className="max-w-5xl mx-auto px-6 py-16 text-center">
          <Building2 size={48} className="mx-auto text-gray-300 mb-4" />
          <h2 className="text-xl font-semibold text-gray-900 mb-2">Institution not found</h2>
          <p className="text-gray-500 mb-6">This institution profile is not available.</p>
          <Link to="/browse" className="text-brand-slate-600 hover:underline">Browse programs</Link>
        </div>
      </div>
    )
  }

  const location = [inst.city, inst.region, inst.country].filter(Boolean).join(', ')

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between">
        <Link to="/" className="text-lg font-bold">UniPaith</Link>
        <div className="flex gap-3">
          <Link to="/browse" className="text-sm text-gray-600 hover:text-gray-900">Browse</Link>
          <Link to="/login" className="text-sm text-gray-600 hover:text-gray-900">Log in</Link>
          <Link to="/signup" className="text-sm bg-gray-900 text-white px-3 py-1 rounded hover:bg-gray-800">Sign up</Link>
        </div>
      </header>

      <div className="max-w-5xl mx-auto px-6 py-8">
        {/* Hero */}
        <div className="bg-white rounded-xl border border-gray-200 p-6 mb-6">
          <div className="flex items-start gap-5">
            {inst.logo_url ? (
              <img src={inst.logo_url} alt={inst.name} className="w-16 h-16 rounded-lg object-cover border" />
            ) : (
              <div className="w-16 h-16 rounded-lg bg-brand-slate-100 flex items-center justify-center">
                <Building2 size={28} className="text-brand-slate-600" />
              </div>
            )}
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-3 mb-1">
                <h1 className="text-2xl font-bold text-gray-900 truncate">{inst.name}</h1>
                {inst.is_verified && <Badge variant="success">Verified</Badge>}
              </div>
              <div className="flex items-center gap-4 text-sm text-gray-500 mb-3">
                <Badge variant="neutral">{inst.type}</Badge>
                {location && (
                  <span className="flex items-center gap-1">
                    <MapPin size={14} /> {location}
                  </span>
                )}
              </div>
              <div className="flex flex-wrap gap-4 text-sm">
                {inst.student_body_size != null && (
                  <span className="flex items-center gap-1.5 text-gray-600">
                    <Users size={14} /> {inst.student_body_size.toLocaleString()} students
                  </span>
                )}
                {inst.program_count != null && (
                  <span className="flex items-center gap-1.5 text-gray-600">
                    <BookOpen size={14} /> {inst.program_count} programs
                  </span>
                )}
                {inst.campus_setting && (
                  <span className="text-gray-600">{SETTING_LABELS[inst.campus_setting] ?? inst.campus_setting} campus</span>
                )}
              </div>
            </div>
            <div className="flex flex-col gap-2 shrink-0">
              {inst.website_url && (
                <a href={inst.website_url} target="_blank" rel="noopener noreferrer">
                  <Button variant="secondary" className="flex items-center gap-2 w-full">
                    <Globe size={14} /> Website <ExternalLink size={12} />
                  </Button>
                </a>
              )}
              {inst.contact_email && (
                <a href={`mailto:${inst.contact_email}`}>
                  <Button variant="secondary" className="flex items-center gap-2 w-full">
                    <Mail size={14} /> Contact
                  </Button>
                </a>
              )}
              <Button onClick={() => setShowInquiryModal(true)} className="flex items-center gap-2 w-full">
                <MessageSquare size={14} /> Request Info
              </Button>
            </div>
          </div>
        </div>

        {/* Tabs */}
        <Tabs tabs={tabs} activeTab={tab} onChange={setTab} />

        <div className="mt-6">
          {/* Overview Tab */}
          {tab === 'overview' && (
            <div className="space-y-6">
              {inst.description_text && (
                <Card className="p-5">
                  <h3 className="text-sm font-semibold text-gray-900 mb-2">About</h3>
                  <p className="text-sm text-gray-700 whitespace-pre-wrap">{inst.description_text}</p>
                </Card>
              )}
              {inst.campus_description && (
                <Card className="p-5">
                  <h3 className="text-sm font-semibold text-gray-900 mb-2">Campus</h3>
                  <p className="text-sm text-gray-700 whitespace-pre-wrap">{inst.campus_description}</p>
                </Card>
              )}
              <Card className="p-5">
                <h3 className="text-sm font-semibold text-gray-900 mb-3">Quick Facts</h3>
                <div className="grid grid-cols-2 md:grid-cols-3 gap-4 text-sm">
                  <div><span className="text-gray-500">Type:</span> <span className="font-medium">{inst.type}</span></div>
                  <div><span className="text-gray-500">Country:</span> <span className="font-medium">{inst.country}</span></div>
                  {inst.region && <div><span className="text-gray-500">Region:</span> <span className="font-medium">{inst.region}</span></div>}
                  {inst.city && <div><span className="text-gray-500">City:</span> <span className="font-medium">{inst.city}</span></div>}
                  {inst.campus_setting && <div><span className="text-gray-500">Setting:</span> <span className="font-medium">{SETTING_LABELS[inst.campus_setting] ?? inst.campus_setting}</span></div>}
                  {inst.student_body_size != null && <div><span className="text-gray-500">Students:</span> <span className="font-medium">{inst.student_body_size.toLocaleString()}</span></div>}
                </div>
              </Card>
              {inst.social_links && Object.keys(inst.social_links).length > 0 && (
                <Card className="p-5">
                  <h3 className="text-sm font-semibold text-gray-900 mb-3">Social Links</h3>
                  <div className="flex flex-wrap gap-3">
                    {Object.entries(inst.social_links).map(([platform, url]) => (
                      <a key={platform} href={url} target="_blank" rel="noopener noreferrer" className="text-sm text-brand-slate-600 hover:underline capitalize flex items-center gap-1">
                        {platform} <ExternalLink size={12} />
                      </a>
                    ))}
                  </div>
                </Card>
              )}
            </div>
          )}

          {/* Programs Tab */}
          {tab === 'programs' && (
            <div className="space-y-4">
              <div className="flex gap-3">
                <select
                  value={degreeFilter}
                  onChange={e => { setDegreeFilter(e.target.value); setProgPage(1) }}
                  className="px-3 py-2 text-sm border border-gray-300 rounded-lg bg-white"
                >
                  <option value="">All Degrees</option>
                  {Object.entries(DEGREE_LABELS).map(([v, l]) => (
                    <option key={v} value={v}>{l}</option>
                  ))}
                </select>
              </div>

              {programsQ.isLoading ? (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {Array.from({ length: 6 }).map((_, i) => <Skeleton key={i} className="h-32" />)}
                </div>
              ) : programs.length === 0 ? (
                <EmptyState icon={<BookOpen size={40} />} title="No programs" description="No published programs match this filter." />
              ) : (
                <>
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {programs.map(p => (
                      <Link key={p.id} to={`/program/${p.id}`} className="bg-white rounded-lg border p-4 hover:shadow-md transition-shadow">
                        <h3 className="font-semibold text-gray-900 truncate">{p.program_name}</h3>
                        <div className="flex items-center gap-2 mt-2">
                          <Badge variant="info">{DEGREE_LABELS[p.degree_type] || p.degree_type}</Badge>
                          {p.tuition != null && <span className="text-xs text-gray-500">{formatCurrency(p.tuition)}</span>}
                        </div>
                        {p.department && <p className="text-xs text-gray-400 mt-1">{p.department}</p>}
                        {p.application_deadline && <p className="text-xs text-gray-400 mt-1">Deadline: {formatDate(p.application_deadline)}</p>}
                      </Link>
                    ))}
                  </div>
                  {totalProgramPages > 1 && (
                    <div className="flex justify-center gap-2 mt-6">
                      {Array.from({ length: totalProgramPages }, (_, i) => i + 1).map(p => (
                        <button
                          key={p}
                          onClick={() => setProgPage(p)}
                          className={`px-3 py-1 text-sm rounded ${p === programPage ? 'bg-gray-900 text-white' : 'bg-white border text-gray-600 hover:bg-gray-50'}`}
                        >
                          {p}
                        </button>
                      ))}
                    </div>
                  )}
                </>
              )}
            </div>
          )}

          {/* Services Tab */}
          {tab === 'services' && (() => {
            const ss = inst.support_services || {}
            const pol = inst.policies || {}
            const hasServices = Object.keys(ss).length > 0
            const hasPolicies = Object.keys(pol).length > 0

            return (
              <div className="space-y-6">
                <Card className="p-5">
                  <div className="flex items-center gap-2 mb-3">
                    <HeartHandshake size={16} className="text-stone-600" />
                    <h3 className="text-sm font-semibold text-gray-900">Support Services</h3>
                  </div>
                  {hasServices ? (
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                      {Object.entries(ss).map(([key, val]) => (
                        <div key={key} className="bg-stone-50 rounded-lg p-3">
                          <p className="text-sm font-medium text-stone-700 capitalize">{key.replace(/_/g, ' ')}</p>
                          <p className="text-xs text-gray-600 mt-0.5">{String(val)}</p>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-sm text-gray-500">Support service details not yet available. Contact the institution for more information.</p>
                  )}
                </Card>

                <Card className="p-5">
                  <div className="flex items-center gap-2 mb-3">
                    <Shield size={16} className="text-stone-600" />
                    <h3 className="text-sm font-semibold text-gray-900">Policies</h3>
                  </div>
                  {hasPolicies ? (
                    <dl className="space-y-2 text-sm">
                      {Object.entries(pol).map(([key, val]) => (
                        <div key={key} className="flex justify-between border-b border-gray-100 pb-2">
                          <dt className="text-gray-500 capitalize">{key.replace(/_/g, ' ')}</dt>
                          <dd className="font-medium text-stone-700">{String(val)}</dd>
                        </div>
                      ))}
                    </dl>
                  ) : (
                    <p className="text-sm text-gray-500">Policy information not yet available.</p>
                  )}
                </Card>
              </div>
            )
          })()}

          {/* International Tab */}
          {tab === 'international' && (() => {
            const ii = inst.international_info || {}
            const hasInfo = Object.keys(ii).length > 0

            return (
              <div className="space-y-6">
                <Card className="p-5">
                  <div className="flex items-center gap-2 mb-3">
                    <Plane size={16} className="text-stone-600" />
                    <h3 className="text-sm font-semibold text-gray-900">International Student Information</h3>
                  </div>
                  {hasInfo ? (
                    <div className="space-y-3">
                      {ii.visa_support && (
                        <div className="bg-emerald-50 rounded-lg p-3">
                          <p className="text-sm font-medium text-emerald-700">Visa Support Available</p>
                          <p className="text-xs text-emerald-600 mt-0.5">{String(ii.visa_support)}</p>
                        </div>
                      )}
                      {ii.english_requirements && (
                        <div className="bg-stone-50 rounded-lg p-3">
                          <p className="text-sm font-medium text-stone-700">English Requirements</p>
                          <p className="text-xs text-gray-600 mt-0.5">{String(ii.english_requirements)}</p>
                        </div>
                      )}
                      {ii.international_student_percentage != null && (
                        <div className="bg-stone-50 rounded-lg p-3">
                          <p className="text-sm font-medium text-stone-700">International Students</p>
                          <p className="text-xs text-gray-600 mt-0.5">{ii.international_student_percentage}% of student body</p>
                        </div>
                      )}
                      {Object.entries(ii)
                        .filter(([k]) => !['visa_support', 'english_requirements', 'international_student_percentage'].includes(k))
                        .map(([key, val]) => (
                          <div key={key} className="bg-stone-50 rounded-lg p-3">
                            <p className="text-sm font-medium text-stone-700 capitalize">{key.replace(/_/g, ' ')}</p>
                            <p className="text-xs text-gray-600 mt-0.5">{String(val)}</p>
                          </div>
                        ))}
                    </div>
                  ) : (
                    <p className="text-sm text-gray-500">International student information not yet available. Contact the institution for details.</p>
                  )}
                </Card>
              </div>
            )
          })()}

          {/* Outcomes Tab */}
          {tab === 'outcomes' && (() => {
            const so = inst.school_outcomes || {}
            const hasOutcomes = Object.keys(so).length > 0

            return (
              <div className="space-y-6">
                {hasOutcomes ? (
                  <>
                    <Card className="p-5">
                      <div className="flex items-center gap-2 mb-3">
                        <TrendingUp size={16} className="text-stone-600" />
                        <h3 className="text-sm font-semibold text-gray-900">School-Level Outcomes</h3>
                      </div>
                      <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                        {so.overall_employment_rate != null && (
                          <div className="text-center">
                            <p className="text-2xl font-bold text-emerald-700">{(Number(so.overall_employment_rate) * 100).toFixed(0)}%</p>
                            <p className="text-xs text-gray-500">Employment Rate</p>
                          </div>
                        )}
                        {so.median_starting_salary != null && (
                          <div className="text-center">
                            <p className="text-2xl font-bold text-stone-700">{formatCurrency(Number(so.median_starting_salary))}</p>
                            <p className="text-xs text-gray-500">Median Starting Salary</p>
                          </div>
                        )}
                        {so.graduation_rate != null && (
                          <div className="text-center">
                            <p className="text-2xl font-bold text-stone-700">{(Number(so.graduation_rate) * 100).toFixed(0)}%</p>
                            <p className="text-xs text-gray-500">Graduation Rate</p>
                          </div>
                        )}
                        {so.avg_time_to_employment && (
                          <div className="text-center">
                            <p className="text-2xl font-bold text-stone-700">{so.avg_time_to_employment}</p>
                            <p className="text-xs text-gray-500">Avg Time to Employment</p>
                          </div>
                        )}
                        {so.alumni_network_size != null && (
                          <div className="text-center">
                            <p className="text-2xl font-bold text-stone-700">{Number(so.alumni_network_size).toLocaleString()}</p>
                            <p className="text-xs text-gray-500">Alumni Network</p>
                          </div>
                        )}
                      </div>
                    </Card>

                    {so.top_hiring_companies && Array.isArray(so.top_hiring_companies) && (
                      <Card className="p-5">
                        <div className="flex items-center gap-2 mb-3">
                          <Briefcase size={16} className="text-stone-600" />
                          <h3 className="text-sm font-semibold text-gray-900">Top Hiring Companies</h3>
                        </div>
                        <div className="flex flex-wrap gap-2">
                          {so.top_hiring_companies.map((c: string) => (
                            <Badge key={c} variant="neutral">{c}</Badge>
                          ))}
                        </div>
                      </Card>
                    )}

                    {so.industry_breakdown && typeof so.industry_breakdown === 'object' && (
                      <Card className="p-5">
                        <div className="flex items-center gap-2 mb-3">
                          <Building2 size={16} className="text-stone-600" />
                          <h3 className="text-sm font-semibold text-gray-900">Industry Breakdown</h3>
                        </div>
                        <div className="space-y-2">
                          {Object.entries(so.industry_breakdown).map(([ind, pct]) => (
                            <div key={ind} className="flex items-center gap-3">
                              <span className="text-xs text-gray-500 w-32 capitalize">{ind.replace(/_/g, ' ')}</span>
                              <div className="flex-1 h-2 bg-gray-100 rounded-full overflow-hidden">
                                <div className="h-full bg-stone-500 rounded-full" style={{ width: `${Number(pct)}%` }} />
                              </div>
                              <span className="text-xs font-medium text-stone-700 w-10 text-right">{Number(pct)}%</span>
                            </div>
                          ))}
                        </div>
                      </Card>
                    )}
                  </>
                ) : (
                  <Card className="p-6 text-center">
                    <TrendingUp size={32} className="text-gray-300 mx-auto mb-3" />
                    <p className="text-sm text-gray-500">School-level outcomes data is not yet available.</p>
                  </Card>
                )}
              </div>
            )
          })()}

          {/* Events Tab */}
          {tab === 'events' && (
            <div className="space-y-3">
              {events.length === 0 ? (
                <EmptyState icon={<CalendarDays size={40} />} title="No upcoming events" description="Check back later for info sessions, webinars, and campus visits." />
              ) : (
                events.map(e => (
                  <Card key={e.id} className="p-4 flex items-center justify-between">
                    <div>
                      <h4 className="font-medium text-gray-900">{e.event_name}</h4>
                      <p className="text-sm text-gray-500">{formatDate(e.start_time)}{e.location ? ` \u00B7 ${e.location}` : ''}</p>
                      {e.event_type && <Badge variant="neutral" className="mt-1">{e.event_type}</Badge>}
                    </div>
                    {e.capacity != null && (
                      <span className="text-xs text-gray-400">{e.rsvp_count}/{e.capacity} spots</span>
                    )}
                  </Card>
                ))
              )}
            </div>
          )}

          {/* Posts Tab */}
          {tab === 'posts' && (
            <div className="space-y-4">
              {publicPosts.length === 0 ? (
                <EmptyState icon={<FileText size={40} />} title="No posts yet" description="This institution hasn't published any updates yet." />
              ) : (
                publicPosts.map(post => (
                  <Card key={post.id} className="p-5">
                    <div className="flex items-start gap-3">
                      {post.pinned && <Pin size={14} className="text-amber-500 mt-1 flex-shrink-0" />}
                      <div className="flex-1">
                        <h4 className="font-semibold text-gray-900 mb-1">{post.title}</h4>
                        <p className="text-sm text-gray-700 whitespace-pre-wrap mb-3">{post.body}</p>
                        {post.media_urls && Array.isArray(post.media_urls) && post.media_urls.length > 0 && (
                          <div className="flex gap-2 mb-3 flex-wrap">
                            {post.media_urls.filter(m => m.type === 'image').map((m, i) => (
                              <img key={i} src={m.url} alt={m.caption || `Media ${i + 1}`} className="h-32 rounded-lg object-cover border" />
                            ))}
                          </div>
                        )}
                        <div className="flex items-center gap-3 text-xs text-gray-500">
                          {post.published_at && <span>{formatDate(post.published_at)}</span>}
                          {post.program_names && post.program_names.length > 0 && (
                            <span className="flex items-center gap-1">{post.program_names.join(', ')}</span>
                          )}
                          {post.tagged_intake && <Badge variant="neutral">{post.tagged_intake}</Badge>}
                        </div>
                      </div>
                    </div>
                  </Card>
                ))
              )}
            </div>
          )}

          {/* Gallery Tab */}
          {tab === 'gallery' && gallery.length > 0 && (
            <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
              {gallery.map((url, i) => (
                <a key={i} href={url} target="_blank" rel="noopener noreferrer" className="rounded-lg overflow-hidden border hover:shadow-md transition-shadow">
                  <img src={url} alt={`${inst.name} gallery ${i + 1}`} className="w-full h-48 object-cover" />
                </a>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Request Info Modal */}
      <Modal isOpen={showInquiryModal} onClose={() => setShowInquiryModal(false)} title={`Request Info — ${inst?.name ?? ''}`}>
        <div className="space-y-4">
          <Input label="Subject" value={inquirySubject} onChange={e => setInquirySubject(e.target.value)} placeholder="What would you like to know?" />
          <Textarea label="Message" value={inquiryMessage} onChange={e => setInquiryMessage(e.target.value)} rows={4} placeholder="Tell us about your interests, questions about programs, admissions, campus life..." />
          <div className="flex justify-end gap-2">
            <Button variant="ghost" onClick={() => setShowInquiryModal(false)}>Cancel</Button>
            <Button
              onClick={() => institutionId && inquiryMut.mutate({
                institution_id: institutionId,
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
    </div>
  )
}
