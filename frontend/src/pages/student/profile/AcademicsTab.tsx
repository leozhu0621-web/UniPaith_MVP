/**
 * Profile → Academics tab (spec 10 §6).
 * Academics (records + GPA) · Test Scores · Languages · Research.
 * Reads the shared ['profile'] query; reuses ProfileForms.
 */
import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { FlaskConical, GraduationCap, Languages as LanguagesIcon, ClipboardList } from 'lucide-react'

import {
  createAcademic,
  createLanguage,
  createResearch,
  createTestScore,
  deleteAcademic,
  deleteLanguage,
  deleteResearch,
  deleteTestScore,
  updateAcademic,
  updateLanguage,
  updateResearch,
  updateTestScore,
} from '../../../api/students'
import Modal from '../../../components/ui/Modal'
import { SkeletonCard } from '../../../components/ui/Skeleton'
import { showToast } from '../../../stores/toast-store'
import { DEGREE_LABELS, PROFICIENCY_LEVELS, RESEARCH_ROLES } from '../../../utils/constants'
import { formatDate } from '../../../utils/format'
import { AcademicForm, LanguageForm, ResearchForm, TestScoreForm } from '../components/ProfileForms'
import { EmptyHint, ItemRow, SectionCard, useProfile } from './_shared'

const lastUpdated = (xs: any[] = []) => {
  const ds = xs.map(x => x?.updated_at).filter(Boolean).sort()
  return ds.length ? ds[ds.length - 1] : null
}

type Editing = { kind: 'academic' | 'test' | 'language' | 'research'; item: any } | null

