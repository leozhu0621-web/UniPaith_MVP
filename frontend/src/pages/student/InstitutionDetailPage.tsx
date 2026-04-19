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
  BookOpen, Mail,
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

            {inst.support_services && Object.keys(inst.support_services).length > 0 && (
              <Card className="p-5">
                <h2 className="font-semibold text-student-ink mb-2">Support Services</h2>
                <div className="flex flex-wrap gap-2">
                  {Object.entries(inst.support_services).map(([key, val]) => (
                    <Badge key={key} variant="neutral">{typeof val === 'string' ? val : key.replace(/_/g, ' ')}</Badge>
                  ))}
                </div>
              </Card>
            )}

            {inst.policies && Object.keys(inst.policies).length > 0 && (
              <Card className="p-5">
                <h2 className="font-semibold text-student-ink mb-2">Policies</h2>
                <dl className="grid grid-cols-2 gap-2 text-sm">
                  {Object.entries(inst.policies).map(([key, val]) => (
                    <div key={key}>
                      <dt className="text-student-text capitalize">{key.replace(/_/g, ' ')}</dt>
                      <dd className="text-student-ink">{String(val)}</dd>
                    </div>
                  ))}
                </dl>
              </Card>
            )}

            {inst.international_info && Object.keys(inst.international_info).length > 0 && (
              <Card className="p-5">
                <h2 className="font-semibold text-student-ink mb-2">International Students</h2>
                <dl className="grid grid-cols-2 gap-2 text-sm">
                  {Object.entries(inst.international_info).map(([key, val]) => (
                    <div key={key}>
                      <dt className="text-student-text capitalize">{key.replace(/_/g, ' ')}</dt>
                      <dd className="text-student-ink">{String(val)}</dd>
                    </div>
                  ))}
                </dl>
              </Card>
            )}

            {inst.school_outcomes && Object.keys(inst.school_outcomes).length > 0 && (
              <Card className="p-5">
                <h2 className="font-semibold text-student-ink mb-2">Outcomes</h2>
                <dl className="grid grid-cols-2 gap-2 text-sm">
                  {Object.entries(inst.school_outcomes).map(([key, val]) => (
                    <div key={key}>
                      <dt className="text-student-text capitalize">{key.replace(/_/g, ' ')}</dt>
                      <dd className="text-student-ink font-medium">{typeof val === 'number' ? val.toLocaleString() : String(val)}</dd>
                    </div>
                  ))}
                </dl>
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
                <PostCard key={post.id} post={{ ...post, institution_name: inst.name }} />
              ))
            )}
          </div>
        )}
      </div>
    </div>
  )
}
