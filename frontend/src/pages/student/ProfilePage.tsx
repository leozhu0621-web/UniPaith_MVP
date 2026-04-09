import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { getProfile, updateProfile, createAcademic, updateAcademic, deleteAcademic, createTestScore, updateTestScore, deleteTestScore, createActivity, updateActivity, deleteActivity, createOnlinePresence, updateOnlinePresence, deleteOnlinePresence, createPortfolioItem, updatePortfolioItem, deletePortfolioItem, createResearch, updateResearch, deleteResearch, createLanguage, updateLanguage, deleteLanguage, createWorkExperience, updateWorkExperience, deleteWorkExperience, createCompetition, updateCompetition, deleteCompetition, upsertAccommodations, upsertScheduling, upsertVisaInfo, upsertPreferences, getNextStep } from '../../api/students'
import { getOnboarding, getTimeline, getAnalytics, getPeerComparison, exportProfileJson, upsertDataRights } from '../../api/students'
import { listDocuments } from '../../api/documents'
import Modal from '../../components/ui/Modal'
import Button from '../../components/ui/Button'
import Card from '../../components/ui/Card'
import Badge from '../../components/ui/Badge'
import { SkeletonCard } from '../../components/ui/Skeleton'
import { showToast } from '../../stores/toast-store'
import { formatDate, formatCurrency, formatFileSize } from '../../utils/format'
import { DEGREE_LABELS, ACTIVITY_TYPES, PLATFORM_TYPES, PORTFOLIO_ITEM_TYPES, RESEARCH_ROLES, RESEARCH_OUTPUTS, PROFICIENCY_LEVELS, WORK_EXPERIENCE_TYPES, COMPETITION_LEVELS } from '../../utils/constants'
import { Pencil, Trash2, Plus, Upload, Sparkles, CheckCircle2, Circle, ExternalLink, FolderOpen, FlaskConical, Languages, Briefcase, Trophy, Accessibility, CalendarClock, Plane, Clock, BarChart3, Users, Download, Shield } from 'lucide-react'
import { BasicInfoForm, AcademicForm, CourseForm, TestScoreForm, ActivityForm, PreferencesForm, OnlinePresenceForm, PortfolioItemForm, ResearchForm, LanguageForm, WorkExperienceForm, CompetitionForm, AccommodationForm, SchedulingForm, VisaInfoForm, DataRightsForm } from './components/ProfileForms'
import { createCourse, updateCourse, deleteCourse } from '../../api/students'
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
  { key: 'online_presence', label: 'Online Presence', fields: [] },
  { key: 'portfolio', label: 'Portfolio', fields: [] },
  { key: 'research', label: 'Research', fields: [] },
  { key: 'languages', label: 'Languages', fields: [] },
  { key: 'work_experience', label: 'Work & Service', fields: [] },
  { key: 'competitions', label: 'Competitions', fields: [] },
  { key: 'preferences', label: 'Preferences', fields: [] },
  { key: 'documents', label: 'Documents', fields: [] },
]

