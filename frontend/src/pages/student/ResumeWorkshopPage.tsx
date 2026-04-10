import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  generateResume,
  listResumes,
  updateResume,
  finalizeResume,
  requestResumeFeedback,
} from '../../api/resumes'
import Card from '../../components/ui/Card'
import Button from '../../components/ui/Button'
import Badge from '../../components/ui/Badge'
import EmptyState from '../../components/ui/EmptyState'
import { SkeletonCard } from '../../components/ui/Skeleton'
import ProgressBar from '../../components/ui/ProgressBar'
import Textarea from '../../components/ui/Textarea'
import { showToast } from '../../stores/toast-store'
import { formatDate } from '../../utils/format'
import {
  Sparkles,
  FileText,
  Save,
  Lock,
  MessageSquare,
  ChevronLeft,
  Plus,
  Clock,
  Target,
  Eye,
  BarChart3,
  Lightbulb,
} from 'lucide-react'

interface ResumeItem {
  id: string
  format_type: string
  target_program_id?: string | null
  target_program_name?: string | null
  status: string
  content: ResumeContent | null
  versions?: ResumeVersion[]
  created_at: string
  updated_at?: string
}

interface ResumeContent {
  summary?: string
  education?: string
  experience?: string
  skills?: string
  projects?: string
  awards?: string
  extracurriculars?: string
  [key: string]: string | undefined
}

interface ResumeVersion {
  version: number
  created_at: string
  summary?: string
}

interface FeedbackResult {
  clarity_score?: number
  impact_score?: number
  gap_analysis?: string[]
  competitiveness_tips?: string[]
  summary?: string
}

const STATUS_CONFIG: Record<string, { label: string; variant: 'success' | 'neutral' }> = {
  draft: { label: 'Draft', variant: 'neutral' },
  finalized: { label: 'Finalized', variant: 'success' },
}

const SECTION_LABELS: Record<string, { label: string; placeholder: string }> = {
  summary: { label: 'Professional Summary', placeholder: 'A brief overview of your background and goals...' },
  education: { label: 'Education', placeholder: 'Degree, institution, GPA, relevant coursework...' },
  experience: { label: 'Experience', placeholder: 'Internships, jobs, research positions...' },
  skills: { label: 'Skills', placeholder: 'Technical and soft skills...' },
  projects: { label: 'Projects', placeholder: 'Academic or personal projects...' },
  awards: { label: 'Awards & Honors', placeholder: 'Scholarships, competitions, recognitions...' },
  extracurriculars: { label: 'Extracurricular Activities', placeholder: 'Clubs, volunteering, leadership...' },
}

const SECTION_ORDER = ['summary', 'education', 'experience', 'skills', 'projects', 'awards', 'extracurriculars']

const FEEDBACK_TYPES = [
  { id: 'general', label: 'General', icon: Eye },
  { id: 'clarity', label: 'Clarity', icon: MessageSquare },
  { id: 'impact', label: 'Impact', icon: BarChart3 },
  { id: 'evidence', label: 'Evidence', icon: Target },
]

const FORMAT_OPTIONS = [
  { value: 'general', label: 'General Resume' },
  { value: 'academic', label: 'Academic CV' },
  { value: 'program-specific', label: 'Program-Specific' },
]

const FORMAT_LABEL: Record<string, string> = Object.fromEntries(
  FORMAT_OPTIONS.map(o => [o.value, o.label]),
)

function formatLabel(type: string) {
  return FORMAT_LABEL[type] ?? type
}

