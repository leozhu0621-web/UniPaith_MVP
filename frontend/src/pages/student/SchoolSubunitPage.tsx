import { Fragment, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import {
  getInstitutionSchools, getSchoolPrograms, getPublicInstitution, getPublicPosts,
} from '../../api/institutions'
import { listEvents } from '../../api/events'
import { listSaved, saveProgram, unsaveProgram } from '../../api/saved-lists'
import { useCompareStore } from '../../stores/compare-store'
import { showToast } from '../../stores/toast-store'
import ProgramCard from './explore/cards/ProgramCard'
import NewsGrid from '../../components/NewsGrid'
import SocialLinks from '../../components/SocialLinks'
import Card from '../../components/ui/Card'
import Button from '../../components/ui/Button'
import QueryError from '../../components/ui/QueryError'
import Skeleton from '../../components/ui/Skeleton'
import { ArrowLeft, BookOpen, GraduationCap, Users, TrendingUp, Percent, Building2, Globe } from 'lucide-react'
import type { SchoolSummary, ProgramSummary, InstitutionPost } from '../../types'

function fmtPct(v: number | null | undefined) {
  if (v == null) return null
  const pct = v > 1 ? v : v * 100
  return `${Math.round(pct)}%`
}
function fmtNum(v: number | null | undefined) {
  if (v == null) return null
  return v.toLocaleString()
}

interface Props { isAuthenticated?: boolean }

/**
 * SchoolSubunitPage — a school *within* an institution (Spec 12 §4).
 * Auth route: /s/institutions/:institutionId/schools/:schoolId
 * Public route: /school/:institutionId/schools/:schoolId
 * Campus-photo hero inherited from the parent institution, fading into the
 * cream page background; no logo, no geo — mirrors the institution page.
 */
export default function SchoolSubunitPage({ isAuthenticated = true }: Props) {
  const { institutionId, schoolId } = useParams<{ institutionId: string; schoolId: string }>()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const compareStore = useCompareStore()
  const [degFilter, setDegFilter] = useState<string>('all')
  const [tab, setTab] = useState<'about' | 'programs' | 'updates'>('about')

  const instHref = isAuthenticated ? `/s/institutions/${institutionId}` : `/school/${institutionId}`
  const programHref = (id: string) => (isAuthenticated ? `/s/programs/${id}` : `/program/${id}`)

  const { data: institution } = useQuery({
    queryKey: ['institution', institutionId],
    queryFn: () => getPublicInstitution(institutionId!),
    enabled: !!institutionId,
  })

  const { data: schools, isLoading: schoolsLoading, isError: schoolsError, refetch: refetchSchools } = useQuery({
    queryKey: ['institution-schools', institutionId],
    queryFn: () => getInstitutionSchools(institutionId!),
    enabled: !!institutionId,
  })

  const { data: programs, isLoading: programsLoading, isError: programsError, refetch: refetchPrograms } = useQuery({
    queryKey: ['school-programs', institutionId, schoolId],
    queryFn: () => getSchoolPrograms(institutionId!, schoolId!),
    enabled: !!institutionId && !!schoolId,
  })

  // Channel-sourced Updates (news) + Events, scoped to this school.
  const { data: schoolPosts } = useQuery({
    queryKey: ['school-posts', institutionId, schoolId],
    queryFn: () => getPublicPosts(institutionId!, { school_id: schoolId! }),
    enabled: !!institutionId && !!schoolId,
  })
  const { data: schoolEvents } = useQuery({
    queryKey: ['school-events', schoolId],
    queryFn: () => listEvents({ school_id: schoolId!, limit: 10 }),
    enabled: !!schoolId,
  })
  const postList: InstitutionPost[] = Array.isArray(schoolPosts) ? schoolPosts : []
  const eventList: any[] = Array.isArray(schoolEvents) ? schoolEvents : []

  const { data: savedData } = useQuery({ queryKey: ['saved-programs'], queryFn: listSaved, enabled: isAuthenticated, retry: false })
  const savedIds = new Set<string>((savedData as any[] ?? []).map((s: any) => String(s.program_id)))

  const toggleSave = async (programId: string) => {
    if (!isAuthenticated) { navigate('/login'); return }
    const wasSaved = savedIds.has(programId)
    try {
      if (wasSaved) await unsaveProgram(programId)
      else await saveProgram(programId)
      queryClient.invalidateQueries({ queryKey: ['saved-programs'] })
    } catch {
      showToast(`We couldn't ${wasSaved ? 'remove' : 'save'} this program. Please try again.`, 'error')
    }
  }

  const schoolList: SchoolSummary[] = Array.isArray(schools) ? schools : []
  const school = schoolList.find(s => s.id === schoolId)
  const programList: ProgramSummary[] = Array.isArray(programs) ? programs : []

  // Hero inherits the parent institution's campus photo (a school has no photo of
  // its own); falls back to a gradient. Picks a real photo, never the logo SVG.
  const heroPhoto = (institution?.media_gallery ?? []).find(u => /\.(jpe?g|png|webp|avif)(\?|$)/i.test(u)) ?? null
  const DEG: Record<string, string> = { bachelors: "Bachelor's", masters: "Master's", phd: 'PhD', doctoral: 'Doctorate', associate: 'Associate', certificate: 'Certificate', diploma: 'Diploma', professional: 'Professional' }
  const degreeTypes = [...new Set(programList.map(p => p.degree_type).filter(Boolean) as string[])]
  const degreeLevels = degreeTypes.map(d => DEG[d] ?? d)
  // Degree-level filter for the program grid (parity with the explore page).
  const activeDegFilter = degreeTypes.includes(degFilter) ? degFilter : 'all'
  const filteredPrograms = activeDegFilter === 'all' ? programList : programList.filter(p => p.degree_type === activeDegFilter)
  const progCount = programList.length || school?.program_count || 0
  const heroStats = [
    { value: String(progCount), label: progCount === 1 ? 'program' : 'programs' },
    degreeLevels.length ? { value: degreeLevels.slice(0, 4).join(' · '), label: 'offered' } : null,
  ].filter(Boolean) as { value: string; label: string }[]

  if (schoolsLoading) {
    return (
      <div className="p-6 max-w-5xl w-full mx-auto space-y-4">
        <Skeleton className="h-8 w-48" />
        <Skeleton className="h-32" />
        <Skeleton className="h-96" />
      </div>
    )
  }

  // A failed schools fetch is retryable — don't show it as "School not found".
  if (schoolsError && !school) {
    return (
      <div className="p-6 max-w-3xl mx-auto">
        <QueryError detail="We couldn't load this school." onRetry={() => refetchSchools()} />
      </div>
    )
  }

  if (!school) {
    return (
      <div className="p-6 max-w-3xl mx-auto text-center py-20">
        <GraduationCap size={32} className="mx-auto text-muted-foreground mb-3" />
        <p className="text-sm text-foreground mb-4">School not found.</p>
        <Button size="sm" variant="secondary" onClick={() => navigate(instHref)}>Back</Button>
      </div>
    )
  }

  return (
    <div className="p-6 max-w-5xl w-full mx-auto animate-page-in">
      {/* Back to the last level (falls back to the institution when opened directly) */}
      <button
        onClick={() => { if (window.history.length > 1) navigate(-1); else navigate(instHref) }}
        className="inline-flex items-center gap-1.5 text-[13px] font-medium text-secondary hover:underline mb-3"
      >
        <ArrowLeft size={15} /> Back
      </button>

      {/* Breadcrumb */}
      <nav className="text-sm text-muted-foreground mb-4" aria-label="Breadcrumb">
        <button onClick={() => navigate(instHref)} className="hover:text-foreground transition-colors">{institution?.name || 'University'}</button>
        <span className="mx-1.5 text-border" aria-hidden="true">·</span>
        <span className="text-foreground font-medium">{school.name}</span>
      </nav>

      {/* Hero — parent campus photo fading into the cream page background. No logo, no geo. */}
      <div className="relative rounded-xl overflow-hidden border border-border mb-5 bg-background">
        <div className="relative h-40 sm:h-52 md:h-56">
          {heroPhoto ? (
            <img src={heroPhoto} alt="" aria-hidden="true" className="absolute inset-0 h-full w-full object-cover" />
          ) : (
            <div className="absolute inset-0 bg-gradient-to-br from-secondary/10 to-background" />
          )}
          <div
            className="absolute inset-0"
            style={{ background: 'linear-gradient(to bottom, rgba(10,18,36,0.30) 0%, rgba(10,18,36,0.04) 24%, rgba(10,18,36,0) 44%, hsl(var(--background)) 97%)' }}
          />
        </div>
        <div className="relative -mt-14 px-5 sm:px-7 pb-6">
          <button onClick={() => navigate(instHref)} className="text-eyebrow uppercase text-secondary mb-1.5 hover:underline">{institution?.name || 'School'}</button>
          <h1 className="text-2xl sm:text-3xl md:text-[2.25rem] font-bold text-foreground leading-[1.1] tracking-tight max-w-[24ch]">{school.name}</h1>
          {heroStats.length > 0 && (
            <div className="flex flex-wrap items-center gap-x-2.5 gap-y-1 mt-2.5 text-[13px] text-muted-foreground">
              {heroStats.map((s, i) => (
                <Fragment key={s.label}>
                  {i > 0 && <span className="text-border" aria-hidden="true">·</span>}
                  {s.label === 'offered' ? (
                    <span><span className="font-semibold text-foreground" title="Degree levels offered">{s.value}</span></span>
                  ) : (
                    <span><span className="font-semibold text-foreground">{s.value}</span> {s.label}</span>
                  )}
                </Fragment>
              ))}
            </div>
          )}
          <div className="flex flex-wrap items-center gap-3 mt-4">
            {school.website_url && (
              <a
                href={school.website_url}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1.5 text-[13px] font-medium text-secondary hover:underline"
              >
                <Globe size={14} /> Website
              </a>
            )}
          </div>
        </div>
      </div>

      {/* Tabs — the school's own Overview / About / Programs / Updates */}
      <div className="border-b border-border mb-5">
        <div className="flex gap-1 -mb-px overflow-x-auto" role="tablist">
          {([
            ['about', 'About'],
            ['updates', 'Events & Updates'],
            ['programs', `Programs${progCount ? ` (${progCount})` : ''}`],
          ] as const).map(([id, label]) => (
            <button
              key={id}
              role="tab"
              aria-selected={tab === id}
              onClick={() => setTab(id)}
              className={`px-4 py-2.5 text-sm font-medium border-b-2 whitespace-nowrap transition-colors ${
                tab === id ? 'border-secondary text-secondary' : 'border-transparent text-muted-foreground hover:text-foreground'
              }`}
            >
              {label}
            </button>
          ))}
        </div>
      </div>

      {/* About — quick-facts (moved from the former Overview tab) + full description */}
      {tab === 'about' && (
      <>
      {/* School quick-facts — derived from institution + program grid where available */}
      {(() => {
        const rd: any = institution?.ranking_data || {}
        const outcomes: any = institution?.school_outcomes || {}
        const acceptanceRate = fmtPct(outcomes.admit_rate ?? rd.acceptance_rate)
        const gradRate = fmtPct(outcomes.graduation_rate_6yr ?? rd.graduation_rate)
        const bodySize = fmtNum(institution?.student_body_size)
        const setting = institution?.campus_setting
        const tiles = [
          progCount > 0 && { icon: GraduationCap, label: 'Programs', value: String(progCount) },
          acceptanceRate && { icon: Percent, label: 'Acceptance', value: acceptanceRate },
          gradRate && { icon: TrendingUp, label: 'Grad Rate', value: gradRate },
          bodySize && { icon: Users, label: 'Students', value: bodySize },
          setting && { icon: Building2, label: 'Setting', value: setting.charAt(0).toUpperCase() + setting.slice(1) },
        ].filter(Boolean) as { icon: any; label: string; value: string }[]

        if (tiles.length === 0) return null

        return (
          <div className={`grid gap-2 mb-5 ${tiles.length <= 2 ? 'grid-cols-2' : tiles.length === 3 ? 'grid-cols-3' : tiles.length === 4 ? 'grid-cols-2 sm:grid-cols-4' : 'grid-cols-2 sm:grid-cols-3 md:grid-cols-5'}`}>
            {tiles.map((t, i) => (
              <div key={i} className="flex items-center gap-2.5 px-3 py-2.5 bg-card border border-border rounded-lg">
                <div className="w-7 h-7 rounded-md bg-muted flex items-center justify-center flex-shrink-0">
                  <t.icon size={13} className="text-foreground/70" />
                </div>
                <div className="min-w-0">
                  <p className="text-[10px] text-muted-foreground uppercase tracking-wide leading-tight">{t.label}</p>
                  <p className="text-sm font-bold text-foreground leading-tight truncate" title={t.label}>{t.value}</p>
                </div>
              </div>
            ))}
          </div>
        )
      })()}
      <Card pad={false} className="p-5 mb-5">
        <div className="flex items-center gap-2 mb-2">
          <BookOpen size={14} className="text-secondary" />
          <h2 className="font-semibold text-foreground">About this school</h2>
        </div>
        {school.description_text ? (
          <p className="text-sm text-muted-foreground leading-relaxed whitespace-pre-line">{school.description_text}</p>
        ) : (
          <p className="text-sm text-muted-foreground">No details published yet for this school. Explore programs below.</p>
        )}
      </Card>

      {school.about_detail && (
        <>
          {(school.about_detail.founded != null || school.about_detail.named_for || school.about_detail.leadership) && (
            <Card pad={false} className="p-5 mb-5">
              <h2 className="font-semibold text-foreground mb-3">Facts &amp; leadership</h2>
              <dl className="space-y-2.5 text-sm">
                {school.about_detail.founded != null && (
                  <div className="flex gap-3">
                    <dt className="w-24 shrink-0 text-[11px] font-semibold uppercase tracking-wide text-muted-foreground pt-0.5">Founded</dt>
                    <dd className="text-foreground">{school.about_detail.founded}</dd>
                  </div>
                )}
                {school.about_detail.named_for && (
                  <div className="flex gap-3">
                    <dt className="w-24 shrink-0 text-[11px] font-semibold uppercase tracking-wide text-muted-foreground pt-0.5">Named for</dt>
                    <dd className="text-muted-foreground leading-relaxed">{school.about_detail.named_for}</dd>
                  </div>
                )}
                {school.about_detail.leadership && (
                  <div className="flex gap-3">
                    <dt className="w-24 shrink-0 text-[11px] font-semibold uppercase tracking-wide text-muted-foreground pt-0.5">Leadership</dt>
                    <dd className="text-foreground">{school.about_detail.leadership}</dd>
                  </div>
                )}
              </dl>
            </Card>
          )}

          {school.about_detail.faculty && school.about_detail.faculty.length > 0 && (
            <Card pad={false} className="p-5 mb-5">
              <h2 className="font-semibold text-foreground mb-3">Notable faculty</h2>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {school.about_detail.faculty.map(f => (
                  <div key={f.name} className="px-3 py-2.5 rounded-lg bg-muted/60 border border-border/50">
                    <p className="text-sm font-semibold text-foreground">{f.name}</p>
                    <p className="text-[12px] text-foreground/80">{f.title}</p>
                    {f.focus && <p className="text-[11px] text-muted-foreground mt-0.5">{f.focus}</p>}
                  </div>
                ))}
              </div>
            </Card>
          )}

          {school.about_detail.research_centers && school.about_detail.research_centers.length > 0 && (
            <Card pad={false} className="p-5 mb-5">
              <h2 className="font-semibold text-foreground mb-3">Research centers &amp; labs</h2>
              <div className="flex flex-wrap gap-2">
                {school.about_detail.research_centers.map(c => (
                  <span key={c} className="inline-flex items-center px-2.5 py-1 rounded-full text-[12px] font-medium bg-secondary/10 text-secondary border border-secondary/20">{c}</span>
                ))}
              </div>
              {school.about_detail.source && (
                <p className="text-[11px] text-muted-foreground mt-3">
                  <span className="font-semibold text-foreground/70">Source:</span>{' '}
                  <a href={school.about_detail.source.url} target="_blank" rel="noopener noreferrer" className="text-secondary hover:underline">{school.about_detail.source.label} ↗</a>
                </p>
              )}
            </Card>
          )}
        </>
      )}
      </>
      )}

      {tab === 'programs' && (
      <>
      {/* Programs */}
      <div className="mb-3 flex items-center justify-between">
        <h2 className="text-lg font-semibold text-foreground">Programs</h2>
        <span className="text-xs text-muted-foreground">
          {activeDegFilter === 'all'
            ? `${programList.length} program${programList.length !== 1 ? 's' : ''}`
            : `${filteredPrograms.length} of ${programList.length}`}
        </span>
      </div>

      {/* Degree-level filter — only when the school offers more than one level. */}
      {degreeTypes.length > 1 && (
        <div className="mb-4 flex flex-wrap gap-1.5">
          <FilterChip active={activeDegFilter === 'all'} onClick={() => setDegFilter('all')}>
            All
          </FilterChip>
          {degreeTypes.map(d => (
            <FilterChip key={d} active={activeDegFilter === d} onClick={() => setDegFilter(d)}>
              {DEG[d] ?? d}
            </FilterChip>
          ))}
        </div>
      )}

      {programsLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {[1, 2, 3].map(i => <div key={i} className="h-64 bg-card rounded-xl border border-border animate-pulse" />)}
        </div>
      ) : programsError ? (
        // Distinguish a failed fetch from a school that simply has no programs.
        <div className="bg-card rounded-xl border border-border">
          <QueryError detail="We couldn't load this school's programs." onRetry={() => refetchPrograms()} />
        </div>
      ) : programList.length === 0 ? (
        <div className="text-center py-16 bg-card rounded-xl border border-border">
          <GraduationCap size={32} className="mx-auto text-muted-foreground mb-3" />
          <p className="text-sm text-foreground font-medium mb-1">No programs yet</p>
          <p className="text-xs text-muted-foreground">This school hasn&rsquo;t published any programs yet.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredPrograms.map(p => (
            <ProgramCard
              key={p.id}
              program={p}
              saved={savedIds.has(p.id)}
              comparing={compareStore.has(p.id)}
              onSave={() => toggleSave(p.id)}
              onCompare={() => compareStore.has(p.id)
                ? compareStore.remove(p.id)
                : compareStore.add({ program_id: p.id, program_name: p.program_name, institution_name: p.institution_name, degree_type: p.degree_type })}
              onAskCounselor={isAuthenticated ? () => navigate(`/s?prefill=${encodeURIComponent(`Tell me about ${p.program_name} at ${p.institution_name}. Is it a good fit?`)}`) : undefined}
              onView={() => navigate(programHref(p.id))}
            />
          ))}
        </div>
      )}
      </>
      )}

      {tab === 'updates' && (
        <div className="space-y-5">
          {school.content_sources?.social && (
            <div>
              <h2 className="text-[12px] font-semibold text-muted-foreground uppercase tracking-wide mb-2">Follow {school.name}</h2>
              <SocialLinks social={school.content_sources.social} />
            </div>
          )}
          <NewsGrid
            posts={postList}
            events={eventList}
            emptyText={`${school.name} hasn’t posted any events or updates yet.`}
          />
        </div>
      )}

      {/* Data attribution footer */}
      <footer className="mt-8 pt-4 border-t border-border">
        <p className="text-[11px] leading-relaxed text-muted-foreground">
          <span className="font-semibold text-foreground/70">Data sources:</span>{' '}
          U.S. Department of Education College Scorecard (admissions &amp; outcomes);
          institution-published program listings.
          {' '}Figures reflect the latest available data; verify on the official school page.
        </p>
      </footer>
    </div>
  )
}

/* ── Degree-level filter chip ── */
function FilterChip({ active, onClick, children }: { active: boolean; onClick: () => void; children: React.ReactNode }) {
  return (
    <button
      type="button"
      onClick={onClick}
      aria-pressed={active}
      className={`px-3 py-1 rounded-full text-[12px] font-medium border transition-colors ${
        active
          ? 'bg-secondary text-secondary-foreground border-secondary'
          : 'bg-card text-muted-foreground border-border hover:bg-muted hover:text-foreground'
      }`}
    >
      {children}
    </button>
  )
}
