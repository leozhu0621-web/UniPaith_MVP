import { useState, lazy, Suspense } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { getProfile, updateProfile, createAcademic, updateAcademic, deleteAcademic, createTestScore, updateTestScore, deleteTestScore, createActivity, updateActivity, deleteActivity, createOnlinePresence, updateOnlinePresence, deleteOnlinePresence, createPortfolioItem, updatePortfolioItem, deletePortfolioItem, createResearch, updateResearch, deleteResearch, createLanguage, updateLanguage, deleteLanguage, upsertPreferences, getNextStep, listWorkExperiences, createWorkExperience, updateWorkExperience, deleteWorkExperience, listCompetitions, createCompetition, updateCompetition, deleteCompetition, getAccommodations, upsertAccommodations, getScheduling, upsertScheduling, getPeerComparison, getTimeline, getDataRights, upsertDataRights } from '../../api/students'
import { getOnboarding } from '../../api/students'
import apiClient from '../../api/client'
import { listDocuments } from '../../api/documents'
import Modal from '../../components/ui/Modal'
import Button from '../../components/ui/Button'
import Card from '../../components/ui/Card'
import Badge from '../../components/ui/Badge'
import { SkeletonCard } from '../../components/ui/Skeleton'
import { showToast } from '../../stores/toast-store'
import { formatDate, formatCurrency, formatFileSize } from '../../utils/format'
import { DEGREE_LABELS, ACTIVITY_TYPES, PLATFORM_TYPES, PORTFOLIO_ITEM_TYPES, RESEARCH_ROLES, RESEARCH_OUTPUTS, PROFICIENCY_LEVELS } from '../../utils/constants'
import { Pencil, Trash2, Plus, Upload, Sparkles, CheckCircle2, Circle, ExternalLink, FolderOpen, FlaskConical, Languages, MessageSquare, Briefcase, Trophy, Accessibility, Clock, BarChart3, Download, Milestone, ShieldCheck } from 'lucide-react'
import { BasicInfoForm, AcademicForm, TestScoreForm, ActivityForm, PreferencesForm, OnlinePresenceForm, PortfolioItemForm, ResearchForm, LanguageForm, WorkExperienceForm, CompetitionForm, AccommodationForm, SchedulingForm, DataRightsForm } from './components/ProfileForms'
import type { StudentProfile } from '../../types'

// Lazy-load absorbed pages as tabs
const EssayWorkshopPage = lazy(() => import('./EssayWorkshopPage'))
const ResumeWorkshopPage = lazy(() => import('./ResumeWorkshopPage'))
const RecommendationsPage = lazy(() => import('./RecommendationsPage'))
const FinancialAidPage = lazy(() => import('./FinancialAidPage'))

type ProfileTab = 'overview' | 'essays' | 'recommenders' | 'financial'

const PROFILE_TABS: { key: ProfileTab; label: string }[] = [
  { key: 'overview', label: 'Overview' },
  { key: 'essays', label: 'Essays & Resume' },
  { key: 'recommenders', label: 'Recommenders' },
  { key: 'financial', label: 'Financial' },
]

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
  { key: 'preferences', label: 'Preferences', fields: [] },
  { key: 'documents', label: 'Documents', fields: [] },
]

