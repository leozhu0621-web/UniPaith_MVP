import { useMemo, useState, type ComponentType } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  getPublicInstitution, getPublicPosts, getInstitutionSchools, submitInquiry,
} from '../../../api/institutions'
import { searchPrograms } from '../../../api/programs'
import {
  listEvents, rsvpEvent, cancelRsvp, getMyRsvps, addEventToCalendar,
  getMyFollows, followInstitution, unfollowInstitution,
} from '../../../api/events'
import { listSaved, saveProgram, unsaveProgram } from '../../../api/saved-lists'
import { useCompareStore } from '../../../stores/compare-store'
import { showToast } from '../../../stores/toast-store'
import ProgramCard from '../explore/cards/ProgramCard'
import SchoolCard from '../explore/cards/SchoolCard'
import PostCard from '../explore/cards/PostCard'
import Card from '../../../components/ui/Card'
import Button from '../../../components/ui/Button'
import Skeleton from '../../../components/ui/Skeleton'
import Modal from '../../../components/ui/Modal'
import Input from '../../../components/ui/Input'
import Select from '../../../components/ui/Select'
import Textarea from '../../../components/ui/Textarea'
import QueryError from '../../../components/ui/QueryError'
import {
  Bookmark, BookmarkCheck, MapPin, Globe, Users, Building2, BookOpen,
  Mail, Phone, CalendarPlus, Check, ChevronDown, X, Search, GraduationCap,
  Filter, ArrowRight, Calendar, Send, Link2,
} from 'lucide-react'
import type { Institution, ProgramSummary, InstitutionPost, SchoolSummary } from '../../../types'

type TabId = 'overview' | 'about' | 'schools' | 'programs' | 'events' | 'updates'

interface Props {
  institutionId: string
  isAuthenticated: boolean
}

/**
 * InstitutionDetail — the single student-facing School Detail view (Spec 12).
 *
 * One component, two surfaces: rendered authenticated at `/s/institutions/:id`
 * and public at `/school/:id` (Spec 12 §5, gap G-S9 — consolidated). Editorial,
 * text-driven, no campus photos (Spec 12 §9). Save school == follow the
 * institution (drives the Connect feed); public actions become sign-in CTAs.
 */
