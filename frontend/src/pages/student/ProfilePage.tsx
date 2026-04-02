import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useForm } from 'react-hook-form'
import { getProfile, updateProfile, createAcademic, updateAcademic, deleteAcademic, createTestScore, updateTestScore, deleteTestScore, createActivity, updateActivity, deleteActivity, upsertPreferences, getNextStep } from '../../api/students'
import { getOnboarding } from '../../api/students'
import { listDocuments } from '../../api/documents'
import Modal from '../../components/ui/Modal'
import Button from '../../components/ui/Button'
import Input from '../../components/ui/Input'
import Textarea from '../../components/ui/Textarea'
import Select from '../../components/ui/Select'
import Card from '../../components/ui/Card'
import Badge from '../../components/ui/Badge'
import { SkeletonCard } from '../../components/ui/Skeleton'
import { showToast } from '../../stores/toast-store'
import { formatDate, formatCurrency, formatFileSize } from '../../utils/format'
import { DEGREE_LABELS, TEST_TYPES, ACTIVITY_TYPES, GPA_SCALES, CITY_SIZE_OPTIONS, FUNDING_OPTIONS } from '../../utils/constants'
import { Pencil, Trash2, Plus, Upload, Sparkles, CheckCircle2, Circle } from 'lucide-react'
import type { StudentProfile } from '../../types'

// --- Profile Strength Ring ---
function StrengthRing({ value }: { value: number }) {
  const radius = 44
  const stroke = 6
  const circumference = 2 * Math.PI * radius
  const offset = circumference - (value / 100) * circumference
  const color = value >= 80 ? '#22c55e' : value >= 50 ? '#f59e0b' : '#ef4444'

  return (
    <div className="relative w-28 h-28 flex-shrink-0">
      <svg className="w-28 h-28 -rotate-90" viewBox="0 0 100 100">
        <circle cx="50" cy="50" r={radius} fill="none" stroke="#e5e7eb" strokeWidth={stroke} />
        <circle
          cx="50" cy="50" r={radius} fill="none"
          stroke={color} strokeWidth={stroke}
          strokeDasharray={circumference} strokeDashoffset={offset}
          strokeLinecap="round"
          className="transition-all duration-700"
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="text-2xl font-bold">{value}%</span>
        <span className="text-[10px] text-gray-500">Complete</span>
      </div>
    </div>
  )
}

// --- Onboarding Section Checklist ---
const PROFILE_SECTIONS = [
  { key: 'basic_info', label: 'Basic Info', fields: ['first_name', 'last_name', 'nationality'] },
  { key: 'academics', label: 'Academic Records', fields: [] },
  { key: 'test_scores', label: 'Test Scores', fields: [] },
  { key: 'activities', label: 'Activities', fields: [] },
  { key: 'preferences', label: 'Preferences', fields: [] },
  { key: 'documents', label: 'Documents', fields: [] },
]

