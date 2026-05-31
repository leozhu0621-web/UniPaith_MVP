/**
 * Profile → Academics tab (Spec/08 §6).
 * 6.1 Academics (summary + per-course table + transcript upload)
 * 6.2 Test Scores (cards + auto superscore)
 * 6.3 Languages
 * 6.4 Research
 */
import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  ChevronDown,
  ChevronRight,
  ExternalLink,
  FlaskConical,
  Languages as LanguagesIcon,
  Pencil,
  Plus,
  Trash2,
} from 'lucide-react'

import Badge from '../../../components/ui/Badge'
import Button from '../../../components/ui/Button'
import Card from '../../../components/ui/Card'
import EmptyState from '../../../components/ui/EmptyState'
import Modal from '../../../components/ui/Modal'
import Select from '../../../components/ui/Select'
import { SkeletonCard } from '../../../components/ui/Skeleton'
import {
  createAcademic,
  createCourse,
  createLanguage,
  createResearch,
  createTestScore,
  deleteAcademic,
  deleteCourse,
  deleteLanguage,
  deleteResearch,
  deleteTestScore,
  getProfile,
  listCourses,
  updateAcademic,
  updateCourse,
  updateLanguage,
  updateResearch,
  updateTestScore,
} from '../../../api/students'
import { deleteDocument, listDocuments } from '../../../api/documents'
import { showToast } from '../../../stores/toast-store'
import { formatDate, formatFileSize } from '../../../utils/format'
import {
  COURSE_LEVELS,
  DEGREE_LABELS,
  PROFICIENCY_LEVELS,
  RESEARCH_OUTPUTS,
  RESEARCH_ROLES,
} from '../../../utils/constants'
import {
  AcademicForm,
  CourseForm,
  LanguageForm,
  ResearchForm,
  TestScoreForm,
} from '../components/ProfileForms'
import { SectionHeader } from './shared'
import FileDropzone from './FileDropzone'

const courseLevelLabel = (v: string) => COURSE_LEVELS.find(o => o.value === v)?.label || v