export default function InstitutionDetail({ institutionId, isAuthenticated }: Props) {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const compareStore = useCompareStore()
  const [searchParams, setSearchParams] = useSearchParams()

  const { data: institution, isLoading, isError: instError, refetch: refetchInst } = useQuery({
    queryKey: ['institution', institutionId],
    queryFn: () => getPublicInstitution(institutionId),
    enabled: !!institutionId,
  })

  const schoolsQ = useQuery({
    queryKey: ['institution-schools', institutionId],
    queryFn: () => getInstitutionSchools(institutionId),
    enabled: !!institutionId,
  })
  const schools = schoolsQ.data

  const programsQ = useQuery({
    queryKey: ['institution-programs', institutionId],
    queryFn: () => searchPrograms({ institution_id: institutionId, page_size: 100 }),
    enabled: !!institutionId,
  })
  const programsResp = programsQ.data

  const eventsQ = useQuery({
    queryKey: ['institution-events', institutionId],
    queryFn: () => listEvents({ institution_id: institutionId, limit: 30 }),
    enabled: !!institutionId,
  })
  const events = eventsQ.data

  const postsQ = useQuery({
    queryKey: ['institution-posts', institutionId],
    queryFn: () => getPublicPosts(institutionId),
    enabled: !!institutionId,
  })
  const posts = postsQ.data

  // Authenticated-only: RSVP set, saved programs, followed schools.
  const { data: rsvps } = useQuery({ queryKey: ['my-rsvps'], queryFn: getMyRsvps, enabled: isAuthenticated, retry: false })
  const { data: savedData } = useQuery({ queryKey: ['saved-programs'], queryFn: listSaved, enabled: isAuthenticated, retry: false })
  const { data: follows } = useQuery({ queryKey: ['my-follows'], queryFn: getMyFollows, enabled: isAuthenticated, retry: false })

  const inst = institution as Institution | undefined
  const schoolList: SchoolSummary[] = Array.isArray(schools) ? schools : []
  const programList: ProgramSummary[] = Array.isArray(programsResp?.items) ? programsResp.items : []
  const eventList: any[] = Array.isArray(events) ? events : []
  const postList: InstitutionPost[] = useMemo(() => {
    const list = Array.isArray(posts) ? [...posts] : []
    // Pinned posts first (Spec 12 §3.6).
    return list.sort((a, b) => Number(b.pinned ?? false) - Number(a.pinned ?? false))
  }, [posts])

  const rsvpSet = new Set((rsvps as any[] ?? []).map((r: any) => r.event_id))
  const savedIds = new Set((savedData as any[] ?? []).map((s: any) => String(s.program_id)))
  const followedIds = new Set((follows as any[] ?? []).map((f: any) => String(f.institution_id)))
  const isSaved = !!institutionId && followedIds.has(String(institutionId))

  // Default tab: Schools when the institution has sub-schools, else Overview
  // (Spec 12 §3.3 — Schools is the headline tab). A ?tab= param wins.
  const paramTab = searchParams.get('tab') as TabId | null
  const defaultTab: TabId = schoolList.length > 0 ? 'schools' : 'overview'
  const tab: TabId = paramTab ?? defaultTab
  const setTab = (next: TabId) => {
    const sp = new URLSearchParams(searchParams)
    sp.set('tab', next)
    setSearchParams(sp, { replace: true })
  }

  // ── Save school (= follow) ──────────────────────────────────────────────
  const followMut = useMutation({
    mutationFn: () => (isSaved ? unfollowInstitution(institutionId) : followInstitution(institutionId)),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['my-follows'] })
      queryClient.invalidateQueries({ queryKey: ['student-feed'] })
      showToast(isSaved ? 'Removed from your schools.' : 'Saved. You’ll see this school’s updates in Connect.', 'success')
    },
    onError: () => showToast('Something didn’t work. Try again.', 'error'),
  })
  const onSaveSchool = () => {
    if (!isAuthenticated) { navigate('/login'); return }
    followMut.mutate()
  }

  const rsvpMut = useMutation({
    mutationFn: (eventId: string) => (rsvpSet.has(eventId) ? cancelRsvp(eventId) : rsvpEvent(eventId)),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['institution-events'] })
      queryClient.invalidateQueries({ queryKey: ['my-rsvps'] })
    },
    onError: () => showToast('Couldn’t update your RSVP. Try again.', 'error'),
  })
  const onRsvp = (eventId: string) => {
    if (!isAuthenticated) { navigate('/login'); return }
    rsvpMut.mutate(eventId)
  }

  // Save/unsave a program. Guarded against double-clicks: a per-id in-flight set
  // drops repeat taps while a toggle is still resolving (ProgramCard's button has
  // no disabled state of its own).
  const saveProgramMut = useMutation({
    mutationFn: async (programId: string) => {
      if (savedIds.has(programId)) await unsaveProgram(programId)
      else await saveProgram(programId)
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['saved-programs'] }),
    onError: () => showToast('Couldn’t save that program. Try again.', 'error'),
  })
  const [savingIds, setSavingIds] = useState<Set<string>>(new Set())
  const toggleSaveProgram = (programId: string) => {
    if (!isAuthenticated) { navigate('/login'); return }
    if (savingIds.has(programId)) return
    setSavingIds(prev => new Set(prev).add(programId))
    saveProgramMut.mutate(programId, {
      onSettled: () => setSavingIds(prev => {
        const next = new Set(prev)
        next.delete(programId)
        return next
      }),
    })
  }

  // ── Request info (Spec 22 §7) — opens an inquiry routed per inquiry_routing ─
  const [inquiryOpen, setInquiryOpen] = useState(false)
  const [inquiryType, setInquiryType] = useState('general')
  const [inquirySubject, setInquirySubject] = useState('')
  const [inquiryMessage, setInquiryMessage] = useState('')
  const inquiryMut = useMutation({
    mutationFn: () => submitInquiry({
      institution_id: institutionId,
      subject: inquirySubject.trim(),
      message: inquiryMessage.trim(),
      inquiry_type: inquiryType,
    }),
    onSuccess: () => {
      setInquiryOpen(false)
      setInquirySubject('')
      setInquiryMessage('')
      showToast('Request sent. The school will be in touch.', 'success')
    },
    onError: () => showToast('Couldn’t send your request. Try again.', 'error'),
  })
  const onRequestInfo = () => {
    if (!isAuthenticated) { navigate('/login'); return }
    setInquiryOpen(true)
  }

  // ── Link builders (auth vs public surfaces) ─────────────────────────────
  const programHref = (id: string) => (isAuthenticated ? `/s/programs/${id}` : `/program/${id}`)
  const schoolHref = (sid: string) =>
    isAuthenticated ? `/s/institutions/${institutionId}/schools/${sid}` : `/school/${institutionId}/schools/${sid}`

  if (isLoading) {
    return (
      <div className="p-6 max-w-5xl mx-auto space-y-4">
        <Skeleton className="h-5 w-64" />
        <Skeleton className="h-40" />
        <Skeleton className="h-10 w-full" />
        <Skeleton className="h-64" />
      </div>
    )
  }

  // A failed institution fetch (network / 5xx) is retryable — distinct from a
  // genuine "not found" where the load succeeded but returned nothing.
  if (instError) {
    return (
      <div className="p-6 max-w-3xl mx-auto py-20">
        <QueryError detail="We couldn't load this school." onRetry={() => refetchInst()} />
      </div>
    )
  }

  if (!inst) {
    return (
      <div className="p-6 max-w-3xl mx-auto text-center py-20">
        <Building2 size={32} className="mx-auto text-muted-foreground mb-3" />
        <p className="text-sm text-foreground mb-4">Institution not found.</p>
        <Button size="sm" variant="secondary" onClick={() => navigate(isAuthenticated ? '/s/explore' : '/browse')}>
          {isAuthenticated ? 'Back to Match' : 'Browse programs'}
        </Button>
      </div>
    )
  }

  const location = [inst.city, inst.region, inst.country].filter(Boolean).join(', ')
  const eyebrow = classifyType(inst)

  const TABS: { id: TabId; label: string }[] = [
    { id: 'overview', label: 'Overview' },
    { id: 'about', label: 'About' },
    { id: 'schools', label: `Schools${schoolList.length ? ` (${schoolList.length})` : ''}` },
    { id: 'programs', label: `Programs${programList.length ? ` (${programList.length})` : ''}` },
    { id: 'events', label: 'Events' },
    { id: 'updates', label: 'Updates' },
  ]

  // Inquiry types offered in the Request-info modal — the institution's
  // configured routing keys, with a generic "general" always available.
  const inquiryTypes = ['general', ...Object.keys((inst.inquiry_routing as Record<string, unknown>) ?? {}).filter(k => k !== 'general')]

  return (
    <div className="p-6 max-w-5xl mx-auto">
      {/* Breadcrumb (Spec 12 §2, design system §7) */}
      <nav className="flex items-center gap-1.5 text-[13px] text-muted-foreground mb-4 flex-wrap" aria-label="Breadcrumb">
        {isAuthenticated ? (
          <>
            <button onClick={() => navigate('/s/explore')} className="hover:text-secondary transition-colors">Match</button>
            <span className="text-muted-foreground">·</span>
            <button onClick={() => navigate('/s/explore')} className="hover:text-secondary transition-colors">Search</button>
          </>
        ) : (
          <>
            <button onClick={() => navigate('/')} className="hover:text-secondary transition-colors">Home</button>
            <span className="text-muted-foreground">·</span>
            <button onClick={() => navigate('/browse')} className="hover:text-secondary transition-colors">Browse</button>
          </>
        )}
        <span className="text-muted-foreground">·</span>
        <span className="text-foreground font-medium truncate max-w-[40ch]" aria-current="page">{inst.name}</span>
      </nav>

      {/* Header */}
      <div className="bg-card rounded-xl border border-border p-6 mb-5">
        <div className="flex items-start gap-4">
          {/* Text-only monogram tile — brand rule: no logo images (Spec 12 §9) */}
          <div className="w-16 h-16 rounded-xl bg-muted border border-border/60 flex items-center justify-center flex-shrink-0">
            <span className="text-secondary font-bold text-xl tracking-tight">{monogram(inst.name)}</span>
          </div>

          <div className="flex-1 min-w-0">
            {eyebrow && (
              <p className="text-eyebrow uppercase text-secondary mb-1">{eyebrow}</p>
            )}
            <h1 className="text-2xl font-bold text-foreground leading-tight">{inst.name}</h1>
            <div className="flex items-center gap-x-3 gap-y-1 mt-1.5 text-[13px] text-muted-foreground flex-wrap">
              {location && <span className="inline-flex items-center gap-1"><MapPin size={13} /> {location}</span>}
              {inst.founded_year != null && <span className="inline-flex items-center gap-1"><Calendar size={13} /> Founded {inst.founded_year}</span>}
              {inst.campus_setting && <span className="inline-flex items-center gap-1"><Building2 size={13} /> {SETTING_LABELS[inst.campus_setting] ?? inst.campus_setting}</span>}
              {inst.student_body_size != null && <span className="inline-flex items-center gap-1"><Users size={13} /> {inst.student_body_size.toLocaleString()} students</span>}
            </div>

            {/* Secondary links (Spec 22 §3 — Web presence) */}
            {(inst.website_url || inst.contact_email || inst.contact_phone || hasSocialLinks(inst.social_links)) && (
              <div className="flex items-center gap-4 mt-2.5 text-[12px] flex-wrap">
                {inst.website_url && (
                  <a href={inst.website_url} target="_blank" rel="noopener noreferrer" className="inline-flex items-center gap-1 text-secondary hover:underline">
                    <Globe size={12} /> Website
                  </a>
                )}
                {inst.contact_email && (
                  <a href={`mailto:${inst.contact_email}`} className="inline-flex items-center gap-1 text-secondary hover:underline">
                    <Mail size={12} /> Contact
                  </a>
                )}
                {inst.contact_phone && (
                  <a href={`tel:${inst.contact_phone.replace(/\s/g, '')}`} className="inline-flex items-center gap-1 text-secondary hover:underline">
                    <Phone size={12} /> {inst.contact_phone}
                  </a>
                )}
                <SocialLinks links={inst.social_links} />
              </div>
            )}
          </div>
        </div>

        {/* Actions (Spec 12 §2) */}
        <div className="flex flex-wrap items-center gap-2 mt-5">
          <Button
            size="sm"
            variant={isSaved ? 'secondary' : 'tertiary'}
            onClick={onSaveSchool}
            disabled={followMut.isPending}
            aria-pressed={isSaved}
          >
            {isSaved ? <BookmarkCheck size={14} className="mr-1.5" /> : <Bookmark size={14} className="mr-1.5" />}
            {isAuthenticated ? (isSaved ? 'Saved' : 'Save school') : 'Sign in to save'}
          </Button>
          <Button size="sm" variant="tertiary" onClick={onRequestInfo}>
            <Send size={14} className="mr-1.5" />
            Request info
          </Button>
          {schoolList.length > 0 ? (
            <Button size="sm" variant="ghost" onClick={() => setTab('schools')}>
              View all schools <ArrowRight size={14} className="ml-1" />
            </Button>
          ) : (
            <Button size="sm" variant="ghost" onClick={() => setTab('programs')}>
              View all programs at this school <ArrowRight size={14} className="ml-1" />
            </Button>
          )}
        </div>
        {isAuthenticated && isSaved && (
          <p className="text-[11.5px] text-muted-foreground/80 mt-2">Following — this school&rsquo;s updates and events show up in Connect.</p>
        )}
      </div>

      {/* Tabs — underline in --accent (cobalt), Spec 12 §9 */}
      <TabBar tabs={TABS} active={tab} onChange={setTab} />

      <div className="mt-6">
        {tab === 'overview' && <OverviewTab inst={inst} schoolCount={schoolList.length} programCount={programList.length} />}
        {tab === 'about' && <AboutTab inst={inst} />}
        {tab === 'schools' && (
          schoolsQ.isError ? (
            <QueryError variant="inline" detail="We couldn't load this school's schools." onRetry={() => schoolsQ.refetch()} />
          ) : (
            <SchoolsTab
              schoolList={schoolList}
              institutionName={inst.name}
              onOpen={sid => navigate(schoolHref(sid))}
              onShowPrograms={() => setTab('programs')}
            />
          )
        )}
        {tab === 'programs' && (
          programsQ.isError ? (
            <QueryError variant="inline" detail="We couldn't load this school's programs." onRetry={() => programsQ.refetch()} />
          ) : (
            <ProgramsTab
              programs={programList}
              institutionName={inst.name}
              savedIds={savedIds}
              comparing={(id: string) => compareStore.has(id)}
              onSave={toggleSaveProgram}
              onCompare={(p) => compareStore.has(p.id)
                ? compareStore.remove(p.id)
                : compareStore.add({ program_id: p.id, program_name: p.program_name, institution_name: p.institution_name ?? inst.name, degree_type: p.degree_type })}
              onView={(id) => navigate(programHref(id))}
              onAsk={isAuthenticated ? (p) => navigate(`/s?prefill=${encodeURIComponent(`Tell me about ${p.program_name} at ${inst.name}. Is it a good fit?`)}`) : undefined}
            />
          )
        )}
        {tab === 'events' && (
          eventsQ.isError ? (
            <QueryError variant="inline" detail="We couldn't load this school's events." onRetry={() => eventsQ.refetch()} />
          ) : (
          <EventsTab
            events={eventList}
            institutionName={inst.name}
            isAuthenticated={isAuthenticated}
            rsvpSet={rsvpSet}
            onRsvp={onRsvp}
            rsvpPending={rsvpMut.isPending}
          />
          )
        )}
        {tab === 'updates' && (
          postsQ.isError ? (
            <QueryError variant="inline" detail="We couldn't load this school's updates." onRetry={() => postsQ.refetch()} />
          ) : (
            <UpdatesTab posts={postList} institutionName={inst.name} />
          )
        )}
      </div>

      {/* Request info (Spec 22 §7 / §15) — authenticated only; public surfaces
          route to sign-in before reaching here. */}
      <Modal
        isOpen={inquiryOpen}
        onClose={() => setInquiryOpen(false)}
        title={`Request info from ${inst.name}`}
        size="md"
        footer={
          <div className="flex justify-end gap-2">
            <Button variant="ghost" onClick={() => setInquiryOpen(false)}>Cancel</Button>
            <Button
              onClick={() => inquiryMut.mutate()}
              disabled={inquiryMut.isPending || !inquirySubject.trim() || !inquiryMessage.trim()}
            >
              {inquiryMut.isPending ? 'Sending…' : <><Send size={14} className="mr-1.5" /> Send request</>}
            </Button>
          </div>
        }
      >
        <div className="space-y-3">
          <p className="text-[13px] text-muted-foreground">Ask {inst.name} about admissions, programs, financial aid, or anything else. They’ll reply to your account email.</p>
          {inquiryTypes.length > 1 && (
            <Select
              label="Topic"
              options={inquiryTypes.map(t => ({ value: t, label: titleCase(t.replace(/_/g, ' ')) }))}
              value={inquiryType}
              onChange={e => setInquiryType(e.target.value)}
            />
          )}
          <Input label="Subject" value={inquirySubject} onChange={e => setInquirySubject(e.target.value)} placeholder="What would you like to know?" />
          <Textarea label="Message" value={inquiryMessage} onChange={e => setInquiryMessage(e.target.value)} rows={4} placeholder="Tell them about your interests and questions…" />
        </div>
      </Modal>
    </div>
  )
}

