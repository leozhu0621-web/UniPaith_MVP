import { useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { getMyApplication, submitApplication, getChecklist, generateChecklist, respondToOffer } from '../../api/applications'
import { listEssays, createEssay } from '../../api/essays'
import { listResumes, generateResume } from '../../api/resumes'
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
import { ArrowLeft, Check, Circle } from 'lucide-react'
import type { Application, Essay, Resume } from '../../types'

const STATUS_STEPS = ['draft', 'submitted', 'under_review', 'interview', 'decision_made']

export default function ApplicationDetailPage() {
  const { appId } = useParams<{ appId: string }>()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [tab, setTab] = useState('documents')
  const [showEssayModal, setShowEssayModal] = useState(false)
  const [essayContent, setEssayContent] = useState('')
  const [essayPrompt, setEssayPrompt] = useState('')
  const [essayType, setEssayType] = useState('personal_statement')
  const [offerResponse, setOfferResponse] = useState('')
  const [declineReason, setDeclineReason] = useState('')

  const { data: app, isLoading } = useQuery({ queryKey: ['application', appId], queryFn: () => getMyApplication(appId!) })
  const { data: checklist } = useQuery({ queryKey: ['checklist', appId], queryFn: () => getChecklist(appId!).catch(() => generateChecklist(appId!)) })
  const { data: essays } = useQuery({ queryKey: ['essays', app?.program_id], queryFn: () => listEssays(app?.program_id), enabled: !!app?.program_id && tab === 'essays' })
  const { data: resumes } = useQuery({ queryKey: ['resumes', app?.program_id], queryFn: () => listResumes(app?.program_id), enabled: !!app?.program_id && tab === 'resume' })

  const submitMut = useMutation({ mutationFn: () => submitApplication(appId!), onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['application', appId] }); showToast('Application submitted!', 'success') } })
  const essayMut = useMutation({ mutationFn: (data: any) => createEssay(data), onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['essays'] }); setShowEssayModal(false); showToast('Essay created', 'success') } })
  const resumeGenMut = useMutation({ mutationFn: () => generateResume({ format_type: 'standard', target_program_id: app?.program_id }), onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['resumes'] }); showToast('Resume generated', 'success') } })
  const offerMut = useMutation({ mutationFn: () => respondToOffer(appId!, offerResponse, declineReason || undefined), onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['application', appId] }); showToast('Response submitted', 'success') } })

  if (isLoading) return <div className="p-6"><Skeleton className="h-64" /></div>

  const application: Application = app
  const currentStepIdx = STATUS_STEPS.indexOf(application.status)
  const checklistItems = checklist?.items ?? []
  const completionPct = checklist?.completion_percentage ?? 0

  const tabs = [
    { id: 'documents', label: 'Documents' },
    { id: 'essays', label: 'Essays' },
    { id: 'resume', label: 'Resume' },
    ...(application.decision === 'admitted' ? [{ id: 'offer', label: 'Offer' }] : []),
  ]

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <button onClick={() => navigate('/s/applications')} className="flex items-center gap-1 text-sm text-gray-500 hover:text-gray-700 mb-4">
        <ArrowLeft size={16} /> My Applications
      </button>

      <h1 className="text-xl font-bold mb-1">{application.program?.program_name || 'Application'}</h1>

      {/* Status timeline */}
      <div className="flex items-center gap-1 my-4">
        {STATUS_STEPS.map((step, i) => (
          <div key={step} className="flex items-center">
            <div className={`w-6 h-6 rounded-full flex items-center justify-center text-xs ${i <= currentStepIdx ? 'bg-gray-900 text-white' : 'bg-gray-200 text-gray-400'}`}>
              {i < currentStepIdx ? <Check size={12} /> : <Circle size={12} />}
            </div>
            {i < STATUS_STEPS.length - 1 && <div className={`w-12 h-0.5 ${i < currentStepIdx ? 'bg-gray-900' : 'bg-gray-200'}`} />}
          </div>
        ))}
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
            <Button
              className="w-full mt-3"
              disabled={application.status !== 'draft'}
              onClick={() => submitMut.mutate()}
              loading={submitMut.isPending}
              size="sm"
            >
              Submit Application
            </Button>
          </Card>
        </div>

        {/* Main content */}
        <div className="flex-1 min-w-0">
          <Tabs tabs={tabs} activeTab={tab} onChange={setTab} />
          <div className="mt-4">
            {tab === 'documents' && (
              <div className="text-sm text-gray-500">
                Documents from your profile are automatically linked to this application. Upload additional documents from your Profile page.
              </div>
            )}

            {tab === 'essays' && (
              <div className="space-y-3">
                <Button size="sm" onClick={() => setShowEssayModal(true)}>+ New Essay</Button>
                {(essays ?? []).length === 0 ? (
                  <p className="text-sm text-gray-500 mt-2">No essays yet for this application.</p>
                ) : (
                  (essays ?? []).map((e: Essay) => (
                    <Card key={e.id} className="p-4">
                      <div className="flex justify-between items-start">
                        <div>
                          <p className="font-medium text-sm">{e.prompt_text || 'Essay'}</p>
                          <p className="text-xs text-gray-500 mt-1">{e.word_count ?? 0} words | <Badge variant={(STATUS_COLORS[e.status] || 'neutral') as any} size="sm">{e.status}</Badge></p>
                        </div>
                      </div>
                      <p className="text-sm text-gray-600 mt-2 line-clamp-3">{e.content}</p>
                    </Card>
                  ))
                )}
              </div>
            )}

            {tab === 'resume' && (
              <div className="space-y-3">
                {(resumes ?? []).length === 0 ? (
                  <div>
                    <p className="text-sm text-gray-500 mb-3">No resume targeting this program yet.</p>
                    <Button size="sm" onClick={() => resumeGenMut.mutate()} loading={resumeGenMut.isPending}>Generate Resume</Button>
                  </div>
                ) : (
                  (resumes ?? []).map((r: Resume) => (
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
          <Textarea label="Content" value={essayContent} onChange={e => setEssayContent(e.target.value)} placeholder="Write your essay..." />
          <Button onClick={() => essayMut.mutate({ program_id: application.program_id, essay_type: essayType, content: essayContent, prompt_text: essayPrompt })} loading={essayMut.isPending} className="w-full">Save Essay</Button>
        </div>
      </Modal>
    </div>
  )
}