const SECTION_COUNSELOR_TIPS: Record<string, { tip: string; prefill: string }> = {
  basic_info: { tip: "Your basic info helps programs know where you're coming from.", prefill: 'What basic info should I include to strengthen my profile?' },
  academics: { tip: 'Academic records show your foundation — even one record helps.', prefill: 'What academic records should I add to my profile?' },
  test_scores: { tip: 'Test scores help programs assess your readiness. Add what you have.', prefill: 'Which test scores matter most for my target programs?' },
  activities: { tip: 'Activities show who you are beyond academics — even one meaningful one helps.', prefill: 'What activities should I include to make my profile stand out?' },
  online_presence: { tip: 'LinkedIn, GitHub, or a portfolio site shows programs your professional side.', prefill: 'What online profiles should I link to strengthen my application?' },
  portfolio: { tip: 'Portfolio items demonstrate tangible skills and achievements.', prefill: 'What kind of portfolio items would strengthen my profile?' },
  research: { tip: 'Research experience is valued highly — include papers, projects, or lab work.', prefill: 'How should I present my research experience?' },
  languages: { tip: 'Language skills matter for international programs and career flexibility.', prefill: 'How do programs evaluate language proficiency?' },
  preferences: { tip: 'Your preferences help the AI find programs that truly fit your life.', prefill: 'How should I think about my program preferences?' },
  documents: { tip: 'Upload transcripts, certificates, or recommendation letters.', prefill: 'What documents do I need for my applications?' },
}

