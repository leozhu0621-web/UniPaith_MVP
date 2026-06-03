import { useParams, useNavigate } from 'react-router-dom'
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
import { ArrowLeft, BookOpen, ChevronRight, GraduationCap } from 'lucide-react'
import type { SchoolSummary, ProgramSummary } from '../../types'

interface Props { isAuthenticated?: boolean }

/**
 * SchoolSubunitPage — a school *within* an institution (Spec 12 §4).
 * Auth route: /s/institutions/:institutionId/schools/:schoolId
 * Public route: /school/:institutionId/schools/:schoolId
 * Text-driven, no campus photos / logo images (Spec 12 §9).
 */
export default function SchoolSubunitPage({ isAuthenticated = true }: Props) {
  const { institutionId, schoolId } = useParams<{ institutionId: string; schoolId: string }>()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const compareStore = useCompareStore()

  const instHref = isAuthenticated ? `/s/institutions/${institutionId}` : `/school/${institutionId}`
  const programHref = (id: string) => (isAuthenticated ? `/s/programs/${id}` : `/program/${id}`)

  const { data: institution } = useQuery({
    queryKey: ['institution', institutionId],
    queryFn: () => getPublicInstitution(institutionId!),
    enabled: !!institutionId,
  })

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

  const { data: savedData } = useQuery({ queryKey: ['saved-programs'], queryFn: listSaved, enabled: isAuthenticated, retry: false })
  const savedIds = new Set<string>((savedData as any[] ?? []).map((s: any) => String(s.program_id)))

  const toggleSave = async (programId: string) => {
    if (!isAuthenticated) { navigate('/login'); return }
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
        <Skeleton className="h-32" />
        <Skeleton className="h-96" />
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
    <div className="p-6 max-w-6xl mx-auto">
      {/* Breadcrumb / back */}
      <button onClick={() => navigate(instHref)} className="flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground mb-4 transition-colors">
        <ArrowLeft size={14} /> Back to {institution?.name || 'university'}
      </button>

      {/* Header — text-only monogram tile, no images */}
      <div className="bg-card rounded-xl border border-border p-6 mb-5">
        <div className="flex items-start gap-4">
          <div className="w-16 h-16 rounded-xl bg-muted border border-border/60 flex items-center justify-center flex-shrink-0">
            <span className="text-secondary font-bold text-xl tracking-tight">{monogram(school.name)}</span>
          </div>
          <div className="flex-1 min-w-0">
            <h1 className="text-2xl font-bold text-foreground leading-tight">{school.name}</h1>
            <div className="flex items-center gap-1 mt-1.5 text-[13px] text-muted-foreground flex-wrap">
              <button onClick={() => navigate(instHref)} className="text-secondary hover:underline font-medium">
                {institution?.name || 'University'}
              </button>
              <ChevronRight size={11} className="text-muted-foreground" />
              <span>{school.name}</span>
            </div>
            <div className="flex items-center gap-3 mt-3 text-xs text-muted-foreground">
              <span className="inline-flex items-center gap-1">
                <BookOpen size={11} className="text-secondary" />
                <span className="font-semibold text-foreground">{school.program_count}</span> programs
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* About this school */}
      <Card className="p-5 mb-5">
        <div className="flex items-center gap-2 mb-2">
          <BookOpen size={14} className="text-secondary" />
          <h2 className="font-semibold text-foreground">About this school</h2>
        </div>
        {school.description_text ? (
          <p className="text-sm text-muted-foreground leading-relaxed whitespace-pre-line">{school.description_text}</p>
        ) : (
          <p className="text-sm text-muted-foreground/70 italic">A profile for this school is coming soon. Explore its programs below.</p>
        )}
      </Card>

      {/* Programs */}
      <div className="mb-3 flex items-center justify-between">
        <h2 className="text-lg font-semibold text-foreground">Programs</h2>
        <span className="text-xs text-muted-foreground">{programList.length} program{programList.length !== 1 ? 's' : ''}</span>
      </div>

      {programsLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {[1, 2, 3].map(i => <div key={i} className="h-64 bg-card rounded-xl border border-border animate-pulse" />)}
        </div>
      ) : programList.length === 0 ? (
        <div className="text-center py-16 bg-card rounded-xl border border-border">
          <GraduationCap size={32} className="mx-auto text-muted-foreground mb-3" />
          <p className="text-sm text-foreground font-medium mb-1">No programs yet</p>
          <p className="text-xs text-muted-foreground">This school hasn&rsquo;t published any programs yet.</p>
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
              onAskCounselor={isAuthenticated ? () => navigate(`/s?prefill=${encodeURIComponent(`Tell me about ${p.program_name} at ${p.institution_name}. Is it a good fit?`)}`) : undefined}
              onView={() => navigate(programHref(p.id))}
            />
          ))}
        </div>
      )}
    </div>
  )
}

function monogram(name: string): string {
  const stop = new Set(['of', 'the', 'and', 'at', 'for', 'de', 'la', 'school'])
  const words = name.split(/\s+/).filter(w => w && !stop.has(w.toLowerCase()))
  if (words.length === 0) return name.slice(0, 2).toUpperCase()
  if (words.length === 1) return words[0].slice(0, 2).toUpperCase()
  return (words[0][0] + words[1][0]).toUpperCase()
}
