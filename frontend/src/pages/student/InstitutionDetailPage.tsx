import { useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { getPublicInstitution, getPublicPosts, getInstitutionSchools } from '../../api/institutions'
import { searchPrograms } from '../../api/programs'
import { listEvents, rsvpEvent, cancelRsvp, getMyRsvps } from '../../api/events'
import { listSaved, saveProgram, unsaveProgram } from '../../api/saved-lists'
import { useCompareStore } from '../../stores/compare-store'
import ProgramCard from './explore/cards/ProgramCard'
import SchoolCard from './explore/cards/SchoolCard'
import EventCard from './explore/cards/EventCard'
import PostCard from './explore/cards/PostCard'
import Card from '../../components/ui/Card'
import Badge from '../../components/ui/Badge'
import Button from '../../components/ui/Button'
import Tabs from '../../components/ui/Tabs'
import Skeleton from '../../components/ui/Skeleton'
import {
  ArrowLeft, GraduationCap, MapPin, Globe, Users, Building2,
  BookOpen, Mail,
} from 'lucide-react'
import type { Institution, ProgramSummary, InstitutionPost, SchoolSummary } from '../../types'

// Schools is the headline tab — the primary purpose of the university detail
// page is to let students drill into a school, then into a program. Overview,
// Programs, Events, and Updates are supporting context.
const TABS = [
  { id: 'schools', label: 'Schools' },
  { id: 'overview', label: 'About' },
  { id: 'programs', label: 'All Programs' },
  { id: 'events', label: 'Events' },
  { id: 'updates', label: 'Updates' },
]

export default function InstitutionDetailPage() {
  const { institutionId } = useParams<{ institutionId: string }>()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const compareStore = useCompareStore()
  const [tab, setTab] = useState('schools')

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

  // Schools is the landing tab, so fetch eagerly instead of waiting for click.
  const { data: schools } = useQuery({
    queryKey: ['institution-schools', institutionId],
    queryFn: () => getInstitutionSchools(institutionId!),
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
  const schoolList: SchoolSummary[] = Array.isArray(schools) ? schools : []
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

      {/* Media gallery — campus photo strip */}
      {Array.isArray((inst as any).media_gallery) && (inst as any).media_gallery.length > 0 && (
        <div className="grid grid-cols-3 gap-2 mb-4 rounded-xl overflow-hidden">
          {((inst as any).media_gallery as string[]).slice(0, 3).map((url: string, i: number) => (
            <div key={i} className={`relative ${i === 0 ? 'col-span-2 row-span-2 aspect-[16/9]' : 'aspect-square'} bg-slate-100`}>
              <img
                src={url}
                alt=""
                className="w-full h-full object-cover"
                onError={e => { e.currentTarget.style.display = 'none' }}
              />
            </div>
          ))}
        </div>
      )}

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

            {/* Social links — icons row */}
            {inst.social_links && typeof inst.social_links === 'object' && (
              <div className="flex items-center gap-3 mt-3">
                {Object.entries(inst.social_links)
                  .filter(([k, v]) => !k.startsWith('_') && typeof v === 'string' && v)
                  .map(([platform, url]) => (
                    <a
                      key={platform}
                      href={url as string}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-[11px] text-student-text/70 hover:text-student capitalize transition-colors"
                      title={`${platform} profile`}
                    >
                      {platform}
                    </a>
                  ))}
              </div>
            )}
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
        {tab === 'overview' && (() => {
          const isInternalKey = (k: string) => k.startsWith('_') || k === 'source'
          const formatKey = (k: string) => k.replace(/_/g, ' ')
          const outcomes: any = inst.school_outcomes || {}
          const policies: any = inst.policies || {}
          const support: any = inst.support_services || {}
          const intlInfo: any = inst.international_info || {}
          const routing: any = (inst as any).inquiry_routing || {}

          const pctFmt = (v: any) => typeof v === 'number' && v <= 1 ? `${Math.round(v * 100)}%` : String(v)
          const numFmt = (v: any) => typeof v === 'number' ? v.toLocaleString() : String(v)

          return (
            <div className="space-y-5">
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

              {/* Graduate Outcomes — headline metrics + geographic + industries */}
              {Object.keys(outcomes).filter(k => !isInternalKey(k)).length > 0 && (
                <Card className="p-5">
                  <h2 className="font-semibold text-student-ink mb-3">Graduate Outcomes</h2>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
                    {outcomes.graduation_rate_6yr != null && (
                      <StatBlock label="6yr Grad Rate" value={pctFmt(outcomes.graduation_rate_6yr)} />
                    )}
                    {outcomes.graduation_rate_4yr != null && (
                      <StatBlock label="4yr Grad Rate" value={pctFmt(outcomes.graduation_rate_4yr)} />
                    )}
                    {outcomes.retention_rate_4yr != null && (
                      <StatBlock label="Retention" value={pctFmt(outcomes.retention_rate_4yr)} />
                    )}
                    {outcomes.graduate_school_yield != null && (
                      <StatBlock label="→ Grad School" value={pctFmt(outcomes.graduate_school_yield)} />
                    )}
                    {outcomes.alumni_network_size != null && (
                      <StatBlock
                        label="Alumni Network"
                        value={outcomes.alumni_network_size >= 1000
                          ? `${Math.round(outcomes.alumni_network_size / 1000)}K+`
                          : numFmt(outcomes.alumni_network_size)}
                      />
                    )}
                  </div>

                  {/* Geographic placement */}
                  {outcomes.geographic_placement && typeof outcomes.geographic_placement === 'object' && (
                    <div className="mb-4">
                      <p className="text-[11px] uppercase tracking-wider font-semibold text-student-text/70 mb-2">Where Graduates Go</p>
                      <div className="space-y-1.5">
                        {Object.entries(outcomes.geographic_placement)
                          .sort(([, a]: any, [, b]: any) => b - a)
                          .map(([region, pct]: any) => (
                            <div key={region} className="grid grid-cols-[140px_1fr_50px] gap-3 items-center text-sm">
                              <span className="text-student-text capitalize">{formatKey(region)}</span>
                              <div className="h-2 rounded-full bg-slate-100 overflow-hidden">
                                <div className="h-full bg-gradient-to-r from-blue-400 to-blue-600 rounded-full" style={{ width: `${pct * 100}%` }} />
                              </div>
                              <span className="text-student-ink font-semibold text-right tabular-nums">{pctFmt(pct)}</span>
                            </div>
                          ))}
                      </div>
                    </div>
                  )}

                  {/* Top employer industries */}
                  {Array.isArray(outcomes.top_employer_industries) && outcomes.top_employer_industries.length > 0 && (
                    <div>
                      <p className="text-[11px] uppercase tracking-wider font-semibold text-student-text/70 mb-2">Top Employer Industries</p>
                      <div className="flex flex-wrap gap-1.5">
                        {outcomes.top_employer_industries.map((ind: string, i: number) => (
                          <span key={i} className="inline-flex items-center gap-1 px-2.5 py-1 text-[11px] rounded-md bg-emerald-50 text-emerald-700 border border-emerald-200">
                            {ind}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  {outcomes._source && (
                    <a href={outcomes._source} target="_blank" rel="noopener noreferrer" className="text-[10px] text-student-text/50 italic mt-3 block hover:text-student">
                      Source ↗
                    </a>
                  )}
                </Card>
              )}

              {/* Support services — link rows */}
              {Object.keys(support).filter(k => !isInternalKey(k)).length > 0 && (
                <Card className="p-5">
                  <h2 className="font-semibold text-student-ink mb-3">Support Services</h2>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                    {Object.entries(support).filter(([k]) => !isInternalKey(k)).map(([key, val]: any) => {
                      const name = (val && typeof val === 'object' && val.name) || formatKey(key)
                      const url = val && typeof val === 'object' && val.url
                      const inner = (
                        <div className="flex items-center justify-between gap-2 px-3 py-2 rounded-lg bg-slate-50 border border-slate-100 hover:border-student transition-colors">
                          <span className="text-sm text-student-ink capitalize truncate">{name}</span>
                          {url && <Globe size={12} className="text-student-text/40 flex-shrink-0" />}
                        </div>
                      )
                      return url
                        ? <a key={key} href={url} target="_blank" rel="noopener noreferrer">{inner}</a>
                        : <div key={key}>{inner}</div>
                    })}
                  </div>
                </Card>
              )}

              {/* International Students */}
              {Object.keys(intlInfo).filter(k => !isInternalKey(k)).length > 0 && (
                <Card className="p-5">
                  <h2 className="font-semibold text-student-ink mb-3">International Students</h2>
                  <dl className="grid grid-cols-1 md:grid-cols-2 gap-3 text-sm">
                    {intlInfo.visa && typeof intlInfo.visa === 'object' && (
                      <div className="col-span-full px-3 py-2 rounded-lg bg-slate-50 border border-slate-100">
                        <dt className="text-[10px] uppercase tracking-wider font-semibold text-student-text/70 mb-1">{intlInfo.visa.office_name || 'Visa Office'}</dt>
                        {intlInfo.visa.email && <dd className="text-student-ink">{intlInfo.visa.email}</dd>}
                        {intlInfo.visa.phone && <dd className="text-student-text">{intlInfo.visa.phone}</dd>}
                      </div>
                    )}
                    {Array.isArray(intlInfo.supported_visas) && intlInfo.supported_visas.length > 0 && (
                      <div>
                        <dt className="text-student-text text-xs">Supported Visas</dt>
                        <dd className="mt-1 flex flex-wrap gap-1">
                          {intlInfo.supported_visas.map((v: string) => <Badge key={v} variant="info" size="sm">{v}</Badge>)}
                        </dd>
                      </div>
                    )}
                    {intlInfo.english_proficiency && typeof intlInfo.english_proficiency === 'object' && (
                      <div>
                        <dt className="text-student-text text-xs">English Proficiency</dt>
                        <dd className="text-student-ink">
                          {intlInfo.english_proficiency.url
                            ? <a href={intlInfo.english_proficiency.url} target="_blank" rel="noopener noreferrer" className="text-student hover:underline">Requirements ↗</a>
                            : 'Details available'}
                        </dd>
                      </div>
                    )}
                  </dl>
                </Card>
              )}

              {/* Policies */}
              {Object.keys(policies).filter(k => !isInternalKey(k)).length > 0 && (
                <Card className="p-5">
                  <h2 className="font-semibold text-student-ink mb-3">Policies</h2>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                    {Object.entries(policies).filter(([k]) => !isInternalKey(k)).map(([key, val]: any) => {
                      const summary = (val && typeof val === 'object' && val.summary) || null
                      const url = val && typeof val === 'object' && val.url
                      return (
                        <div key={key} className="px-3 py-2 rounded-lg bg-slate-50 border border-slate-100">
                          <div className="flex items-center justify-between gap-2 mb-0.5">
                            <p className="text-sm font-medium text-student-ink capitalize">{formatKey(key)}</p>
                            {url && <a href={url} target="_blank" rel="noopener noreferrer" className="text-[11px] text-student hover:underline flex-shrink-0">View ↗</a>}
                          </div>
                          {summary && <p className="text-[11px] text-student-text leading-snug">{summary}</p>}
                        </div>
                      )
                    })}
                  </div>
                </Card>
              )}

              {/* Inquiry routing — specialized contacts */}
              {Object.keys(routing).filter(k => !isInternalKey(k)).length > 0 && (
                <Card className="p-5">
                  <h2 className="font-semibold text-student-ink mb-3">Contact</h2>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                    {Object.entries(routing).filter(([k]) => !isInternalKey(k)).map(([key, val]: any) => {
                      const email = val && typeof val === 'object' && val.email
                      const phone = val && typeof val === 'object' && val.phone
                      const url = val && typeof val === 'object' && val.url
                      return (
                        <div key={key} className="px-3 py-2 rounded-lg bg-slate-50 border border-slate-100">
                          <p className="text-[10px] uppercase tracking-wider font-semibold text-student-text/70 mb-1 capitalize">{formatKey(key)}</p>
                          <div className="space-y-0.5 text-xs">
                            {email && <p><a href={`mailto:${email}`} className="text-student hover:underline">{email}</a></p>}
                            {phone && <p className="text-student-text">{phone}</p>}
                            {url && !email && !phone && <a href={url} target="_blank" rel="noopener noreferrer" className="text-student hover:underline text-xs">Website ↗</a>}
                          </div>
                        </div>
                      )
                    })}
                  </div>
                </Card>
              )}
            </div>
          )
        })()}

        {/* Schools Tab — the default, headline view */}
        {tab === 'schools' && (
          <div>
            {schoolList.length === 0 ? (
              <div className="text-center py-16 bg-white rounded-xl border border-divider">
                <GraduationCap size={32} className="mx-auto text-stone mb-3" />
                <p className="text-sm text-student-ink font-medium mb-1">No schools found</p>
                <p className="text-xs text-student-text">This university hasn't organized programs into schools yet — try the All Programs tab.</p>
              </div>
            ) : (
              <>
                <div className="flex items-baseline justify-between mb-3">
                  <p className="text-[13px] text-student-text">
                    <span className="font-semibold text-student-ink">{schoolList.length}</span> school{schoolList.length === 1 ? '' : 's'} at {inst.name}. Pick one to see its programs.
                  </p>
                  <button
                    onClick={() => setTab('programs')}
                    className="text-[12px] text-student hover:underline"
                  >
                    Skip schools, show all programs →
                  </button>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {schoolList.map(school => (
                    <SchoolCard
                      key={school.id}
                      school={school}
                      institutionName={inst.name}
                      onClick={() => navigate(`/s/institutions/${inst.id}/schools/${school.id}`)}
                    />
                  ))}
                </div>
              </>
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

/** Compact stat block for Graduate Outcomes section. */
function StatBlock({ label, value }: { label: string; value: string }) {
  return (
    <div className="px-3 py-2.5 rounded-lg bg-slate-50 border border-slate-100">
      <p className="text-[10px] uppercase tracking-wider font-semibold text-student-text/70">{label}</p>
      <p className="text-lg font-bold text-student-ink tabular-nums mt-0.5">{value}</p>
    </div>
  )
}
