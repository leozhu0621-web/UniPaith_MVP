import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { FileStack, Plus, Edit2, Trash2, Star, Send, Eye } from 'lucide-react'
import {
  getTemplates, createTemplate, updateTemplate, deleteTemplate,
  previewTemplate, getInstitutionPrograms,
} from '../../api/institutions'
import Card from '../../components/ui/Card'
import Badge from '../../components/ui/Badge'
import Button from '../../components/ui/Button'
import Modal from '../../components/ui/Modal'
import Input from '../../components/ui/Input'
import Select from '../../components/ui/Select'
import Textarea from '../../components/ui/Textarea'
import Tabs from '../../components/ui/Tabs'
import EmptyState from '../../components/ui/EmptyState'
import Skeleton from '../../components/ui/Skeleton'
import InstitutionPageHeader from '../../components/institution/InstitutionPageHeader'
import { showToast } from '../../stores/toast-store'
import { formatDate } from '../../utils/format'
import type { CommunicationTemplate, Program } from '../../types'

const TYPE_OPTIONS = [
  { value: 'missing_items', label: 'Missing Items' },
  { value: 'interview_invite', label: 'Interview Invite' },
  { value: 'clarification', label: 'Clarification' },
  { value: 'decision_notice', label: 'Decision Notice' },
  { value: 'offer_notice', label: 'Offer Notice' },
  { value: 'custom', label: 'Custom' },
]

const TYPE_BADGE: Record<string, 'warning' | 'info' | 'neutral' | 'success'> = {
  missing_items: 'warning',
  interview_invite: 'info',
  clarification: 'neutral',
  decision_notice: 'success',
  offer_notice: 'success',
  custom: 'neutral',
}

const VARIABLES = ['first_name', 'last_name', 'email', 'program_name', 'institution_name']

