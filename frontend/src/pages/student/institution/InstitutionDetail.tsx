import { useEffect, useMemo, useState, type ComponentType } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  getPublicInstitution, getPublicPosts, getInstitutionSchools,
} from '../../../api/institutions'
import { searchPrograms } from '../../../api/programs'
import {
  listEvents, getMyFollows, followInstitution, unfollowInstitution,
} from '../../../api/events'
import { listSaved, saveProgram, unsaveProgram } from '../../../api/saved-lists'
import { useCompareStore } from '../../../stores/compare-store'
import { showToast } from '../../../stores/toast-store'
import ProgramCard from '../explore/cards/ProgramCard'
import SchoolCard from '../explore/cards/SchoolCard'
import NewsGrid from '../../../components/NewsGrid'
import Card from '../../../components/ui/Card'
import Button from '../../../components/ui/Button'
import Skeleton from '../../../components/ui/Skeleton'
import QueryError from '../../../components/ui/QueryError'
import {
  Bookmark, BookmarkCheck, MapPin, Globe, Building2, BookOpen,
  Mail, Phone, ChevronDown, ChevronLeft, ChevronRight, X, Search, GraduationCap,
  Filter, ArrowRight, Link2, Award, Trophy, DollarSign, TrendingUp, Users, FlaskConical, Camera,
} from 'lucide-react'
import type { Institution, ProgramSummary, InstitutionPost, SchoolSummary } from '../../../types'
import { AdmissionsFunnel, ChipList, DiversityBar, RankingBadge, StatBar } from './overviewWidgets'

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
 * Niche-modeled, led by a campus-photo hero that fades into the page background;
 * clicking the hero opens the campus-photo lightbox (school_outcomes.campus_photos).
 * Save school == follow the institution (drives the Connect feed); public actions
 * become sign-in CTAs.
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

  // institution_scope: only institution-wide items, so a school/program copy of
  // the same article doesn't duplicate the institution-wide one.
  const eventsQ = useQuery({
    queryKey: ['institution-events', institutionId],
    queryFn: () => listEvents({ institution_id: institutionId, limit: 30, institution_scope: true }),
    enabled: !!institutionId,
  })
  const events = eventsQ.data

  const postsQ = useQuery({
    queryKey: ['institution-posts', institutionId],
    queryFn: () => getPublicPosts(institutionId, { institution_scope: true }),
    enabled: !!institutionId,
  })
  const posts = postsQ.data

  // Authenticated-only: saved programs, followed schools.
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

  const savedIds = new Set((savedData as any[] ?? []).map((s: any) => String(s.program_id)))
  const followedIds = new Set((follows as any[] ?? []).map((f: any) => String(f.institution_id)))
  const isSaved = !!institutionId && followedIds.has(String(institutionId))

  // Default tab: Schools when the institution has sub-schools, else Overview
  // Overview is the headline tab — it now carries the rich, Niche-style context
  // (report card · rankings · distinction · facts). A ?tab= param still wins.
  const paramTab = searchParams.get('tab') as TabId | null
  const defaultTab: TabId = 'overview'
  // Events + Updates merged into one tab; map legacy ?tab=updates deep links.
  const tab: TabId = (paramTab === 'updates' ? 'events' : paramTab) ?? defaultTab
  const setTab = (next: TabId) => {
    const sp = new URLSearchParams(searchParams)
    sp.set('tab', next)
    setSearchParams(sp, { replace: true })
  }

  // ── Save school (= follow) ──────────────────────────────────────────────
  // Optimistic so the button flips instantly on click; rolls back on error.
  // The action is captured explicitly (not from the `isSaved` closure) so the
  // optimistic cache write can't race the in-flight request.
  const followMut = useMutation({
    mutationFn: (action: 'follow' | 'unfollow') =>
      action === 'unfollow' ? unfollowInstitution(institutionId) : followInstitution(institutionId),
    onMutate: async (action: 'follow' | 'unfollow') => {
      await queryClient.cancelQueries({ queryKey: ['my-follows'] })
      const prev = queryClient.getQueryData(['my-follows'])
      queryClient.setQueryData(['my-follows'], (old: any) => {
        const list = Array.isArray(old) ? old : []
        if (action === 'unfollow') {
          return list.filter((f: any) => String(f.institution_id) !== String(institutionId))
        }
        if (list.some((f: any) => String(f.institution_id) === String(institutionId))) return list
        return [...list, { institution_id: institutionId }]
      })
      return { prev }
    },
    onError: (err: any, _action, ctx: any) => {
      if (ctx?.prev !== undefined) queryClient.setQueryData(['my-follows'], ctx.prev)
      showToast(err?.response?.data?.detail || 'Something didn’t work. Try again.', 'error')
    },
    onSuccess: (_data, action) => {
      queryClient.invalidateQueries({ queryKey: ['student-feed'] })
      showToast(
        action === 'unfollow' ? 'Removed from your schools.' : 'Saved. You’ll see this school’s updates in Connect.',
        'success',
      )
    },
    onSettled: () => queryClient.invalidateQueries({ queryKey: ['my-follows'] }),
  })
  const onSaveSchool = () => {
    if (!isAuthenticated) { navigate('/login'); return }
    followMut.mutate(isSaved ? 'unfollow' : 'follow')
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
  // Campus-photo lightbox — null = closed, otherwise the index being viewed.
  const [galleryAt, setGalleryAt] = useState<number | null>(null)
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


  // ── Link builders (auth vs public surfaces) ─────────────────────────────
  const programHref = (id: string) => (isAuthenticated ? `/s/programs/${id}` : `/program/${id}`)
  const schoolHref = (sid: string) =>
    isAuthenticated ? `/s/institutions/${institutionId}/schools/${sid}` : `/school/${institutionId}/schools/${sid}`

  if (isLoading) {
    return (
      <div className="p-6 max-w-5xl w-full mx-auto space-y-4">
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

  const eyebrow = classifyType(inst)
  // Hero campus photo — first raster image in the gallery (logos are SVG → skipped).
  const heroPhoto = (inst.media_gallery ?? []).find(u => /\.(jpe?g|png|webp|avif)(\?|$)/i.test(u)) ?? null
  // Attribution for the campus hero photo (e.g. "Wikimedia Commons / Author (CC BY-SA 4.0)").
  const mediaCredit: string | null = ((inst.school_outcomes as any)?.media_credit) || null
  // Campus-photo gallery — verified [{url, credit}] from school_outcomes.campus_photos;
  // falls back to the single legacy hero photo. Clicking the hero opens the lightbox.
  const campusPhotos: { url: string; credit: string | null }[] = (() => {
    const raw = (inst.school_outcomes as any)?.campus_photos
    const list = (Array.isArray(raw) ? raw : [])
      .map((p: any) => ({ url: typeof p?.url === 'string' ? p.url : '', credit: p?.credit || null }))
      .filter(p => /\.(jpe?g|png|webp|avif)(\?|$)/i.test(p.url))
    if (list.length) return list
    return heroPhoto ? [{ url: heroPhoto, credit: mediaCredit }] : []
  })()
  const heroUrl = campusPhotos[0]?.url ?? heroPhoto
  const heroCredit = campusPhotos[0]?.credit ?? mediaCredit
  // The header is intentionally chip-free — no founded/ranking/acceptance/enrollment
  // line. Founded lives in Quick facts; ranking in the Rankings section; acceptance
  // in the Overview stat card; enrollment in Quick facts / Diversity.

  const TABS: { id: TabId; label: string }[] = [
    { id: 'overview', label: 'Overview' },
    { id: 'about', label: 'About' },
    { id: 'events', label: 'Events & Updates' },
    { id: 'schools', label: `Schools${schoolList.length ? ` (${schoolList.length})` : ''}` },
    { id: 'programs', label: `Programs${programList.length ? ` (${programList.length})` : ''}` },
  ]

  // Inquiry types offered in the Request-info modal — the institution's
  // configured routing keys, with a generic "general" always available.

  return (
    <div className="p-6 max-w-5xl w-full mx-auto">
      {/* Breadcrumb (Spec 12 §2, design system §7) */}
      <nav className="flex items-center gap-1.5 text-[13px] text-muted-foreground mb-4 flex-wrap" aria-label="Breadcrumb">
        {isAuthenticated ? (
          <>
            <button onClick={() => navigate('/s/explore')} className="hover:text-secondary transition-colors">Discover</button>
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

      {/* Hero — campus photo fading into the page background. No logo, no geo. */}
      <div className="relative rounded-xl overflow-hidden border border-border mb-5 bg-background">
        {/* Photo banner — click to browse the campus-photo gallery. */}
        <div
          className={`relative h-52 sm:h-64 md:h-72 ${heroUrl ? 'cursor-zoom-in' : ''}`}
          {...(heroUrl
            ? {
                role: 'button' as const,
                tabIndex: 0,
                'aria-label': `View ${campusPhotos.length > 1 ? `all ${campusPhotos.length} campus photos` : 'campus photo'}`,
                onClick: () => setGalleryAt(0),
                onKeyDown: (e: React.KeyboardEvent) => {
                  if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); setGalleryAt(0) }
                },
              }
            : {})}
        >
          {heroUrl ? (
            <img src={heroUrl} alt="" aria-hidden="true" className="absolute inset-0 h-full w-full object-cover" />
          ) : (
            <div className="absolute inset-0 bg-gradient-to-br from-secondary/10 to-background" />
          )}
          {/* Fade to the cream page background at the bottom; soft top scrim for glare. */}
          <div
            className="absolute inset-0"
            style={{
              background:
                'linear-gradient(to bottom, rgba(10,18,36,0.30) 0%, rgba(10,18,36,0.04) 24%, rgba(10,18,36,0) 44%, hsl(var(--background)) 97%)',
            }}
          />
          {heroUrl && heroCredit && (
            <p className="absolute top-1.5 right-2.5 text-[10px] text-white/75 drop-shadow-sm" title="Campus photo credit">
              Photo: {heroCredit}
            </p>
          )}
          {campusPhotos.length > 1 && (
            <span className="absolute top-1.5 left-2.5 inline-flex items-center gap-1.5 rounded-full bg-black/45 px-2.5 py-1 text-[11px] font-medium text-white backdrop-blur-sm">
              <Camera size={12} /> {campusPhotos.length} photos
            </span>
          )}
        </div>

        {/* Identity — overlaps onto the cream gradient base; dark text reads cleanly. */}
        <div className="relative -mt-20 px-5 sm:px-7 pb-6">
          {eyebrow && <p className="text-eyebrow uppercase text-secondary mb-1.5">{eyebrow}</p>}
          <h1 className="text-2xl sm:text-3xl md:text-[2.5rem] font-bold text-foreground leading-[1.08] tracking-tight max-w-[22ch]">
            {inst.name}
          </h1>

          {/* Web presence (Spec 22 §3) */}
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

          {/* Actions (Spec 12 §2) */}
          <div className="flex flex-wrap items-center gap-2 mt-4">
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
          (eventsQ.isError || postsQ.isError) ? (
            <QueryError variant="inline" detail="We couldn't load events & updates." onRetry={() => { eventsQ.refetch(); postsQ.refetch() }} />
          ) : (
            <NewsGrid
              posts={postList}
              events={eventList}
              emptyText={`${inst.name} hasn't posted any events or updates yet.`}
            />
          )
        )}
      </div>

      {galleryAt !== null && campusPhotos.length > 0 && (
        <PhotoLightbox
          photos={campusPhotos}
          index={Math.min(galleryAt, campusPhotos.length - 1)}
          schoolName={inst.name}
          onNavigate={setGalleryAt}
          onClose={() => setGalleryAt(null)}
        />
      )}
    </div>
  )
}