export default function ProfilePage() {
  const queryClient = useQueryClient()
  const [editModal, setEditModal] = useState<string | null>(null)
  const [editItem, setEditItem] = useState<any>(null)

  const { data: profile, isLoading } = useQuery({ queryKey: ['profile'], queryFn: getProfile })
  const { data: onboarding } = useQuery({ queryKey: ['onboarding'], queryFn: getOnboarding })
  const { data: nextStep } = useQuery({ queryKey: ['next-step'], queryFn: getNextStep })
  const { data: documents } = useQuery({ queryKey: ['documents'], queryFn: listDocuments })

  const invalidateAll = () => {
    queryClient.invalidateQueries({ queryKey: ['profile'] })
    queryClient.invalidateQueries({ queryKey: ['onboarding'] })
    queryClient.invalidateQueries({ queryKey: ['next-step'] })
  }

  const profileMut = useMutation({ mutationFn: (data: any) => updateProfile(data), onSuccess: () => { invalidateAll(); setEditModal(null); showToast('Profile updated', 'success') } })
  const acadCreateMut = useMutation({ mutationFn: createAcademic, onSuccess: () => { invalidateAll(); setEditModal(null); showToast('Record added', 'success') } })
  const acadUpdateMut = useMutation({ mutationFn: ({ id, data }: { id: string; data: any }) => updateAcademic(id, data), onSuccess: () => { invalidateAll(); setEditModal(null); showToast('Record updated', 'success') } })
  const acadDeleteMut = useMutation({ mutationFn: deleteAcademic, onSuccess: () => { invalidateAll(); showToast('Record deleted', 'success') } })
  const testCreateMut = useMutation({ mutationFn: createTestScore, onSuccess: () => { invalidateAll(); setEditModal(null); showToast('Score added', 'success') } })
  const testUpdateMut = useMutation({ mutationFn: ({ id, data }: { id: string; data: any }) => updateTestScore(id, data), onSuccess: () => { invalidateAll(); setEditModal(null); showToast('Score updated', 'success') } })
  const testDeleteMut = useMutation({ mutationFn: deleteTestScore, onSuccess: () => { invalidateAll(); showToast('Score deleted', 'success') } })
  const actCreateMut = useMutation({ mutationFn: createActivity, onSuccess: () => { invalidateAll(); setEditModal(null); showToast('Activity added', 'success') } })
  const actUpdateMut = useMutation({ mutationFn: ({ id, data }: { id: string; data: any }) => updateActivity(id, data), onSuccess: () => { invalidateAll(); setEditModal(null); showToast('Activity updated', 'success') } })
  const actDeleteMut = useMutation({ mutationFn: deleteActivity, onSuccess: () => { invalidateAll(); showToast('Activity deleted', 'success') } })
  const prefsMut = useMutation({ mutationFn: upsertPreferences, onSuccess: () => { invalidateAll(); setEditModal(null); showToast('Preferences updated', 'success') } })

  if (isLoading) return <div className="p-6 space-y-4">{Array.from({ length: 4 }).map((_, i) => <SkeletonCard key={i} />)}</div>

  const p: StudentProfile | null = profile
  const completionPct = onboarding?.completion_percentage ?? 0
  const stepsCompleted = onboarding?.steps_completed ?? []
  const documentsList: any[] = Array.isArray(documents) ? documents : []

  // Derive section completion
  const sectionDone = (key: string) => {
    if (stepsCompleted.includes(key)) return true
    switch (key) {
      case 'basic_info': return !!(p?.first_name && p?.last_name && p?.nationality)
      case 'academics': return (p?.academic_records ?? []).length > 0
      case 'test_scores': return (p?.test_scores ?? []).length > 0
      case 'activities': return (p?.activities ?? []).length > 0
      case 'preferences': return !!p?.preferences
      case 'documents': return documentsList.length > 0
      default: return false
    }
  }

  return (
    <div className="p-6 max-w-3xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">My Profile</h1>
      </div>

      {/* Profile Strength Card */}
      <Card className="p-5">
        <div className="flex items-center gap-6">
          <StrengthRing value={completionPct} />
          <div className="flex-1 min-w-0">
            <h2 className="font-semibold text-gray-900 mb-2">Profile Strength</h2>
            <div className="grid grid-cols-2 gap-1.5">
              {PROFILE_SECTIONS.map(s => (
                <div key={s.key} className="flex items-center gap-2 text-sm">
                  {sectionDone(s.key) ? (
                    <CheckCircle2 size={14} className="text-green-500 flex-shrink-0" />
                  ) : (
                    <Circle size={14} className="text-gray-300 flex-shrink-0" />
                  )}
                  <span className={sectionDone(s.key) ? 'text-gray-500' : 'text-gray-900'}>{s.label}</span>
                </div>
              ))}
            </div>
            {nextStep && completionPct < 100 && (
              <div className="mt-3 flex items-start gap-2 bg-blue-50 rounded-lg px-3 py-2">
                <Sparkles size={14} className="text-blue-600 mt-0.5 flex-shrink-0" />
                <div className="text-sm text-blue-800">
                  <span className="font-medium">Tip:</span> {nextStep.guidance_text || `Complete your ${nextStep.section} to improve your profile.`}
                </div>
              </div>
            )}
          </div>
        </div>
      </Card>

      {/* Basic Info */}
      <Card className="p-5">
        <div className="flex justify-between items-start mb-3">
          <h2 className="font-semibold text-gray-900">Basic Info</h2>
          <Button size="sm" variant="ghost" onClick={() => { setEditItem(p); setEditModal('basic') }}><Pencil size={14} /></Button>
        </div>
        <dl className="grid grid-cols-2 gap-2 text-sm">
          <div><dt className="text-gray-500">Name</dt><dd>{p?.first_name ?? '—'} {p?.last_name ?? ''}</dd></div>
          <div><dt className="text-gray-500">Nationality</dt><dd>{p?.nationality ?? '—'}</dd></div>
          <div><dt className="text-gray-500">Residence</dt><dd>{p?.country_of_residence ?? '—'}</dd></div>
          <div><dt className="text-gray-500">DOB</dt><dd>{formatDate(p?.date_of_birth)}</dd></div>
        </dl>
        {p?.bio_text && <p className="mt-3 text-sm text-gray-600">{p.bio_text}</p>}
      </Card>

      {/* Academic Records */}
      <Card className="p-5">
        <div className="flex justify-between items-start mb-3">
          <h2 className="font-semibold text-gray-900">Academic Records</h2>
          <Button size="sm" variant="ghost" onClick={() => { setEditItem(null); setEditModal('academic') }}><Plus size={14} /></Button>
        </div>
        {(p?.academic_records ?? []).length === 0 ? (
          <p className="text-sm text-gray-500">No academic records yet</p>
        ) : (
          <div className="space-y-3">
            {p!.academic_records.map(rec => (
              <div key={rec.id} className="flex justify-between items-start border-b border-gray-100 pb-3 last:border-0">
                <div>
                  <p className="font-medium text-sm">{rec.institution_name} — {DEGREE_LABELS[rec.degree_type] || rec.degree_type} {rec.field_of_study || ''}</p>
                  <p className="text-xs text-gray-500">GPA: {rec.gpa ?? '—'}/{rec.gpa_scale ?? '4.0'} | {rec.start_date?.slice(0, 4)}-{rec.is_current ? 'Present' : rec.end_date?.slice(0, 4)}</p>
                </div>
                <div className="flex gap-1">
                  <Button size="sm" variant="ghost" onClick={() => { setEditItem(rec); setEditModal('academic') }}><Pencil size={12} /></Button>
                  <Button size="sm" variant="ghost" onClick={() => acadDeleteMut.mutate(rec.id)}><Trash2 size={12} /></Button>
                </div>
              </div>
            ))}
          </div>
        )}
      </Card>

      {/* Test Scores */}
      <Card className="p-5">
        <div className="flex justify-between items-start mb-3">
          <h2 className="font-semibold text-gray-900">Test Scores</h2>
          <Button size="sm" variant="ghost" onClick={() => { setEditItem(null); setEditModal('test') }}><Plus size={14} /></Button>
        </div>
        {(p?.test_scores ?? []).length === 0 ? (
          <p className="text-sm text-gray-500">No test scores yet</p>
        ) : (
          <div className="space-y-3">
            {p!.test_scores.map(ts => (
              <div key={ts.id} className="flex justify-between items-start border-b border-gray-100 pb-3 last:border-0">
                <div>
                  <p className="font-medium text-sm">{ts.test_type}: {ts.total_score ?? '—'}</p>
                  {ts.section_scores && <p className="text-xs text-gray-500">{Object.entries(ts.section_scores).map(([k, v]) => `${k}: ${v}`).join(', ')}</p>}
                  <p className="text-xs text-gray-400">{ts.is_official ? 'Official' : 'Self-reported'} | {formatDate(ts.test_date)}</p>
                </div>
                <div className="flex gap-1">
                  <Button size="sm" variant="ghost" onClick={() => { setEditItem(ts); setEditModal('test') }}><Pencil size={12} /></Button>
                  <Button size="sm" variant="ghost" onClick={() => testDeleteMut.mutate(ts.id)}><Trash2 size={12} /></Button>
                </div>
              </div>
            ))}
          </div>
        )}
      </Card>

      {/* Activities */}
      <Card className="p-5">
        <div className="flex justify-between items-start mb-3">
          <h2 className="font-semibold text-gray-900">Activities</h2>
          <Button size="sm" variant="ghost" onClick={() => { setEditItem(null); setEditModal('activity') }}><Plus size={14} /></Button>
        </div>
        {(p?.activities ?? []).length === 0 ? (
          <p className="text-sm text-gray-500">No activities yet</p>
        ) : (
          <div className="space-y-3">
            {p!.activities.map(act => (
              <div key={act.id} className="flex justify-between items-start border-b border-gray-100 pb-3 last:border-0">
                <div>
                  <p className="font-medium text-sm">{act.title} — {act.organization ?? ''}</p>
                  <p className="text-xs text-gray-500">{ACTIVITY_TYPES.find(t => t.value === act.activity_type)?.label} | {act.start_date?.slice(0, 7)}-{act.is_current ? 'Present' : act.end_date?.slice(0, 7) ?? ''} {act.hours_per_week ? `| ${act.hours_per_week} hrs/wk` : ''}</p>
                </div>
                <div className="flex gap-1">
                  <Button size="sm" variant="ghost" onClick={() => { setEditItem(act); setEditModal('activity') }}><Pencil size={12} /></Button>
                  <Button size="sm" variant="ghost" onClick={() => actDeleteMut.mutate(act.id)}><Trash2 size={12} /></Button>
                </div>
              </div>
            ))}
          </div>
        )}
      </Card>

      {/* Preferences */}
      <Card className="p-5">
        <div className="flex justify-between items-start mb-3">
          <h2 className="font-semibold text-gray-900">Preferences</h2>
          <Button size="sm" variant="ghost" onClick={() => { setEditItem(p?.preferences); setEditModal('preferences') }}><Pencil size={14} /></Button>
        </div>
        {p?.preferences ? (
          <dl className="grid grid-cols-2 gap-2 text-sm">
            <div><dt className="text-gray-500">Countries</dt><dd>{p.preferences.preferred_countries?.join(', ') || '—'}</dd></div>
            <div><dt className="text-gray-500">Budget</dt><dd>{p.preferences.budget_min != null ? `${formatCurrency(p.preferences.budget_min)} - ${formatCurrency(p.preferences.budget_max)}` : '—'}</dd></div>
            <div><dt className="text-gray-500">Funding</dt><dd>{p.preferences.funding_requirement ?? '—'}</dd></div>
            <div><dt className="text-gray-500">City Size</dt><dd>{p.preferences.preferred_city_size ?? '—'}</dd></div>
          </dl>
        ) : (
          <p className="text-sm text-gray-500">No preferences set yet</p>
        )}
      </Card>

      {/* Documents */}
      <Card className="p-5">
        <div className="flex justify-between items-start mb-3">
          <h2 className="font-semibold text-gray-900">Documents</h2>
          <Button size="sm" variant="ghost" onClick={() => setEditModal('upload')}><Upload size={14} /></Button>
        </div>
        {documentsList.length === 0 ? (
          <p className="text-sm text-gray-500">No documents uploaded</p>
        ) : (
          <div className="space-y-2">
            {documentsList.map((doc: any) => (
              <div key={doc.id} className="flex justify-between items-center text-sm">
                <span>{doc.file_name} ({formatFileSize(doc.file_size_bytes)})</span>
                <Badge variant="neutral">{doc.document_type}</Badge>
              </div>
            ))}
          </div>
        )}
      </Card>

      {/* === MODALS === */}

      {/* Basic Info Modal */}
      <Modal isOpen={editModal === 'basic'} onClose={() => setEditModal(null)} title="Edit Basic Info">
        <BasicInfoForm
          defaultValues={editItem}
          onSubmit={data => profileMut.mutate(data)}
          loading={profileMut.isPending}
        />
      </Modal>

      {/* Academic Modal */}
      <Modal isOpen={editModal === 'academic'} onClose={() => setEditModal(null)} title={editItem ? 'Edit Academic Record' : 'Add Academic Record'}>
        <AcademicForm
          defaultValues={editItem}
          onSubmit={data => editItem ? acadUpdateMut.mutate({ id: editItem.id, data }) : acadCreateMut.mutate(data)}
          loading={acadCreateMut.isPending || acadUpdateMut.isPending}
        />
      </Modal>

      {/* Test Score Modal */}
      <Modal isOpen={editModal === 'test'} onClose={() => setEditModal(null)} title={editItem ? 'Edit Test Score' : 'Add Test Score'}>
        <TestScoreForm
          defaultValues={editItem}
          onSubmit={data => editItem ? testUpdateMut.mutate({ id: editItem.id, data }) : testCreateMut.mutate(data)}
          loading={testCreateMut.isPending || testUpdateMut.isPending}
        />
      </Modal>

      {/* Activity Modal */}
      <Modal isOpen={editModal === 'activity'} onClose={() => setEditModal(null)} title={editItem ? 'Edit Activity' : 'Add Activity'}>
        <ActivityForm
          defaultValues={editItem}
          onSubmit={data => editItem ? actUpdateMut.mutate({ id: editItem.id, data }) : actCreateMut.mutate(data)}
          loading={actCreateMut.isPending || actUpdateMut.isPending}
        />
      </Modal>

      {/* Preferences Modal */}
      <Modal isOpen={editModal === 'preferences'} onClose={() => setEditModal(null)} title="Edit Preferences" size="lg">
        <PreferencesForm
          defaultValues={editItem}
          onSubmit={data => prefsMut.mutate(data)}
          loading={prefsMut.isPending}
        />
      </Modal>
    </div>
  )
}

