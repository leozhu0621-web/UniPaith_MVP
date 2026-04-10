import { useState, useEffect, useMemo, useRef } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { listEssays, createEssay, getEssay, updateEssay, finalizeEssay, requestEssayFeedback } from '../../api/essays'
import { listMyApplications } from '../../api/applications'
import { listSaved } from '../../api/saved-lists'
import Card from '../../components/ui/Card'
import Badge from '../../components/ui/Badge'
import Button from '../../components/ui/Button'
import Modal from '../../components/ui/Modal'
import Select from '../../components/ui/Select'
import EmptyState from '../../components/ui/EmptyState'
import { SkeletonCard } from '../../components/ui/Skeleton'
import { formatRelative } from '../../utils/format'
import {
  Pencil, Plus, Lock, MessageSquare, ChevronRight,
  FileText, Sparkles, History, Copy,
} from 'lucide-react'

interface Essay {
  id: string
  program_id: string
  essay_type: string
  content: string
  prompt_text: string | null
  status: string
  created_at: string
  updated_at: string
  versions?: { saved_at: string; word_count: number }[]
  reused_program_ids?: string[]
}

interface ProgramOption {
  id: string
  name: string
  institution: string
}

const ESSAY_TYPES = [
  { value: 'personal_statement', label: 'Personal Statement' },
  { value: 'supplemental', label: 'Supplemental Essay' },
  { value: 'diversity', label: 'Diversity Statement' },
  { value: 'why_us', label: 'Why Us' },
]

const FEEDBACK_TYPES = [
  { value: 'general', label: 'General Review' },
  { value: 'narrative_coherence', label: 'Narrative Coherence' },
  { value: 'competitiveness', label: 'Competitiveness' },
]

function wordCount(text: string): number {
  const trimmed = text.trim()
  return trimmed ? trimmed.split(/\s+/).length : 0
}

function typeLabel(type: string): string {
  return ESSAY_TYPES.find(t => t.value === type)?.label ?? type
}