/* ──────────────────────────────────────────────────────────────────────────
   Social links — Spec 22 §3 Web presence. Text links only (brand rule: no logos).
   ────────────────────────────────────────────────────────────────────────── */
function hasSocialLinks(links: Record<string, string> | null | undefined): boolean {
  return !!links && Object.values(links).some(v => typeof v === 'string' && v.trim().length > 0)
}

function SocialLinks({ links }: { links: Record<string, string> | null | undefined }) {
  const entries = Object.entries(links ?? {}).filter(([, url]) => typeof url === 'string' && url.trim())
  if (!entries.length) return null
  return (
    <>
      {entries.map(([platform, url]) => (
        <a
          key={platform}
          href={url}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center gap-1 text-secondary hover:underline capitalize"
        >
          <Link2 size={12} /> {platform}
        </a>
      ))}
    </>
  )
}

/* ──────────────────────────────────────────────────────────────────────────
   Tab bar — cobalt underline (Spec 12 §9)
   ────────────────────────────────────────────────────────────────────────── */
function TabBar({ tabs, active, onChange }: { tabs: { id: TabId; label: string }[]; active: TabId; onChange: (t: TabId) => void }) {
  return (
    <div className="flex items-center gap-1 border-b border-border overflow-x-auto" role="tablist">
      {tabs.map(t => {
        const on = t.id === active
        return (
          <button
            key={t.id}
            role="tab"
            aria-selected={on}
            onClick={() => onChange(t.id)}
            className={`relative px-3.5 py-2.5 text-[13px] font-semibold whitespace-nowrap transition-colors ${
              on ? 'text-foreground' : 'text-muted-foreground hover:text-foreground'
            }`}
          >
            {t.label}
            {on && <span className="absolute left-2 right-2 -bottom-px h-0.5 rounded-full bg-secondary" />}
          </button>
        )
      })}
    </div>
  )
}