/* ──────────────────────────────────────────────────────────────────────────
   Campus-photo lightbox — opened by clicking the hero banner. Scroll through
   the gallery with the arrows / arrow keys / dots; Esc or backdrop closes.
   Each photo shows its own verified credit.
   ────────────────────────────────────────────────────────────────────────── */
function PhotoLightbox({ photos, index, schoolName, onNavigate, onClose }: {
  photos: { url: string; credit: string | null }[]
  index: number
  schoolName: string
  onNavigate: (i: number) => void
  onClose: () => void
}) {
  const count = photos.length
  const prev = () => onNavigate((index - 1 + count) % count)
  const next = () => onNavigate((index + 1) % count)

  // Keyboard: Esc closes, arrows navigate. Lock page scroll while open.
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose()
      else if (e.key === 'ArrowLeft' && count > 1) onNavigate((index - 1 + count) % count)
      else if (e.key === 'ArrowRight' && count > 1) onNavigate((index + 1) % count)
    }
    window.addEventListener('keydown', onKey)
    const prevOverflow = document.body.style.overflow
    document.body.style.overflow = 'hidden'
    return () => {
      window.removeEventListener('keydown', onKey)
      document.body.style.overflow = prevOverflow
    }
  }, [index, count, onNavigate, onClose])

  const photo = photos[index]
  return (
    <div
      className="fixed inset-0 z-50 bg-black/90 flex flex-col items-center justify-center p-4 sm:p-8"
      role="dialog"
      aria-modal="true"
      aria-label={`${schoolName} campus photos, ${index + 1} of ${count}`}
      onClick={onClose}
    >
      <button
        type="button"
        onClick={onClose}
        aria-label="Close photo viewer"
        className="absolute top-3 right-3 rounded-full bg-white/10 hover:bg-white/20 p-2 text-white transition-colors"
      >
        <X size={18} />
      </button>

      <div className="relative max-w-5xl w-full flex items-center justify-center" onClick={e => e.stopPropagation()}>
        {count > 1 && (
          <button
            type="button"
            onClick={prev}
            aria-label="Previous photo"
            className="absolute left-0 sm:-left-2 z-10 rounded-full bg-white/10 hover:bg-white/20 p-2.5 text-white transition-colors"
          >
            <ChevronLeft size={20} />
          </button>
        )}
        <img
          src={photo.url}
          alt={`${schoolName} campus photo ${index + 1} of ${count}`}
          className="max-h-[78vh] w-auto max-w-full rounded-lg object-contain select-none"
          draggable={false}
        />
        {count > 1 && (
          <button
            type="button"
            onClick={next}
            aria-label="Next photo"
            className="absolute right-0 sm:-right-2 z-10 rounded-full bg-white/10 hover:bg-white/20 p-2.5 text-white transition-colors"
          >
            <ChevronRight size={20} />
          </button>
        )}
      </div>

      <div className="mt-3 flex flex-col items-center gap-2" onClick={e => e.stopPropagation()}>
        {photo.credit && (
          <p className="text-[11px] text-white/70" title="Photo credit">Photo: {photo.credit}</p>
        )}
        {count > 1 && (
          <div className="flex items-center gap-2" role="tablist" aria-label="Choose photo">
            {photos.map((_, i) => (
              <button
                key={i}
                type="button"
                role="tab"
                aria-selected={i === index}
                aria-label={`Photo ${i + 1}`}
                onClick={() => onNavigate(i)}
                className={`h-2 rounded-full transition-all ${i === index ? 'w-5 bg-white' : 'w-2 bg-white/40 hover:bg-white/60'}`}
              />
            ))}
          </div>
        )}
        {count > 1 && <p className="text-[11px] text-white/50">{index + 1} / {count}</p>}
      </div>
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
    <div className="flex items-center gap-1 border-b border-border overflow-x-auto overflow-y-hidden" role="tablist">
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
            {on && <span className="absolute left-2 right-2 bottom-0 h-0.5 rounded-full bg-secondary" />}
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

  // ── Niche-style headline blocks (all grounded in real fields) ─────────────
  const flag: any = outcomes.flagship || {}
  const keyStats: { value: string; label: string; hint?: string }[] = []
  if (admitRate != null) keyStats.push({ value: `${(admitRate * 100).toFixed(admitRate < 0.1 ? 1 : 0)}%`, label: 'Acceptance rate' })
  if (netPrice != null) keyStats.push({ value: money(netPrice), label: 'Avg net price', hint: 'per year, after aid' })
  if (earn10 != null) keyStats.push({ value: money(earn10), label: 'Median earnings', hint: '10 yrs after entry' })
  if (grad4 != null) keyStats.push({ value: pct(grad4), label: 'Graduation rate' })
  const rankings: { key: string; label: string; rank: number; year?: number }[] = []
  for (const [k, v] of Object.entries(rd)) {
    if (v && typeof v === 'object' && typeof (v as any).rank === 'number') {
      rankings.push({ key: k, label: rankingLabel(k), rank: (v as any).rank, year: (v as any).year })
    }
  }
  const enrollTotal = flag.enrollment_total ?? inst.student_body_size
  const gradCount =
    enrollTotal != null && inst.student_body_size != null && enrollTotal > inst.student_body_size
      ? enrollTotal - inst.student_body_size
      : null
  const industries: string[] = Array.isArray(outcomes.top_employer_industries)
    ? outcomes.top_employer_industries
    : []
  const hasFunnel = flag.applicants != null && flag.admits != null && admitRate != null
  const diversity = [
    { label: 'Asian', pct: demo.asian as number },
    { label: 'White', pct: demo.white as number },
    { label: 'Hispanic', pct: demo.hispanic as number },
    { label: 'Black', pct: demo.black as number },
  ]
    .filter(s => typeof s.pct === 'number' && s.pct > 0)
    .sort((a, b) => b.pct - a.pct)
  const costSource = Array.isArray(outcomes.sources)
    ? outcomes.sources.find(
        (s: any) => typeof s?.source === 'string' && s.source.toLowerCase().includes('scorecard'),
      )
    : undefined

  return (
    <div className="space-y-5">
      {/* Key stats — the Niche-style "at a glance" report card. */}
      {keyStats.length > 0 && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {keyStats.map(s => (
            <Card key={s.label} className="p-4">
              <p className="text-[1.9rem] leading-none font-bold text-foreground tracking-tight tabular-nums">{s.value}</p>
              {/* The hint qualifier (e.g. "per year, after aid", "10 yrs after
                  entry") lives in the label's hover tooltip to declutter. */}
              <p className="text-[12px] font-medium text-foreground/80 mt-2" title={s.hint || undefined}>{s.label}</p>
            </Card>
          ))}
        </div>
      )}

      {/* Editorial intro */}
      {inst.description_text && (
        <Card className="p-5">
          <p className="text-sm text-muted-foreground leading-relaxed whitespace-pre-line">{trimSource(inst.description_text)}</p>
          <IntroSourceLine outcomes={outcomes} />
        </Card>
      )}

      {/* Rankings — badge row; the #1 earns the gold beat */}
      {rankings.length > 0 && (
        <Card className="p-5">
          <h2 className="font-semibold text-foreground mb-3 flex items-center gap-2"><Trophy size={15} className="text-secondary" /> Rankings</h2>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5">
            {rankings.map(r => (
              <RankingBadge
                key={r.label}
                rank={r.rank}
                label={r.label}
                year={r.year}
                peak={r.rank === 1}
                href={rankingHref(r.key, outcomes.sources)}
              />
            ))}
          </div>
        </Card>
      )}

      {/* Admissions — funnel + test scores + retention */}
      {(hasFunnel || rng(ts.sat_reading_25_75) || rng(ts.sat_math_25_75) || rng(ts.act_25_75) || retention != null) && (
        <Card className="p-5">
          <h2 className="font-semibold text-foreground mb-3">Admissions</h2>
          {hasFunnel && (
            <div className="mb-4">
              <AdmissionsFunnel applicants={Number(flag.applicants)} admits={Number(flag.admits)} rate={admitRate} cycle={flag.admissions_cycle} />
            </div>
          )}
          {(rng(ts.sat_reading_25_75) || rng(ts.sat_math_25_75) || rng(ts.act_25_75) || retention != null) && (
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              {rng(ts.sat_reading_25_75) && <Fact label="SAT EBRW (25–75th)" value={rng(ts.sat_reading_25_75)!} />}
              {rng(ts.sat_math_25_75) && <Fact label="SAT Math (25–75th)" value={rng(ts.sat_math_25_75)!} />}
              {rng(ts.act_25_75) && <Fact label="ACT (25–75th)" value={rng(ts.act_25_75)!} />}
              {retention != null && <Fact label="First-year retention" value={pct(retention)} />}
            </div>
          )}
        </Card>
      )}

      {/* Cost & aid — net price lead + aid bars + debt (parent-facing) */}
      {(netPrice != null || aid.pell_grant_rate != null || aid.federal_loan_rate != null || aid.median_debt_completers != null) && (
        <Card className="p-5">
          <h2 className="font-semibold text-foreground mb-3 flex items-center gap-2"><DollarSign size={15} className="text-secondary" /> Cost &amp; aid</h2>
          <div className="grid md:grid-cols-2 gap-x-6 gap-y-4">
            <div className="space-y-3">
              {netPrice != null && (
                <div>
                  {/* Sticker-cost contrast folded into the value's hover; the
                      descriptor condensed from a full sentence to a short label. */}
                  <p
                    className="text-2xl font-bold text-foreground tabular-nums leading-none"
                    title={aid.cost_of_attendance != null ? `Sticker cost of attendance ${money(aid.cost_of_attendance)}/yr before aid` : undefined}
                  >{money(netPrice)}</p>
                  <p className="text-[12px] text-muted-foreground mt-1">Avg net price — per year, after aid</p>
                </div>
              )}
            </div>
            <div className="space-y-3 self-center">
              {aid.pell_grant_rate != null && <StatBar label="Pell grant recipients" pct={aid.pell_grant_rate} />}
              {aid.federal_loan_rate != null && <StatBar label="Federal loan recipients" pct={aid.federal_loan_rate} />}
            </div>
          </div>
          {(aid.tuition_free_rate != null || aid.no_loan_debt_rate != null || aid.median_scholarship != null || aid.median_debt_completers != null) && (
            <div className="mt-4 grid grid-cols-2 md:grid-cols-4 gap-3 border-t border-border/60 pt-4">
              {aid.tuition_free_rate != null && <Fact label="Attend tuition-free" value={pct(aid.tuition_free_rate)} />}
              {aid.no_loan_debt_rate != null && <Fact label="Graduate debt-free" value={pct(aid.no_loan_debt_rate)} />}
              {aid.median_scholarship != null && <Fact label="Median scholarship" value={money(aid.median_scholarship)} />}
              {aid.median_debt_completers != null && <Fact label="Median debt at graduation" value={money(aid.median_debt_completers)} />}
            </div>
          )}
          {costSource && (
            <p className="text-[11px] text-muted-foreground/70 mt-3">
              Source:{' '}
              {costSource.url ? (
                <a href={costSource.url} target="_blank" rel="noopener noreferrer" className="text-secondary hover:underline">
                  {costSource.source}
                </a>
              ) : (
                costSource.source
              )}
              {costSource.year ? ` · ${costSource.year}` : ''}
            </p>
          )}
        </Card>
      )}

      {/* Outcomes — placement, earnings, top industries */}
      {(placement != null || earn10 != null || industries.length > 0) && (
        <Card className="p-5">
          <h2 className="font-semibold text-foreground mb-3 flex items-center gap-2"><TrendingUp size={15} className="text-secondary" /> Outcomes</h2>
          {(placement != null || earn10 != null) && (
            <div className="grid grid-cols-2 gap-3 mb-3">
              {placement != null && <OutcomeStat label="Employed or continuing ed" value={pct(placement)} />}
              {earn10 != null && <OutcomeStat label="Median earnings" value={money(earn10)} hint="10 yrs after entry" />}
            </div>
          )}
          {industries.length > 0 && (
            <>
              <p className="text-[12px] font-medium text-foreground/80 mb-1.5">Top industries</p>
              <ChipList items={industries} />
            </>
          )}
        </Card>
      )}

      {/* Diversity — race/ethnicity + women lead; compact enrollment underneath */}
      {(diversity.length > 0 || demo.women != null || enrollTotal != null) && (
        <Card className="p-5">
          {/* Enrollment breakdown folded into the heading's hover tooltip (was a
              muted caption line under the bar — declutter). */}
          <h2
            className="font-semibold text-foreground mb-3 flex items-center gap-2"
            title={
              enrollTotal != null
                ? [
                    inst.student_body_size != null ? `${inst.student_body_size.toLocaleString()} undergraduate` : null,
                    gradCount != null ? `${gradCount.toLocaleString()} graduate` : null,
                    `${Number(enrollTotal).toLocaleString()} total enrollment`,
                  ]
                    .filter(Boolean)
                    .join(' · ')
                : undefined
            }
          >
            <Users size={15} className="text-secondary" /> Diversity
          </h2>
          {diversity.length > 0 && (
            <div className="mb-4">
              <p className="text-[12px] font-medium text-foreground/80 mb-1.5">Race &amp; ethnicity</p>
              <DiversityBar segments={diversity} />
            </div>
          )}
        </Card>
      )}

      {/* Quick facts — deduped (no duplicate acceptance/size band) + enriched.
          The Carnegie classification is folded into the heading's hover tooltip
          (was an italic caption line — declutter). */}
      <Card className="p-5">
        <h2
          className="font-semibold text-foreground mb-3"
          title={rd.carnegie_classification ? String(rd.carnegie_classification) : undefined}
        >
          Quick facts
        </h2>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
          <Fact label="Type" value={ownershipLabel(rd.ownership_type) ?? titleCase(inst.type)} />
          {inst.campus_setting && <Fact label="Campus setting" value={SETTING_LABELS[inst.campus_setting] ?? titleCase(inst.campus_setting)} />}
          {inst.founded_year != null && <Fact label="Founded" value={String(inst.founded_year)} />}
          <Fact label="Schools" value={String(schoolCount)} />
          <Fact label="Programs" value={String(programCount)} />
          {rd.accreditor && <Fact label="Accreditation" value={String(rd.accreditor)} />}
        </div>
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

      {/* Sources — data-driven from school_outcomes.sources when present
          (each with year + link), else a generic citation line. */}
      {Array.isArray(outcomes.sources) && outcomes.sources.length > 0 ? (
        <Card className="p-5">
          <h2 className="font-semibold text-foreground mb-3 flex items-center gap-2">
            <BookOpen size={15} className="text-secondary" /> Sources
          </h2>
          <ul className="space-y-1.5">
            {outcomes.sources.map((s: any, i: number) => (
              <li key={i} className="text-[12px] text-muted-foreground">
                {s.label ? <span className="text-foreground/80">{s.label}: </span> : null}
                {s.url ? (
                  <a href={s.url} target="_blank" rel="noopener noreferrer" className="text-secondary hover:underline">
                    {s.source}
                  </a>
                ) : (
                  <span>{s.source}</span>
                )}
                {s.year ? ` · ${s.year}` : ''}
              </li>
            ))}
          </ul>
        </Card>
      ) : (
        <p className="text-[11px] leading-relaxed text-muted-foreground pt-1">
          <span className="font-semibold text-foreground/70">Data sources:</span>{' '}
          U.S. Department of Education College Scorecard; institution-published facts; map ©{' '}
          Google. Latest available data.
        </p>
      )}
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
  // Institutional depth (relocated from Overview): recognition, scale, research, campus life.
  const outcomes: any = inst.school_outcomes || {}
  const flag: any = outcomes.flagship || {}
  const scale: any = outcomes.scale || {}
  const recognition: { value: string; label: string }[] = []
  if (flag.nobel_laureates != null) recognition.push({ value: String(flag.nobel_laureates), label: 'Nobel laureates' })
  if (flag.us_presidents != null) recognition.push({ value: String(flag.us_presidents), label: 'U.S. Presidents' })
  if (flag.macarthur_fellows != null) recognition.push({ value: String(flag.macarthur_fellows), label: 'MacArthur Fellows' })
  if (flag.pulitzer_prizes != null) recognition.push({ value: String(flag.pulitzer_prizes), label: 'Pulitzer Prizes' })
  if (flag.national_medal_science != null) recognition.push({ value: String(flag.national_medal_science), label: 'National Medal of Science' })
  if (flag.national_medal_tech != null) recognition.push({ value: String(flag.national_medal_tech), label: 'National Medal of Technology' })
  const scaleStats: { value: string; label: string }[] = []
  if (scale.faculty_count != null) scaleStats.push({ value: Number(scale.faculty_count).toLocaleString(), label: 'Faculty' })
  if (scale.student_faculty_ratio) scaleStats.push({ value: String(scale.student_faculty_ratio), label: 'Student–faculty ratio' })
  if (scale.research_centers != null) scaleStats.push({ value: `${scale.research_centers}+`, label: 'Research centers & labs' })
  if (scale.endowment_usd != null) scaleStats.push({ value: `$${(scale.endowment_usd / 1e9).toFixed(1)}B`, label: 'Endowment' })
  if (scale.campus_acres != null) scaleStats.push({ value: `${Number(scale.campus_acres).toLocaleString()} acres`, label: 'Campus' })
  if (scale.undergrad_majors != null) scaleStats.push({ value: String(scale.undergrad_majors), label: 'Undergraduate majors' })
  const research: any = outcomes.research || {}
  const researchLabs: string[] = Array.isArray(research.labs) ? research.labs : []
  const researchAreas: string[] = Array.isArray(research.areas) ? research.areas : []
  const campusLife: any = outcomes.campus_life || {}
  const campusStats: { value: string; label: string }[] = []
  if (campusLife.varsity_sports != null) campusStats.push({ value: String(campusLife.varsity_sports), label: campusLife.athletics_division ? `Varsity sports · ${campusLife.athletics_division}` : 'Varsity sports' })
  if (campusLife.student_orgs != null) campusStats.push({ value: String(campusLife.student_orgs), label: 'Student organizations' })
  if (campusLife.arts_groups != null) campusStats.push({ value: `${campusLife.arts_groups}+`, label: 'Arts groups' })
  if (campusLife.greek_life) campusStats.push({ value: String(campusLife.greek_life), label: 'Greek life (FSILGs)' })
  if (campusLife.residence_halls != null) campusStats.push({ value: String(campusLife.residence_halls), label: 'Residence halls' })
  if (campusLife.housing) campusStats.push({ value: String(campusLife.housing), label: 'On-campus housing' })
  const labLinks: Record<string, string> = (research.lab_links && typeof research.lab_links === 'object') ? research.lab_links : {}
  // Resources come from the routine as {name,url} and from MIT as {label,url};
  // accept either (and a bare url) so the "Explore & get involved" links always
  // show a label instead of an empty arrow button.
  const campusResources: { label: string; url: string }[] = (Array.isArray(campusLife.resources) ? campusLife.resources : [])
    .map((r: any) => (typeof r === 'string'
      ? { label: r, url: r }
      : { label: r?.label || r?.name || r?.title || r?.url || '', url: r?.url || r?.href || '' }))
    .filter((r: { label: string; url: string }) => r.label && r.url)
  const basics: any = outcomes.campus_basics || {}
  const facts = [
    inst.type ? { label: 'Type', value: titleCase(inst.type) } : null,
    inst.founded_year != null ? { label: 'Founded', value: String(inst.founded_year) } : null,
    basics.location ? { label: 'Location', value: String(basics.location) } : null,
    inst.campus_setting ? { label: 'Campus setting', value: titleCase(inst.campus_setting) } : null,
    basics.academic_calendar ? { label: 'Academic calendar', value: String(basics.academic_calendar) } : null,
    // Campus size/description shown as its own box (was a caption line below).
    inst.campus_description ? { label: 'Campus', value: trimSource(inst.campus_description) } : null,
  ].filter(Boolean) as { label: string; value: string }[]
  const nothing = !inst.description_text && !supportKeys.length && !policyKeys.length && !intlKeys.length && !facts.length

  if (nothing) {
    return <EmptyBlock icon={BookOpen} title="More about this school is coming" body="Institution details haven't been published yet. Explore the schools and programs in the meantime." />
  }

  return (
    <div className="space-y-5">

      {/* Recognition — accolades with context */}
      {recognition.length > 0 && (
        <Card className="p-5">
          {/* "Among faculty & alumni" scope note → heading hover tooltip. */}
          <h2 className="font-semibold text-foreground mb-3 flex items-center gap-2" title="Among faculty & alumni"><Award size={15} className="text-secondary" /> Recognition</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            {recognition.map(d => <Fact key={d.label} label={d.label} value={d.value} />)}
          </div>
        </Card>
      )}

      {/* By the numbers — institutional scale (MIT Facts) */}
      {scaleStats.length > 0 && (
        <Card className="p-5">
          <h2 className="font-semibold text-foreground mb-3 flex items-center gap-2"><Building2 size={15} className="text-secondary" /> By the numbers</h2>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
            {scaleStats.map(s => <Fact key={s.label} label={s.label} value={s.value} />)}
          </div>
        </Card>
      )}

      {/* Campus resources — research + campus life + links, merged. */}
      {(researchLabs.length > 0 || researchAreas.length > 0 || campusStats.length > 0 || campusResources.length > 0) && (
        <Card className="p-5">
          <h2
            className="font-semibold text-foreground mb-3 flex items-center gap-2"
            title={
              scale.research_centers != null || research.industry_collaborators != null
                ? [
                    scale.research_centers != null ? `${scale.research_centers}+ centers, labs & institutes` : null,
                    research.industry_collaborators != null ? `~${research.industry_collaborators} industry collaborators` : null,
                  ]
                    .filter(Boolean)
                    .join(' · ')
                : undefined
            }
          >
            <FlaskConical size={15} className="text-secondary" /> Campus resources
          </h2>

          {researchLabs.length > 0 && (
            <div className="mb-4">
              <p className="text-[12px] font-medium text-foreground/80 mb-1.5">Notable labs &amp; institutes</p>
              <div className="flex flex-wrap gap-2">
                {researchLabs.map(name => {
                  const url = labLinks[name]
                  return url ? (
                    <a key={name} href={url} target="_blank" rel="noopener noreferrer" className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-[12px] font-medium border border-border bg-card text-foreground/80 hover:text-secondary hover:border-secondary/40 transition-colors">
                      {name} ↗
                    </a>
                  ) : (
                    <span key={name} className="inline-flex items-center px-2.5 py-1 rounded-full text-[12px] font-medium border border-border bg-card text-foreground/80">{name}</span>
                  )
                })}
              </div>
            </div>
          )}

          {researchAreas.length > 0 && (
            <div className="mb-4">
              <p className="text-[12px] font-medium text-foreground/80 mb-1.5">Research areas</p>
              <ChipList items={researchAreas} />
            </div>
          )}

          {campusStats.length > 0 && (
            <div className="mb-4">
              <p className="text-[12px] font-medium text-foreground/80 mb-2">Campus life</p>
              <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                {campusStats.map(s => <Fact key={s.label} label={s.label} value={s.value} />)}
              </div>
            </div>
          )}

          {campusResources.length > 0 && (
            <div>
              <p className="text-[12px] font-medium text-foreground/80 mb-1.5">Explore &amp; get involved</p>
              <div className="flex flex-wrap gap-2">
                {campusResources.map(r => (
                  <a key={r.label} href={r.url} target="_blank" rel="noopener noreferrer" className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-[12px] font-medium border border-secondary/20 bg-secondary/10 text-secondary hover:bg-secondary/15 transition-colors">
                    {r.label} ↗
                  </a>
                ))}
              </div>
            </div>
          )}
        </Card>
      )}

      {facts.length > 0 && (
        <Card className="p-5">
          <h2 className="font-semibold text-foreground mb-3">Basic Info</h2>
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
            {facts.map(f => (
              <div key={f.label} className="px-3 py-2 rounded-lg bg-muted/60 border border-border/50">
                <p className="text-[11px] font-semibold uppercase tracking-wide text-muted-foreground">{f.label}</p>
                <p className="text-sm font-medium text-foreground mt-0.5">{f.value}</p>
              </div>
            ))}
          </div>
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
   Shared bits
   ────────────────────────────────────────────────────────────────────────── */
/** A "Source:" line under descriptive prose — surfaces the official primary
 *  facts source (e.g. "MIT Facts", "Harvard at a Glance") from
 *  school_outcomes.sources. Renders nothing if absent. */
function IntroSourceLine({ outcomes }: { outcomes: { sources?: { source: string; url?: string; year?: number }[] } }) {
  const list = outcomes?.sources
  const s = Array.isArray(list)
    ? list.find(x => typeof x?.source === 'string' && /facts|at a glance/i.test(x.source))
    : undefined
  if (!s) return null
  return (
    <p className="text-[11px] text-muted-foreground/70 mt-2">
      Source:{' '}
      {s.url ? (
        <a href={s.url} target="_blank" rel="noopener noreferrer" className="text-secondary hover:underline">
          {s.source}
        </a>
      ) : (
        s.source
      )}
      {s.year ? ` · ${s.year}` : ''}
    </p>
  )
}

// A bigger, headline-weight stat tile for the Outcomes card (the two numbers
// students/parents scan first). Larger value + label than the compact Fact tile.
function OutcomeStat({ label, value, hint }: { label: string; value: string; hint?: string }) {
  return (
    <div className="px-4 py-4 rounded-lg bg-muted/60 border border-border/50" title={hint || undefined}>
      <p className="text-[11px] uppercase tracking-wider font-semibold text-muted-foreground">{label}</p>
      <p className="text-[28px] sm:text-3xl font-bold text-foreground tabular-nums mt-1.5 leading-none">{value}</p>
    </div>
  )
}

function Fact({ label, value, hint }: { label: string; value: string; hint?: string }) {
  // Semantic foreground tokens (not fixed charcoal/slate) so the tile stays
  // legible when bg-muted flips to dark navy in dark mode. The hint qualifier
  // is folded into the tile's hover tooltip to declutter.
  return (
    <div className="px-3 py-2.5 rounded-lg bg-muted/60 border border-border/50" title={hint || undefined}>
      <p className="text-[10px] uppercase tracking-wider font-semibold text-muted-foreground">{label}</p>
      <p className="text-[15px] font-bold text-foreground tabular-nums mt-0.5 leading-tight">{value}</p>
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

function titleCase(s?: string | null): string {
  if (!s) return ''
  return s.split(/[\s_]+/).map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ')
}

function rankingLabel(key: string): string {
  const map: Record<string, string> = {
    qs_world_university_rankings: 'QS World University Rankings',
    times_higher_education: 'Times Higher Education',
    us_news_national: 'U.S. News — National Universities',
    arwu: 'Academic Ranking of World Universities',
  }
  return map[key] ?? key.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())
}

const RANKING_SOURCE_KEYWORD: Record<string, string> = {
  qs_world_university_rankings: 'qs',
  times_higher_education: 'times higher',
  us_news_national: 'u.s. news',
}

/** Link a ranking to its reference page by matching the stored sources list. */
function rankingHref(key: string, sources: unknown): string | undefined {
  const kw = RANKING_SOURCE_KEYWORD[key]
  if (!kw || !Array.isArray(sources)) return undefined
  const match = sources.find(
    (s: any) => typeof s?.source === 'string' && s.source.toLowerCase().includes(kw) && s.url,
  )
  return match?.url
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