export default function EssayWorkshopPage() {
  const qc = useQueryClient()

  const { data: essays, isLoading: essaysLoading } = useQuery({
    queryKey: ['essays'],
    queryFn: () => listEssays(),
  })
  const { data: applications } = useQuery({ queryKey: ['my-applications'], queryFn: listMyApplications })
  const { data: saved } = useQuery({ queryKey: ['saved'], queryFn: listSaved })

  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [showNewModal, setShowNewModal] = useState(false)
  const [editorContent, setEditorContent] = useState('')
  const [feedbackType, setFeedbackType] = useState('general')
  const [feedbackResult, setFeedbackResult] = useState<string | null>(null)
  const [showHistory, setShowHistory] = useState(false)
  const saveTimer = useRef<ReturnType<typeof setTimeout> | null>(null)

  useEffect(() => {
    return () => { if (saveTimer.current) clearTimeout(saveTimer.current) }
  }, [])

  const essayList: Essay[] = useMemo(() => (Array.isArray(essays) ? essays : []), [essays])

  const programs: ProgramOption[] = useMemo(() => {
    const map = new Map<string, ProgramOption>()
    const apps: any[] = Array.isArray(applications) ? applications : []
    const svd: any[] = Array.isArray(saved) ? saved : []
    apps.forEach((a: any) => {
      if (a.program && !map.has(a.program_id)) {
        map.set(a.program_id, { id: a.program_id, name: a.program.program_name ?? 'Program', institution: a.program.institution_name ?? '' })
      }
    })
    svd.forEach((s: any) => {
      if (s.program && !map.has(s.program_id)) {
        map.set(s.program_id, { id: s.program_id, name: s.program.program_name ?? 'Program', institution: s.program.institution_name ?? '' })
      }
    })
    return Array.from(map.values())
  }, [applications, saved])

  const programMap = useMemo(() => new Map(programs.map(p => [p.id, p])), [programs])

  const grouped = useMemo(() => {
    const g: Record<string, Essay[]> = {}
    essayList.forEach(e => {
      const key = e.program_id
      ;(g[key] ??= []).push(e)
    })
    return g
  }, [essayList])

  const { data: selectedEssay } = useQuery({
    queryKey: ['essay', selectedId],
    queryFn: () => getEssay(selectedId!),
    enabled: !!selectedId,
  })

  const lastSyncedId = useRef<string | null>(null)
  if (selectedEssay && selectedEssay.id !== lastSyncedId.current) {
    lastSyncedId.current = selectedEssay.id
    setEditorContent(selectedEssay.content ?? '')
    setFeedbackResult(null)
  }

  const createMut = useMutation({
    mutationFn: createEssay,
    onSuccess: (data) => {
      qc.invalidateQueries({ queryKey: ['essays'] })
      setShowNewModal(false)
      setSelectedId(data.id)
    },
  })

  const updateMut = useMutation({
    mutationFn: ({ id, data }: { id: string; data: { content?: string } }) => updateEssay(id, data),
  })

  const finalizeMut = useMutation({
    mutationFn: finalizeEssay,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['essays'] })
      qc.invalidateQueries({ queryKey: ['essay', selectedId] })
    },
  })

  const feedbackMut = useMutation({
    mutationFn: ({ id, type }: { id: string; type: string }) => requestEssayFeedback(id, type),
    onSuccess: (data) => {
      setFeedbackResult(typeof data === 'string' ? data : (data?.feedback ?? data?.text ?? JSON.stringify(data)))
    },
  })

  // Keep latest values in refs so the debounce timer never reads stale closures
  const latestRef = useRef({ selectedId, selectedEssay, editorContent })
  latestRef.current = { selectedId, selectedEssay, editorContent }

  const flushSave = () => {
    if (saveTimer.current) { clearTimeout(saveTimer.current); saveTimer.current = null }
    const { selectedId: id, selectedEssay: essay, editorContent: content } = latestRef.current
    if (!id || !essay || essay.status === 'finalized') return
    if (content === essay.content) return
    updateMut.mutate(
      { id, data: { content } },
      { onSuccess: () => { qc.invalidateQueries({ queryKey: ['essay', id] }); qc.invalidateQueries({ queryKey: ['essays'] }) } },
    )
  }

  const handleEditorChange = (val: string) => {
    setEditorContent(val)
    if (saveTimer.current) clearTimeout(saveTimer.current)
    saveTimer.current = setTimeout(flushSave, 3000)
  }

  const [newProgramId, setNewProgramId] = useState('')
  const [newType, setNewType] = useState('personal_statement')
  const [newPrompt, setNewPrompt] = useState('')

  if (essaysLoading) {
    return (
      <div className="p-6 max-w-6xl mx-auto space-y-4">
        {Array.from({ length: 3 }).map((_, i) => <SkeletonCard key={i} />)}
      </div>
    )
  }

  const isFinalized = selectedEssay?.status === 'finalized'
  const versions: { saved_at: string; word_count: number }[] = selectedEssay?.versions ?? []
  const reusedIds: string[] = selectedEssay?.reused_program_ids ?? []

  return (
    <div className="p-6 max-w-6xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-2">
          <Pencil size={22} className="text-brand-slate-600" />
          <h1 className="text-2xl font-semibold">Essay Workshop</h1>
        </div>
        <Button onClick={() => setShowNewModal(true)} size="sm">
          <Plus size={14} className="mr-1" /> New Essay
        </Button>
      </div>

      {essayList.length === 0 ? (
        <EmptyState
          icon={<FileText size={48} />}
          title="No essays yet"
          description="Start a new essay to begin writing. Select a target program and essay type."
          action={{ label: 'Create Essay', onClick: () => setShowNewModal(true) }}
        />
      ) : (
        <div className="grid grid-cols-12 gap-6">
          <div className="col-span-3 space-y-4 max-h-[calc(100vh-12rem)] overflow-y-auto pr-1">
            {Object.entries(grouped).map(([programId, items]) => {
              const prog = programMap.get(programId)
              return (
                <div key={programId}>
                  <p className="text-xs font-medium text-gray-500 mb-1 truncate">
                    {prog?.name ?? 'Unknown Program'}
                  </p>
                  {items.map(e => (
                    <Card
                      key={e.id}
                      className={`p-3 mb-2 border ${selectedId === e.id ? 'border-brand-slate-400 bg-brand-slate-50' : 'border-transparent hover:border-gray-200'}`}
                      onClick={() => setSelectedId(e.id)}
                    >
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-sm font-medium truncate">{typeLabel(e.essay_type)}</span>
                        <ChevronRight size={14} className="text-gray-400 shrink-0" />
                      </div>
                      {e.prompt_text && (
                        <p className="text-xs text-gray-500 line-clamp-2 mb-1">{e.prompt_text}</p>
                      )}
                      <div className="flex items-center gap-2">
                        <Badge variant={e.status === 'finalized' ? 'success' : 'neutral'} size="sm">
                          {e.status === 'finalized' ? 'Finalized' : 'Draft'}
                        </Badge>
                        <span className="text-[10px] text-gray-400">{wordCount(e.content ?? '')} words</span>
                      </div>
                    </Card>
                  ))}
                </div>
              )
            })}
          </div>

          <div className="col-span-6">
            {!selectedEssay ? (
              <Card className="p-8 text-center text-gray-400">
                <FileText size={32} className="mx-auto mb-2" />
                <p className="text-sm">Select an essay from the sidebar to start editing</p>
              </Card>
            ) : (
              <div className="space-y-4">
                {selectedEssay.prompt_text && (
                  <Card className="p-4 bg-amber-50 border border-amber-200">
                    <p className="text-xs font-medium text-amber-700 mb-1">Prompt</p>
                    <p className="text-sm text-amber-900">{selectedEssay.prompt_text}</p>
                  </Card>
                )}

                <Card className="p-4">
                  <div className="flex items-center justify-between mb-2">
                    <p className="text-sm font-medium">{typeLabel(selectedEssay.essay_type)}</p>
                    <div className="flex items-center gap-2">
                      {isFinalized && (
                        <Badge variant="success" size="sm">
                          <Lock size={10} className="mr-1" /> Finalized
                        </Badge>
                      )}
                      {updateMut.isPending && <span className="text-[10px] text-gray-400">Saving...</span>}
                    </div>
                  </div>
                  <textarea
                    className="w-full min-h-[400px] border border-gray-200 rounded-lg p-3 text-sm focus:outline-none focus:ring-2 focus:ring-brand-slate-600 resize-y"
                    value={editorContent}
                    onChange={e => handleEditorChange(e.target.value)}
                    onBlur={flushSave}
                    disabled={isFinalized}
                    placeholder="Start writing your essay..."
                  />
                  <div className="flex items-center justify-between mt-2">
                    <span className="text-xs text-gray-400">{wordCount(editorContent)} words</span>
                    <div className="flex gap-2">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => setShowHistory(!showHistory)}
                      >
                        <History size={14} className="mr-1" /> History
                      </Button>
                      {!isFinalized && (
                        <Button
                          variant="secondary"
                          size="sm"
                          loading={finalizeMut.isPending}
                          onClick={() => { if (selectedId) finalizeMut.mutate(selectedId) }}
                        >
                          <Lock size={14} className="mr-1" /> Finalize
                        </Button>
                      )}
                    </div>
                  </div>
                </Card>

                {reusedIds.length > 0 && (
                  <div className="flex items-center gap-2">
                    <Copy size={14} className="text-blue-500" />
                    <span className="text-xs text-blue-600">
                      Reused across {reusedIds.length} program{reusedIds.length > 1 ? 's' : ''}
                    </span>
                  </div>
                )}

                {showHistory && (
                  <Card className="p-4">
                    <p className="text-sm font-medium mb-2">Version History</p>
                    {versions.length === 0 ? (
                      <p className="text-xs text-gray-400">No version history available</p>
                    ) : (
                      <ul className="space-y-1">
                        {versions.map((v, i) => (
                          <li key={i} className="flex items-center justify-between text-xs text-gray-500 py-1 border-b border-gray-100 last:border-0">
                            <span>{formatRelative(v.saved_at)}</span>
                            <span>{v.word_count} words</span>
                          </li>
                        ))}
                      </ul>
                    )}
                  </Card>
                )}
              </div>
            )}
          </div>

          <div className="col-span-3">
            {selectedEssay && (
              <Card className="p-4 space-y-4">
                <div className="flex items-center gap-2">
                  <Sparkles size={16} className="text-purple-500" />
                  <p className="text-sm font-medium">AI Feedback</p>
                </div>

                <Select
                  options={FEEDBACK_TYPES}
                  value={feedbackType}
                  onChange={e => setFeedbackType(e.target.value)}
                  label="Feedback Type"
                />

                <Button
                  size="sm"
                  className="w-full"
                  loading={feedbackMut.isPending}
                  onClick={() => { if (selectedId) feedbackMut.mutate({ id: selectedId, type: feedbackType }) }}
                >
                  <MessageSquare size={14} className="mr-1" /> Get Feedback
                </Button>

                {feedbackResult && (
                  <div className="bg-purple-50 border border-purple-200 rounded-lg p-3 text-sm text-purple-900 whitespace-pre-wrap max-h-80 overflow-y-auto">
                    {feedbackResult}
                  </div>
                )}
              </Card>
            )}
          </div>
        </div>
      )}

      <Modal isOpen={showNewModal} onClose={() => setShowNewModal(false)} title="New Essay">
        <div className="space-y-4">
          <Select
            label="Target Program"
            options={programs.map(p => ({ value: p.id, label: `${p.name} - ${p.institution}` }))}
            placeholder="Select a program"
            value={newProgramId}
            onChange={e => setNewProgramId(e.target.value)}
          />
          <Select
            label="Essay Type"
            options={ESSAY_TYPES}
            value={newType}
            onChange={e => setNewType(e.target.value)}
          />
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Prompt (optional)</label>
            <textarea
              className="w-full border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-slate-600 resize-y min-h-[80px]"
              value={newPrompt}
              onChange={e => setNewPrompt(e.target.value)}
              placeholder="Paste the essay prompt here..."
            />
          </div>
          <div className="flex justify-end gap-2 pt-2">
            <Button variant="secondary" onClick={() => setShowNewModal(false)}>Cancel</Button>
            <Button
              loading={createMut.isPending}
              disabled={!newProgramId}
              onClick={() => {
                createMut.mutate({
                  program_id: newProgramId,
                  essay_type: newType,
                  content: '',
                  prompt_text: newPrompt || undefined,
                })
              }}
            >
              Create
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  )
}