// --- Sub-forms ---

function BasicInfoForm({ defaultValues, onSubmit, loading }: { defaultValues: any; onSubmit: (d: any) => void; loading: boolean }) {
  const { register, handleSubmit } = useForm({ defaultValues: { first_name: defaultValues?.first_name || '', last_name: defaultValues?.last_name || '', date_of_birth: defaultValues?.date_of_birth?.slice(0, 10) || '', nationality: defaultValues?.nationality || '', country_of_residence: defaultValues?.country_of_residence || '', bio_text: defaultValues?.bio_text || '', goals_text: defaultValues?.goals_text || '' } })
  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-3">
      <div className="grid grid-cols-2 gap-3">
        <Input label="First Name" {...register('first_name')} />
        <Input label="Last Name" {...register('last_name')} />
      </div>
      <Input label="Date of Birth" type="date" {...register('date_of_birth')} />
      <Input label="Nationality" {...register('nationality')} />
      <Input label="Country of Residence" {...register('country_of_residence')} />
      <Textarea label="Bio" {...register('bio_text')} />
      <Textarea label="Goals" {...register('goals_text')} />
      <Button type="submit" loading={loading} className="w-full">Save</Button>
    </form>
  )
}

function AcademicForm({ defaultValues, onSubmit, loading }: { defaultValues: any; onSubmit: (d: any) => void; loading: boolean }) {
  const { register, handleSubmit } = useForm({ defaultValues: { institution_name: defaultValues?.institution_name || '', degree_type: defaultValues?.degree_type || 'bachelors', field_of_study: defaultValues?.field_of_study || '', gpa: defaultValues?.gpa || '', gpa_scale: defaultValues?.gpa_scale || '4.0', start_date: defaultValues?.start_date?.slice(0, 10) || '', end_date: defaultValues?.end_date?.slice(0, 10) || '', is_current: defaultValues?.is_current || false, country: defaultValues?.country || '' } })
  return (
    <form onSubmit={handleSubmit(d => onSubmit({ ...d, gpa: d.gpa ? Number(d.gpa) : null }))} className="space-y-3">
      <Input label="Institution Name" {...register('institution_name')} />
      <Select label="Degree Type" options={Object.entries(DEGREE_LABELS).map(([v, l]) => ({ value: v, label: l }))} {...register('degree_type')} />
      <Input label="Field of Study" {...register('field_of_study')} />
      <div className="grid grid-cols-2 gap-3">
        <Input label="GPA" type="number" step="0.01" {...register('gpa')} />
        <Select label="GPA Scale" options={GPA_SCALES} {...register('gpa_scale')} />
      </div>
      <div className="grid grid-cols-2 gap-3">
        <Input label="Start Date" type="date" {...register('start_date')} />
        <Input label="End Date" type="date" {...register('end_date')} />
      </div>
      <Input label="Country" {...register('country')} />
      <Button type="submit" loading={loading} className="w-full">Save</Button>
    </form>
  )
}