/* ──────────────────────────────────────────────────────────────────────────
   Overview tab — quick facts + headline outcomes (Spec 12 §3.1)
   ────────────────────────────────────────────────────────────────────────── */
function OverviewTab({ inst, schoolCount, programCount }: { inst: Institution; schoolCount: number; programCount: number }) {
  const rd: any = inst.ranking_data || {}
  const outcomes: any = inst.school_outcomes || {}
  const placement = outcomes.employed_or_continuing_ed ?? outcomes.first_destination_placement_rate
  const gradRate = outcomes.graduation_rate_6yr ?? rd.graduation_rate
  const sizeBand = sizeBandLabel(inst.student_body_size)
  // Geo + US-News/Niche-grade depth (College Scorecard), surfaced from school_outcomes.
  const loc: any = outcomes.location || {}
  const ts: any = outcomes.test_scores || {}
  const aid: any = outcomes.financial_aid || {}
  const demo: any = outcomes.demographics || {}
  const admitRate = outcomes.admit_rate ?? rd.acceptance_rate
  const grad4 = outcomes.completion_rate_4yr_150pct ?? gradRate
  const earn10 = outcomes.median_earnings_10yr ?? rd.median_earnings
  const netPrice = outcomes.avg_net_price
  const retention = outcomes.retention_rate_first_year ?? rd.retention_rate
  const rng = (a: any): string | null =>
    Array.isArray(a) && a[0] != null && a[1] != null ? `${a[0]}–${a[1]}` : null

  return (
    <div className="space-y-5">
      {inst.description_text && (
        <Card className="p-5">
          <p className="text-sm text-muted-foreground leading-relaxed">{trimSource(inst.description_text)}</p>
        </Card>
      )}

      <Card className="p-5">
        <h2 className="font-semibold text-foreground mb-3">Quick facts</h2>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
          <Fact label="Type" value={ownershipLabel(rd.ownership_type) ?? titleCase(inst.type)} />
          {inst.campus_setting && <Fact label="Campus setting" value={SETTING_LABELS[inst.campus_setting] ?? titleCase(inst.campus_setting)} />}
          {sizeBand && <Fact label="Size" value={sizeBand} />}
          {inst.founded_year != null && <Fact label="Founded" value={String(inst.founded_year)} />}
          {inst.student_body_size != null && <Fact label="Students" value={inst.student_body_size.toLocaleString()} />}
          <Fact label="Schools" value={String(schoolCount)} />
          <Fact label="Programs" value={String(programCount)} />
        </div>
        {rd.accreditor && (
          <p className="text-[11.5px] text-muted-foreground/70 mt-3 italic">Accredited by {rd.accreditor}</p>
        )}
      </Card>

      {/* Location — small Google Map showing where the campus is. */}
      {loc.lat != null && loc.lng != null && (
        <Card className="p-0 overflow-hidden">
          <div className="px-5 pt-5 pb-2 flex items-center gap-2">
            <MapPin size={14} className="text-secondary" />
            <h2 className="font-semibold text-foreground">Location</h2>
            <span className="ml-auto text-xs text-muted-foreground">
              {[inst.city, inst.region].filter(Boolean).join(', ')}
            </span>
          </div>
          <iframe
            title={`${inst.name} location map`}
            loading="lazy"
            referrerPolicy="no-referrer-when-downgrade"
            src={`https://maps.google.com/maps?q=${loc.lat},${loc.lng}&z=14&output=embed`}
            className="w-full h-64 border-0"
          />
        </Card>
      )}

      {/* Admissions & test scores (US News / Niche depth). */}
      {(admitRate != null ||
        rng(ts.sat_reading_25_75) ||
        rng(ts.sat_math_25_75) ||
        rng(ts.act_25_75) ||
        retention != null) && (
        <Card className="p-5">
          <h2 className="font-semibold text-foreground mb-3">Admissions</h2>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
            {admitRate != null && <Fact label="Acceptance rate" value={pct(admitRate)} />}
            {rng(ts.sat_reading_25_75) && <Fact label="SAT EBRW (25–75th)" value={rng(ts.sat_reading_25_75)!} />}
            {rng(ts.sat_math_25_75) && <Fact label="SAT Math (25–75th)" value={rng(ts.sat_math_25_75)!} />}
            {rng(ts.act_25_75) && <Fact label="ACT (25–75th)" value={rng(ts.act_25_75)!} />}
            {retention != null && <Fact label="First-year retention" value={pct(retention)} />}
          </div>
        </Card>
      )}

      {(placement != null || grad4 != null || earn10 != null || netPrice != null) && (
        <Card className="p-5">
          <h2 className="font-semibold text-foreground mb-1">Outcomes &amp; cost at a glance</h2>
          <p className="text-[11.5px] text-muted-foreground/70 mb-3">Institution-wide signals — specific program outcomes appear on each program page.</p>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
            {placement != null && <Fact label="Placement" value={pct(placement)} hint="employed or continuing ed" />}
            {grad4 != null && <Fact label="Graduation rate" value={pct(grad4)} />}
            {earn10 != null && <Fact label="Median earnings (10yr)" value={money(earn10)} />}
            {netPrice != null && <Fact label="Avg net price / yr" value={money(netPrice)} hint="after aid" />}
          </div>
        </Card>
      )}

      {/* Financial aid (Scorecard). */}
      {(aid.pell_grant_rate != null || aid.median_debt_completers != null || aid.federal_loan_rate != null) && (
        <Card className="p-5">
          <h2 className="font-semibold text-foreground mb-3">Financial aid</h2>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
            {aid.pell_grant_rate != null && <Fact label="Pell grant recipients" value={pct(aid.pell_grant_rate)} />}
            {aid.federal_loan_rate != null && <Fact label="Federal loan recipients" value={pct(aid.federal_loan_rate)} />}
            {aid.median_debt_completers != null && <Fact label="Median debt at graduation" value={money(aid.median_debt_completers)} />}
          </div>
        </Card>
      )}

      {/* Student body / diversity (Scorecard). */}
      {(demo.women != null || demo.white != null || demo.asian != null) && (
        <Card className="p-5">
          <h2 className="font-semibold text-foreground mb-3">Student body</h2>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
            {demo.women != null && <Fact label="Women" value={pct(demo.women)} />}
            {demo.asian != null && <Fact label="Asian" value={pct(demo.asian)} />}
            {demo.hispanic != null && <Fact label="Hispanic" value={pct(demo.hispanic)} />}
            {demo.black != null && <Fact label="Black" value={pct(demo.black)} />}
            {demo.white != null && <Fact label="White" value={pct(demo.white)} />}
          </div>
        </Card>
      )}

      <p className="text-[11px] leading-relaxed text-muted-foreground pt-1">
        <span className="font-semibold text-foreground/70">Data sources:</span>{' '}
        U.S. Department of Education College Scorecard; institution-published facts; map ©{' '}
        Google. Latest available data.
      </p>
    </div>
  )
}

