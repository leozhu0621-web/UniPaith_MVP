import { useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { getPublicInstitution, getPublicPosts } from '../../api/institutions'
import { searchPrograms } from '../../api/programs'
import { listEvents, rsvpEvent, cancelRsvp, getMyRsvps } from '../../api/events'
import { listSaved, saveProgram, unsaveProgram } from '../../api/saved-lists'
import { useCompareStore } from '../../stores/compare-store'
import ProgramCard from './explore/cards/ProgramCard'
import EventCard from './explore/cards/EventCard'
import PostCard from './explore/cards/PostCard'
import Card from '../../components/ui/Card'
import Badge from '../../components/ui/Badge'
import Button from '../../components/ui/Button'
import Tabs from '../../components/ui/Tabs'
import Skeleton from '../../components/ui/Skeleton'
import {
  ArrowLeft, GraduationCap, MapPin, Globe, Users, Building2,
  BookOpen, Mail, Phone, ExternalLink, Shield, HandHeart,
  BadgeCheck, Briefcase,
} from 'lucide-react'
import type { Institution, ProgramSummary, InstitutionPost } from '../../types'

const TABS = [
  { id: 'overview', label: 'Overview' },
  { id: 'programs', label: 'Programs' },
  { id: 'events', label: 'Events' },
  { id: 'updates', label: 'Updates' },
]

export default function InstitutionDetailPage() {
  const { institutionId } = useParams<{ institutionId: string }>()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const compareStore = useCompareStore()
  const [tab, setTab] = useState('overview')

  const { data: institution, isLoading } = useQuery({
    queryKey: ['institution', institutionId],
    queryFn: () => getPublicInstitution(institutionId!),
    enabled: !!institutionId,
  })

  const { data: programs } = useQuery({
    queryKey: ['institution-programs', institutionId],
    queryFn: () => searchPrograms({ institution_id: institutionId, page_size: 50 }),
    enabled: !!institutionId,
  })

  const { data: events } = useQuery({
    queryKey: ['institution-events', institutionId],
    queryFn: () => listEvents({ institution_id: institutionId, limit: 20 }),
    enabled: !!institutionId && tab === 'events',
  })

  const { data: posts } = useQuery({
    queryKey: ['institution-posts', institutionId],
    queryFn: () => getPublicPosts(institutionId!),
    enabled: !!institutionId && tab === 'updates',
  })

  const { data: rsvps } = useQuery({ queryKey: ['my-rsvps'], queryFn: getMyRsvps, retry: false })
  const { data: savedData } = useQuery({ queryKey: ['saved-programs'], queryFn: listSaved, retry: false })

  const rsvpSet = new Set((rsvps as any[] ?? []).map((r: any) => r.event_id))
  const savedIds = new Set((savedData as any[] ?? []).map((s: any) => String(s.program_id)))

  const rsvpMut = useMutation({
    mutationFn: (eventId: string) => rsvpSet.has(eventId) ? cancelRsvp(eventId) : rsvpEvent(eventId),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['institution-events'] }); queryClient.invalidateQueries({ queryKey: ['my-rsvps'] }) },
  })

  const toggleSave = async (programId: string) => {
    try {
      if (savedIds.has(programId)) await unsaveProgram(programId)
      else await saveProgram(programId)
      queryClient.invalidateQueries({ queryKey: ['saved-programs'] })
    } catch { /* */ }
  }

  const inst: Institution | undefined = institution
  const programList: ProgramSummary[] = Array.isArray(programs?.items) ? programs.items : []
  const eventList: any[] = Array.isArray(events) ? events : []
  const postList: InstitutionPost[] = Array.isArray(posts) ? posts : []

  if (isLoading) {
    return (
      <div className="p-6 max-w-4xl mx-auto space-y-4">
        <Skeleton className="h-8 w-48" />
        <Skeleton className="h-40" />
        <Skeleton className="h-40" />
      </div>
    )
  }

  if (!inst) {
    return (
      <div className="p-6 max-w-4xl mx-auto text-center py-20">
        <p className="text-student-text">Institution not found.</p>
        <Button size="sm" className="mt-4" onClick={() => navigate('/s/explore')}>Back to Explore</Button>
      </div>
    )
  }

  return (
    <div className="p-6 max-w-4xl mx-auto">
      {/* Back button */}
      <button onClick={() => navigate(-1)} className="flex items-center gap-1 text-sm text-student-text hover:text-student-ink mb-4">
        <ArrowLeft size={14} /> Back
      </button>

      {/* School Header */}
      <div className="bg-white rounded-xl border border-divider p-6 mb-6">
        <div className="flex items-start gap-4">
          <div className="w-16 h-16 rounded-xl bg-school-mist flex items-center justify-center flex-shrink-0">
            {inst.logo_url ? (
              <img src={inst.logo_url} alt="" className="w-12 h-12 object-contain" onError={e => { e.currentTarget.style.display = 'none'; e.currentTarget.parentElement!.innerHTML = '<svg width="24" height="24"><text x="0" y="20" font-size="20">🎓</text></svg>' }} />
            ) : (
              <GraduationCap size={28} className="text-school" />
            )}
          </div>
          <div className="flex-1 min-w-0">
            <h1 className="text-2xl font-bold text-student-ink">{inst.name}</h1>
            <div className="flex items-center gap-3 mt-1 text-sm text-student-text">
              <span className="flex items-center gap-1"><MapPin size={13} /> {inst.city ? `${inst.city}, ` : ''}{inst.country}</span>
              {inst.type && <Badge variant="neutral">{inst.type}</Badge>}
              {inst.campus_setting && <span className="flex items-center gap-1"><Building2 size={13} /> {inst.campus_setting}</span>}
            </div>
            <div className="flex items-center gap-3 mt-2 text-xs text-student-text">
              {inst.student_body_size && <span className="flex items-center gap-1"><Users size={11} /> {inst.student_body_size.toLocaleString()} students</span>}
              {inst.program_count != null && <span className="flex items-center gap-1"><BookOpen size={11} /> {inst.program_count} programs</span>}
            </div>
          </div>
          <div className="flex gap-2 flex-shrink-0">
            {inst.website_url && (
              <Button size="sm" variant="secondary" onClick={() => window.open(inst.website_url!, '_blank')}>
                <Globe size={14} className="mr-1" /> Website
              </Button>
            )}
            {inst.contact_email && (
              <Button size="sm" variant="secondary" onClick={() => window.open(`mailto:${inst.contact_email}`)}>
                <Mail size={14} className="mr-1" /> Contact
              </Button>
            )}
          </div>
        </div>
      </div>

      {/* Tabs */}
      <Tabs tabs={TABS} activeTab={tab} onChange={setTab} />

      <div className="mt-6">
        {/* Overview Tab */}
        {tab === 'overview' && (
          <div className="space-y-6">
            {inst.description_text && (
              <Card className="p-5">
                <h2 className="font-semibold text-student-ink mb-2">About</h2>
                <p className="text-sm text-student-text leading-relaxed">{inst.description_text}</p>
              </Card>
            )}

            {inst.campus_description && (
              <Card className="p-5">
                <h2 className="font-semibold text-student-ink mb-2">Campus & Environment</h2>
                <p className="text-sm text-student-text leading-relaxed">{inst.campus_description}</p>
              </Card>
            )}

            {/* Support Services — each value is {name, url, email} */}
            {inst.support_services && Object.keys(inst.support_services).filter(k => !k.startsWith('_')).length > 0 && (
              <Card className="p-5">
                <div className="flex items-center gap-2 mb-3">
                  <HandHeart size={14} className="text-student" />
                  <h2 className="font-semibold text-student-ink">Support Services</h2>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-sm">
                  {Object.entries(inst.support_services).filter(([k]) => !k.startsWith('_')).map(([key, val]: [string, any]) => {
                    const label = val?.name || key.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())
                    return (
                      <div key={key} className="flex justify-between items-start gap-2 border-b border-gray-100 pb-2">
                        <div className="flex-1">
                          <div className="font-medium text-student-ink">{label}</div>
                          {val?.hours && <div className="text-xs text-student-text">{val.hours}</div>}
                          {val?.phone && <div className="text-xs text-student-text"><Phone size={10} className="inline mr-1" />{val.phone}</div>}
                        </div>
                        {val?.url && (
                          <a href={val.url} target="_blank" rel="noopener noreferrer" className="text-xs text-student hover:underline flex items-center gap-1">
                            Visit <ExternalLink size={10} />
                          </a>
                        )}
                      </div>
                    )
                  })}
                </div>
                {(inst.support_services as any)._source && <p className="text-[10px] text-gray-400 mt-2">Source: {(inst.support_services as any)._source}</p>}
              </Card>
            )}

            {/* Policies — each value is {url, summary, name} */}
            {inst.policies && Object.keys(inst.policies).filter(k => !k.startsWith('_')).length > 0 && (
              <Card className="p-5">
                <div className="flex items-center gap-2 mb-3">
                  <Shield size={14} className="text-student" />
                  <h2 className="font-semibold text-student-ink">Policies</h2>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-sm">
                  {Object.entries(inst.policies).filter(([k]) => !k.startsWith('_')).map(([key, val]: [string, any]) => {
                    const label = val?.name || key.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())
                    return (
                      <div key={key} className="border-b border-gray-100 pb-2">
                        <div className="flex justify-between items-start gap-2">
                          <div className="font-medium text-student-ink">{label}</div>
                          {val?.url && (
                            <a href={val.url} target="_blank" rel="noopener noreferrer" className="text-xs text-student hover:underline flex items-center gap-1 flex-shrink-0">
                              Read <ExternalLink size={10} />
                            </a>
                          )}
                        </div>
                        {val?.summary && <div className="text-xs text-student-text mt-1">{val.summary}</div>}
                      </div>
                    )
                  })}
                </div>
              </Card>
            )}

            {/* International student info */}
            {inst.international_info && Object.keys(inst.international_info).filter(k => !k.startsWith('_')).length > 0 && (() => {
              const ii: any = inst.international_info
              const ep = ii.english_proficiency || {}
              const visa = ii.visa || {}
              return (
                <Card className="p-5">
                  <div className="flex items-center gap-2 mb-3">
                    <Globe size={14} className="text-student" />
                    <h2 className="font-semibold text-student-ink">International Students</h2>
                  </div>
                  <div className="space-y-3 text-sm">
                    {(ep.toefl_ibt_min || ep.ielts_min || ep.duolingo_min || ep.pte_min) && (
                      <div>
                        <p className="text-xs font-semibold text-student-text uppercase mb-2">English Proficiency Minimums</p>
                        <div className="flex flex-wrap gap-2">
                          {ep.toefl_ibt_min && <Badge variant="info">TOEFL iBT ≥ {ep.toefl_ibt_min}</Badge>}
                          {ep.ielts_min && <Badge variant="info">IELTS ≥ {ep.ielts_min}</Badge>}
                          {ep.duolingo_min && <Badge variant="info">Duolingo ≥ {ep.duolingo_min}</Badge>}
                          {ep.pte_min && <Badge variant="info">PTE ≥ {ep.pte_min}</Badge>}
                        </div>
                        {ep.note && <p className="text-xs text-student-text mt-1">{ep.note}</p>}
                      </div>
                    )}
                    {Array.isArray(ii.supported_visas) && ii.supported_visas.length > 0 && (
                      <div>
                        <p className="text-xs font-semibold text-student-text uppercase mb-2">Supported Visa Types</p>
                        <div className="flex flex-wrap gap-2">
                          {ii.supported_visas.map((v: string) => <Badge key={v} variant="neutral">{v}</Badge>)}
                        </div>
                      </div>
                    )}
                    {(visa.office_name || visa.email || visa.phone || visa.url) && (
                      <div>
                        <p className="text-xs font-semibold text-student-text uppercase mb-2">Visa Office</p>
                        {visa.office_name && <div className="font-medium text-student-ink">{visa.office_name}</div>}
                        {visa.email && <div className="text-xs text-student-text"><Mail size={10} className="inline mr-1" /><a href={`mailto:${visa.email}`} className="hover:underline">{visa.email}</a></div>}
                        {visa.phone && <div className="text-xs text-student-text"><Phone size={10} className="inline mr-1" />{visa.phone}</div>}
                        {visa.url && <a href={visa.url} target="_blank" rel="noopener noreferrer" className="text-xs text-student hover:underline flex items-center gap-1 mt-1">Visit office site <ExternalLink size={10} /></a>}
                      </div>
                    )}
                    {ii.international_student_count && (
                      <p className="text-xs text-student-text">International students on campus: <span className="font-medium text-student-ink">{Number(ii.international_student_count).toLocaleString()}</span></p>
                    )}
                    {ii.scholarship_eligibility && (
                      <p className="text-xs text-student-text">{ii.scholarship_eligibility}</p>
                    )}
                  </div>
                </Card>
              )
            })()}

            {/* School-wide outcomes — mix of rates, lists, nested dicts */}
            {inst.school_outcomes && Object.keys(inst.school_outcomes).filter(k => !k.startsWith('_') && k !== 'source').length > 0 && (() => {
              const so: any = inst.school_outcomes
              const fmtPct = (v: any) => typeof v === 'number' && v <= 1 ? `${Math.round(v * 100)}%` : String(v)
              const scalarPairs = Object.entries(so).filter(([k, v]) =>
                !k.startsWith('_') && k !== 'source' && (typeof v === 'number' || typeof v === 'string')
              )
              const industries: string[] = Array.isArray(so.top_employer_industries) ? so.top_employer_industries : []
              const geo: any = so.geographic_placement || {}
              return (
                <Card className="p-5">
                  <div className="flex items-center gap-2 mb-3">
                    <BadgeCheck size={14} className="text-emerald-600" />
                    <h2 className="font-semibold text-student-ink">School-Wide Outcomes</h2>
                  </div>
                  <div className="space-y-4 text-sm">
                    {scalarPairs.length > 0 && (
                      <dl className="grid grid-cols-2 gap-2">
                        {scalarPairs.map(([key, val]) => (
                          <div key={key}>
                            <dt className="text-xs text-student-text capitalize">{key.replace(/_/g, ' ')}</dt>
                            <dd className="text-student-ink font-medium">{fmtPct(val)}</dd>
                          </div>
                        ))}
                      </dl>
                    )}
                    {industries.length > 0 && (
                      <div>
                        <p className="text-xs font-semibold text-student-text uppercase mb-2">Top Employer Industries</p>
                        <div className="flex flex-wrap gap-2">
                          {industries.map(ind => <Badge key={ind} variant="info">{ind}</Badge>)}
                        </div>
                      </div>
                    )}
                    {Object.keys(geo).length > 0 && (
                      <div>
                        <p className="text-xs font-semibold text-student-text uppercase mb-2">Geographic Placement</p>
                        <div className="space-y-1">
                          {Object.entries(geo).map(([region, share]: [string, any]) => {
                            const pct = typeof share === 'number' ? Math.round(share * 100) : null
                            return (
                              <div key={region} className="flex items-center gap-2 text-xs">
                                <span className="text-student-text capitalize w-28">{region.replace(/_/g, ' ')}</span>
                                {pct != null && (
                                  <>
                                    <div className="flex-1 h-1.5 bg-gray-100 rounded-full">
                                      <div className="h-full bg-student rounded-full" style={{ width: `${pct}%` }} />
                                    </div>
                                    <span className="font-medium text-student-ink w-10 text-right">{pct}%</span>
                                  </>
                                )}
                              </div>
                            )
                          })}
                        </div>
                      </div>
                    )}
                    {so.source && <p className="text-[10px] text-gray-400">Source: {so.source}</p>}
                  </div>
                </Card>
              )
            })()}

            {/* Social links */}
            {inst.social_links && Object.keys(inst.social_links).filter(k => !k.startsWith('_')).length > 0 && (
              <Card className="p-5">
                <div className="flex items-center gap-2 mb-3">
                  <Globe size={14} className="text-student" />
                  <h2 className="font-semibold text-student-ink">Follow {inst.name}</h2>
                </div>
                <div className="flex flex-wrap gap-2">
                  {Object.entries(inst.social_links).filter(([k]) => !k.startsWith('_')).map(([platform, url]: [string, any]) => (
                    <a key={platform} href={url} target="_blank" rel="noopener noreferrer" className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs rounded-full bg-student-mist text-student-ink hover:bg-student/10 transition">
                      <ExternalLink size={10} />
                      <span className="capitalize">{platform}</span>
                    </a>
                  ))}
                </div>
              </Card>
            )}

            {/* Inquiry routing — contact channels for admissions, international, aid, etc. */}
            {inst.inquiry_routing && Object.keys(inst.inquiry_routing).filter(k => !k.startsWith('_')).length > 0 && (
              <Card className="p-5">
                <div className="flex items-center gap-2 mb-3">
                  <Briefcase size={14} className="text-student" />
                  <h2 className="font-semibold text-student-ink">Admissions & Contact</h2>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-sm">
                  {Object.entries(inst.inquiry_routing).filter(([k]) => !k.startsWith('_')).map(([channel, info]: [string, any]) => {
                    const label = channel.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())
                    return (
                      <div key={channel} className="border-b border-gray-100 pb-2">
                        <div className="font-medium text-student-ink mb-0.5">{label}</div>
                        {info?.email && <div className="text-xs text-student-text"><Mail size={10} className="inline mr-1" /><a href={`mailto:${info.email}`} className="hover:underline">{info.email}</a></div>}
                        {info?.phone && <div className="text-xs text-student-text"><Phone size={10} className="inline mr-1" />{info.phone}</div>}
                        {info?.url && <a href={info.url} target="_blank" rel="noopener noreferrer" className="text-xs text-student hover:underline flex items-center gap-1">Visit <ExternalLink size={10} /></a>}
                      </div>
                    )
                  })}
                </div>
              </Card>
            )}
          </div>
        )}

        {/* Programs Tab */}
        {tab === 'programs' && (
          <div className="space-y-4">
            {programList.length === 0 ? (
              <p className="text-sm text-student-text text-center py-8">No published programs yet.</p>
            ) : (
              programList.map(p => (
                <ProgramCard
                  key={p.id}
                  program={p}
                  saved={savedIds.has(p.id)}
                  comparing={compareStore.has(p.id)}
                  onSave={() => toggleSave(p.id)}
                  onCompare={() => compareStore.has(p.id) ? compareStore.remove(p.id) : compareStore.add({ program_id: p.id, program_name: p.program_name, institution_name: p.institution_name, degree_type: p.degree_type })}
                  onAskCounselor={() => navigate(`/s?prefill=${encodeURIComponent(`Tell me about ${p.program_name} at ${inst.name}. Is it a good fit?`)}`)}
                  onView={() => navigate(`/s/programs/${p.id}`)}
                />
              ))
            )}
          </div>
        )}

        {/* Events Tab */}
        {tab === 'events' && (
          <div className="space-y-3">
            {eventList.length === 0 ? (
              <p className="text-sm text-student-text text-center py-8">No upcoming events.</p>
            ) : (
              eventList.map(ev => (
                <EventCard
                  key={ev.id}
                  event={{ ...ev, institution_name: inst.name }}
                  isRsvped={rsvpSet.has(ev.id)}
                  onRsvp={() => rsvpMut.mutate(ev.id)}
                />
              ))
            )}
          </div>
        )}

        {/* Updates Tab */}
        {tab === 'updates' && (
          <div className="space-y-3">
            {postList.length === 0 ? (
              <p className="text-sm text-student-text text-center py-8">No updates yet.</p>
            ) : (
              postList.map(post => (
                <PostCard key={post.id} post={{ ...post, institution_name: inst.name } as any} />
              ))
            )}
          </div>
        )}
      </div>
    </div>
  )
}