export default function ProfilePage() {
  const queryClient = useQueryClient()
  const [editModal, setEditModal] = useState<string | null>(null)
  const [courseRecordId, setCourseRecordId] = useState<string | null>(null)
  const [editItem, setEditItem] = useState<any>(null)

  const { data: profile, isLoading } = useQuery({ queryKey: ['profile'], queryFn: getProfile })
  const { data: onboarding } = useQuery({ queryKey: ['onboarding'], queryFn: getOnboarding })
  const { data: nextStep } = useQuery({ queryKey: ['next-step'], queryFn: getNextStep })
  const { data: documents } = useQuery({ queryKey: ['documents'], queryFn: listDocuments })
  const { data: timeline } = useQuery({ queryKey: ['timeline'], queryFn: getTimeline })
  const { data: analytics } = useQuery({ queryKey: ['analytics'], queryFn: getAnalytics })
  const { data: peerComparison } = useQuery({ queryKey: ['peer-comparison'], queryFn: getPeerComparison })

  const invalidateAll = () => {
    queryClient.invalidateQueries({ queryKey: ['profile'] })
    queryClient.invalidateQueries({ queryKey: ['onboarding'] })
    queryClient.invalidateQueries({ queryKey: ['next-step'] })
  }

  const profileMut = useMutation({ mutationFn: (data: any) => updateProfile(data), onSuccess: () => { invalidateAll(); setEditModal(null); showToast('Profile updated', 'success') } })
  const acadCreateMut = useMutation({ mutationFn: createAcademic, onSuccess: () => { invalidateAll(); setEditModal(null); showToast('Record added', 'success') } })
  const acadUpdateMut = useMutation({ mutationFn: ({ id, data }: { id: string; data: any }) => updateAcademic(id, data), onSuccess: () => { invalidateAll(); setEditModal(null); showToast('Record updated', 'success') } })
  const acadDeleteMut = useMutation({ mutationFn: deleteAcademic, onSuccess: () => { invalidateAll(); showToast('Record deleted', 'success') } })
  const courseCreateMut = useMutation({ mutationFn: ({ recordId, data }: { recordId: string; data: any }) => createCourse(recordId, data), onSuccess: () => { invalidateAll(); setEditModal(null); showToast('Course added', 'success') } })
  const courseUpdateMut = useMutation({ mutationFn: ({ recordId, courseId, data }: { recordId: string; courseId: string; data: any }) => updateCourse(recordId, courseId, data), onSuccess: () => { invalidateAll(); setEditModal(null); showToast('Course updated', 'success') } })
  const courseDeleteMut = useMutation({ mutationFn: ({ recordId, courseId }: { recordId: string; courseId: string }) => deleteCourse(recordId, courseId), onSuccess: () => { invalidateAll(); showToast('Course removed', 'success') } })
  const testCreateMut = useMutation({ mutationFn: createTestScore, onSuccess: () => { invalidateAll(); setEditModal(null); showToast('Score added', 'success') } })
  const testUpdateMut = useMutation({ mutationFn: ({ id, data }: { id: string; data: any }) => updateTestScore(id, data), onSuccess: () => { invalidateAll(); setEditModal(null); showToast('Score updated', 'success') } })
  const testDeleteMut = useMutation({ mutationFn: deleteTestScore, onSuccess: () => { invalidateAll(); showToast('Score deleted', 'success') } })
  const actCreateMut = useMutation({ mutationFn: createActivity, onSuccess: () => { invalidateAll(); setEditModal(null); showToast('Activity added', 'success') } })
  const actUpdateMut = useMutation({ mutationFn: ({ id, data }: { id: string; data: any }) => updateActivity(id, data), onSuccess: () => { invalidateAll(); setEditModal(null); showToast('Activity updated', 'success') } })
  const actDeleteMut = useMutation({ mutationFn: deleteActivity, onSuccess: () => { invalidateAll(); showToast('Activity deleted', 'success') } })
  const opCreateMut = useMutation({ mutationFn: createOnlinePresence, onSuccess: () => { invalidateAll(); setEditModal(null); showToast('Link added', 'success') } })
  const opUpdateMut = useMutation({ mutationFn: ({ id, data }: { id: string; data: any }) => updateOnlinePresence(id, data), onSuccess: () => { invalidateAll(); setEditModal(null); showToast('Link updated', 'success') } })
  const opDeleteMut = useMutation({ mutationFn: deleteOnlinePresence, onSuccess: () => { invalidateAll(); showToast('Link removed', 'success') } })
  const pfCreateMut = useMutation({ mutationFn: createPortfolioItem, onSuccess: () => { invalidateAll(); setEditModal(null); showToast('Item added', 'success') } })
  const pfUpdateMut = useMutation({ mutationFn: ({ id, data }: { id: string; data: any }) => updatePortfolioItem(id, data), onSuccess: () => { invalidateAll(); setEditModal(null); showToast('Item updated', 'success') } })
  const pfDeleteMut = useMutation({ mutationFn: deletePortfolioItem, onSuccess: () => { invalidateAll(); showToast('Item removed', 'success') } })
  const rsCreateMut = useMutation({ mutationFn: createResearch, onSuccess: () => { invalidateAll(); setEditModal(null); showToast('Research added', 'success') } })
  const rsUpdateMut = useMutation({ mutationFn: ({ id, data }: { id: string; data: any }) => updateResearch(id, data), onSuccess: () => { invalidateAll(); setEditModal(null); showToast('Research updated', 'success') } })
  const rsDeleteMut = useMutation({ mutationFn: deleteResearch, onSuccess: () => { invalidateAll(); showToast('Research removed', 'success') } })
  const lnCreateMut = useMutation({ mutationFn: createLanguage, onSuccess: () => { invalidateAll(); setEditModal(null); showToast('Language added', 'success') } })
  const lnUpdateMut = useMutation({ mutationFn: ({ id, data }: { id: string; data: any }) => updateLanguage(id, data), onSuccess: () => { invalidateAll(); setEditModal(null); showToast('Language updated', 'success') } })
  const lnDeleteMut = useMutation({ mutationFn: deleteLanguage, onSuccess: () => { invalidateAll(); showToast('Language removed', 'success') } })
  const weCreateMut = useMutation({ mutationFn: createWorkExperience, onSuccess: () => { invalidateAll(); setEditModal(null); showToast('Experience added', 'success') } })
  const weUpdateMut = useMutation({ mutationFn: ({ id, data }: { id: string; data: any }) => updateWorkExperience(id, data), onSuccess: () => { invalidateAll(); setEditModal(null); showToast('Experience updated', 'success') } })
  const weDeleteMut = useMutation({ mutationFn: deleteWorkExperience, onSuccess: () => { invalidateAll(); showToast('Experience removed', 'success') } })
  const cpCreateMut = useMutation({ mutationFn: createCompetition, onSuccess: () => { invalidateAll(); setEditModal(null); showToast('Competition added', 'success') } })
  const cpUpdateMut = useMutation({ mutationFn: ({ id, data }: { id: string; data: any }) => updateCompetition(id, data), onSuccess: () => { invalidateAll(); setEditModal(null); showToast('Competition updated', 'success') } })
  const cpDeleteMut = useMutation({ mutationFn: deleteCompetition, onSuccess: () => { invalidateAll(); showToast('Competition removed', 'success') } })
  const accomMut = useMutation({ mutationFn: upsertAccommodations, onSuccess: () => { invalidateAll(); setEditModal(null); showToast('Accommodations updated', 'success') } })
  const schedMut = useMutation({ mutationFn: upsertScheduling, onSuccess: () => { invalidateAll(); setEditModal(null); showToast('Scheduling updated', 'success') } })
  const visaMut = useMutation({ mutationFn: upsertVisaInfo, onSuccess: () => { invalidateAll(); setEditModal(null); showToast('Visa info updated', 'success') } })
  const dataRightsMut = useMutation({ mutationFn: upsertDataRights, onSuccess: () => { invalidateAll(); setEditModal(null); showToast('Data rights updated', 'success') } })
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
      case 'online_presence': return (p?.online_presence ?? []).length > 0
      case 'portfolio': return (p?.portfolio_items ?? []).length > 0
      case 'research': return (p?.research_entries ?? []).length > 0
      case 'languages': return (p?.languages ?? []).length > 0
      case 'work_experience': return (p?.work_experiences ?? []).length > 0
      case 'competitions': return (p?.competitions ?? []).length > 0
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
            <h2 className="font-semibold text-brand-slate-700 mb-2">Profile Strength</h2>
            <div className="grid grid-cols-2 gap-1.5">
              {PROFILE_SECTIONS.map(s => (
                <div key={s.key} className="flex items-center gap-2 text-sm">
                  {sectionDone(s.key) ? (
                    <CheckCircle2 size={14} className="text-green-500 flex-shrink-0" />
                  ) : (
                    <Circle size={14} className="text-gray-300 flex-shrink-0" />
                  )}
                  <span className={sectionDone(s.key) ? 'text-gray-500' : 'text-brand-slate-700'}>{s.label}</span>
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
          <h2 className="font-semibold text-brand-slate-700">Basic Info</h2>
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
          <h2 className="font-semibold text-brand-slate-700">Academic Records</h2>
          <Button size="sm" variant="ghost" onClick={() => { setEditItem(null); setEditModal('academic') }}><Plus size={14} /></Button>
        </div>
        {(p?.academic_records ?? []).length === 0 ? (
          <p className="text-sm text-gray-500">No academic records yet</p>
        ) : (
          <div className="space-y-4">
            {p!.academic_records.map(rec => (
              <div key={rec.id} className="border-b border-gray-100 pb-4 last:border-0">
                <div className="flex justify-between items-start">
                  <div>
                    <p className="font-medium text-sm">{rec.institution_name} — {DEGREE_LABELS[rec.degree_type] || rec.degree_type} {rec.field_of_study || ''}</p>
                    <p className="text-xs text-gray-500">GPA: {rec.gpa ?? '—'}/{rec.gpa_scale ?? '4.0'} | {rec.start_date?.slice(0, 4)}-{rec.is_current ? 'Present' : rec.end_date?.slice(0, 4)}</p>
                    {rec.transcript_language && <p className="text-xs text-gray-400">Transcript: {rec.transcript_language}</p>}
                    {rec.credential_evaluation_status && rec.credential_evaluation_status !== 'none' && <p className="text-xs text-gray-400">Credential eval: {rec.credential_evaluation_status}</p>}
                    {rec.rigor_indicator_count != null && rec.rigor_indicator_count > 0 && <p className="text-xs text-gray-400">{rec.rigor_indicator_count} AP/IB/Honors courses</p>}
                  </div>
                  <div className="flex gap-1">
                    <Button size="sm" variant="ghost" onClick={() => { setEditItem(rec); setEditModal('academic') }}><Pencil size={12} /></Button>
                    <Button size="sm" variant="ghost" onClick={() => acadDeleteMut.mutate(rec.id)}><Trash2 size={12} /></Button>
                  </div>
                </div>
                {/* Nested courses */}
                {(rec.courses ?? []).length > 0 && (
                  <div className="mt-2 ml-4 space-y-1">
                    {rec.courses.map(c => (
                      <div key={c.id} className="flex justify-between items-center text-xs">
                        <span className="text-gray-600">{c.course_code ? `${c.course_code} — ` : ''}{c.course_name} <span className="text-gray-400">({c.course_level})</span>{c.grade ? ` — ${c.grade}` : ''}</span>
                        <div className="flex gap-1">
                          <Button size="sm" variant="ghost" onClick={() => { setCourseRecordId(rec.id); setEditItem(c); setEditModal('course') }}><Pencil size={10} /></Button>
                          <Button size="sm" variant="ghost" onClick={() => courseDeleteMut.mutate({ recordId: rec.id, courseId: c.id })}><Trash2 size={10} /></Button>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
                <button
                  onClick={() => { setCourseRecordId(rec.id); setEditItem(null); setEditModal('course') }}
                  className="mt-2 ml-4 text-xs text-sky-600 hover:underline"
                >
                  + Add course
                </button>
              </div>
            ))}
          </div>
        )}
      </Card>

      {/* Test Scores */}
      <Card className="p-5">
        <div className="flex justify-between items-start mb-3">
          <h2 className="font-semibold text-brand-slate-700">Test Scores</h2>
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
          <h2 className="font-semibold text-brand-slate-700">Activities</h2>
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

      {/* Online Presence */}
      <Card className="p-5">
        <div className="flex justify-between items-start mb-3">
          <h2 className="font-semibold text-brand-slate-700">Online Presence</h2>
          <Button size="sm" variant="ghost" onClick={() => { setEditItem(null); setEditModal('online_presence') }}><Plus size={14} /></Button>
        </div>
        {(p?.online_presence ?? []).length === 0 ? (
          <p className="text-sm text-gray-500">Add your LinkedIn, GitHub, or portfolio links</p>
        ) : (
          <div className="space-y-3">
            {p!.online_presence.map(op => (
              <div key={op.id} className="flex justify-between items-start border-b border-gray-100 pb-3 last:border-0">
                <div className="flex items-center gap-2">
                  <ExternalLink size={14} className="text-gray-400 flex-shrink-0" />
                  <div>
                    <p className="font-medium text-sm">{PLATFORM_TYPES.find(t => t.value === op.platform_type)?.label || op.platform_type}</p>
                    <a href={op.url} target="_blank" rel="noopener noreferrer" className="text-xs text-sky-600 hover:underline truncate block max-w-xs">{op.display_name || op.url}</a>
                  </div>
                </div>
                <div className="flex gap-1">
                  <Button size="sm" variant="ghost" onClick={() => { setEditItem(op); setEditModal('online_presence') }}><Pencil size={12} /></Button>
                  <Button size="sm" variant="ghost" onClick={() => opDeleteMut.mutate(op.id)}><Trash2 size={12} /></Button>
                </div>
              </div>
            ))}
          </div>
        )}
      </Card>

      {/* Portfolio */}
      <Card className="p-5">
        <div className="flex justify-between items-start mb-3">
          <h2 className="font-semibold text-brand-slate-700">Portfolio</h2>
          <Button size="sm" variant="ghost" onClick={() => { setEditItem(null); setEditModal('portfolio') }}><Plus size={14} /></Button>
        </div>
        {(p?.portfolio_items ?? []).length === 0 ? (
          <p className="text-sm text-gray-500">Showcase your projects and work samples</p>
        ) : (
          <div className="space-y-3">
            {p!.portfolio_items.map(item => (
              <div key={item.id} className="flex justify-between items-start border-b border-gray-100 pb-3 last:border-0">
                <div className="flex items-start gap-2">
                  <FolderOpen size={14} className="text-gray-400 mt-0.5 flex-shrink-0" />
                  <div>
                    <p className="font-medium text-sm">{item.title}</p>
                    <p className="text-xs text-gray-500">{PORTFOLIO_ITEM_TYPES.find(t => t.value === item.item_type)?.label || item.item_type}</p>
                    {item.url && <a href={item.url} target="_blank" rel="noopener noreferrer" className="text-xs text-sky-600 hover:underline truncate block max-w-xs">{item.url}</a>}
                    {item.description && <p className="text-xs text-gray-400 mt-1 line-clamp-2">{item.description}</p>}
                  </div>
                </div>
                <div className="flex gap-1">
                  <Button size="sm" variant="ghost" onClick={() => { setEditItem(item); setEditModal('portfolio') }}><Pencil size={12} /></Button>
                  <Button size="sm" variant="ghost" onClick={() => pfDeleteMut.mutate(item.id)}><Trash2 size={12} /></Button>
                </div>
              </div>
            ))}
          </div>
        )}
      </Card>

      {/* Research */}
      <Card className="p-5">
        <div className="flex justify-between items-start mb-3">
          <h2 className="font-semibold text-brand-slate-700">Research</h2>
          <Button size="sm" variant="ghost" onClick={() => { setEditItem(null); setEditModal('research') }}><Plus size={14} /></Button>
        </div>
        {(p?.research_entries ?? []).length === 0 ? (
          <p className="text-sm text-gray-500">Add your research experience, labs, and publications</p>
        ) : (
          <div className="space-y-3">
            {p!.research_entries.map(r => (
              <div key={r.id} className="flex justify-between items-start border-b border-gray-100 pb-3 last:border-0">
                <div className="flex items-start gap-2">
                  <FlaskConical size={14} className="text-gray-400 mt-0.5 flex-shrink-0" />
                  <div>
                    <p className="font-medium text-sm">{r.title}</p>
                    <p className="text-xs text-gray-500">
                      {RESEARCH_ROLES.find(x => x.value === r.role)?.label || r.role}
                      {r.institution_lab ? ` at ${r.institution_lab}` : ''}
                    </p>
                    {r.field_discipline && <p className="text-xs text-gray-400">{r.field_discipline}</p>}
                    {r.publication_link && <a href={r.publication_link} target="_blank" rel="noopener noreferrer" className="text-xs text-sky-600 hover:underline">{RESEARCH_OUTPUTS.find(x => x.value === r.outputs)?.label || 'Link'}</a>}
                  </div>
                </div>
                <div className="flex gap-1">
                  <Button size="sm" variant="ghost" onClick={() => { setEditItem(r); setEditModal('research') }}><Pencil size={12} /></Button>
                  <Button size="sm" variant="ghost" onClick={() => rsDeleteMut.mutate(r.id)}><Trash2 size={12} /></Button>
                </div>
              </div>
            ))}
          </div>
        )}
      </Card>

      {/* Languages */}
      <Card className="p-5">
        <div className="flex justify-between items-start mb-3">
          <h2 className="font-semibold text-brand-slate-700">Languages</h2>
          <Button size="sm" variant="ghost" onClick={() => { setEditItem(null); setEditModal('language') }}><Plus size={14} /></Button>
        </div>
        {(p?.languages ?? []).length === 0 ? (
          <p className="text-sm text-gray-500">Add the languages you speak and any certifications</p>
        ) : (
          <div className="space-y-3">
            {p!.languages.map(lang => (
              <div key={lang.id} className="flex justify-between items-start border-b border-gray-100 pb-3 last:border-0">
                <div className="flex items-start gap-2">
                  <Languages size={14} className="text-gray-400 mt-0.5 flex-shrink-0" />
                  <div>
                    <p className="font-medium text-sm">{lang.language}</p>
                    <p className="text-xs text-gray-500">{PROFICIENCY_LEVELS.find(x => x.value === lang.proficiency_level)?.label || lang.proficiency_level}</p>
                    {lang.certification_type && <p className="text-xs text-gray-400">{lang.certification_type}{lang.certification_score ? `: ${lang.certification_score}` : ''}</p>}
                  </div>
                </div>
                <div className="flex gap-1">
                  <Button size="sm" variant="ghost" onClick={() => { setEditItem(lang); setEditModal('language') }}><Pencil size={12} /></Button>
                  <Button size="sm" variant="ghost" onClick={() => lnDeleteMut.mutate(lang.id)}><Trash2 size={12} /></Button>
                </div>
              </div>
            ))}
          </div>
        )}
      </Card>

      {/* Work & Service */}
      <Card className="p-5">
        <div className="flex justify-between items-start mb-3">
          <h2 className="font-semibold text-stone-800">Work & Service</h2>
          <Button size="sm" variant="ghost" onClick={() => { setEditItem(null); setEditModal('work_experience') }}><Plus size={14} /></Button>
        </div>
        {(p?.work_experiences ?? []).length === 0 ? (
          <p className="text-sm text-stone-500">Add employment, internships, or volunteer experience</p>
        ) : (
          <div className="space-y-3">
            {p!.work_experiences.map(we => (
              <div key={we.id} className="flex justify-between items-start border-b border-stone-100 pb-3 last:border-0">
                <div className="flex items-start gap-2">
                  <Briefcase size={14} className="text-stone-400 mt-0.5 flex-shrink-0" />
                  <div>
                    <p className="font-medium text-sm">{we.role_title} at {we.organization}</p>
                    <p className="text-xs text-stone-500">{WORK_EXPERIENCE_TYPES.find(t => t.value === we.experience_type)?.label}{we.hours_per_week ? ` | ${we.hours_per_week} hrs/wk` : ''}</p>
                    <p className="text-xs text-stone-400">{we.start_date?.slice(0, 7)}{we.is_current ? ' — Present' : we.end_date ? ` — ${we.end_date.slice(0, 7)}` : ''}</p>
                  </div>
                </div>
                <div className="flex gap-1">
                  <Button size="sm" variant="ghost" onClick={() => { setEditItem(we); setEditModal('work_experience') }}><Pencil size={12} /></Button>
                  <Button size="sm" variant="ghost" onClick={() => weDeleteMut.mutate(we.id)}><Trash2 size={12} /></Button>
                </div>
              </div>
            ))}
          </div>
        )}
      </Card>

      {/* Competitions */}
      <Card className="p-5">
        <div className="flex justify-between items-start mb-3">
          <h2 className="font-semibold text-stone-800">Competitions</h2>
          <Button size="sm" variant="ghost" onClick={() => { setEditItem(null); setEditModal('competition') }}><Plus size={14} /></Button>
        </div>
        {(p?.competitions ?? []).length === 0 ? (
          <p className="text-sm text-stone-500">Add hackathons, Olympiads, and competition results</p>
        ) : (
          <div className="space-y-3">
            {p!.competitions.map(cp => (
              <div key={cp.id} className="flex justify-between items-start border-b border-stone-100 pb-3 last:border-0">
                <div className="flex items-start gap-2">
                  <Trophy size={14} className="text-stone-400 mt-0.5 flex-shrink-0" />
                  <div>
                    <p className="font-medium text-sm">{cp.competition_name}</p>
                    <p className="text-xs text-stone-500">{COMPETITION_LEVELS.find(l => l.value === cp.level)?.label}{cp.domain ? ` | ${cp.domain}` : ''}{cp.year ? ` | ${cp.year}` : ''}</p>
                    {cp.result_placement && <p className="text-xs text-amber-600 font-medium">{cp.result_placement}</p>}
                  </div>
                </div>
                <div className="flex gap-1">
                  <Button size="sm" variant="ghost" onClick={() => { setEditItem(cp); setEditModal('competition') }}><Pencil size={12} /></Button>
                  <Button size="sm" variant="ghost" onClick={() => cpDeleteMut.mutate(cp.id)}><Trash2 size={12} /></Button>
                </div>
              </div>
            ))}
          </div>
        )}
      </Card>

      {/* Accommodations */}
      <Card className="p-5">
        <div className="flex justify-between items-start mb-3">
          <h2 className="font-semibold text-brand-slate-700">Accommodations</h2>
          <Button size="sm" variant="ghost" onClick={() => { setEditItem(p?.accommodations); setEditModal('accommodations') }}><Pencil size={14} /></Button>
        </div>
        {p?.accommodations ? (
          <div className="flex items-start gap-2">
            <Accessibility size={14} className="text-gray-400 mt-0.5 flex-shrink-0" />
            <dl className="text-sm space-y-1">
              <div><dt className="text-gray-500 inline">Needed:</dt> <dd className="inline">{p.accommodations.accommodations_needed ? 'Yes' : 'No'}</dd></div>
              {p.accommodations.category && <div><dt className="text-gray-500 inline">Category:</dt> <dd className="inline">{p.accommodations.category}</dd></div>}
              {p.accommodations.documentation_status && <div><dt className="text-gray-500 inline">Documentation:</dt> <dd className="inline capitalize">{p.accommodations.documentation_status.replace(/_/g, ' ')}</dd></div>}
            </dl>
          </div>
        ) : (
          <p className="text-sm text-gray-500">Optional — add if you need accessibility support</p>
        )}
      </Card>

      {/* Scheduling */}
      <Card className="p-5">
        <div className="flex justify-between items-start mb-3">
          <h2 className="font-semibold text-brand-slate-700">Scheduling</h2>
          <Button size="sm" variant="ghost" onClick={() => { setEditItem(p?.scheduling); setEditModal('scheduling') }}><Pencil size={14} /></Button>
        </div>
        {p?.scheduling ? (
          <div className="flex items-start gap-2">
            <CalendarClock size={14} className="text-gray-400 mt-0.5 flex-shrink-0" />
            <dl className="text-sm space-y-1">
              {p.scheduling.timezone && <div><dt className="text-gray-500 inline">Timezone:</dt> <dd className="inline">{p.scheduling.timezone}</dd></div>}
              {p.scheduling.preferred_interview_format && <div><dt className="text-gray-500 inline">Interview:</dt> <dd className="inline capitalize">{p.scheduling.preferred_interview_format.replace(/_/g, ' ')}</dd></div>}
              <div><dt className="text-gray-500 inline">Campus visits:</dt> <dd className="inline">{p.scheduling.campus_visit_interest ? 'Interested' : 'Not interested'}</dd></div>
              {p.scheduling.notes && <div className="text-xs text-gray-400 italic mt-1">{p.scheduling.notes}</div>}
            </dl>
          </div>
        ) : (
          <p className="text-sm text-gray-500">Set your availability for interviews and visits</p>
        )}
      </Card>

      {/* Visa & Immigration */}
      <Card className="p-5">
        <div className="flex justify-between items-start mb-3">
          <h2 className="font-semibold text-brand-slate-700">Visa & Immigration</h2>
          <Button size="sm" variant="ghost" onClick={() => { setEditItem(p?.visa_info); setEditModal('visa_info') }}><Pencil size={14} /></Button>
        </div>
        {p?.visa_info ? (
          <div className="flex items-start gap-2">
            <Plane size={14} className="text-gray-400 mt-0.5 flex-shrink-0" />
            <dl className="text-sm space-y-1">
              {p.visa_info.current_immigration_status && <div><dt className="text-gray-500 inline">Status:</dt> <dd className="inline">{p.visa_info.current_immigration_status}</dd></div>}
              {p.visa_info.target_study_country && <div><dt className="text-gray-500 inline">Target:</dt> <dd className="inline">{p.visa_info.target_study_country}</dd></div>}
              {p.visa_info.sponsorship_source && <div><dt className="text-gray-500 inline">Sponsorship:</dt> <dd className="inline capitalize">{p.visa_info.sponsorship_source}</dd></div>}
              <div><dt className="text-gray-500 inline">Visa required:</dt> <dd className="inline">{p.visa_info.visa_required ? 'Yes' : 'No'}</dd></div>
              {p.visa_info.post_study_work_interest && <div className="text-xs text-sky-600">Interested in post-study work</div>}
            </dl>
          </div>
        ) : (
          <p className="text-sm text-gray-500">Add visa and immigration details if applicable</p>
        )}
      </Card>

      {/* Preferences */}
      <Card className="p-5">
        <div className="flex justify-between items-start mb-3">
          <h2 className="font-semibold text-brand-slate-700">Preferences</h2>
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
          <h2 className="font-semibold text-brand-slate-700">Documents</h2>
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

      {/* Timeline */}
      <Card className="p-5">
        <div className="flex items-center gap-2 mb-4">
          <Clock size={18} className="text-gray-500" />
          <h2 className="font-semibold text-brand-slate-700">Your Journey</h2>
        </div>
        {!timeline || (Array.isArray(timeline) && timeline.length === 0) ? (
          <p className="text-sm text-gray-500">Your milestones will appear here as you build your profile.</p>
        ) : (
          <div className="relative">
            <div className="absolute left-3 top-0 bottom-0 w-px bg-gray-200" />
            <div className="space-y-4">
              {(Array.isArray(timeline) ? timeline : []).map((m: any, i: number) => (
                <div key={i} className="flex items-start gap-4 relative">
                  <div className="w-6 h-6 rounded-full bg-white border-2 border-gray-300 flex items-center justify-center flex-shrink-0 z-10">
                    <div className="w-2 h-2 rounded-full bg-gray-400" />
                  </div>
                  <div className="min-w-0 pb-1">
                    <p className="text-sm font-medium text-gray-700">{m.label}</p>
                    {m.detail && <p className="text-xs text-gray-500">{m.detail}</p>}
                    <p className="text-xs text-gray-400">{formatDate(m.date)}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </Card>

      {/* Analytics */}
      <Card className="p-5">
        <div className="flex items-center gap-2 mb-4">
          <BarChart3 size={18} className="text-gray-500" />
          <h2 className="font-semibold text-brand-slate-700">Analytics</h2>
        </div>
        {analytics ? (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <div className="text-center p-3 bg-gray-50 rounded-xl">
              <p className="text-2xl font-bold text-brand-slate-700">{analytics.profile?.sections_completed ?? 0}</p>
              <p className="text-xs text-gray-500">Sections done</p>
            </div>
            <div className="text-center p-3 bg-gray-50 rounded-xl">
              <p className="text-2xl font-bold text-brand-slate-700">{analytics.profile?.total_items ?? 0}</p>
              <p className="text-xs text-gray-500">Total items</p>
            </div>
            <div className="text-center p-3 bg-gray-50 rounded-xl">
              <p className="text-2xl font-bold text-brand-slate-700">{analytics.matches?.count ?? 0}</p>
              <p className="text-xs text-gray-500">AI Matches</p>
            </div>
            <div className="text-center p-3 bg-gray-50 rounded-xl">
              <p className="text-2xl font-bold text-brand-slate-700">{analytics.applications?.total ?? 0}</p>
              <p className="text-xs text-gray-500">Applications</p>
            </div>
          </div>
        ) : (
          <p className="text-sm text-gray-500">Analytics will appear as you build your profile.</p>
        )}
      </Card>

      {/* Peer Comparison */}
      <Card className="p-5">
        <div className="flex items-center gap-2 mb-4">
          <Users size={18} className="text-gray-500" />
          <h2 className="font-semibold text-brand-slate-700">Peer Comparison</h2>
        </div>
        {peerComparison?.metrics?.length > 0 ? (
          <div className="space-y-3">
            {peerComparison.metrics.map((m: any, i: number) => (
              <div key={i}>
                <div className="flex justify-between text-sm mb-1">
                  <span className="text-gray-700">{m.metric}</span>
                  <span className="text-xs text-gray-500">{m.label} ({m.percentile}th percentile)</span>
                </div>
                <div className="w-full bg-gray-100 rounded-full h-2">
                  <div
                    className="h-2 rounded-full transition-all duration-500"
                    style={{
                      width: `${m.percentile}%`,
                      backgroundColor: m.percentile >= 75 ? '#059669' : m.percentile >= 50 ? '#d97706' : '#6b7280',
                    }}
                  />
                </div>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-sm text-gray-500">Add more profile data to see how you compare with peers.</p>
        )}
      </Card>

      {/* Export */}
      <Card className="p-5">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Download size={18} className="text-gray-500" />
            <div>
              <h2 className="font-semibold text-brand-slate-700">Export Profile</h2>
              <p className="text-xs text-gray-500">Download your full profile as a portable JSON file.</p>
            </div>
          </div>
          <Button size="sm" variant="secondary" onClick={() => exportProfileJson()}>
            <Download size={14} className="mr-1" /> Download JSON
          </Button>
        </div>
      </Card>

      {/* Data Rights */}
      <Card className="p-5">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <Shield size={18} className="text-gray-500" />
            <h2 className="font-semibold text-brand-slate-700">Data Rights</h2>
          </div>
          <Button size="sm" variant="ghost" onClick={() => { setEditItem(p?.data_consent); setEditModal('data_rights') }}><Pencil size={14} /></Button>
        </div>
        {p?.data_consent ? (
          <div className="text-sm space-y-1">
            <p className="text-gray-600">Matching: {p.data_consent.consent_matching ? 'Allowed' : 'Denied'}</p>
            <p className="text-gray-600">Outreach: {p.data_consent.consent_outreach ? 'Allowed' : 'Denied'}</p>
            <p className="text-gray-600">Research: {p.data_consent.consent_research ? 'Allowed' : 'Denied'}</p>
            {p.data_consent.data_retention_preference && <p className="text-gray-400 text-xs">Retention: {p.data_consent.data_retention_preference.replace(/_/g, ' ')}</p>}
            {p.data_consent.deletion_requested && <p className="text-xs text-rose-600 font-medium">Data deletion requested</p>}
          </div>
        ) : (
          <p className="text-sm text-gray-500">Manage how your data is used and stored.</p>
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

      {/* Course Modal */}
      <Modal isOpen={editModal === 'course'} onClose={() => { setEditModal(null); setCourseRecordId(null) }} title={editItem ? 'Edit Course' : 'Add Course'}>
        <CourseForm
          defaultValues={editItem}
          onSubmit={data => editItem && courseRecordId
            ? courseUpdateMut.mutate({ recordId: courseRecordId, courseId: editItem.id, data })
            : courseRecordId ? courseCreateMut.mutate({ recordId: courseRecordId, data }) : undefined
          }
          loading={courseCreateMut.isPending || courseUpdateMut.isPending}
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

      {/* Online Presence Modal */}
      <Modal isOpen={editModal === 'online_presence'} onClose={() => setEditModal(null)} title={editItem ? 'Edit Link' : 'Add Link'}>
        <OnlinePresenceForm
          defaultValues={editItem}
          onSubmit={data => editItem ? opUpdateMut.mutate({ id: editItem.id, data }) : opCreateMut.mutate(data)}
          loading={opCreateMut.isPending || opUpdateMut.isPending}
        />
      </Modal>

      {/* Portfolio Modal */}
      <Modal isOpen={editModal === 'portfolio'} onClose={() => setEditModal(null)} title={editItem ? 'Edit Portfolio Item' : 'Add Portfolio Item'}>
        <PortfolioItemForm
          defaultValues={editItem}
          onSubmit={data => editItem ? pfUpdateMut.mutate({ id: editItem.id, data }) : pfCreateMut.mutate(data)}
          loading={pfCreateMut.isPending || pfUpdateMut.isPending}
        />
      </Modal>

      {/* Research Modal */}
      <Modal isOpen={editModal === 'research'} onClose={() => setEditModal(null)} title={editItem ? 'Edit Research' : 'Add Research'} size="lg">
        <ResearchForm
          defaultValues={editItem}
          onSubmit={data => editItem ? rsUpdateMut.mutate({ id: editItem.id, data }) : rsCreateMut.mutate(data)}
          loading={rsCreateMut.isPending || rsUpdateMut.isPending}
        />
      </Modal>

      {/* Language Modal */}
      <Modal isOpen={editModal === 'language'} onClose={() => setEditModal(null)} title={editItem ? 'Edit Language' : 'Add Language'}>
        <LanguageForm
          defaultValues={editItem}
          onSubmit={data => editItem ? lnUpdateMut.mutate({ id: editItem.id, data }) : lnCreateMut.mutate(data)}
          loading={lnCreateMut.isPending || lnUpdateMut.isPending}
        />
      </Modal>

      {/* Work Experience Modal */}
      <Modal isOpen={editModal === 'work_experience'} onClose={() => setEditModal(null)} title={editItem ? 'Edit Experience' : 'Add Experience'} size="lg">
        <WorkExperienceForm
          defaultValues={editItem}
          onSubmit={data => editItem ? weUpdateMut.mutate({ id: editItem.id, data }) : weCreateMut.mutate(data)}
          loading={weCreateMut.isPending || weUpdateMut.isPending}
        />
      </Modal>

      {/* Competition Modal */}
      <Modal isOpen={editModal === 'competition'} onClose={() => setEditModal(null)} title={editItem ? 'Edit Competition' : 'Add Competition'}>
        <CompetitionForm
          defaultValues={editItem}
          onSubmit={data => editItem ? cpUpdateMut.mutate({ id: editItem.id, data }) : cpCreateMut.mutate(data)}
          loading={cpCreateMut.isPending || cpUpdateMut.isPending}
        />
      </Modal>

      {/* Accommodations Modal */}
      <Modal isOpen={editModal === 'accommodations'} onClose={() => setEditModal(null)} title="Accommodations">
        <AccommodationForm
          defaultValues={editItem}
          onSubmit={data => accomMut.mutate(data)}
          loading={accomMut.isPending}
        />
      </Modal>

      {/* Scheduling Modal */}
      <Modal isOpen={editModal === 'scheduling'} onClose={() => setEditModal(null)} title="Scheduling & Availability">
        <SchedulingForm
          defaultValues={editItem}
          onSubmit={data => schedMut.mutate(data)}
          loading={schedMut.isPending}
        />
      </Modal>

      {/* Visa Info Modal */}
      <Modal isOpen={editModal === 'visa_info'} onClose={() => setEditModal(null)} title="Visa & Immigration" size="lg">
        <VisaInfoForm
          defaultValues={editItem}
          onSubmit={data => visaMut.mutate(data)}
          loading={visaMut.isPending}
        />
      </Modal>

      {/* Data Rights Modal */}
      <Modal isOpen={editModal === 'data_rights'} onClose={() => setEditModal(null)} title="Data Rights & Privacy">
        <DataRightsForm
          defaultValues={editItem}
          onSubmit={data => dataRightsMut.mutate(data)}
          loading={dataRightsMut.isPending}
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