/* ──────────────────────────────────────────────────────────────────────────
   About tab — environment, support, international, policies (Spec 12 §3.2)
   ────────────────────────────────────────────────────────────────────────── */
function AboutTab({ inst }: { inst: Institution }) {
  const isInternal = (k: string) => k.startsWith('_') || k === 'source'
  const fmtKey = (k: string) => k.replace(/_/g, ' ')
  const support: any = inst.support_services || {}
  const policies: any = inst.policies || {}
  const intl: any = inst.international_info || {}
  const supportKeys = Object.keys(support).filter(k => !isInternal(k))
  const policyKeys = Object.keys(policies).filter(k => !isInternal(k))
  const intlKeys = Object.keys(intl).filter(k => !isInternal(k))
  const nothing = !inst.campus_description && !inst.description_text && !supportKeys.length && !policyKeys.length && !intlKeys.length

  if (nothing) {
    return <EmptyBlock icon={BookOpen} title="More about this school is coming" body="Institution details haven't been published yet. Explore the schools and programs in the meantime." />
  }

  return (
    <div className="space-y-5">
      {(inst.campus_description || inst.description_text) && (
        <Card className="p-5">
          <h2 className="font-semibold text-foreground mb-2">Academic environment</h2>
          <p className="text-sm text-muted-foreground leading-relaxed whitespace-pre-line">{trimSource(inst.campus_description || inst.description_text || '')}</p>
        </Card>
      )}

      {supportKeys.length > 0 && (
        <Card className="p-5">
          <h2 className="font-semibold text-foreground mb-3">Support services</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
            {supportKeys.map(key => {
              const val: any = support[key]
              const name = (val && typeof val === 'object' && val.name) || titleCase(fmtKey(key))
              const url = val && typeof val === 'object' && val.url
              const inner = (
                <div className="flex items-center justify-between gap-2 px-3 py-2 rounded-lg bg-muted/60 border border-border/50 hover:border-secondary transition-colors">
                  <span className="text-sm text-foreground truncate">{name}</span>
                  {url && <Globe size={12} className="text-muted-foreground flex-shrink-0" />}
                </div>
              )
              return url
                ? <a key={key} href={url} target="_blank" rel="noopener noreferrer">{inner}</a>
                : <div key={key}>{inner}</div>
            })}
          </div>
        </Card>
      )}

      {intlKeys.length > 0 && (
        <Card className="p-5">
          <h2 className="font-semibold text-foreground mb-3">International students</h2>
          <div className="space-y-2 text-sm">
            {intlKeys.map(key => {
              const text = humanizeValue(intl[key])
              // Omit entries with no human-readable summary rather than leaking raw JSON.
              if (!text) return null
              return (
                <div key={key} className="px-3 py-2 rounded-lg bg-muted/60 border border-border/50">
                  <p className="text-[12px] font-medium text-foreground capitalize">{fmtKey(key)}</p>
                  <p className="text-[12px] text-muted-foreground mt-0.5 leading-snug">{text}</p>
                </div>
              )
            })}
          </div>
        </Card>
      )}

      {policyKeys.length > 0 && (
        <Card className="p-5">
          <h2 className="font-semibold text-foreground mb-3">Policies</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
            {policyKeys.map(key => {
              const val: any = policies[key]
              const summary = (val && typeof val === 'object' && val.summary) || (typeof val === 'string' ? val : null)
              const url = val && typeof val === 'object' && val.url
              return (
                <div key={key} className="px-3 py-2 rounded-lg bg-muted/60 border border-border/50">
                  <div className="flex items-center justify-between gap-2">
                    <p className="text-sm font-medium text-foreground capitalize">{fmtKey(key)}</p>
                    {url && <a href={url} target="_blank" rel="noopener noreferrer" className="text-[11px] text-secondary hover:underline flex-shrink-0">View</a>}
                  </div>
                  {summary && <p className="text-[11.5px] text-muted-foreground leading-snug mt-0.5">{summary}</p>}
                </div>
              )
            })}
          </div>
        </Card>
      )}
    </div>
  )
}