function TestScoreForm({ defaultValues, onSubmit, loading }: { defaultValues: any; onSubmit: (d: any) => void; loading: boolean }) {
  const { register, handleSubmit } = useForm({ defaultValues: { test_type: defaultValues?.test_type || 'SAT', total_score: defaultValues?.total_score || '', test_date: defaultValues?.test_date?.slice(0, 10) || '', is_official: defaultValues?.is_official || false } })
  return (
    <form onSubmit={handleSubmit(d => onSubmit({ ...d, total_score: d.total_score ? Number(d.total_score) : null }))} className="space-y-3">
      <Select label="Test Type" options={TEST_TYPES.map(t => ({ value: t, label: t }))} {...register('test_type')} />
      <Input label="Total Score" type="number" {...register('total_score')} />
      <Input label="Test Date" type="date" {...register('test_date')} />
      <label className="flex items-center gap-2 text-sm"><input type="checkbox" {...register('is_official')} /> Official Score</label>
      <Button type="submit" loading={loading} className="w-full">Save</Button>
    </form>
  )
}

function ActivityForm({ defaultValues, onSubmit, loading }: { defaultValues: any; onSubmit: (d: any) => void; loading: boolean }) {
  const { register, handleSubmit } = useForm({ defaultValues: { activity_type: defaultValues?.activity_type || 'extracurricular', title: defaultValues?.title || '', organization: defaultValues?.organization || '', description: defaultValues?.description || '', start_date: defaultValues?.start_date?.slice(0, 10) || '', end_date: defaultValues?.end_date?.slice(0, 10) || '', is_current: defaultValues?.is_current || false, hours_per_week: defaultValues?.hours_per_week || '', impact_description: defaultValues?.impact_description || '' } })
  return (
    <form onSubmit={handleSubmit(d => onSubmit({ ...d, hours_per_week: d.hours_per_week ? Number(d.hours_per_week) : null }))} className="space-y-3">
      <Select label="Type" options={ACTIVITY_TYPES} {...register('activity_type')} />
      <Input label="Title" {...register('title')} />
      <Input label="Organization" {...register('organization')} />
      <Textarea label="Description" {...register('description')} />
      <div className="grid grid-cols-2 gap-3">
        <Input label="Start Date" type="date" {...register('start_date')} />
        <Input label="End Date" type="date" {...register('end_date')} />
      </div>
      <Input label="Hours/Week" type="number" {...register('hours_per_week')} />
      <Textarea label="Impact" {...register('impact_description')} />
      <Button type="submit" loading={loading} className="w-full">Save</Button>
    </form>
  )
}

