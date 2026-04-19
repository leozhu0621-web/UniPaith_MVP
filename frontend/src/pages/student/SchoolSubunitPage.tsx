import { useParams, useNavigate, Link } from 'react-router-dom'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import {
  getInstitutionSchools, getSchoolPrograms, getPublicInstitution,
} from '../../api/institutions'
import { listSaved, saveProgram, unsaveProgram } from '../../api/saved-lists'
import { useCompareStore } from '../../stores/compare-store'
import ProgramCard from './explore/cards/ProgramCard'
import Card from '../../components/ui/Card'
import Button from '../../components/ui/Button'
import Skeleton from '../../components/ui/Skeleton'
import {
  ArrowLeft, Building2, BookOpen, ChevronRight, GraduationCap,
} from 'lucide-react'
import type { SchoolSummary, ProgramSummary } from '../../types'

/**
 * SchoolSubunitPage — detail page for a school within an institution.
 *
 * Route: /s/institutions/:institutionId/schools/:schoolId
 *
 * Shows the school's logo, name, description, campus media, and a grid of
 * all programs offered by that school. Replaces the old in-Explore drill
 * level 1 panel with a real URL so refresh and deep-linking work.
 */
export default function SchoolSubunitPage() {
  const { institutionId, schoolId } = useParams<{ institutionId: string; schoolId: string }>()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const compareStore = useCompareStore()

  // Fetch institution (for the breadcrumb label)
  const { data: institution } = useQuery({
    queryKey: ['institution', institutionId],
    queryFn: () => getPublicInstitution(institutionId!),
    enabled: !!institutionId,
  })

  // Fetch the schools list and filter to the one we want. There's no
  // single-school endpoint — the list already includes everything we need
  // (name, description, media_urls, logo_url, program_count).
  const { data: schools, isLoading: schoolsLoading } = useQuery({
    queryKey: ['institution-schools', institutionId],
    queryFn: () => getInstitutionSchools(institutionId!),
    enabled: !!institutionId,
  })

  const { data: programs, isLoading: programsLoading } = useQuery({
    queryKey: ['school-programs', institutionId, schoolId],
    queryFn: () => getSchoolPrograms(institutionId!, schoolId!),
    enabled: !!institutionId && !!schoolId,
  })

  const { data: savedData } = useQuery({ queryKey: ['saved-programs'], queryFn: listSaved, retry: false })
  const savedIds = new Set<string>((savedData as any[] ?? []).map((s: any) => String(s.program_id)))

  const toggleSave = async (programId: string) => {
    try {
      if (savedIds.has(programId)) await unsaveProgram(programId)
      else await saveProgram(programId)
      queryClient.invalidateQueries({ queryKey: ['saved-programs'] })
    } catch { /* */ }
  }

  const schoolList: SchoolSummary[] = Array.isArray(schools) ? schools : []
  const school = schoolList.find(s => s.id === schoolId)
  const programList: ProgramSummary[] = Array.isArray(programs) ? programs : []

  if (schoolsLoading) {
    return (
      <div className="p-6 max-w-6xl mx-auto space-y-4">
        <Skeleton className="h-8 w-48" />
        <Skeleton className="h-40" />
        <Skeleton className="h-96" />
      </div>
    )
  }

  if (!school) {
    return (
      <div className="p-6 max-w-3xl mx-auto text-center py-20">
        <GraduationCap size={32} className="mx-auto text-stone mb-3" />
        <p className="text-sm text-student-text mb-4">School not found.</p>
        <Button size="sm" variant="secondary" onClick={() => navigate(institutionId ? `/s/institutions/${institutionId}` : '/s/explore')}>
          Back
        </Button>
      </div>
    )
  }

  // media_urls can be an array, a dict with array inside, or null.
  const mediaList: string[] = (() => {
    const m: any = school.media_urls
    if (!m) return []
    if (Array.isArray(m)) return m.filter(x => typeof x === 'string')
    if (typeof m === 'object') {
      for (const k of ['images', 'photos', 'media', 'urls']) {
        if (Array.isArray(m[k])) return m[k].filter((x: any) => typeof x === 'string')
      }
    }
    return []
  })()

  return (
    <div className="p-6 max-w-6xl mx-auto">
      {/* Back button */}
      <button
        onClick={() => navigate(`/s/institutions/${institutionId}`)}
        className="flex items-center gap-1 text-sm text-student-text hover:text-student-ink mb-4 transition-colors"
      >
        <ArrowLeft size={14} /> Back to {institution?.name || 'university'}
      </button>

      {/* Header */}
      <div className="bg-white rounded-xl border border-divider p-6 mb-5">
        <div className="flex items-start gap-4">
          <div className="w-16 h-16 rounded-xl bg-student-mist flex items-center justify-center flex-shrink-0 overflow-hidden">
            {school.logo_url ? (
              <img src={school.logo_url} alt="" className="w-full h-full object-contain p-2" onError={e => { (e.currentTarget.style.display = 'none') }} />
            ) : (
              <Building2 size={28} className="text-student" />
            )}
          </div>
          <div className="flex-1 min-w-0">
            <h1 className="text-2xl font-bold text-student-ink leading-tight">{school.name}</h1>
            {/* Breadcrumb */}
            <div className="flex items-center gap-1 mt-1.5 text-[13px] text-student-text flex-wrap">
              <Link to={`/s/institutions/${institutionId}`} className="text-student hover:underline font-medium">
                {institution?.name || 'University'}
              </Link>
              <ChevronRight size={11} className="text-student-text/40" />
              <span>{school.name}</span>
            </div>
            <div className="flex items-center gap-3 mt-3 text-xs text-student-text">
              <span className="flex items-center gap-1">
                <BookOpen size={11} className="text-student" />
                <span className="font-semibold text-student-ink">{school.program_count}</span> programs
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Hero media strip — show campus photos if the school has any */}
      {mediaList.length > 0 ? (
        <div className={`mb-5 rounded-xl overflow-hidden border border-divider grid gap-1 ${
          mediaList.length === 1 ? 'grid-cols-1' : 'grid-cols-2'
        }`}>
          {mediaList.slice(0, 4).map((url, i) => (
            <img
              key={i}
              src={url}
              alt=""
              className="w-full h-48 object-cover bg-student-mist"
              onError={e => (e.currentTarget.style.display = 'none')}
            />
          ))}
        </div>
      ) : null}

      {/* Description */}
      <Card className="p-5 mb-5">
        <div className="flex items-center gap-2 mb-3">
          <BookOpen size={14} className="text-student" />
          <h2 className="font-semibold text-student-ink">About this school</h2>
        </div>
        {school.description_text ? (
          <p className="text-sm text-student-text leading-relaxed whitespace-pre-line">{school.description_text}</p>
        ) : (
          <p className="text-sm text-student-text/70 italic">
            About this school coming soon. In the meantime, explore the programs below.
          </p>
        )}
      </Card>

      {/* Programs */}
      <div className="mb-3 flex items-center justify-between">
        <h2 className="text-lg font-semibold text-student-ink">Programs</h2>
        <span className="text-xs text-student-text">{programList.length} program{programList.length !== 1 ? 's' : ''}</span>
      </div>

      {programsLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {[1, 2, 3].map(i => <div key={i} className="h-64 bg-white rounded-xl border border-divider animate-pulse" />)}
        </div>
      ) : programList.length === 0 ? (
        <div className="text-center py-16 bg-white rounded-xl border border-divider">
          <GraduationCap size={32} className="mx-auto text-stone mb-3" />
          <p className="text-sm text-student-ink font-medium mb-1">No programs yet</p>
          <p className="text-xs text-student-text">This school hasn't published any programs yet.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {programList.map(p => (
            <ProgramCard
              key={p.id}
              program={p}
              saved={savedIds.has(p.id)}
              comparing={compareStore.has(p.id)}
              onSave={() => toggleSave(p.id)}
              onCompare={() => compareStore.has(p.id)
                ? compareStore.remove(p.id)
                : compareStore.add({ program_id: p.id, program_name: p.program_name, institution_name: p.institution_name, degree_type: p.degree_type })}
              onAskCounselor={() => navigate(`/s?prefill=${encodeURIComponent(`Tell me about ${p.program_name} at ${p.institution_name}. Is it a good fit?`)}`)}
              onView={() => navigate(`/s/programs/${p.id}`)}
            />
          ))}
        </div>
      )}
    </div>
  )
}