/* ──────────────────────────────────────────────────────────────────────────
   Schools tab (default) — Spec 12 §3.3
   ────────────────────────────────────────────────────────────────────────── */
function SchoolsTab({ schoolList, institutionName, onOpen, onShowPrograms }: {
  schoolList: SchoolSummary[]; institutionName: string; onOpen: (sid: string) => void; onShowPrograms: () => void
}) {
  if (schoolList.length === 0) {
    return <EmptyBlock icon={GraduationCap} title="No schools listed" body="This institution hasn't organized its programs into schools yet — browse all programs instead." action={{ label: 'View all programs', onClick: onShowPrograms }} />
  }
  return (
    <div>
      <div className="flex items-baseline justify-between mb-3">
        <p className="text-[13px] text-muted-foreground">
          <span className="font-semibold text-foreground">{schoolList.length}</span> school{schoolList.length === 1 ? '' : 's'} at {institutionName}. Open one to see its programs.
        </p>
        <button onClick={onShowPrograms} className="text-[12px] text-secondary hover:underline">Skip to all programs →</button>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {schoolList.map(school => (
          <SchoolCard key={school.id} school={school} institutionName={institutionName} onClick={() => onOpen(school.id)} />
        ))}
      </div>
    </div>
  )
}

/* ──────────────────────────────────────────────────────────────────────────
   Programs tab — Discovery chip + filter + sort UX (Spec 12 §3.4)
   ────────────────────────────────────────────────────────────────────────── */
interface ProgFilter { q: string; degree: string; delivery: string; sort: string }
const EMPTY_PROG_FILTER: ProgFilter = { q: '', degree: '', delivery: '', sort: 'relevance' }

function ProgramsTab({ programs, institutionName, savedIds, comparing, onSave, onCompare, onView, onAsk }: {
  programs: ProgramSummary[]
  institutionName: string
  savedIds: Set<string>
  comparing: (id: string) => boolean
  onSave: (id: string) => void
  onCompare: (p: ProgramSummary) => void
  onView: (id: string) => void
  onAsk?: (p: ProgramSummary) => void
}) {
  const [f, setF] = useState<ProgFilter>(EMPTY_PROG_FILTER)

  const degreeOpts = useMemo(() => uniqueSorted(programs.map(p => p.degree_type)), [programs])
  const deliveryOpts = useMemo(() => uniqueSorted(programs.map(p => p.delivery_format)), [programs])
  const hasScores = programs.some(p => programScore(p) != null)

  const filtered = useMemo(() => {
    let xs = programs.filter(p => {
      if (f.degree && p.degree_type !== f.degree) return false
      if (f.delivery && p.delivery_format !== f.delivery) return false
      if (f.q) {
        const hay = `${p.program_name} ${(p as any).field_of_study ?? ''} ${p.department ?? ''}`.toLowerCase()
        if (!hay.includes(f.q.toLowerCase())) return false
      }
      return true
    })
    xs = [...xs].sort((a, b) => {
      switch (f.sort) {
        case 'name': return a.program_name.localeCompare(b.program_name)
        case 'tuition': return (a.tuition ?? Infinity) - (b.tuition ?? Infinity)
        case 'deadline': return (dl(a) ?? Infinity) - (dl(b) ?? Infinity)
        default: return (programScore(b) ?? 0) - (programScore(a) ?? 0)
      }
    })
    return xs
  }, [programs, f])

  const activeChips: { label: string; clear: () => void }[] = []
  if (f.q) activeChips.push({ label: `Search · ${f.q}`, clear: () => setF(s => ({ ...s, q: '' })) })
  if (f.degree) activeChips.push({ label: `Degree · ${DEGREE_LABELS[f.degree] ?? f.degree}`, clear: () => setF(s => ({ ...s, degree: '' })) })
  if (f.delivery) activeChips.push({ label: `Delivery · ${titleCase(String(f.delivery).replace(/_/g, ' '))}`, clear: () => setF(s => ({ ...s, delivery: '' })) })

  return (
    <div className="space-y-4">
      {/* Filter bar */}
      <div className="flex flex-wrap items-center gap-2">
        <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-muted-foreground/70 uppercase tracking-wider mr-1"><Filter size={11} /> Filter</span>
        <div className="relative flex-1 min-w-[180px] max-w-xs">
          <Search size={13} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-muted-foreground/50" />
          <input
            value={f.q}
            onChange={e => setF(s => ({ ...s, q: e.target.value }))}
            placeholder="Search programs"
            className="w-full pl-8 pr-2.5 py-1.5 text-[12px] rounded-full border border-border bg-card text-foreground placeholder:text-muted-foreground/50 focus:outline-none focus:border-secondary focus:ring-1 focus:ring-secondary/40"
          />
        </div>
        {degreeOpts.length > 1 && (
          <SelectPill label="Degree" value={f.degree} onChange={v => setF(s => ({ ...s, degree: v }))}
            options={degreeOpts.map(d => ({ value: d, label: DEGREE_LABELS[d] ?? d }))} />
        )}
        {deliveryOpts.length > 1 && (
          <SelectPill label="Delivery" value={f.delivery} onChange={v => setF(s => ({ ...s, delivery: v }))}
            options={deliveryOpts.map(d => ({ value: d, label: titleCase(String(d).replace(/_/g, ' ')) }))} />
        )}
        <SelectPill label="Sort" value={f.sort} onChange={v => setF(s => ({ ...s, sort: v }))} hideEmpty
          options={[
            ...(hasScores ? [{ value: 'relevance', label: 'Best match' }] : []),
            { value: 'name', label: 'Name A–Z' },
            { value: 'tuition', label: 'Tuition (low to high)' },
            { value: 'deadline', label: 'Deadline (soonest)' },
          ]} />
      </div>

      {/* Constraint chips — locked scope chip first (Spec 12 §3.4) */}
      <div className="flex flex-wrap items-center gap-1.5">
        <span className="inline-flex items-center gap-1 px-2 py-0.5 text-[10.5px] rounded-full bg-secondary/10 text-secondary border border-secondary/25 font-medium">
          Institution · {institutionName}
        </span>
        {activeChips.map((c, i) => (
          <span key={i} className="inline-flex items-center gap-1 px-2 py-0.5 text-[10.5px] rounded-full bg-card text-foreground border border-secondary/40">
            {c.label}
            <button onClick={c.clear} className="ml-0.5 text-muted-foreground hover:text-foreground" aria-label={`Remove ${c.label}`}><X size={10} /></button>
          </span>
        ))}
        {activeChips.length > 0 && (
          <button onClick={() => setF(EMPTY_PROG_FILTER)} className="text-[11px] text-muted-foreground hover:text-foreground ml-1">Clear all</button>
        )}
      </div>

      {programs.length === 0 ? (
        <EmptyBlock icon={BookOpen} title="No published programs yet" body="This school hasn't published any programs yet. Check back soon." />
      ) : filtered.length === 0 ? (
        <p className="text-sm text-muted-foreground text-center py-10">No programs match these filters. <button onClick={() => setF(EMPTY_PROG_FILTER)} className="text-secondary hover:underline">Clear filters</button></p>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filtered.map(p => (
            <ProgramCard
              key={p.id}
              program={p}
              saved={savedIds.has(p.id)}
              comparing={comparing(p.id)}
              onSave={() => onSave(p.id)}
              onCompare={() => onCompare(p)}
              onAskCounselor={onAsk ? () => onAsk(p) : undefined}
              onView={() => onView(p.id)}
            />
          ))}
        </div>
      )}
    </div>
  )
}