function CoursesPanel({ recordId }: { recordId: string }) {
  const qc = useQueryClient()
  const { data: courses = [] } = useQuery({
    queryKey: ['courses', recordId],
    queryFn: () => listCourses(recordId),
  })
  const [open, setOpen] = useState(false)
  const [modal, setModal] = useState(false)
  const [editItem, setEditItem] = useState<any>(null)
  const [termFilter, setTermFilter] = useState('')
  const [levelFilter, setLevelFilter] = useState('')

  const invalidate = () => qc.invalidateQueries({ queryKey: ['courses', recordId] })
  const createMut = useMutation({
    mutationFn: (d: any) => createCourse(recordId, d),
    onSuccess: () => {
      invalidate()
      setModal(false)
      showToast('Course added', 'success')
    },
  })
  const updateMut = useMutation({
    mutationFn: ({ id, data }: { id: string; data: any }) => updateCourse(recordId, id, data),
    onSuccess: () => {
      invalidate()
      setModal(false)
      showToast('Course updated', 'success')
    },
  })
  const deleteMut = useMutation({
    mutationFn: (id: string) => deleteCourse(recordId, id),
    onSuccess: () => {
      invalidate()
      showToast('Course removed', 'success')
    },
  })

  const list: any[] = Array.isArray(courses) ? courses : []
  const terms = Array.from(new Set(list.map(c => c.term).filter(Boolean)))
  const filtered = list.filter(
    c => (!termFilter || c.term === termFilter) && (!levelFilter || c.course_level === levelFilter),
  )

  return (
    <div className="mt-3 border-t border-border pt-3">
      <button
        className="flex items-center gap-1.5 text-sm font-semibold text-foreground"
        onClick={() => setOpen(o => !o)}
      >
        {open ? <ChevronDown size={15} /> : <ChevronRight size={15} />}
        Courses {list.length > 0 && <span className="text-muted-foreground font-normal">({list.length})</span>}
      </button>
      {open && (
        <div className="mt-3 space-y-3">
          <div className="flex flex-wrap items-end gap-2">
            {terms.length > 0 && (
              <div className="w-36">
                <Select
                  uiSize="sm"
                  placeholder="All terms"
                  options={terms.map(t => ({ value: t, label: t }))}
                  value={termFilter}
                  onChange={e => setTermFilter(e.target.value)}
                />
              </div>
            )}
            <div className="w-40">
              <Select
                uiSize="sm"
                placeholder="All levels"
                options={COURSE_LEVELS}
                value={levelFilter}
                onChange={e => setLevelFilter(e.target.value)}
              />
            </div>
            <Button
              size="sm"
              variant="tertiary"
              className="ml-auto"
              onClick={() => {
                setEditItem(null)
                setModal(true)
              }}
            >
              <Plus size={14} /> Add course
            </Button>
          </div>

          {filtered.length === 0 ? (
            <p className="text-sm text-muted-foreground">No courses recorded yet.</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-left text-xs uppercase tracking-wide text-muted-foreground border-b border-border">
                    <th className="py-2 pr-3 font-semibold">Course</th>
                    <th className="py-2 pr-3 font-semibold">Level</th>
                    <th className="py-2 pr-3 font-semibold">Term</th>
                    <th className="py-2 pr-3 font-semibold">Grade</th>
                    <th className="py-2 w-16" />
                  </tr>
                </thead>
                <tbody>
                  {filtered.map(c => (
                    <tr key={c.id} className="border-b border-border/60 hover:bg-muted/50">
                      <td className="py-2 pr-3">
                        <span className="font-medium text-foreground">{c.course_name}</span>
                        {c.course_code && <span className="text-muted-foreground"> · {c.course_code}</span>}
                      </td>
                      <td className="py-2 pr-3 text-muted-foreground">{courseLevelLabel(c.course_level)}</td>
                      <td className="py-2 pr-3 text-muted-foreground">{c.term || '—'}</td>
                      <td className="py-2 pr-3 text-muted-foreground tabular-nums">{c.grade || '—'}</td>
                      <td className="py-2">
                        <div className="flex gap-0.5 justify-end">
                          <Button
                            size="sm"
                            variant="ghost"
                            onClick={() => {
                              setEditItem(c)
                              setModal(true)
                            }}
                          >
                            <Pencil size={12} />
                          </Button>
                          <Button size="sm" variant="ghost" onClick={() => deleteMut.mutate(c.id)}>
                            <Trash2 size={12} />
                          </Button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      <Modal isOpen={modal} onClose={() => setModal(false)} title={editItem ? 'Edit course' : 'Add course'}>
        <CourseForm
          defaultValues={editItem}
          loading={createMut.isPending || updateMut.isPending}
          onSubmit={(data: any) =>
            editItem ? updateMut.mutate({ id: editItem.id, data }) : createMut.mutate(data)
          }
        />
      </Modal>
    </div>
  )
}

function computeSuperscore(scores: any[], testType: string): number | null {
  const same = scores.filter(s => s.test_type === testType && s.section_scores)
  if (same.length < 2) return null
  const bestSections: Record<string, number> = {}
  for (const s of same) {
    for (const [k, v] of Object.entries(s.section_scores as Record<string, number>)) {
      const n = Number(v)
      if (!Number.isNaN(n)) bestSections[k] = Math.max(bestSections[k] ?? 0, n)
    }
  }
  const sum = Object.values(bestSections).reduce((a, b) => a + b, 0)
  return sum > 0 ? sum : null
}

export default function AcademicsTab() {
  const qc = useQueryClient()
  const { data: profile, isLoading } = useQuery({ queryKey: ['profile'], queryFn: getProfile })
  const { data: documents } = useQuery({ queryKey: ['documents'], queryFn: listDocuments })
  const [modal, setModal] = useState<null | 'academic' | 'test' | 'language' | 'research'>(null)
  const [editItem, setEditItem] = useState<any>(null)

  const inv = () => qc.invalidateQueries({ queryKey: ['profile'] })
  const open = (kind: typeof modal, item: any = null) => {
    setEditItem(item)
    setModal(kind)
  }
  const close = () => setModal(null)
  const onSaved = (msg: string) => {
    inv()
    setModal(null)
    showToast(msg, 'success')
  }
  const onErr = () => showToast("Something didn't work. Try again.", 'error')

  const acadCreate = useMutation({ mutationFn: createAcademic, onSuccess: () => onSaved('Record added'), onError: onErr })
  const acadUpdate = useMutation({ mutationFn: ({ id, data }: any) => updateAcademic(id, data), onSuccess: () => onSaved('Record updated'), onError: onErr })
  const acadDelete = useMutation({ mutationFn: deleteAcademic, onSuccess: () => { inv(); showToast('Record deleted', 'success') } })
  const testCreate = useMutation({ mutationFn: createTestScore, onSuccess: () => onSaved('Score added'), onError: onErr })
  const testUpdate = useMutation({ mutationFn: ({ id, data }: any) => updateTestScore(id, data), onSuccess: () => onSaved('Score updated'), onError: onErr })
  const testDelete = useMutation({ mutationFn: deleteTestScore, onSuccess: () => { inv(); showToast('Score deleted', 'success') } })
  const langCreate = useMutation({ mutationFn: createLanguage, onSuccess: () => onSaved('Language added'), onError: onErr })
  const langUpdate = useMutation({ mutationFn: ({ id, data }: any) => updateLanguage(id, data), onSuccess: () => onSaved('Language updated'), onError: onErr })
  const langDelete = useMutation({ mutationFn: deleteLanguage, onSuccess: () => { inv(); showToast('Language removed', 'success') } })
  const rsCreate = useMutation({ mutationFn: createResearch, onSuccess: () => onSaved('Research added'), onError: onErr })
  const rsUpdate = useMutation({ mutationFn: ({ id, data }: any) => updateResearch(id, data), onSuccess: () => onSaved('Research updated'), onError: onErr })
  const rsDelete = useMutation({ mutationFn: deleteResearch, onSuccess: () => { inv(); showToast('Research removed', 'success') } })
  const docDelete = useMutation({
    mutationFn: deleteDocument,
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['documents'] }); showToast('Document removed', 'success') },
  })

  if (isLoading || !profile) return <div className="space-y-3">{Array.from({ length: 3 }).map((_, i) => <SkeletonCard key={i} />)}</div>

  const p: any = profile
  const records: any[] = p.academic_records ?? []
  const testScores: any[] = p.test_scores ?? []
  const languages: any[] = p.languages ?? []
  const research: any[] = p.research_entries ?? []
  const transcripts: any[] = (Array.isArray(documents) ? documents : []).filter((d: any) => d.document_type === 'transcript')

  return (
    <div className="space-y-10">
      {/* 6.1 Academics */}
      <section>
        <SectionHeader
          title="Academics"
          description="Degrees, GPA, and rigor. Add coursework under each record."
          action={
            <Button size="sm" onClick={() => open('academic')}>
              <Plus size={14} /> Add record
            </Button>
          }
        />
        {records.length === 0 ? (
          <EmptyState
            title="No academic records yet"
            description="Add a record to surface programs that fit your background — match scores improve with grades."
            action={{ label: 'Add a record', onClick: () => open('academic') }}
          />
        ) : (
          <div className="space-y-3">
            {records.map(rec => (
              <Card key={rec.id} className="p-5">
                <div className="flex items-start justify-between gap-3">
                  <div className="min-w-0">
                    <p className="font-semibold text-foreground">
                      {rec.institution_name} — {DEGREE_LABELS[rec.degree_type] || rec.degree_type}
                      {rec.field_of_study ? `, ${rec.field_of_study}` : ''}
                    </p>
                    <p className="text-sm text-muted-foreground mt-0.5">
                      GPA {rec.gpa ?? '—'}/{rec.gpa_scale ?? '4.0'}
                      {rec.rigor_indicator_count ? ` · ${rec.rigor_indicator_count} AP/IB/Honors` : ''}
                      {' · '}
                      {rec.start_date?.slice(0, 4)}–{rec.is_current ? 'Present' : rec.end_date?.slice(0, 4) ?? '—'}
                    </p>
                  </div>
                  <div className="flex gap-0.5 shrink-0">
                    <Button size="sm" variant="ghost" onClick={() => open('academic', rec)}>
                      <Pencil size={14} />
                    </Button>
                    <Button size="sm" variant="ghost" onClick={() => acadDelete.mutate(rec.id)}>
                      <Trash2 size={14} />
                    </Button>
                  </div>
                </div>
                <CoursesPanel recordId={rec.id} />
              </Card>
            ))}
          </div>
        )}

        {/* Transcript upload */}
        <div className="mt-4">
          <FileDropzone
            documentType="transcript"
            label="Upload a transcript"
            onUploaded={() => qc.invalidateQueries({ queryKey: ['documents'] })}
          />
          {transcripts.length > 0 && (
            <div className="mt-3 space-y-2">
              {transcripts.map((d: any) => (
                <div
                  key={d.id}
                  className="flex items-center justify-between rounded-lg border border-border bg-card px-3 py-2"
                >
                  <div className="min-w-0">
                    <p className="text-sm font-medium text-foreground truncate">{d.file_name}</p>
                    <p className="text-xs text-muted-foreground">{formatFileSize(d.file_size_bytes)}</p>
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge variant={d.verification_status === 'verified' ? 'success' : 'neutral'}>
                      {d.verification_status || 'uploaded'}
                    </Badge>
                    <Button size="sm" variant="ghost" onClick={() => docDelete.mutate(d.id)}>
                      <Trash2 size={14} />
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </section>

      {/* 6.2 Test Scores */}
      <section>
        <SectionHeader
          title="Test scores"
          description="Superscore is computed automatically across attempts of the same test."
          action={
            <Button size="sm" onClick={() => open('test')}>
              <Plus size={14} /> Add score
            </Button>
          }
        />
        {testScores.length === 0 ? (
          <EmptyState title="No test scores yet" description="Add SAT, ACT, GRE, TOEFL, or other scores to round out your readiness." action={{ label: 'Add a score', onClick: () => open('test') }} />
        ) : (
          <div className="grid sm:grid-cols-2 gap-3">
            {testScores.map(ts => {
              const superscore = computeSuperscore(testScores, ts.test_type)
              return (
                <Card key={ts.id} className="p-4">
                  <div className="flex items-start justify-between gap-2">
                    <div>
                      <p className="font-semibold text-foreground">
                        {ts.test_type}: {ts.total_score ?? '—'}
                      </p>
                      {ts.section_scores && (
                        <p className="text-xs text-muted-foreground mt-0.5">
                          {Object.entries(ts.section_scores).map(([k, v]) => `${k} ${v}`).join(' · ')}
                        </p>
                      )}
                    </div>
                    <div className="flex gap-0.5 shrink-0">
                      <Button size="sm" variant="ghost" onClick={() => open('test', ts)}>
                        <Pencil size={12} />
                      </Button>
                      <Button size="sm" variant="ghost" onClick={() => testDelete.mutate(ts.id)}>
                        <Trash2 size={12} />
                      </Button>
                    </div>
                  </div>
                  <div className="flex flex-wrap items-center gap-1.5 mt-2">
                    <Badge variant={ts.is_official ? 'success' : 'neutral'}>
                      {ts.is_official ? 'Verified' : 'Self-reported'}
                    </Badge>
                    {ts.test_date && <span className="text-xs text-muted-foreground">{formatDate(ts.test_date)}</span>}
                    {superscore != null && <Badge variant="info">Superscore {superscore}</Badge>}
                  </div>
                </Card>
              )
            })}
          </div>
        )}
      </section>

      {/* 6.3 Languages */}
      <section>
        <SectionHeader
          title="Languages"
          description="Proficiency and any certifications."
          action={
            <Button size="sm" onClick={() => open('language')}>
              <Plus size={14} /> Add language
            </Button>
          }
        />
        {languages.length === 0 ? (
          <EmptyState title="No languages yet" description="Add the languages you speak and any proof of proficiency." action={{ label: 'Add a language', onClick: () => open('language') }} />
        ) : (
          <div className="space-y-2">
            {languages.map(lang => (
              <Card key={lang.id} className="p-4 flex items-start justify-between gap-2">
                <div className="flex items-start gap-2.5">
                  <LanguagesIcon size={16} className="text-muted-foreground mt-0.5" />
                  <div>
                    <p className="font-medium text-foreground">{lang.language}</p>
                    <p className="text-sm text-muted-foreground">
                      {PROFICIENCY_LEVELS.find(x => x.value === lang.proficiency_level)?.label || lang.proficiency_level}
                      {lang.certification_type ? ` · ${lang.certification_type}` : ''}
                      {lang.certification_score ? ` ${lang.certification_score}` : ''}
                    </p>
                  </div>
                </div>
                <div className="flex gap-0.5 shrink-0">
                  <Button size="sm" variant="ghost" onClick={() => open('language', lang)}>
                    <Pencil size={12} />
                  </Button>
                  <Button size="sm" variant="ghost" onClick={() => langDelete.mutate(lang.id)}>
                    <Trash2 size={12} />
                  </Button>
                </div>
              </Card>
            ))}
          </div>
        )}
      </section>

      {/* 6.4 Research */}
      <section>
        <SectionHeader
          title="Research"
          description="Projects, labs, and publications."
          action={
            <Button size="sm" onClick={() => open('research')}>
              <Plus size={14} /> Add research
            </Button>
          }
        />
        {research.length === 0 ? (
          <EmptyState title="No research yet" description="Add research projects, lab work, and any outputs like papers or posters." action={{ label: 'Add research', onClick: () => open('research') }} />
        ) : (
          <div className="space-y-3">
            {research.map(r => (
              <Card key={r.id} className="p-4">
                <div className="flex items-start justify-between gap-2">
                  <div className="flex items-start gap-2.5 min-w-0">
                    <FlaskConical size={16} className="text-muted-foreground mt-0.5" />
                    <div className="min-w-0">
                      <p className="font-semibold text-foreground">{r.title}</p>
                      <p className="text-sm text-muted-foreground">
                        {RESEARCH_ROLES.find(x => x.value === r.role)?.label || r.role}
                        {r.institution_lab ? ` · ${r.institution_lab}` : ''}
                        {r.field_discipline ? ` · ${r.field_discipline}` : ''}
                      </p>
                    </div>
                  </div>
                  <div className="flex gap-0.5 shrink-0">
                    <Button size="sm" variant="ghost" onClick={() => open('research', r)}>
                      <Pencil size={12} />
                    </Button>
                    <Button size="sm" variant="ghost" onClick={() => rsDelete.mutate(r.id)}>
                      <Trash2 size={12} />
                    </Button>
                  </div>
                </div>
                <div className="flex flex-wrap items-center gap-1.5 mt-2">
                  {r.outputs && r.outputs !== 'none' && (
                    <Badge variant="info">{RESEARCH_OUTPUTS.find(x => x.value === r.outputs)?.label || r.outputs}</Badge>
                  )}
                  {r.publication_link && (
                    <a
                      href={r.publication_link}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-1 text-xs font-semibold text-secondary hover:underline"
                    >
                      <ExternalLink size={12} /> Publication
                    </a>
                  )}
                </div>
              </Card>
            ))}
          </div>
        )}
      </section>

      {/* Modals */}
      <Modal isOpen={modal === 'academic'} onClose={close} title={editItem ? 'Edit academic record' : 'Add academic record'} size="lg">
        <AcademicForm defaultValues={editItem} loading={acadCreate.isPending || acadUpdate.isPending} onSubmit={(d: any) => (editItem ? acadUpdate.mutate({ id: editItem.id, data: d }) : acadCreate.mutate(d))} />
      </Modal>
      <Modal isOpen={modal === 'test'} onClose={close} title={editItem ? 'Edit test score' : 'Add test score'}>
        <TestScoreForm defaultValues={editItem} loading={testCreate.isPending || testUpdate.isPending} onSubmit={(d: any) => (editItem ? testUpdate.mutate({ id: editItem.id, data: d }) : testCreate.mutate(d))} />
      </Modal>
      <Modal isOpen={modal === 'language'} onClose={close} title={editItem ? 'Edit language' : 'Add language'}>
        <LanguageForm defaultValues={editItem} loading={langCreate.isPending || langUpdate.isPending} onSubmit={(d: any) => (editItem ? langUpdate.mutate({ id: editItem.id, data: d }) : langCreate.mutate(d))} />
      </Modal>
      <Modal isOpen={modal === 'research'} onClose={close} title={editItem ? 'Edit research' : 'Add research'} size="lg">
        <ResearchForm defaultValues={editItem} loading={rsCreate.isPending || rsUpdate.isPending} onSubmit={(d: any) => (editItem ? rsUpdate.mutate({ id: editItem.id, data: d }) : rsCreate.mutate(d))} />
      </Modal>
    </div>
  )
}
