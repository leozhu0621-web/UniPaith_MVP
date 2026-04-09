import { useState } from 'react'
import { useParams, Link, useSearchParams } from 'react-router-dom'
import { useQuery, useMutation } from '@tanstack/react-query'
import {
  GraduationCap, MapPin, Clock, DollarSign, CalendarDays,
  Users, Globe, ExternalLink, BookOpen, CheckCircle2, ArrowLeft, MessageSquare,
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
  const gallery: string[] = Array.isArray(p?.media_urls) ? p.media_urls : []
  const tracks: string[] = Array.isArray(p?.tracks) ? p.tracks : []
  const highlights: string[] = Array.isArray(p?.highlights) ? p.highlights : []
  const faculty: Record<string, any>[] = Array.isArray(p?.faculty_contacts) ? p.faculty_contacts : []
  const appReqs: Record<string, any>[] = Array.isArray(p?.application_requirements) ? p.application_requirements : []
  const intakeRounds: Record<string, any>[] = Array.isArray(p?.intake_rounds) ? p.intake_rounds : []
  const outcomes: Record<string, any> = p?.outcomes_data && typeof p.outcomes_data === 'object' ? p.outcomes_data : {}

  const tabs = [
    { id: 'overview', label: 'Overview' },
    { id: 'admissions', label: 'Admissions' },
    { id: 'cost', label: 'Cost & Outcomes' },
    ...(events.length > 0 ? [{ id: 'events', label: `Events (${events.length})` }] : []),
    ...(gallery.length > 0 ? [{ id: 'gallery', label: 'Gallery' }] : []),
  ]

  // --- Loading ---
  if (programQ.isLoading) {
    return (
      <div className="min-h-screen bg-gray-50">
        <Header />
        <div className="max-w-5xl mx-auto px-6 py-10 space-y-6">
          <Skeleton className="h-10 w-96" />
          <Skeleton className="h-6 w-64" />
          <div className="grid grid-cols-3 gap-4">{Array.from({ length: 3 }).map((_, i) => <Skeleton key={i} className="h-24" />)}</div>
        </div>
      </div>
    )
  }

  // --- Not found ---
  if (!p) {
    return (
      <div className="min-h-screen bg-gray-50">
        <Header />
        <div className="max-w-5xl mx-auto px-6 py-16 text-center">
          <GraduationCap size={48} className="mx-auto text-gray-300 mb-4" />
          <h2 className="text-xl font-semibold text-gray-900 mb-2">Program not found</h2>
          <p className="text-gray-500 mb-6">This program may not be published or the link is incorrect.</p>
          <Link to="/browse" className="text-indigo-600 hover:underline">Browse programs</Link>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Header />

      <div className="max-w-5xl mx-auto px-6 py-8">
        {/* Back link */}
        {inst && (
          <Link to={`/school/${p.institution_id}`} className="inline-flex items-center gap-1 text-sm text-gray-500 hover:text-gray-700 mb-4">
            <ArrowLeft size={14} /> {inst.name}
          </Link>
        )}

        {/* Hero */}
        <div className="bg-white rounded-xl border border-gray-200 p-6 mb-6">
          <div className="flex items-start justify-between gap-6">
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-3 mb-1">
                <h1 className="text-2xl font-bold text-gray-900">{p.program_name}</h1>
                <Badge variant="info">{DEGREE_LABELS[p.degree_type] || p.degree_type}</Badge>
              </div>
              {p.department && <p className="text-gray-500 mb-1">{p.department}</p>}
              {inst && (
                <Link to={`/school/${p.institution_id}`} className="text-sm text-indigo-600 hover:underline">
                  {inst.name}
                </Link>
              )}

              {/* Quick stats */}
              <div className="flex flex-wrap gap-4 mt-4 text-sm text-gray-600">
                {p.tuition != null && (
                  <span className="flex items-center gap-1.5"><DollarSign size={14} /> {formatCurrency(p.tuition)}</span>
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

              {/* Deadline callout */}
              {p.application_deadline && (
                <div className="flex items-center gap-2 mt-3 text-sm">
                  <CalendarDays size={14} className="text-amber-600" />
                  <span className="text-amber-700 font-medium">Application deadline: {formatDate(p.application_deadline)}</span>
                </div>
              )}
            </div>

            {/* Actions */}
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

        {/* Tabs */}
        <Tabs tabs={tabs} activeTab={tab} onChange={setTab} />

        <div className="mt-6">
          {/* ===== OVERVIEW ===== */}
          {tab === 'overview' && (
            <div className="space-y-6">
              {p.description_text && (
                <Card className="p-5">
                  <h3 className="text-sm font-semibold text-gray-900 mb-2">About this program</h3>
                  <p className="text-sm text-gray-700 whitespace-pre-wrap">{p.description_text}</p>
                </Card>
              )}

              {p.who_its_for && (
                <Card className="p-5">
                  <h3 className="text-sm font-semibold text-gray-900 mb-2">Who it's for</h3>
                  <p className="text-sm text-gray-700 whitespace-pre-wrap">{p.who_its_for}</p>
                </Card>
              )}

              {tracks.length > 0 && (
                <Card className="p-5">
                  <h3 className="text-sm font-semibold text-gray-900 mb-3">Tracks & Concentrations</h3>
                  <div className="flex flex-wrap gap-2">
                    {tracks.map((t, i) => (
                      <Badge key={i} variant="info">{t}</Badge>
                    ))}
                  </div>
                </Card>
              )}

              {highlights.length > 0 && (
                <Card className="p-5">
                  <h3 className="text-sm font-semibold text-gray-900 mb-3">Highlights</h3>
                  <ul className="space-y-2">
                    {highlights.map((h, i) => (
                      <li key={i} className="flex items-start gap-2 text-sm text-gray-700">
                        <CheckCircle2 size={16} className="text-emerald-500 mt-0.5 shrink-0" />
                        {h}
                      </li>
                    ))}
                  </ul>
                </Card>
              )}

              {faculty.length > 0 && (
                <Card className="p-5">
                  <h3 className="text-sm font-semibold text-gray-900 mb-3">Faculty Contacts</h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    {faculty.map((f, i) => (
                      <div key={i} className="flex items-center gap-3 p-3 rounded-lg bg-gray-50">
                        <div className="w-9 h-9 rounded-full bg-indigo-100 flex items-center justify-center text-sm font-medium text-indigo-700">
                          {(f.name || '?')[0].toUpperCase()}
                        </div>
                        <div className="min-w-0">
                          <p className="text-sm font-medium text-gray-900 truncate">{f.name}</p>
                          {f.role && <p className="text-xs text-gray-500">{f.role}</p>}
                          {f.email && <p className="text-xs text-gray-400">{f.email}</p>}
                        </div>
                      </div>
                    ))}
                  </div>
                </Card>
              )}

              {/* Quick facts */}
              <Card className="p-5">
                <h3 className="text-sm font-semibold text-gray-900 mb-3">Quick Facts</h3>
                <div className="grid grid-cols-2 md:grid-cols-3 gap-4 text-sm">
                  <div><span className="text-gray-500">Degree:</span> <span className="font-medium">{DEGREE_LABELS[p.degree_type] || p.degree_type}</span></div>
                  {p.duration_months && <div><span className="text-gray-500">Duration:</span> <span className="font-medium">{p.duration_months} months</span></div>}
                  {p.delivery_format && <div><span className="text-gray-500">Format:</span> <span className="font-medium">{DELIVERY_FORMAT_LABELS[p.delivery_format] ?? p.delivery_format}</span></div>}
                  {p.campus_setting && <div><span className="text-gray-500">Setting:</span> <span className="font-medium">{CAMPUS_SETTING_LABELS[p.campus_setting] ?? p.campus_setting}</span></div>}
                  {p.program_start_date && <div><span className="text-gray-500">Start Date:</span> <span className="font-medium">{formatDate(p.program_start_date)}</span></div>}
                  {p.application_deadline && <div><span className="text-gray-500">Deadline:</span> <span className="font-medium">{formatDate(p.application_deadline)}</span></div>}
                </div>
              </Card>
            </div>
          )}

          {/* ===== ADMISSIONS ===== */}
          {tab === 'admissions' && (
            <div className="space-y-6">
              {/* Deadline + start date */}
              <Card className="p-5">
                <h3 className="text-sm font-semibold text-gray-900 mb-3">Key Dates</h3>
                <div className="grid grid-cols-2 gap-4 text-sm">
                  {p.application_deadline && (
                    <div className="flex items-center gap-2">
                      <CalendarDays size={16} className="text-amber-600" />
                      <div><span className="text-gray-500">Deadline:</span> <span className="font-medium">{formatDate(p.application_deadline)}</span></div>
                    </div>
                  )}
                  {p.program_start_date && (
                    <div className="flex items-center gap-2">
                      <CalendarDays size={16} className="text-indigo-600" />
                      <div><span className="text-gray-500">Start Date:</span> <span className="font-medium">{formatDate(p.program_start_date)}</span></div>
                    </div>
                  )}
                </div>
              </Card>

              {/* Requirements */}
              {p.requirements && Object.keys(p.requirements).length > 0 && (
                <Card className="p-5">
                  <h3 className="text-sm font-semibold text-gray-900 mb-3">Requirements</h3>
                  <dl className="space-y-2 text-sm">
                    {Object.entries(p.requirements).map(([k, v]) => (
                      <div key={k} className="flex justify-between border-b border-gray-100 pb-2">
                        <dt className="text-gray-500 capitalize">{k.replace(/_/g, ' ')}</dt>
                        <dd className="font-medium text-gray-900">{String(v)}</dd>
                      </div>
                    ))}
                  </dl>
                </Card>
              )}

              {/* Application requirements checklist */}
              {appReqs.length > 0 && (
                <Card className="p-5">
                  <h3 className="text-sm font-semibold text-gray-900 mb-3">Application Materials</h3>
                  <ul className="space-y-2">
                    {appReqs.map((req, i) => (
                      <li key={i} className="flex items-start gap-2 text-sm">
                        <CheckCircle2 size={16} className={`mt-0.5 shrink-0 ${req.required ? 'text-amber-500' : 'text-gray-300'}`} />
                        <div>
                          <span className="text-gray-900">{req.item || req.name || JSON.stringify(req)}</span>
                          {req.required && <Badge variant="warning" className="ml-2 text-[10px]">Required</Badge>}
                          {req.format && <span className="text-xs text-gray-400 ml-2">{req.format}</span>}
                        </div>
                      </li>
                    ))}
                  </ul>
                </Card>
              )}

              {/* Intake rounds */}
              {intakeRounds.length > 0 && (
                <Card className="p-5">
                  <h3 className="text-sm font-semibold text-gray-900 mb-3">Intake Rounds</h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    {intakeRounds.map((round, i) => (
                      <div key={i} className="p-3 rounded-lg bg-gray-50 border border-gray-100">
                        <p className="text-sm font-medium text-gray-900">{round.round_name || `Round ${i + 1}`}</p>
                        {round.deadline && <p className="text-xs text-gray-500 mt-1">Deadline: {formatDate(round.deadline)}</p>}
                        {round.capacity && <p className="text-xs text-gray-400">Capacity: {round.capacity}</p>}
                      </div>
                    ))}
                  </div>
                </Card>
              )}

              {/* Empty state */}
              {!p.requirements && appReqs.length === 0 && intakeRounds.length === 0 && (
                <EmptyState icon={<BookOpen size={40} />} title="No admissions details" description="This program has not published admissions requirements yet." />
              )}
            </div>
          )}

          {/* ===== COST & OUTCOMES ===== */}
          {tab === 'cost' && (
            <div className="space-y-6">
              <Card className="p-5">
                <h3 className="text-sm font-semibold text-gray-900 mb-3">Cost</h3>
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <p className="text-gray-500">Tuition</p>
                    <p className="text-2xl font-semibold text-gray-900 mt-1">{p.tuition != null ? formatCurrency(p.tuition) : 'Not published'}</p>
                  </div>
                  <div>
                    <p className="text-gray-500">Acceptance Rate</p>
                    <p className="text-2xl font-semibold text-gray-900 mt-1">{p.acceptance_rate != null ? formatPercent(p.acceptance_rate, 1) : 'Not published'}</p>
                  </div>
                </div>
              </Card>

              {Object.keys(outcomes).length > 0 ? (
                <Card className="p-5">
                  <h3 className="text-sm font-semibold text-gray-900 mb-3">Outcomes</h3>
                  <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                    {Object.entries(outcomes).map(([key, value]) => (
                      <div key={key} className="p-3 rounded-lg bg-gray-50">
                        <p className="text-xs text-gray-500 capitalize">{key.replace(/_/g, ' ')}</p>
                        <p className="text-lg font-semibold text-gray-900 mt-1">{typeof value === 'number' && value < 1 ? formatPercent(value, 0) : String(value)}</p>
                      </div>
                    ))}
                  </div>
                </Card>
              ) : (
                <Card className="p-5 text-center">
                  <p className="text-sm text-gray-500">Outcomes data has not been published for this program yet.</p>
                </Card>
              )}
            </div>
          )}

          {/* ===== EVENTS ===== */}
          {tab === 'events' && (
            <div className="space-y-3">
              {events.length === 0 ? (
                <EmptyState icon={<CalendarDays size={40} />} title="No upcoming events" description="Check back later for program-specific events." />
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

          {/* ===== GALLERY ===== */}
          {tab === 'gallery' && gallery.length > 0 && (
            <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
              {gallery.map((url, i) => (
                <a key={i} href={url} target="_blank" rel="noopener noreferrer" className="rounded-lg overflow-hidden border hover:shadow-md transition-shadow">
                  <img src={url} alt={`${p.program_name} gallery ${i + 1}`} className="w-full h-48 object-cover" />
                </a>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Request Info Modal */}
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
    </div>
  )
}

function Header() {
  return (
    <header className="bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between">
      <Link to="/" className="text-lg font-bold">UniPaith</Link>
      <div className="flex gap-3">
        <Link to="/browse" className="text-sm text-gray-600 hover:text-gray-900">Browse</Link>
        <Link to="/login" className="text-sm text-gray-600 hover:text-gray-900">Log in</Link>
        <Link to="/signup" className="text-sm bg-gray-900 text-white px-3 py-1 rounded hover:bg-gray-800">Sign up</Link>
      </div>
    </header>
  )
}
