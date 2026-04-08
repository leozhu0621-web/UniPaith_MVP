import { useState, useCallback } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { getMyApplication, submitApplication, getChecklist, generateChecklist, respondToOffer, getReadiness } from '../../api/applications'
import { listEssays, createEssay, updateEssay, requestEssayFeedback } from '../../api/essays'
import { listResumes, generateResume } from '../../api/resumes'
import { requestUpload, uploadToS3, confirmUpload, listDocuments } from '../../api/documents'
import Button from '../../components/ui/Button'
import Card from '../../components/ui/Card'
import Badge from '../../components/ui/Badge'
import Tabs from '../../components/ui/Tabs'
import Modal from '../../components/ui/Modal'
import Textarea from '../../components/ui/Textarea'
import Select from '../../components/ui/Select'
import ProgressBar from '../../components/ui/ProgressBar'
import Skeleton from '../../components/ui/Skeleton'
import { showToast } from '../../stores/toast-store'
import { STATUS_COLORS } from '../../utils/constants'
import { ArrowLeft, Check, Circle, Upload, Sparkles, AlertCircle, FileCheck } from 'lucide-react'
import type { Application, Essay, Resume } from '../../types'

const STATUS_STEPS = ['draft', 'submitted', 'under_review', 'interview', 'decision_made']
const STATUS_STEP_LABELS: Record<string, string> = {
  draft: 'Drafting',
  submitted: 'Submitted',
  under_review: 'Under review',
  interview: 'Interview stage',
  decision_made: 'Decision',
}