function PreferencesForm({ defaultValues, onSubmit, loading }: { defaultValues: any; onSubmit: (d: any) => void; loading: boolean }) {
  const { register, handleSubmit } = useForm({ defaultValues: { preferred_countries: defaultValues?.preferred_countries?.join(', ') || '', preferred_city_size: defaultValues?.preferred_city_size || '', budget_min: defaultValues?.budget_min || '', budget_max: defaultValues?.budget_max || '', funding_requirement: defaultValues?.funding_requirement || '', goals_text: defaultValues?.goals_text || '' } })
  return (
    <form onSubmit={handleSubmit(d => onSubmit({ ...d, preferred_countries: d.preferred_countries ? d.preferred_countries.split(',').map((s: string) => s.trim()).filter(Boolean) : [], budget_min: d.budget_min ? Number(d.budget_min) : null, budget_max: d.budget_max ? Number(d.budget_max) : null }))} className="space-y-3">
      <Input label="Preferred Countries (comma-separated)" {...register('preferred_countries')} />
      <Select label="City Size" options={CITY_SIZE_OPTIONS} placeholder="Select..." {...register('preferred_city_size')} />
      <div className="grid grid-cols-2 gap-3">
        <Input label="Budget Min ($)" type="number" {...register('budget_min')} />
        <Input label="Budget Max ($)" type="number" {...register('budget_max')} />
      </div>
      <Select label="Funding Requirement" options={FUNDING_OPTIONS} placeholder="Select..." {...register('funding_requirement')} />
      <Textarea label="Goals" {...register('goals_text')} />
      <Button type="submit" loading={loading} className="w-full">Save</Button>
    </form>
  )
}