export default function ResumeWorkshopPage() {
  const queryClient = useQueryClient()
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [formatType, setFormatType] = useState('general')
  const [feedbackType, setFeedbackType] = useState('general')
  const [feedback, setFeedback] = useState<FeedbackResult | null>(null)
  const [editContent, setEditContent] = useState<ResumeContent | null>(null)
  const [dirty, setDirty] = useState(false)

  const { data: resumes, isLoading, isError, error } = useQuery({
    queryKey: ['resumes'],
    queryFn: () => listResumes(),
  })

  const items: ResumeItem[] = Array.isArray(resumes)
    ? resumes
    : Array.isArray((resumes as any)?.items)
      ? (resumes as any).items
      : []

  const selected = items.find(r => r.id === selectedId) ?? null

  const generateMut = useMutation({
    mutationFn: generateResume,
    onSuccess: (data: any) => {
      queryClient.invalidateQueries({ queryKey: ['resumes'] })
      showToast('Resume generated', 'success')
      if (data?.id) {
        setSelectedId(data.id)
        setEditContent(data.content ?? null)
        setDirty(false)
      }
    },
    onError: () => showToast('Failed to generate resume', 'error'),
  })

  const saveMut = useMutation({
    mutationFn: ({ id, content }: { id: string; content: ResumeContent }) =>
      updateResume(id, content),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['resumes'] })
      setDirty(false)
      showToast('Resume saved', 'success')
    },
    onError: () => showToast('Failed to save', 'error'),
  })

  const finalizeMut = useMutation({
    mutationFn: finalizeResume,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['resumes'] })
      showToast('Resume finalized', 'success')
    },
    onError: () => showToast('Failed to finalize', 'error'),
  })

  const feedbackMut = useMutation({
    mutationFn: ({ id, type }: { id: string; type: string }) =>
      requestResumeFeedback(id, type),
    onSuccess: (data: any) => {
      setFeedback(data)
      showToast('Feedback received', 'success')
    },
    onError: () => showToast('Failed to get feedback', 'error'),
  })

  function handleGenerate() {
    generateMut.mutate({ format_type: formatType })
  }

  function handleSelect(resume: ResumeItem) {
    setSelectedId(resume.id)
    setEditContent(resume.content ? { ...resume.content } : null)
    setDirty(false)
    setFeedback(null)
  }

  function handleSectionChange(key: string, value: string) {
    setEditContent(prev => ({ ...prev, [key]: value }))
    setDirty(true)
  }

  function handleSave() {
    if (!selectedId || !editContent) return
    saveMut.mutate({ id: selectedId, content: editContent })
  }

  function handleFinalize() {
    if (!selectedId) return
    finalizeMut.mutate(selectedId)
  }

  function handleGetFeedback() {
    if (!selectedId) return
    feedbackMut.mutate({ id: selectedId, type: feedbackType })
  }

  if (isLoading) {
    return (
      <div className="p-6 max-w-6xl mx-auto space-y-4">
        <div className="flex items-center gap-2 mb-2">
          <Sparkles size={22} className="text-amber-500" />
          <h1 className="text-2xl font-semibold">Resume Workshop</h1>
        </div>
        {Array.from({ length: 3 }).map((_, i) => <SkeletonCard key={i} />)}
      </div>
    )
  }

  if (isError) {
    const message = error instanceof Error ? error.message : 'Failed to load resumes.'
    return (
      <div className="p-6 max-w-6xl mx-auto">
        <Card className="p-5">
          <h1 className="text-xl font-semibold mb-2">Resume Workshop</h1>
          <p className="text-sm text-red-600">{message}</p>
          <Button size="sm" className="mt-4" onClick={() => queryClient.invalidateQueries({ queryKey: ['resumes'] })}>
            Retry
          </Button>
        </Card>
      </div>
    )
  }

  if (selected) {
    const isFinalized = selected.status === 'finalized'
    const versions: ResumeVersion[] = selected.versions ?? []

    return (
      <div className="p-6 max-w-6xl mx-auto">
        {/* Back + title */}
        <button
          onClick={() => { setSelectedId(null); setFeedback(null) }}
          className="flex items-center gap-1 text-sm text-gray-500 hover:text-gray-700 mb-4"
        >
          <ChevronLeft size={16} /> Back to resumes
        </button>

        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-2xl font-semibold flex items-center gap-2">
              <Sparkles size={22} className="text-amber-500" />
              {formatLabel(selected.format_type)}
            </h1>
            <div className="flex items-center gap-3 mt-1">
              <Badge variant={STATUS_CONFIG[selected.status]?.variant ?? 'neutral'} size="sm">
                {STATUS_CONFIG[selected.status]?.label ?? selected.status}
              </Badge>
              <span className="text-xs text-gray-400">Created {formatDate(selected.created_at)}</span>
              {selected.target_program_name && (
                <span className="text-xs text-gray-400">Target: {selected.target_program_name}</span>
              )}
            </div>
          </div>
          <div className="flex gap-2">
            {!isFinalized && (
              <>
                <Button size="sm" variant="secondary" onClick={handleSave} loading={saveMut.isPending} disabled={!dirty}>
                  <Save size={14} className="mr-1" /> Save
                </Button>
                <Button size="sm" onClick={handleFinalize} loading={finalizeMut.isPending}>
                  <Lock size={14} className="mr-1" /> Finalize
                </Button>
              </>
            )}
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Editor (2 cols) */}
          <div className="lg:col-span-2 space-y-4">
            {SECTION_ORDER.map(key => {
              const meta = SECTION_LABELS[key]
              const value = editContent?.[key] ?? ''
              return (
                <Card key={key} className="p-4">
                  <label className="block text-sm font-medium text-gray-700 mb-1">{meta.label}</label>
                  {isFinalized ? (
                    <p className="text-sm text-gray-600 whitespace-pre-wrap">{value || <span className="italic text-gray-400">Not provided</span>}</p>
                  ) : (
                    <Textarea
                      value={value}
                      onChange={e => handleSectionChange(key, e.target.value)}
                      placeholder={meta.placeholder}
                      className="min-h-[100px]"
                    />
                  )}
                </Card>
              )
            })}
          </div>

          {/* Right sidebar: feedback + versions */}
          <div className="space-y-4">
            {/* AI Feedback */}
            <Card className="p-4">
              <h3 className="text-sm font-semibold mb-3 flex items-center gap-1.5">
                <Sparkles size={14} className="text-amber-500" /> AI Feedback
              </h3>

              {/* Feedback type buttons */}
              <div className="flex flex-wrap gap-1.5 mb-3">
                {FEEDBACK_TYPES.map(ft => {
                  const Icon = ft.icon
                  return (
                    <button
                      key={ft.id}
                      onClick={() => setFeedbackType(ft.id)}
                      className={`flex items-center gap-1 px-2 py-1 rounded text-xs font-medium transition-colors ${
                        feedbackType === ft.id
                          ? 'bg-stone-600 text-white'
                          : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                      }`}
                    >
                      <Icon size={12} /> {ft.label}
                    </button>
                  )
                })}
              </div>

              <Button size="sm" className="w-full" onClick={handleGetFeedback} loading={feedbackMut.isPending}>
                <MessageSquare size={14} className="mr-1" /> Get AI Feedback
              </Button>

              {/* Feedback results */}
              {feedback && (
                <div className="mt-4 space-y-3">
                  {feedback.summary && (
                    <p className="text-sm text-gray-600">{feedback.summary}</p>
                  )}

                  {feedback.clarity_score != null && (
                    <ProgressBar value={feedback.clarity_score} label="Clarity" />
                  )}

                  {feedback.impact_score != null && (
                    <ProgressBar value={feedback.impact_score} label="Impact" />
                  )}

                  {feedback.gap_analysis && feedback.gap_analysis.length > 0 && (
                    <div>
                      <p className="text-xs font-medium text-gray-700 mb-1 flex items-center gap-1">
                        <Target size={12} /> Gap Analysis
                      </p>
                      <ul className="space-y-1">
                        {feedback.gap_analysis.map((gap, i) => (
                          <li key={i} className="text-xs text-gray-600 flex items-start gap-1.5">
                            <span className="text-amber-500 mt-0.5">-</span> {gap}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {feedback.competitiveness_tips && feedback.competitiveness_tips.length > 0 && (
                    <div>
                      <p className="text-xs font-medium text-gray-700 mb-1 flex items-center gap-1">
                        <Lightbulb size={12} /> Competitiveness Tips
                      </p>
                      <ul className="space-y-1">
                        {feedback.competitiveness_tips.map((tip, i) => (
                          <li key={i} className="text-xs text-gray-600 flex items-start gap-1.5">
                            <span className="text-emerald-500 mt-0.5">-</span> {tip}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              )}
            </Card>

            {/* Version History */}
            {versions.length > 0 && (
              <Card className="p-4">
                <h3 className="text-sm font-semibold mb-3 flex items-center gap-1.5">
                  <Clock size={14} /> Version History
                </h3>
                <ul className="space-y-2">
                  {versions.map(v => (
                    <li key={v.version} className="flex items-center gap-2 text-xs text-gray-600">
                      <span className="w-5 h-5 rounded-full bg-gray-100 flex items-center justify-center font-medium text-gray-500">
                        {v.version}
                      </span>
                      <span>{formatDate(v.created_at)}</span>
                      {v.summary && <span className="text-gray-400 truncate">- {v.summary}</span>}
                    </li>
                  ))}
                </ul>
              </Card>
            )}
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-semibold flex items-center gap-2">
            <Sparkles size={22} className="text-amber-500" /> Resume Workshop
          </h1>
          <p className="text-sm text-gray-500 mt-1">Create and refine your resumes with AI feedback.</p>
        </div>
      </div>

      {/* Generate controls */}
      <Card className="p-4 mb-6">
        <h3 className="text-sm font-semibold mb-3 flex items-center gap-1.5">
          <Plus size={14} /> Generate New Resume
        </h3>
        <div className="flex items-end gap-3">
          <div className="flex-1">
            <label className="block text-sm font-medium text-gray-700 mb-1">Format</label>
            <select
              value={formatType}
              onChange={e => setFormatType(e.target.value)}
              className="w-full border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-slate-600 focus:border-transparent bg-white"
            >
              {FORMAT_OPTIONS.map(o => (
                <option key={o.value} value={o.value}>{o.label}</option>
              ))}
            </select>
          </div>
          <Button onClick={handleGenerate} loading={generateMut.isPending}>
            <Sparkles size={14} className="mr-1" /> Generate with AI
          </Button>
        </div>
      </Card>

      {/* Resume list */}
      {items.length === 0 ? (
        <EmptyState
          icon={<FileText size={48} />}
          title="No resumes yet"
          description="Generate your first resume with AI to get started."
          action={{ label: 'Generate Resume', onClick: handleGenerate }}
        />
      ) : (
        <div className="space-y-3">
          {items.map(resume => {
            const cfg = STATUS_CONFIG[resume.status] ?? STATUS_CONFIG.draft
            return (
              <Card key={resume.id} className="p-4" onClick={() => handleSelect(resume)}>
                <div className="flex items-start justify-between">
                  <div className="flex items-start gap-3">
                    <div className="w-10 h-10 rounded-full bg-gray-100 flex items-center justify-center flex-shrink-0">
                      <FileText size={18} className="text-gray-500" />
                    </div>
                    <div>
                      <p className="font-semibold text-sm">
                        {formatLabel(resume.format_type)}
                      </p>
                      <div className="flex items-center gap-2 mt-1">
                        <Badge variant={cfg.variant} size="sm">{cfg.label}</Badge>
                        <span className="text-xs text-gray-400">{formatDate(resume.created_at)}</span>
                      </div>
                      {resume.target_program_name && (
                        <p className="text-xs text-gray-400 mt-0.5">Target: {resume.target_program_name}</p>
                      )}
                    </div>
                  </div>
                  <Button size="sm" variant="ghost">
                    Open
                  </Button>
                </div>
              </Card>
            )
          })}
        </div>
      )}
    </div>
  )
}