export default function TemplatesPage() {
  const queryClient = useQueryClient()
  const [activeTab, setActiveTab] = useState('all')
  const [showModal, setShowModal] = useState(false)
  const [editTarget, setEditTarget] = useState<CommunicationTemplate | null>(null)
  const [deleteTarget, setDeleteTarget] = useState<CommunicationTemplate | null>(null)
  const [previewTarget, setPreviewTarget] = useState<string | null>(null)
  const [previewData, setPreviewData] = useState<{ rendered_subject: string; rendered_body: string } | null>(null)

  // Form
  const [name, setName] = useState('')
  const [templateType, setTemplateType] = useState('missing_items')
  const [subject, setSubject] = useState('')
  const [body, setBody] = useState('')
  const [programId, setProgramId] = useState('')
  const [isDefault, setIsDefault] = useState(false)

  const tabs = [
    { id: 'all', label: 'All' },
    { id: 'missing_items', label: 'Missing Items' },
    { id: 'interview_invite', label: 'Interview' },
    { id: 'clarification', label: 'Clarification' },
    { id: 'decision_notice', label: 'Decision' },
    { id: 'offer_notice', label: 'Offer' },
    { id: 'custom', label: 'Custom' },
  ]

  const typeFilter = activeTab === 'all' ? undefined : activeTab
  const templatesQ = useQuery({ queryKey: ['templates', typeFilter], queryFn: () => getTemplates(typeFilter) })
  const templates: CommunicationTemplate[] = Array.isArray(templatesQ.data) ? templatesQ.data : []

  const programsQ = useQuery({ queryKey: ['institution-programs'], queryFn: getInstitutionPrograms })
  const programs: Program[] = Array.isArray(programsQ.data) ? programsQ.data : []
  const programOptions = [{ value: '', label: 'All Programs' }, ...programs.map(p => ({ value: p.id, label: p.program_name }))]

  const resetForm = () => {
    setName(''); setTemplateType('missing_items'); setSubject(''); setBody('')
    setProgramId(''); setIsDefault(false); setEditTarget(null)
  }
  const openCreate = () => { resetForm(); setShowModal(true) }
  const openEdit = (t: CommunicationTemplate) => {
    setEditTarget(t); setName(t.name); setTemplateType(t.template_type)
    setSubject(t.subject); setBody(t.body); setProgramId(t.program_id || '')
    setIsDefault(t.is_default); setShowModal(true)
  }

  const createMut = useMutation({
    mutationFn: createTemplate,
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['templates'] }); setShowModal(false); resetForm(); showToast('Template created', 'success') },
  })
  const updateMut = useMutation({
    mutationFn: (p: { id: string; payload: Parameters<typeof updateTemplate>[1] }) => updateTemplate(p.id, p.payload),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['templates'] }); setShowModal(false); resetForm(); showToast('Template updated', 'success') },
  })
  const deleteMut = useMutation({
    mutationFn: deleteTemplate,
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['templates'] }); setDeleteTarget(null); showToast('Template deleted', 'success') },
  })

  const handlePreview = async (templateId: string) => {
    setPreviewTarget(templateId)
    try {
      const data = await previewTemplate(templateId)
      setPreviewData(data)
    } catch { setPreviewData(null) }
  }

  const insertVariable = (variable: string, target: 'subject' | 'body') => {
    const tag = `{{${variable}}}`
    if (target === 'subject') setSubject(prev => prev + tag)
    else setBody(prev => prev + tag)
  }

  const handleSubmit = () => {
    if (!name.trim() || !subject.trim() || !body.trim()) { showToast('Name, subject, and body are required', 'warning'); return }
    const payload = {
      name, template_type: templateType, subject, body,
      program_id: programId || undefined, is_default: isDefault,
    }
    if (editTarget) updateMut.mutate({ id: editTarget.id, payload })
    else createMut.mutate(payload)
  }

  return (
    <div className="p-6 space-y-4">
      <InstitutionPageHeader
        title="Communication Templates"
        description="Reusable templates for applicant communications with {{variable}} personalization."
        actions={<Button onClick={openCreate} className="flex items-center gap-2"><Plus size={16} /> New Template</Button>}
      />

      <Tabs tabs={tabs} activeTab={activeTab} onChange={setActiveTab} />

      {templatesQ.isLoading ? (
        <div className="grid grid-cols-2 gap-4">{Array.from({ length: 4 }).map((_, i) => <Skeleton key={i} className="h-40" />)}</div>
      ) : templates.length === 0 ? (
        <EmptyState icon={<FileStack size={40} />} title="No templates" description="Create templates for missing items, interview invites, decisions, and more." action={{ label: 'New Template', onClick: openCreate }} />
      ) : (
        <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
          {templates.map(t => (
            <Card key={t.id} className="p-4">
              <div className="flex items-start justify-between mb-2">
                <div className="flex items-center gap-2">
                  <h3 className="font-semibold text-gray-900">{t.name}</h3>
                  {t.is_default && <Star size={14} className="text-amber-500 fill-amber-500" />}
                </div>
                <div className="flex items-center gap-1">
                  <Badge variant={TYPE_BADGE[t.template_type] ?? 'neutral'}>{t.template_type.replace(/_/g, ' ')}</Badge>
                  {!t.is_active && <Badge variant="neutral">Inactive</Badge>}
                </div>
              </div>
              <p className="text-sm text-gray-600 mb-1"><span className="text-gray-400">Subject:</span> {t.subject}</p>
              <p className="text-sm text-gray-500 line-clamp-2 mb-2">{t.body}</p>
              <div className="flex items-center gap-2 text-xs text-gray-400 mb-2">
                {t.program_name && <Badge variant="info">{t.program_name}</Badge>}
                <span>{formatDate(t.created_at)}</span>
                {t.variables && <span>{(Array.isArray(t.variables) ? t.variables : []).length} variables</span>}
              </div>
              <div className="flex gap-2">
                <Button variant="ghost" size="sm" onClick={() => openEdit(t)} className="flex items-center gap-1"><Edit2 size={14} /> Edit</Button>
                <Button variant="ghost" size="sm" onClick={() => handlePreview(t.id)} className="flex items-center gap-1"><Eye size={14} /> Preview</Button>
                <Button variant="ghost" size="sm" onClick={() => setDeleteTarget(t)} className="flex items-center gap-1 text-red-600"><Trash2 size={14} /></Button>
              </div>
            </Card>
          ))}
        </div>
      )}

      {/* Create/Edit Modal */}
      <Modal isOpen={showModal} onClose={() => { setShowModal(false); resetForm() }} title={editTarget ? 'Edit Template' : 'New Template'}>
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-3">
            <Input label="Name *" value={name} onChange={e => setName(e.target.value)} placeholder="e.g. Missing Transcript Request" />
            <Select label="Type" options={TYPE_OPTIONS} value={templateType} onChange={e => setTemplateType(e.target.value)} />
          </div>
          <div>
            <Input label="Subject *" value={subject} onChange={e => setSubject(e.target.value)} placeholder="e.g. Missing documents for {{program_name}}" />
            <div className="flex gap-1 mt-1">
              {VARIABLES.map(v => (
                <button key={v} type="button" onClick={() => insertVariable(v, 'subject')} className="text-xs bg-gray-100 hover:bg-gray-200 px-1.5 py-0.5 rounded text-gray-600">{`{{${v}}}`}</button>
              ))}
            </div>
          </div>
          <div>
            <Textarea label="Body *" value={body} onChange={e => setBody(e.target.value)} rows={6} placeholder="Dear {{first_name}},&#10;&#10;We noticed your application to {{program_name}} is missing..." />
            <div className="flex gap-1 mt-1">
              {VARIABLES.map(v => (
                <button key={v} type="button" onClick={() => insertVariable(v, 'body')} className="text-xs bg-gray-100 hover:bg-gray-200 px-1.5 py-0.5 rounded text-gray-600">{`{{${v}}}`}</button>
              ))}
            </div>
          </div>
          <Select label="Program (optional)" options={programOptions} value={programId} onChange={e => setProgramId(e.target.value)} />
          <label className="flex items-center gap-2 text-sm text-gray-700">
            <input type="checkbox" checked={isDefault} onChange={e => setIsDefault(e.target.checked)} className="rounded border-gray-300" />
            Set as default template for this type
          </label>
          <div className="flex justify-end gap-2">
            <Button variant="ghost" onClick={() => { setShowModal(false); resetForm() }}>Cancel</Button>
            <Button onClick={handleSubmit} disabled={createMut.isPending || updateMut.isPending}>
              {(createMut.isPending || updateMut.isPending) ? 'Saving...' : 'Save'}
            </Button>
          </div>
        </div>
      </Modal>

      {/* Delete Modal */}
      <Modal isOpen={!!deleteTarget} onClose={() => setDeleteTarget(null)} title="Delete Template">
        <p className="text-sm text-gray-600 mb-4">Delete <strong>{deleteTarget?.name}</strong>?</p>
        <div className="flex justify-end gap-2">
          <Button variant="ghost" onClick={() => setDeleteTarget(null)}>Cancel</Button>
          <Button variant="danger" onClick={() => deleteTarget && deleteMut.mutate(deleteTarget.id)} disabled={deleteMut.isPending}>
            {deleteMut.isPending ? 'Deleting...' : 'Delete'}
          </Button>
        </div>
      </Modal>

      {/* Preview Modal */}
      <Modal isOpen={!!previewTarget} onClose={() => { setPreviewTarget(null); setPreviewData(null) }} title="Template Preview">
        {previewData ? (
          <div className="space-y-3">
            <div>
              <p className="text-xs text-gray-400 mb-1">Subject</p>
              <p className="text-sm font-medium text-gray-900 bg-gray-50 rounded px-3 py-2">{previewData.rendered_subject}</p>
            </div>
            <div>
              <p className="text-xs text-gray-400 mb-1">Body</p>
              <div className="text-sm text-gray-700 bg-gray-50 rounded px-3 py-3 whitespace-pre-wrap">{previewData.rendered_body}</div>
            </div>
          </div>
        ) : (
          <p className="text-sm text-gray-500 text-center py-4">Loading preview...</p>
        )}
      </Modal>
    </div>
  )
}