/* ──────────────────────────────────────────────────────────────────────────
   Events tab — RSVP + add to calendar (Spec 12 §3.5)
   ────────────────────────────────────────────────────────────────────────── */
function EventsTab({ events, institutionName, isAuthenticated, rsvpSet, onRsvp, rsvpPending }: {
  events: any[]; institutionName: string; isAuthenticated: boolean; rsvpSet: Set<string>; onRsvp: (id: string) => void; rsvpPending: boolean
}) {
  if (events.length === 0) {
    return <EmptyBlock icon={CalendarPlus} title="No events scheduled" body={`${institutionName} hasn't scheduled any events yet.`} />
  }
  return (
    <div className="space-y-3">
      {events.map(ev => {
        const rsvped = rsvpSet.has(ev.id)
        const when = formatEventTime(ev.start_time)
        return (
          <Card key={ev.id} className="p-4 flex items-start justify-between gap-4">
            <div className="min-w-0">
              <h3 className="font-semibold text-foreground truncate">{ev.event_name}</h3>
              <p className="text-[13px] text-muted-foreground mt-0.5">{when}{ev.location ? ` · ${ev.location}` : ''}</p>
              {ev.event_type && <span className="inline-block mt-1.5 px-2 py-0.5 text-[10px] rounded-md bg-muted text-muted-foreground border border-border/60 capitalize">{String(ev.event_type).replace(/_/g, ' ')}</span>}
              {ev.capacity != null && <span className="ml-2 text-[11px] text-muted-foreground/70">{ev.rsvp_count}/{ev.capacity} spots</span>}
            </div>
            <div className="flex flex-col items-end gap-1.5 flex-shrink-0">
              <Button size="sm" variant={rsvped ? 'tertiary' : 'secondary'} onClick={() => onRsvp(ev.id)} disabled={rsvpPending}>
                {rsvped ? <><Check size={13} className="mr-1" /> Going</> : (isAuthenticated ? 'RSVP' : 'Sign in to RSVP')}
              </Button>
              <button
                onClick={() => addEventToCalendar(ev.id, ev.event_name).catch(() => showToast('Couldn’t generate the calendar file.', 'error'))}
                className="inline-flex items-center gap-1 text-[11px] text-secondary hover:underline"
              >
                <CalendarPlus size={11} /> Add to calendar
              </button>
            </div>
          </Card>
        )
      })}
    </div>
  )
}

/* ──────────────────────────────────────────────────────────────────────────
   Updates tab — pinned first (Spec 12 §3.6)
   ────────────────────────────────────────────────────────────────────────── */
function UpdatesTab({ posts, institutionName }: { posts: InstitutionPost[]; institutionName: string }) {
  if (posts.length === 0) {
    return (
      <EmptyBlock
        icon={BookOpen}
        title="No updates yet"
        body="Posts arrive here once you publish your first."
      />
    )
  }
  return (
    <div className="space-y-3">
      {posts.map(post => (
        <PostCard key={post.id} post={{ ...post, institution_name: institutionName } as any} />
      ))}
    </div>
  )
}

/* ──────────────────────────────────────────────────────────────────────────
   Shared bits
   ────────────────────────────────────────────────────────────────────────── */
function Fact({ label, value, hint }: { label: string; value: string; hint?: string }) {
  // Semantic foreground tokens (not fixed charcoal/slate) so the tile stays
  // legible when bg-muted flips to dark navy in dark mode.
  return (
    <div className="px-3 py-2.5 rounded-lg bg-muted/60 border border-border/50">
      <p className="text-[10px] uppercase tracking-wider font-semibold text-muted-foreground">{label}</p>
      <p className="text-[15px] font-bold text-foreground tabular-nums mt-0.5 leading-tight">{value}</p>
      {hint && <p className="text-[10.5px] text-muted-foreground mt-0.5">{hint}</p>}
    </div>
  )
}