export default function ProfilePage() {
  const queryClient = useQueryClient()
  const navigate = useNavigate()
  const [searchParams, setSearchParams] = useSearchParams()
  const activeTab = (searchParams.get('tab') as ProfileTab) || 'overview'
  const [editModal, setEditModal] = useState<string | null>(null)
  const [editItem, setEditItem] = useState<any>(null)

  const { data: profile, isLoading } = useQuery({ queryKey: ['profile'], queryFn: getProfile })
  const { data: onboarding } = useQuery({ queryKey: ['onboarding'], queryFn: getOnboarding })
  const { data: nextStep } = useQuery({ queryKey: ['next-step'], queryFn: getNextStep })
  const { data: documents } = useQuery({ queryKey: ['documents'], queryFn: listDocuments })
  const { data: workExperiences } = useQuery({ queryKey: ['work-experiences'], queryFn: listWorkExperiences })
  const { data: competitions } = useQuery({ queryKey: ['competitions'], queryFn: listCompetitions })
  const { data: accommodations } = useQuery({ queryKey: ['accommodations'], queryFn: getAccommodations, retry: false })
  const { data: scheduling } = useQuery({ queryKey: ['scheduling'], queryFn: getScheduling, retry: false })
  const { data: peerComparison } = useQuery({ queryKey: ['peer-comparison'], queryFn: getPeerComparison, retry: false })
  const { data: timeline } = useQuery({ queryKey: ['timeline'], queryFn: getTimeline, retry: false })
  const { data: dataRights } = useQuery({ queryKey: ['data-rights'], queryFn: getDataRights, retry: false })

  const invalidateAll = () => {
    queryClient.invalidateQueries({ queryKey: ['profile'] })
    queryClient.invalidateQueries({ queryKey: ['onboarding'] })
    queryClient.invalidateQueries({ queryKey: ['next-step'] })
    queryClient.invalidateQueries({ queryKey: ['work-experiences'] })
    queryClient.invalidateQueries({ queryKey: ['competitions'] })
    queryClient.invalidateQueries({ queryKey: ['accommodations'] })
    queryClient.invalidateQueries({ queryKey: ['scheduling'] })
    queryClient.invalidateQueries({ queryKey: ['peer-comparison'] })
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
  const prefsMut = useMutation({ mutationFn: upsertPreferences, onSuccess: () => { invalidateAll(); setEditModal(null); showToast('Preferences updated', 'success') } })

  // New section mutations
  const weCreateMut = useMutation({ mutationFn: createWorkExperience, onSuccess: () => { invalidateAll(); setEditModal(null); showToast('Experience added', 'success') } })
  const weUpdateMut = useMutation({ mutationFn: ({ id, data }: { id: string; data: any }) => updateWorkExperience(id, data), onSuccess: () => { invalidateAll(); setEditModal(null); showToast('Experience updated', 'success') } })
  const weDeleteMut = useMutation({ mutationFn: deleteWorkExperience, onSuccess: () => { invalidateAll(); showToast('Experience removed', 'success') } })
  const compCreateMut = useMutation({ mutationFn: createCompetition, onSuccess: () => { invalidateAll(); setEditModal(null); showToast('Competition added', 'success') } })
  const compUpdateMut = useMutation({ mutationFn: ({ id, data }: { id: string; data: any }) => updateCompetition(id, data), onSuccess: () => { invalidateAll(); setEditModal(null); showToast('Competition updated', 'success') } })
  const compDeleteMut = useMutation({ mutationFn: deleteCompetition, onSuccess: () => { invalidateAll(); showToast('Competition removed', 'success') } })
  const accommMut = useMutation({ mutationFn: upsertAccommodations, onSuccess: () => { invalidateAll(); setEditModal(null); showToast('Accommodations updated', 'success') } })
  const schedMut = useMutation({ mutationFn: upsertScheduling, onSuccess: () => { invalidateAll(); setEditModal(null); showToast('Scheduling updated', 'success') } })
  const dataRightsMut = useMutation({ mutationFn: upsertDataRights, onSuccess: () => { invalidateAll(); setEditModal(null); showToast('Data rights updated', 'success') } })

  if (isLoading) return <div className="p-6 space-y-4">{Array.from({ length: 4 }).map((_, i) => <SkeletonCard key={i} />)}</div>

  const p: StudentProfile | null = profile
  const completionPct = onboarding?.completion_percentage ?? 0
  const stepsCompleted = onboarding?.steps_completed ?? []
  const documentsList: any[] = Array.isArray(documents) ? documents : []
  const workList: any[] = Array.isArray(workExperiences) ? workExperiences : []
  const competitionList: any[] = Array.isArray(competitions) ? competitions : []
  const peerMetrics: any[] = peerComparison?.metrics ?? []
  const timelineItems: any[] = Array.isArray(timeline) ? timeline : []

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
      case 'preferences': return !!p?.preferences
      case 'documents': return documentsList.length > 0
      default: return false
    }
  }

  // Tab content for non-overview tabs
  if (activeTab !== 'overview') {
    return (
      <div className="p-6 max-w-4xl mx-auto">
        <div className="flex items-center gap-2 mb-1">
          <Sparkles size={18} className="text-gold" />
          <h1 className="text-2xl font-semibold text-student-ink">My Story</h1>
        </div>
        <p className="text-sm text-gray-500 mb-4">Everything about you in one place.</p>

        {/* Tab bar */}
        <div className="flex gap-1 mb-6 border-b border-divider">
          {PROFILE_TABS.map(tab => (
            <button
              key={tab.key}
              onClick={() => setSearchParams(tab.key === 'overview' ? {} : { tab: tab.key })}
              className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
                activeTab === tab.key
                  ? 'border-student text-student'
                  : 'border-transparent text-student-text hover:text-student-ink'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        <Suspense fallback={<div className="py-10 text-center text-student-text">Loading...</div>}>
          {activeTab === 'essays' && (
            <div className="-mx-6 -mt-2">
              <EssayWorkshopPage />
              <div className="border-t border-divider mt-8 pt-4">
                <ResumeWorkshopPage />
              </div>
            </div>
          )}
          {activeTab === 'recommenders' && <div className="-mx-6 -mt-2"><RecommendationsPage /></div>}
          {activeTab === 'financial' && <div className="-mx-6 -mt-2"><FinancialAidPage /></div>}
        </Suspense>
      </div>
    )
  }

  return (
    <div className="p-6 max-w-3xl mx-auto space-y-6">
      <div>
        <div className="flex items-center gap-2 mb-1">
          <Sparkles size={18} className="text-gold" />
          <h1 className="text-2xl font-semibold text-student-ink">My Story</h1>
        </div>
        <p className="text-sm text-gray-500 mb-4">Everything about you in one place.</p>

        {/* Tab bar */}
        <div className="flex gap-1 border-b border-divider">
          {PROFILE_TABS.map(tab => (
            <button
              key={tab.key}
              onClick={() => setSearchParams(tab.key === 'overview' ? {} : { tab: tab.key })}
              className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
                activeTab === tab.key
                  ? 'border-student text-student'
                  : 'border-transparent text-student-text hover:text-student-ink'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      {/* Self-Discovery Progress */}
      <Card className="p-5">
        <div className="flex items-center gap-6">
          <StrengthRing value={completionPct} />
          <div className="flex-1 min-w-0">
            <h2 className="font-semibold text-student-ink mb-2">Self-Discovery Progress</h2>
            <div className="grid grid-cols-2 gap-1.5">
              {PROFILE_SECTIONS.map(s => (
                <div key={s.key} className="flex items-center gap-2 text-sm">
                  {sectionDone(s.key) ? (
                    <CheckCircle2 size={14} className="text-green-500 flex-shrink-0" />
                  ) : (
                    <Circle size={14} className="text-gray-300 flex-shrink-0" />
                  )}
                  <span className={sectionDone(s.key) ? 'text-gray-500' : 'text-student-ink'}>{s.label}</span>
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
          <div className="flex items-center gap-2">
            <h2 className="font-semibold text-student-ink">Basic Info</h2>
            <button
              onClick={() => navigate(`/s/chat?prefill=${encodeURIComponent(SECTION_COUNSELOR_TIPS.basic_info.prefill)}`)}
              className="flex items-center gap-1 text-[10px] text-gray-400 hover:text-brand-slate-600 transition-colors"
            >
              <MessageSquare size={10} /> Ask counselor
            </button>
          </div>
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
          <h2 className="font-semibold text-student-ink">Academic Records</h2>
          <Button size="sm" variant="ghost" onClick={() => { setEditItem(null); setEditModal('academic') }}><Plus size={14} /></Button>
        </div>
        {(p?.academic_records ?? []).length === 0 ? (
          <>
            <p className="text-sm text-gray-500">No academic records yet</p>
            <p className="text-xs text-blue-600 mt-1 cursor-pointer hover:underline" onClick={() => navigate(`/s/chat?prefill=${encodeURIComponent(SECTION_COUNSELOR_TIPS.academics.prefill)}`)}>
              <Sparkles size={10} className="inline mr-1" />{SECTION_COUNSELOR_TIPS.academics.tip}
            </p>
          </>
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
          <h2 className="font-semibold text-student-ink">Test Scores</h2>
          <Button size="sm" variant="ghost" onClick={() => { setEditItem(null); setEditModal('test') }}><Plus size={14} /></Button>
        </div>
        {(p?.test_scores ?? []).length === 0 ? (
          <>
            <p className="text-sm text-gray-500">No test scores yet</p>
            <p className="text-xs text-blue-600 mt-1 cursor-pointer hover:underline" onClick={() => navigate(`/s/chat?prefill=${encodeURIComponent(SECTION_COUNSELOR_TIPS.test_scores.prefill)}`)}>
              <Sparkles size={10} className="inline mr-1" />{SECTION_COUNSELOR_TIPS.test_scores.tip}
            </p>
          </>
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
          <h2 className="font-semibold text-student-ink">Activities</h2>
          <Button size="sm" variant="ghost" onClick={() => { setEditItem(null); setEditModal('activity') }}><Plus size={14} /></Button>
        </div>
        {(p?.activities ?? []).length === 0 ? (
          <>
            <p className="text-sm text-gray-500">No activities yet</p>
            <p className="text-xs text-blue-600 mt-1 cursor-pointer hover:underline" onClick={() => navigate(`/s/chat?prefill=${encodeURIComponent(SECTION_COUNSELOR_TIPS.activities.prefill)}`)}>
              <Sparkles size={10} className="inline mr-1" />{SECTION_COUNSELOR_TIPS.activities.tip}
            </p>
          </>
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
          <h2 className="font-semibold text-student-ink">Online Presence</h2>
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
          <h2 className="font-semibold text-student-ink">Portfolio</h2>
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
          <h2 className="font-semibold text-student-ink">Research</h2>
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
          <h2 className="font-semibold text-student-ink">Languages</h2>
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

      {/* Preferences */}
      <Card className="p-5">
        <div className="flex justify-between items-start mb-3">
          <h2 className="font-semibold text-student-ink">Preferences</h2>
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
          <h2 className="font-semibold text-student-ink">Documents</h2>
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

      {/* Work & Service */}
      <Card className="p-5">
        <div className="flex justify-between items-start mb-3">
          <div className="flex items-center gap-2">
            <Briefcase size={16} className="text-student" />
            <h2 className="font-semibold text-student-ink">Work & Service</h2>
          </div>
          <Button size="sm" variant="ghost" onClick={() => { setEditItem(null); setEditModal('work') }}><Plus size={14} /></Button>
        </div>
        {workList.length === 0 ? (
          <p className="text-sm text-gray-500">No work experience, internships, or volunteering yet</p>
        ) : (
          <div className="space-y-3">
            {workList.map((w: any) => (
              <div key={w.id} className="flex justify-between items-start border-b border-gray-100 pb-3 last:border-0">
                <div>
                  <p className="text-sm font-medium">{w.role_title} at {w.organization}</p>
                  <p className="text-xs text-gray-500">{w.experience_type}{w.is_current ? ' · Current' : ''}{w.start_date ? ` · ${formatDate(w.start_date)}` : ''}{w.end_date ? ` – ${formatDate(w.end_date)}` : ''}</p>
                  {w.description && <p className="text-xs text-gray-600 mt-1 line-clamp-2">{w.description}</p>}
                </div>
                <div className="flex gap-1">
                  <Button size="sm" variant="ghost" onClick={() => { setEditItem(w); setEditModal('work') }}><Pencil size={12} /></Button>
                  <Button size="sm" variant="ghost" onClick={() => weDeleteMut.mutate(w.id)}><Trash2 size={12} /></Button>
                </div>
              </div>
            ))}
          </div>
        )}
      </Card>

      {/* Competitions */}
      <Card className="p-5">
        <div className="flex justify-between items-start mb-3">
          <div className="flex items-center gap-2">
            <Trophy size={16} className="text-gold" />
            <h2 className="font-semibold text-student-ink">Competitions</h2>
          </div>
          <Button size="sm" variant="ghost" onClick={() => { setEditItem(null); setEditModal('competition') }}><Plus size={14} /></Button>
        </div>
        {competitionList.length === 0 ? (
          <p className="text-sm text-gray-500">No competitions, hackathons, or olympiads yet</p>
        ) : (
          <div className="space-y-3">
            {competitionList.map((c: any) => (
              <div key={c.id} className="flex justify-between items-start border-b border-gray-100 pb-3 last:border-0">
                <div>
                  <p className="text-sm font-medium">{c.competition_name}</p>
                  <p className="text-xs text-gray-500">
                    {c.level}{c.result_placement ? ` · ${c.result_placement}` : ''}{c.year ? ` · ${c.year}` : ''}
                    {c.domain ? ` · ${c.domain}` : ''}
                  </p>
                  {c.description && <p className="text-xs text-gray-600 mt-1 line-clamp-2">{c.description}</p>}
                </div>
                <div className="flex gap-1">
                  <Button size="sm" variant="ghost" onClick={() => { setEditItem(c); setEditModal('competition') }}><Pencil size={12} /></Button>
                  <Button size="sm" variant="ghost" onClick={() => compDeleteMut.mutate(c.id)}><Trash2 size={12} /></Button>
                </div>
              </div>
            ))}
          </div>
        )}
      </Card>

      {/* Accommodations */}
      <Card className="p-5">
        <div className="flex justify-between items-start mb-3">
          <div className="flex items-center gap-2">
            <Accessibility size={16} className="text-student" />
            <h2 className="font-semibold text-student-ink">Accommodations</h2>
          </div>
          <Button size="sm" variant="ghost" onClick={() => { setEditItem(accommodations || {}); setEditModal('accommodations') }}><Pencil size={14} /></Button>
        </div>
        {!accommodations?.accommodations_needed ? (
          <p className="text-sm text-gray-500">No accommodations specified (optional)</p>
        ) : (
          <dl className="grid grid-cols-2 gap-2 text-sm">
            <div><dt className="text-gray-500">Category</dt><dd>{accommodations.category || '—'}</dd></div>
            <div><dt className="text-gray-500">Documentation</dt><dd>{accommodations.documentation_status || '—'}</dd></div>
            {accommodations.details_text && <div className="col-span-2"><dt className="text-gray-500">Details</dt><dd>{accommodations.details_text}</dd></div>}
          </dl>
        )}
      </Card>

      {/* Scheduling */}
      <Card className="p-5">
        <div className="flex justify-between items-start mb-3">
          <div className="flex items-center gap-2">
            <Clock size={16} className="text-student" />
            <h2 className="font-semibold text-student-ink">Scheduling & Availability</h2>
          </div>
          <Button size="sm" variant="ghost" onClick={() => { setEditItem(scheduling || {}); setEditModal('scheduling') }}><Pencil size={14} /></Button>
        </div>
        {!scheduling ? (
          <p className="text-sm text-gray-500">No scheduling preferences set</p>
        ) : (
          <dl className="grid grid-cols-2 gap-2 text-sm">
            <div><dt className="text-gray-500">Timezone</dt><dd>{scheduling.timezone || '—'}</dd></div>
            <div><dt className="text-gray-500">Preferred Format</dt><dd>{scheduling.preferred_interview_format || '—'}</dd></div>
            <div><dt className="text-gray-500">Campus Visit</dt><dd>{scheduling.campus_visit_interest ? 'Interested' : 'Not interested'}</dd></div>
            {scheduling.notes && <div className="col-span-2"><dt className="text-gray-500">Notes</dt><dd>{scheduling.notes}</dd></div>}
          </dl>
        )}
      </Card>

      {/* Peer Comparison */}
      {peerMetrics.length > 0 && (
        <Card className="p-5">
          <div className="flex items-center gap-2 mb-3">
            <BarChart3 size={16} className="text-student" />
            <h2 className="font-semibold text-student-ink">Peer Comparison</h2>
          </div>
          <div className="grid grid-cols-2 gap-3">
            {peerMetrics.map((m: any) => (
              <div key={m.metric} className="bg-student-mist rounded-lg p-3">
                <p className="text-xs text-student-text mb-0.5">{m.metric}</p>
                <p className="text-lg font-bold text-student-ink">{m.value}</p>
                <p className="text-[10px] text-student-text">{m.label} · {m.percentile}th percentile</p>
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* Export */}
      {/* Timeline */}
      {timelineItems.length > 0 && (
        <Card className="p-5">
          <div className="flex items-center gap-2 mb-3">
            <Milestone size={16} className="text-student" />
            <h2 className="font-semibold text-student-ink">Timeline</h2>
          </div>
          <div className="relative pl-6 space-y-3">
            <div className="absolute left-2 top-1 bottom-1 w-0.5 bg-student-mist" />
            {timelineItems.map((item: any, i: number) => (
              <div key={i} className="relative">
                <div className="absolute -left-4 top-1 w-3 h-3 rounded-full bg-student border-2 border-white" />
                <div>
                  <p className="text-sm font-medium text-student-ink">{item.title || item.event || item.label}</p>
                  <p className="text-xs text-student-text">{item.date ? new Date(item.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' }) : ''}{item.section ? ` · ${item.section}` : ''}</p>
                </div>
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* Data Rights */}
      <Card className="p-5">
        <div className="flex justify-between items-start mb-3">
          <div className="flex items-center gap-2">
            <ShieldCheck size={16} className="text-student" />
            <h2 className="font-semibold text-student-ink">Data Rights & Privacy</h2>
          </div>
          <Button size="sm" variant="ghost" onClick={() => { setEditItem(dataRights || {}); setEditModal('data_rights') }}><Pencil size={14} /></Button>
        </div>
        {!dataRights ? (
          <p className="text-sm text-gray-500">Configure your data sharing and privacy preferences</p>
        ) : (
          <dl className="grid grid-cols-2 gap-2 text-sm">
            <div><dt className="text-gray-500">AI Matching</dt><dd>{dataRights.consent_matching ? 'Allowed' : 'Not allowed'}</dd></div>
            <div><dt className="text-gray-500">School Outreach</dt><dd>{dataRights.consent_outreach ? 'Allowed' : 'Not allowed'}</dd></div>
            {dataRights.data_retention && <div><dt className="text-gray-500">Data Retention</dt><dd className="capitalize">{dataRights.data_retention.replace(/_/g, ' ')}</dd></div>}
            {dataRights.deletion_requested && <div><dt className="text-gray-500">Deletion</dt><dd className="text-red-600">Requested</dd></div>}
          </dl>
        )}
      </Card>

      <Card className="p-5">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Download size={16} className="text-student" />
            <div>
              <h2 className="font-semibold text-student-ink">Export Profile</h2>
              <p className="text-xs text-gray-500">Download your full profile as a portable JSON file</p>
            </div>
          </div>
          <Button size="sm" variant="secondary" onClick={async () => {
            try {
              const { data } = await apiClient.get('/students/me/profile/portable-export')
              const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
              const url = URL.createObjectURL(blob)
              const a = document.createElement('a')
              a.href = url; a.download = 'unipaith-profile.json'; a.click()
              URL.revokeObjectURL(url)
              showToast('Profile exported', 'success')
            } catch { showToast('Export failed', 'error') }
          }}>
            <Download size={14} className="mr-1" /> Export
          </Button>
        </div>
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

      {/* Preferences Modal */}
      <Modal isOpen={editModal === 'preferences'} onClose={() => setEditModal(null)} title="Edit Preferences" size="lg">
        <PreferencesForm
          defaultValues={editItem}
          onSubmit={data => prefsMut.mutate(data)}
          loading={prefsMut.isPending}
        />
      </Modal>

      {/* Work Experience Modal */}
      <Modal isOpen={editModal === 'work'} onClose={() => setEditModal(null)} title={editItem ? 'Edit Work Experience' : 'Add Work Experience'} size="lg">
        <WorkExperienceForm
          defaultValues={editItem}
          onSubmit={data => editItem ? weUpdateMut.mutate({ id: editItem.id, data }) : weCreateMut.mutate(data)}
          loading={weCreateMut.isPending || weUpdateMut.isPending}
        />
      </Modal>

      {/* Competition Modal */}
      <Modal isOpen={editModal === 'competition'} onClose={() => setEditModal(null)} title={editItem ? 'Edit Competition' : 'Add Competition'} size="lg">
        <CompetitionForm
          defaultValues={editItem}
          onSubmit={data => editItem ? compUpdateMut.mutate({ id: editItem.id, data }) : compCreateMut.mutate(data)}
          loading={compCreateMut.isPending || compUpdateMut.isPending}
        />
      </Modal>

      {/* Accommodations Modal */}
      <Modal isOpen={editModal === 'accommodations'} onClose={() => setEditModal(null)} title="Accommodations">
        <AccommodationForm
          defaultValues={editItem}
          onSubmit={data => accommMut.mutate(data)}
          loading={accommMut.isPending}
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

      {/* Data Rights Modal */}
      <Modal isOpen={editModal === 'data_rights'} onClose={() => setEditModal(null)} title="Data Rights & Privacy">
        <DataRightsForm
          defaultValues={editItem}
          onSubmit={data => dataRightsMut.mutate(data)}
          loading={dataRightsMut.isPending}
        />
      </Modal>
    </div>
  )
}