export default function ApplicationDetailPage() {
  const { appId } = useParams<{ appId: string }>()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [tab, setTab] = useState('documents')
  const [showEssayModal, setShowEssayModal] = useState(false)
  const [editingEssay, setEditingEssay] = useState<Essay | null>(null)
  const [essayContent, setEssayContent] = useState('')
  const [essayPrompt, setEssayPrompt] = useState('')
  const [essayType, setEssayType] = useState('personal_statement')
  const [offerResponse, setOfferResponse] = useState('')
  const [declineReason, setDeclineReason] = useState('')

  // Upload state
  const [uploading, setUploading] = useState(false)
  const [uploadProgress, setUploadProgress] = useState(0)
  const [dragOver, setDragOver] = useState(false)

  // Readiness state
  const [readiness, setReadiness] = useState<any>(null)
  const [showReadiness, setShowReadiness] = useState(false)

  // Essay feedback state
  const [feedbackLoading, setFeedbackLoading] = useState<string | null>(null)
  const [feedbackResults, setFeedbackResults] = useState<Record<string, any>>({})

  const { data: app, isLoading } = useQuery({ queryKey: ['application', appId], queryFn: () => getMyApplication(appId!) })
  const { data: checklist } = useQuery({ queryKey: ['checklist', appId], queryFn: () => getChecklist(appId!).catch(() => generateChecklist(appId!)) })
  const { data: essays } = useQuery({ queryKey: ['essays', app?.program_id], queryFn: () => listEssays(app?.program_id), enabled: !!app?.program_id && (tab === 'essays' || tab === 'documents') })
  const { data: resumes } = useQuery({ queryKey: ['resumes', app?.program_id], queryFn: () => listResumes(app?.program_id), enabled: !!app?.program_id && tab === 'resume' })
  const { data: documents } = useQuery({ queryKey: ['documents'], queryFn: listDocuments, enabled: tab === 'documents' })

  const submitMut = useMutation({ mutationFn: () => submitApplication(appId!), onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['application', appId] }); showToast('Application submitted!', 'success') } })
  const essayMut = useMutation({ mutationFn: (data: any) => createEssay(data), onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['essays'] }); setShowEssayModal(false); setEssayContent(''); setEssayPrompt(''); showToast('Essay created', 'success') } })
  const essayUpdateMut = useMutation({ mutationFn: ({ id, data }: { id: string; data: any }) => updateEssay(id, data), onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['essays'] }); setEditingEssay(null); showToast('Essay updated', 'success') } })
  const resumeGenMut = useMutation({ mutationFn: () => generateResume({ format_type: 'standard', target_program_id: app?.program_id }), onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['resumes'] }); showToast('Resume generated', 'success') } })
  const offerMut = useMutation({ mutationFn: () => respondToOffer(appId!, offerResponse, declineReason || undefined), onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['application', appId] }); showToast('Response submitted', 'success') } })

  // File upload handler
  const handleFileUpload = useCallback(async (files: FileList | File[]) => {
    const fileArray = Array.from(files)
    if (fileArray.length === 0) return

    setUploading(true)
    setUploadProgress(0)

    try {
      for (const file of fileArray) {
        const docType = file.name.toLowerCase().includes('transcript') ? 'transcript'
          : file.name.toLowerCase().includes('resume') || file.name.toLowerCase().includes('cv') ? 'resume'
          : file.name.toLowerCase().includes('essay') ? 'essay'
          : 'certificate'

        const { upload_url, document_id } = await requestUpload({
          document_type: docType,
          file_name: file.name,
          content_type: file.type || 'application/octet-stream',
          file_size_bytes: file.size,
        })

        await uploadToS3(upload_url, file, (pct) => setUploadProgress(pct))
        await confirmUpload(document_id)
      }

      queryClient.invalidateQueries({ queryKey: ['documents'] })
      queryClient.invalidateQueries({ queryKey: ['checklist', appId] })
      showToast(`${fileArray.length} file(s) uploaded`, 'success')
    } catch {
      showToast('Upload failed', 'error')
    } finally {
      setUploading(false)
      setUploadProgress(0)
    }
  }, [appId, queryClient])

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setDragOver(false)
    if (e.dataTransfer.files.length > 0) {
      handleFileUpload(e.dataTransfer.files)
    }
  }, [handleFileUpload])

  // Readiness check
  const checkReadiness = async () => {
    try {
      const result = await getReadiness(appId!)
      setReadiness(result)
      setShowReadiness(true)
    } catch {
      showToast('Could not check readiness', 'error')
    }
  }

  // Essay feedback
  const handleEssayFeedback = async (essayId: string) => {
    setFeedbackLoading(essayId)
    try {
      const result = await requestEssayFeedback(essayId)
      setFeedbackResults(prev => ({ ...prev, [essayId]: result }))
    } catch {
      showToast('Could not get feedback', 'error')
    } finally {
      setFeedbackLoading(null)
    }
  }

  // Word count helper
  const wordCount = (text: string) => text.trim() ? text.trim().split(/\s+/).length : 0

  if (isLoading) return <div className="p-6"><Skeleton className="h-64" /></div>

  const application: Application = app
  const currentStepIdx = STATUS_STEPS.indexOf(application.status)
  const checklistItems = checklist?.items ?? []
  const completionPct = checklist?.completion_percentage ?? 0
  const documentsList: any[] = Array.isArray(documents) ? documents : []
  const essaysList: Essay[] = Array.isArray(essays) ? essays : []
  const resumesList: Resume[] = Array.isArray(resumes) ? resumes : []

  const tabs = [
    { id: 'documents', label: 'Documents' },
    { id: 'essays', label: 'Essays' },
    { id: 'resume', label: 'Resume' },
    ...(application.decision === 'admitted' ? [{ id: 'offer', label: 'Offer' }] : []),
  ]

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <button onClick={() => navigate('/s/applications')} className="flex items-center gap-1 text-sm text-gray-500 hover:text-brand-slate-600 mb-4">
        <ArrowLeft size={16} /> My Applications
      </button>

      <h1 className="text-xl font-bold mb-1">{application.program?.program_name || 'Application'}</h1>
      <p className="text-sm text-gray-500">Take one section at a time. You can check readiness anytime before submitting.</p>

      {/* Status timeline */}
      <div className="my-4">
        <div className="flex items-center gap-1">
          {STATUS_STEPS.map((step, i) => (
            <div key={step} className="flex items-center">
              <div className={`w-6 h-6 rounded-full flex items-center justify-center text-xs ${i <= currentStepIdx ? 'bg-brand-slate-700 text-white' : 'bg-gray-200 text-gray-400'}`}>
                {i < currentStepIdx ? <Check size={12} /> : <Circle size={12} />}
              </div>
              {i < STATUS_STEPS.length - 1 && <div className={`w-12 h-0.5 ${i < currentStepIdx ? 'bg-brand-slate-700' : 'bg-gray-200'}`} />}
            </div>
          ))}
        </div>
        <div className="flex items-center gap-2 mt-2">
          {STATUS_STEPS.map(step => (
            <span
              key={step}
              className={`text-[11px] px-2 py-0.5 rounded-full ${
                step === application.status ? 'bg-brand-slate-700 text-white' : 'bg-gray-100 text-gray-500'
              }`}
            >
              {STATUS_STEP_LABELS[step]}
            </span>
          ))}
        </div>
      </div>

      <div className="flex gap-6">
        {/* Sidebar: Checklist */}
        <div className="w-56 flex-shrink-0">
          <Card className="p-4">
            <h3 className="font-medium text-sm mb-3">Checklist</h3>
            <div className="space-y-2 mb-3">
              {checklistItems.map((item: any, i: number) => (
                <div key={i} className="flex items-center gap-2 text-sm">
                  <div className={`w-4 h-4 rounded border flex items-center justify-center ${item.status === 'completed' ? 'bg-green-500 border-green-500 text-white' : 'border-gray-300'}`}>
                    {item.status === 'completed' && <Check size={10} />}
                  </div>
                  <span className={item.status === 'completed' ? 'text-gray-500 line-through' : ''}>{item.name}</span>
                </div>
              ))}
            </div>
            <ProgressBar value={completionPct} label="Completion" />

            {/* Readiness Check Button */}
            <Button
              className="w-full mt-3"
              size="sm"
              variant="secondary"
              onClick={checkReadiness}
            >
              <FileCheck size={14} className="mr-1" /> Check Readiness
            </Button>

            <Button
              className="w-full mt-2"
              disabled={application.status !== 'draft'}
              onClick={() => submitMut.mutate()}
              loading={submitMut.isPending}
              size="sm"
            >
              Submit Application
            </Button>
            {application.status === 'draft' && (
              <p className="text-xs text-gray-500 mt-2">
                You can submit when you feel ready. The readiness check will show any missing items clearly.
              </p>
            )}
          </Card>
        </div>

        {/* Main content */}
        <div className="flex-1 min-w-0">
          <Tabs tabs={tabs} activeTab={tab} onChange={setTab} />
          <div className="mt-4">
            {tab === 'documents' && (
              <div className="space-y-4">
                {/* Drag & Drop Upload Zone */}
                <div
                  onDragOver={e => { e.preventDefault(); setDragOver(true) }}
                  onDragLeave={() => setDragOver(false)}
                  onDrop={handleDrop}
                  className={`border-2 border-dashed rounded-lg p-6 text-center transition-colors ${
                    dragOver ? 'border-brand-slate-700 bg-gray-50' : 'border-gray-300 hover:border-gray-400'
                  }`}
                >
                  <Upload size={24} className="mx-auto text-gray-400 mb-2" />
                  <p className="text-sm text-gray-600 mb-1">Drag & drop files here, or</p>
                  <label className="inline-block">
                    <input
                      type="file"
                      multiple
                      className="hidden"
                      onChange={e => e.target.files && handleFileUpload(e.target.files)}
                    />
                    <span className="text-sm font-medium text-brand-slate-700 underline cursor-pointer">browse files</span>
                  </label>
                  <p className="text-xs text-gray-400 mt-1">PDF, DOC, DOCX up to 10MB</p>
                </div>

                {uploading && (
                  <div className="space-y-1">
                    <div className="flex justify-between text-xs text-gray-500">
                      <span>Uploading...</span>
                      <span>{uploadProgress}%</span>
                    </div>
                    <ProgressBar value={uploadProgress} />
                  </div>
                )}

                {/* Existing documents */}
                {documentsList.length > 0 && (
                  <div className="space-y-2">
                    <h3 className="text-sm font-medium text-brand-slate-600">Uploaded Documents</h3>
                    {documentsList.map((doc: any) => (
                      <div key={doc.id} className="flex justify-between items-center p-3 rounded-lg border border-gray-100 text-sm">
                        <div className="flex items-center gap-2">
                          <FileCheck size={16} className="text-green-500" />
                          <span>{doc.file_name}</span>
                        </div>
                        <Badge variant="neutral">{doc.document_type}</Badge>
                      </div>
                    ))}
                  </div>
                )}

                {documentsList.length === 0 && !uploading && (
                  <p className="text-sm text-gray-500">No documents uploaded yet. Upload transcripts, recommendations, and other required documents above.</p>
                )}
              </div>
            )}

            {tab === 'essays' && (
              <div className="space-y-4">
                <Button size="sm" onClick={() => setShowEssayModal(true)}>+ New Essay</Button>
                {essaysList.length === 0 ? (
                  <p className="text-sm text-gray-500 mt-2">No essays yet for this application.</p>
                ) : (
                  essaysList.map((e: Essay) => (
                    <Card key={e.id} className="p-4">
                      <div className="flex justify-between items-start mb-2">
                        <div>
                          <p className="font-medium text-sm">{e.prompt_text || 'Essay'}</p>
                          <div className="flex items-center gap-2 mt-1">
                            <span className="text-xs text-gray-500">{e.word_count ?? wordCount(e.content)} words</span>
                            <Badge variant={(STATUS_COLORS[e.status] || 'neutral') as any} size="sm">{e.status}</Badge>
                          </div>
                        </div>
                        <div className="flex gap-2">
                          <Button
                            size="sm"
                            variant="secondary"
                            onClick={() => handleEssayFeedback(e.id)}
                            loading={feedbackLoading === e.id}
                          >
                            <Sparkles size={12} className="mr-1" /> AI Feedback
                          </Button>
                          <Button
                            size="sm"
                            variant="ghost"
                            onClick={() => {
                              setEditingEssay(e)
                              setEssayContent(e.content)
                              setEssayPrompt(e.prompt_text || '')
                            }}
                          >
                            Edit
                          </Button>
                        </div>
                      </div>
                      <p className="text-sm text-gray-600 line-clamp-3">{e.content}</p>

                      {/* AI Feedback Display */}
                      {feedbackResults[e.id] && (
                        <div className="mt-3 bg-blue-50 rounded-lg p-3">
                          <div className="flex items-center gap-2 mb-2">
                            <Sparkles size={14} className="text-blue-600" />
                            <span className="text-sm font-medium text-blue-800">AI Feedback</span>
                          </div>
                          {feedbackResults[e.id].feedback && (
                            <p className="text-sm text-blue-700 whitespace-pre-wrap">{feedbackResults[e.id].feedback}</p>
                          )}
                          {feedbackResults[e.id].suggestions && (
                            <ul className="text-sm text-blue-700 list-disc list-inside mt-2 space-y-1">
                              {feedbackResults[e.id].suggestions.map((s: string, i: number) => (
                                <li key={i}>{s}</li>
                              ))}
                            </ul>
                          )}
                          {feedbackResults[e.id].score != null && (
                            <div className="mt-2">
                              <span className="text-xs text-blue-600">Score: {feedbackResults[e.id].score}/10</span>
                            </div>
                          )}
                        </div>
                      )}
                    </Card>
                  ))
                )}
              </div>
            )}

            {tab === 'resume' && (
              <div className="space-y-3">
                {resumesList.length === 0 ? (
                  <div>
                    <p className="text-sm text-gray-500 mb-3">No resume targeting this program yet.</p>
                    <Button size="sm" onClick={() => resumeGenMut.mutate()} loading={resumeGenMut.isPending}>Generate Resume</Button>
                  </div>
                ) : (
                  resumesList.map((r: Resume) => (
                    <Card key={r.id} className="p-4">
                      <p className="font-medium text-sm">Resume v{r.resume_version}</p>
                      <Badge variant={(STATUS_COLORS[r.status] || 'neutral') as any} size="sm">{r.status}</Badge>
                    </Card>
                  ))
                )}
              </div>
            )}

            {tab === 'offer' && (
              <Card className="p-4">
                <h3 className="font-medium mb-3">Offer Details</h3>
                <p className="text-sm text-gray-600">Decision: <Badge variant="success">{application.decision}</Badge></p>
                {application.decision_notes && <p className="text-sm text-gray-600 mt-2">{application.decision_notes}</p>}
                <div className="flex gap-3 mt-4">
                  <Button onClick={() => { setOfferResponse('accepted'); offerMut.mutate() }} loading={offerMut.isPending}>Accept</Button>
                  <Button variant="danger" onClick={() => setOfferResponse('declined')}>Decline</Button>
                </div>
                {offerResponse === 'declined' && (
                  <div className="mt-3 space-y-2">
                    <Textarea label="Reason (optional)" value={declineReason} onChange={e => setDeclineReason(e.target.value)} />
                    <Button variant="danger" onClick={() => offerMut.mutate()} loading={offerMut.isPending}>Confirm Decline</Button>
                  </div>
                )}
              </Card>
            )}
          </div>
        </div>
      </div>

      {/* New Essay Modal */}
      <Modal isOpen={showEssayModal} onClose={() => setShowEssayModal(false)} title="New Essay">
        <div className="space-y-3">
          <Select label="Type" options={[
            { value: 'personal_statement', label: 'Personal Statement' },
            { value: 'diversity', label: 'Diversity Statement' },
            { value: 'why_school', label: 'Why This School' },
            { value: 'research', label: 'Research Statement' },
          ]} value={essayType} onChange={e => setEssayType(e.target.value)} />
          <Textarea label="Prompt" value={essayPrompt} onChange={e => setEssayPrompt(e.target.value)} placeholder="The essay question..." />
          <div>
            <Textarea label="Content" value={essayContent} onChange={e => setEssayContent(e.target.value)} placeholder="Write your essay..." />
            <p className="text-xs text-gray-400 mt-1 text-right">{wordCount(essayContent)} words</p>
          </div>
          <Button onClick={() => essayMut.mutate({ program_id: application.program_id, essay_type: essayType, content: essayContent, prompt_text: essayPrompt })} loading={essayMut.isPending} className="w-full">Save Essay</Button>
        </div>
      </Modal>

      {/* Edit Essay Modal */}
      <Modal isOpen={!!editingEssay} onClose={() => setEditingEssay(null)} title="Edit Essay" size="lg">
        {editingEssay && (
          <div className="space-y-3">
            <Textarea label="Prompt" value={essayPrompt} onChange={e => setEssayPrompt(e.target.value)} />
            <div>
              <Textarea label="Content" value={essayContent} onChange={e => setEssayContent(e.target.value)} />
              <p className="text-xs text-gray-400 mt-1 text-right">{wordCount(essayContent)} words</p>
            </div>
            <Button
              onClick={() => essayUpdateMut.mutate({ id: editingEssay.id, data: { content: essayContent, prompt_text: essayPrompt } })}
              loading={essayUpdateMut.isPending}
              className="w-full"
            >
              Save Changes
            </Button>
          </div>
        )}
      </Modal>

      {/* Readiness Check Modal */}
      <Modal isOpen={showReadiness} onClose={() => setShowReadiness(false)} title="Application Readiness">
        {readiness && (
          <div className="space-y-4">
            <div className="flex items-center gap-3">
              {readiness.ready ? (
                <div className="w-12 h-12 rounded-full bg-green-100 flex items-center justify-center">
                  <Check size={24} className="text-green-600" />
                </div>
              ) : (
                <div className="w-12 h-12 rounded-full bg-amber-100 flex items-center justify-center">
                  <AlertCircle size={24} className="text-amber-600" />
                </div>
              )}
              <div>
                <p className="font-medium">{readiness.ready ? 'Ready to submit!' : 'You are close to ready'}</p>
                <p className="text-sm text-gray-500">{readiness.completion_percentage}% complete</p>
              </div>
            </div>

            <ProgressBar value={readiness.completion_percentage} />

            {readiness.missing_items?.length > 0 && (
              <div>
                <h4 className="text-sm font-medium mb-2">Missing items:</h4>
                <ul className="space-y-1">
                  {readiness.missing_items.map((item: string, i: number) => (
                    <li key={i} className="flex items-center gap-2 text-sm text-gray-600">
                      <Circle size={8} className="text-red-400 flex-shrink-0" />
                      {item}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {readiness.warnings?.length > 0 && (
              <div>
                <h4 className="text-sm font-medium mb-2">Warnings:</h4>
                <ul className="space-y-1">
                  {readiness.warnings.map((w: string, i: number) => (
                    <li key={i} className="flex items-center gap-2 text-sm text-amber-700">
                      <AlertCircle size={12} className="flex-shrink-0" />
                      {w}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}
      </Modal>
    </div>
  )
}