export default function AcademicsTab() {
  const qc = useQueryClient()
  const { data: p, isLoading } = useProfile()
  const [editing, setEditing] = useState<Editing>(null)
  const close = () => setEditing(null)
  const done = (msg: string) => {
    qc.invalidateQueries({ queryKey: ['profile'] })
    qc.invalidateQueries({ queryKey: ['profile-overview'] })
    close()
    showToast(msg, 'success')
  }
  const fail = () => showToast("Something didn't work. Try again.", 'error')

  const acadCreate = useMutation({ mutationFn: createAcademic, onSuccess: () => done('Saved'), onError: fail })
  const acadUpdate = useMutation({ mutationFn: ({ id, data }: any) => updateAcademic(id, data), onSuccess: () => done('Saved'), onError: fail })
  const acadDelete = useMutation({ mutationFn: deleteAcademic, onSuccess: () => done('Deleted'), onError: fail })
  const testCreate = useMutation({ mutationFn: createTestScore, onSuccess: () => done('Saved'), onError: fail })
  const testUpdate = useMutation({ mutationFn: ({ id, data }: any) => updateTestScore(id, data), onSuccess: () => done('Saved'), onError: fail })
  const testDelete = useMutation({ mutationFn: deleteTestScore, onSuccess: () => done('Deleted'), onError: fail })
  const langCreate = useMutation({ mutationFn: createLanguage, onSuccess: () => done('Saved'), onError: fail })
  const langUpdate = useMutation({ mutationFn: ({ id, data }: any) => updateLanguage(id, data), onSuccess: () => done('Saved'), onError: fail })
  const langDelete = useMutation({ mutationFn: deleteLanguage, onSuccess: () => done('Deleted'), onError: fail })
  const resCreate = useMutation({ mutationFn: createResearch, onSuccess: () => done('Saved'), onError: fail })
  const resUpdate = useMutation({ mutationFn: ({ id, data }: any) => updateResearch(id, data), onSuccess: () => done('Saved'), onError: fail })
  const resDelete = useMutation({ mutationFn: deleteResearch, onSuccess: () => done('Deleted'), onError: fail })

  if (isLoading) return <div className="space-y-4"><SkeletonCard /><SkeletonCard /></div>

  const academics = p?.academic_records ?? []
  const tests = p?.test_scores ?? []
  const languages = p?.languages ?? []
  const research = p?.research_entries ?? []

  return (
    <div className="space-y-6">
      <SectionCard title="Academics" icon={GraduationCap} count={academics.length} lastUpdated={lastUpdated(academics)} onAdd={() => setEditing({ kind: 'academic', item: null })}>
        {academics.length === 0 ? (
          <EmptyHint>No academic records yet. Add one so match scores can use your grades.</EmptyHint>
        ) : (
          <div className="space-y-3">
            {academics.map(rec => (
              <ItemRow key={rec.id} onEdit={() => setEditing({ kind: 'academic', item: rec })} onDelete={() => acadDelete.mutate(rec.id)}>
                <p className="font-medium text-sm text-charcoal">{rec.institution_name} — {DEGREE_LABELS[rec.degree_type] || rec.degree_type} {rec.field_of_study || ''}</p>
                <p className="text-xs text-slate">GPA: {rec.gpa ?? '—'}/{rec.gpa_scale ?? '4.0'} · {rec.start_date?.slice(0, 4) ?? ''}–{rec.is_current ? 'Present' : rec.end_date?.slice(0, 4) ?? ''}</p>
              </ItemRow>
            ))}
          </div>
        )}
      </SectionCard>

      <SectionCard title="Test Scores" icon={ClipboardList} count={tests.length} lastUpdated={lastUpdated(tests)} onAdd={() => setEditing({ kind: 'test', item: null })}>
        {tests.length === 0 ? (
          <EmptyHint>No test scores yet. Add what you have — even unofficial scores help.</EmptyHint>
        ) : (
          <div className="space-y-3">
            {tests.map(ts => (
              <ItemRow key={ts.id} onEdit={() => setEditing({ kind: 'test', item: ts })} onDelete={() => testDelete.mutate(ts.id)}>
                <p className="font-medium text-sm text-charcoal">{ts.test_type}: {ts.total_score ?? '—'}</p>
                {ts.section_scores && <p className="text-xs text-slate">{Object.entries(ts.section_scores).map(([k, v]) => `${k}: ${v}`).join(', ')}</p>}
                <p className="text-xs text-slate">{ts.is_official ? 'Official' : 'Self-reported'} · {formatDate(ts.test_date)}</p>
              </ItemRow>
            ))}
          </div>
        )}
      </SectionCard>

      <SectionCard title="Languages" icon={LanguagesIcon} count={languages.length} lastUpdated={lastUpdated(languages)} onAdd={() => setEditing({ kind: 'language', item: null })}>
        {languages.length === 0 ? (
          <EmptyHint>Add the languages you speak and any certifications.</EmptyHint>
        ) : (
          <div className="space-y-3">
            {languages.map((lang: any) => (
              <ItemRow key={lang.id} onEdit={() => setEditing({ kind: 'language', item: lang })} onDelete={() => langDelete.mutate(lang.id)}>
                <p className="font-medium text-sm text-charcoal">{lang.language}</p>
                <p className="text-xs text-slate">{PROFICIENCY_LEVELS.find((x: any) => x.value === lang.proficiency_level)?.label || lang.proficiency_level}{lang.certification_type ? ` · ${lang.certification_type}${lang.certification_score ? `: ${lang.certification_score}` : ''}` : ''}</p>
              </ItemRow>
            ))}
          </div>
        )}
      </SectionCard>

      <SectionCard title="Research" icon={FlaskConical} count={research.length} lastUpdated={lastUpdated(research)} onAdd={() => setEditing({ kind: 'research', item: null })}>
        {research.length === 0 ? (
          <EmptyHint>Add research projects, labs, and publications.</EmptyHint>
        ) : (
          <div className="space-y-3">
            {research.map((r: any) => (
              <ItemRow key={r.id} onEdit={() => setEditing({ kind: 'research', item: r })} onDelete={() => resDelete.mutate(r.id)}>
                <p className="font-medium text-sm text-charcoal">{r.title}</p>
                <p className="text-xs text-slate">{RESEARCH_ROLES.find((x: any) => x.value === r.role)?.label || r.role}{r.institution_lab ? ` · ${r.institution_lab}` : ''}{r.field_discipline ? ` · ${r.field_discipline}` : ''}</p>
                {r.publication_link && <a href={r.publication_link} target="_blank" rel="noopener noreferrer" className="text-xs text-cobalt story-link">View publication</a>}
              </ItemRow>
            ))}
          </div>
        )}
      </SectionCard>

      <Modal isOpen={editing?.kind === 'academic'} onClose={close} title={editing?.item ? 'Edit academic record' : 'Add academic record'}>
        <AcademicForm defaultValues={editing?.item} loading={acadCreate.isPending || acadUpdate.isPending} onSubmit={d => (editing?.item ? acadUpdate.mutate({ id: editing.item.id, data: d }) : acadCreate.mutate(d))} />
      </Modal>
      <Modal isOpen={editing?.kind === 'test'} onClose={close} title={editing?.item ? 'Edit test score' : 'Add test score'}>
        <TestScoreForm defaultValues={editing?.item} loading={testCreate.isPending || testUpdate.isPending} onSubmit={d => (editing?.item ? testUpdate.mutate({ id: editing.item.id, data: d }) : testCreate.mutate(d))} />
      </Modal>
      <Modal isOpen={editing?.kind === 'language'} onClose={close} title={editing?.item ? 'Edit language' : 'Add language'}>
        <LanguageForm defaultValues={editing?.item} loading={langCreate.isPending || langUpdate.isPending} onSubmit={d => (editing?.item ? langUpdate.mutate({ id: editing.item.id, data: d }) : langCreate.mutate(d))} />
      </Modal>
      <Modal isOpen={editing?.kind === 'research'} onClose={close} title={editing?.item ? 'Edit research' : 'Add research'} size="lg">
        <ResearchForm defaultValues={editing?.item} loading={resCreate.isPending || resUpdate.isPending} onSubmit={d => (editing?.item ? resUpdate.mutate({ id: editing.item.id, data: d }) : resCreate.mutate(d))} />
      </Modal>
    </div>
  )
}