function EmptyBlock({ icon: Icon, title, body, action }: {
  icon: ComponentType<{ size?: number; className?: string }>; title: string; body: string; action?: { label: string; onClick: () => void }
}) {
  return (
    <div className="text-center py-16 bg-card rounded-xl border border-border">
      <Icon size={32} className="mx-auto text-muted-foreground mb-3" />
      <p className="text-sm text-foreground font-medium mb-1">{title}</p>
      <p className="text-xs text-muted-foreground max-w-md mx-auto">{body}</p>
      {action && <Button size="sm" variant="secondary" className="mt-4" onClick={action.onClick}>{action.label}</Button>}
    </div>
  )
}

function SelectPill({ label, value, onChange, options, hideEmpty }: {
  label: string; value: string; onChange: (v: string) => void; options: { value: string; label: string }[]; hideEmpty?: boolean
}) {
  const [open, setOpen] = useState(false)
  const current = options.find(o => o.value === value)
  const active = !hideEmpty && !!value
  return (
    <div className="relative">
      <button
        type="button"
        onClick={() => setOpen(o => !o)}
        onBlur={() => setTimeout(() => setOpen(false), 150)}
        className={`inline-flex items-center gap-1 px-2.5 py-1.5 text-[11px] font-medium rounded-full border transition-colors ${
          active ? 'bg-secondary text-secondary-foreground border-secondary' : 'bg-card text-foreground border-border hover:border-secondary'
        }`}
      >
        {hideEmpty && current ? current.label : label}{active ? `: ${current?.label}` : ''}
        <ChevronDown size={11} className={open ? 'rotate-180 transition-transform' : 'transition-transform'} />
      </button>
      {open && (
        <div className="absolute z-40 top-full left-0 mt-1 min-w-[180px] rounded-lg border border-border bg-card shadow-lg py-1">
          {!hideEmpty && (
            <button onMouseDown={() => { onChange(''); setOpen(false) }} className="w-full text-left px-3 py-1.5 text-[12px] text-muted-foreground hover:bg-muted">Any {label.toLowerCase()}</button>
          )}
          {options.map(o => (
            <button key={o.value} onMouseDown={() => { onChange(o.value); setOpen(false) }}
              className={`w-full text-left px-3 py-1.5 text-[12px] hover:bg-muted ${o.value === value ? 'text-secondary font-medium' : 'text-foreground'}`}>
              {o.label}
            </button>
          ))}
        </div>
      )}
    </div>
  )
}

/* ── helpers ─────────────────────────────────────────────────────────────── */
const SETTING_LABELS: Record<string, string> = { urban: 'Urban', suburban: 'Suburban', rural: 'Rural' }
const DEGREE_LABELS: Record<string, string> = {
  certificate: 'Certificate', associate: 'Associate', bachelors: "Bachelor's", bachelor: "Bachelor's",
  masters: "Master's", master: "Master's", doctorate: 'Doctorate', phd: 'PhD', professional: 'Professional',
}

function monogram(name: string): string {
  const stop = new Set(['of', 'the', 'and', 'at', 'for', 'de', 'la'])
  const words = name.split(/\s+/).filter(w => w && !stop.has(w.toLowerCase()))
  if (words.length === 0) return name.slice(0, 2).toUpperCase()
  if (words.length === 1) return words[0].slice(0, 2).toUpperCase()
  return (words[0][0] + words[1][0]).toUpperCase()
}

function classifyType(inst: Institution): string | null {
  const rd: any = inst.ranking_data || {}
  // Ownership (Private / Public / …) qualifies the noun; the noun itself comes
  // from inst.type (authoritative) — never both fall back to "University", which
  // produced the "University University" doubling when ownership_type was absent.
  const ownership = ownershipLabel(rd.ownership_type)
  const research = rd.carnegie_classification && /research/i.test(String(rd.carnegie_classification))
  const noun = inst.type ? titleCase(inst.type) : 'University'
  const parts = [ownership, research ? 'Research' : null, noun].filter(Boolean)
  return parts.length ? parts.join(' ') : null
}

function ownershipLabel(t?: string): string | null {
  if (!t) return null
  return t.split('_').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ')
}

function sizeBandLabel(n?: number | null): string | null {
  if (n == null) return null
  if (n < 2000) return 'Small'
  if (n < 15000) return 'Medium'
  if (n < 30000) return 'Large'
  return 'Very large'
}

function titleCase(s?: string | null): string {
  if (!s) return ''
  return s.split(/[\s_]+/).map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ')
}

function pct(v: any): string {
  if (typeof v !== 'number') return String(v)
  return v <= 1 ? `${Math.round(v * 100)}%` : `${Math.round(v)}%`
}

function money(n: number): string {
  if (n >= 1e6) return `$${(n / 1e6).toFixed(1)}M`
  if (n >= 1e3) return `$${Math.round(n / 1e3)}K`
  return `$${n.toLocaleString()}`
}

function trimSource(s: string): string {
  return s.replace(/\s*\[Source:.*?\]\s*/g, '').trim()
}

// Render a JSONB value as human-readable text. Scalars/arrays stringify cleanly;
// objects surface only their summary/note. Returns null (caller omits the row)
// rather than ever leaking raw `{...}` JSON to the user.
function humanizeValue(val: unknown): string | null {
  if (val == null) return null
  if (typeof val === 'string') return val.trim() || null
  if (typeof val === 'number' || typeof val === 'boolean') return String(val)
  if (Array.isArray(val)) {
    const parts = val.map(v => humanizeValue(v)).filter((v): v is string => !!v)
    return parts.length ? parts.join(', ') : null
  }
  if (typeof val === 'object') {
    const o = val as Record<string, unknown>
    const s = o.summary ?? o.note ?? o.description ?? o.label ?? o.name
    return typeof s === 'string' && s.trim() ? s.trim() : null
  }
  return null
}

function uniqueSorted(xs: (string | null | undefined)[]): string[] {
  return Array.from(new Set(xs.filter((x): x is string => !!x))).sort()
}

function dl(p: ProgramSummary): number | null {
  const d = (p as any).application_deadline
  if (!d) return null
  const t = new Date(d).getTime()
  return Number.isNaN(t) ? null : t
}

// Dual-score migration: prefer fitness_score, fall back to legacy match_score
// (Phase E keeps match_score dual-written for one release).
function programScore(p: ProgramSummary): number | null {
  const s = (p as any).fitness_score ?? (p as any).match_score
  return typeof s === 'number' ? s : null
}

function formatEventTime(iso: string): string {
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return ''
  return d.toLocaleString('en-US', { month: 'short', day: 'numeric', year: 'numeric', hour: 'numeric', minute: '2-digit' })
}
