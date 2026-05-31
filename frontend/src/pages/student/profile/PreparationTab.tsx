/**
 * Profile → Preparation tab (spec 10 §11).
 * Documents · Accommodations · Scheduling · Recommenders (migrated here per G-S1).
 */
import { useRef, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Accessibility, CalendarClock, FileText, Upload, Users } from 'lucide-react'

import { getAccommodations, getScheduling, upsertAccommodations, upsertScheduling } from '../../../api/students'
import { confirmUpload, deleteDocument, listDocuments, requestUpload, uploadToS3 } from '../../../api/documents'
import Badge from '../../../components/ui/Badge'
import Button from '../../../components/ui/Button'
import Modal from '../../../components/ui/Modal'
import { showToast } from '../../../stores/toast-store'
import { formatFileSize } from '../../../utils/format'
import { AccommodationForm, SchedulingForm } from '../components/ProfileForms'
import RecommendationsPage from '../RecommendationsPage'
import { EmptyHint, ItemRow, SectionCard } from './_shared'

const DOC_TYPES = [
  { value: 'transcript', label: 'Transcript' },
  { value: 'test_score', label: 'Test score report' },
  { value: 'certificate', label: 'Certificate' },
  { value: 'recommendation', label: 'Recommendation' },
  { value: 'other', label: 'Other' },
]

export default function PreparationTab() {
  const qc = useQueryClient()
  const fileRef = useRef<HTMLInputElement>(null)
  const [docType, setDocType] = useState('transcript')
  const [uploading, setUploading] = useState(false)
  const [modal, setModal] = useState<'accommodations' | 'scheduling' | null>(null)

  const { data: documents } = useQuery<any[]>({ queryKey: ['documents'], queryFn: listDocuments })
  const { data: accommodations } = useQuery({ queryKey: ['accommodations'], queryFn: getAccommodations, retry: false })
  const { data: scheduling } = useQuery({ queryKey: ['scheduling'], queryFn: getScheduling, retry: false })

  const done = (msg: string, keys: string[]) => {
    keys.forEach(k => qc.invalidateQueries({ queryKey: [k] }))
    qc.invalidateQueries({ queryKey: ['profile-overview'] })
    setModal(null)
    showToast(msg, 'success')
  }
  const fail = () => showToast("Something didn't work. Try again.", 'error')

  const accommMut = useMutation({ mutationFn: upsertAccommodations, onSuccess: () => done('Saved', ['accommodations']), onError: fail })
  const schedMut = useMutation({ mutationFn: upsertScheduling, onSuccess: () => done('Saved', ['scheduling']), onError: fail })
  const delDoc = useMutation({ mutationFn: deleteDocument, onSuccess: () => done('Deleted', ['documents']), onError: fail })

  const onFiles = async (files: FileList | null) => {
    const file = files?.[0]
    if (!file) return
    setUploading(true)
    try {
      const res: any = await requestUpload({
        document_type: docType,
        file_name: file.name,
        content_type: file.type || 'application/octet-stream',
        file_size_bytes: file.size,
      })
      const url = res.upload_url || res.url
      const docId = res.document_id || res.id || res.document?.id
      if (url) await uploadToS3(url, file)
      if (docId) await confirmUpload(docId)
      qc.invalidateQueries({ queryKey: ['documents'] })
      qc.invalidateQueries({ queryKey: ['profile-overview'] })
      showToast('Document uploaded', 'success')
    } catch {
      showToast("Upload didn't work. Try again.", 'error')
    } finally {
      setUploading(false)
      if (fileRef.current) fileRef.current.value = ''
    }
  }

  const documentsList = Array.isArray(documents) ? documents : []

  return (
    <div className="space-y-6">
      <SectionCard title="Documents" icon={FileText} count={documentsList.length}>
        <div
          onDragOver={e => e.preventDefault()}
          onDrop={e => {
            e.preventDefault()
            onFiles(e.dataTransfer.files)
          }}
          className="border border-dashed border-border rounded-lg p-4 mb-3 flex flex-col sm:flex-row sm:items-center gap-3"
        >
          <select
            value={docType}
            onChange={e => setDocType(e.target.value)}
            className="text-sm border border-border rounded-lg px-2 py-1.5 bg-card text-charcoal"
          >
            {DOC_TYPES.map(t => (
              <option key={t.value} value={t.value}>{t.label}</option>
            ))}
          </select>
          <input ref={fileRef} type="file" className="hidden" onChange={e => onFiles(e.target.files)} />
          <Button size="sm" variant="secondary" loading={uploading} onClick={() => fileRef.current?.click()}>
            <Upload size={14} className="mr-1" /> Upload or drop a file
          </Button>
        </div>
        {documentsList.length === 0 ? (
          <EmptyHint>No documents uploaded. Add transcripts, certificates, or score reports.</EmptyHint>
        ) : (
          <div className="space-y-2">
            {documentsList.map((doc: any) => (
              <ItemRow key={doc.id} onDelete={() => delDoc.mutate(doc.id)}>
                <span className="text-sm text-charcoal">{doc.file_name} <span className="text-slate">({formatFileSize(doc.file_size_bytes)})</span></span>
                <Badge variant="neutral" size="sm">{doc.document_type}</Badge>
              </ItemRow>
            ))}
          </div>
        )}
      </SectionCard>

      <SectionCard title="Accommodations" icon={Accessibility} onEdit={() => setModal('accommodations')}>
        {!accommodations?.accommodations_needed ? (
          <EmptyHint>No accommodations specified (optional). Anything here stays private until you choose to share it.</EmptyHint>
        ) : (
          <dl className="grid grid-cols-2 gap-2 text-sm">
            <div><dt className="text-slate text-xs">Category</dt><dd className="text-charcoal">{accommodations.category || '—'}</dd></div>
            <div><dt className="text-slate text-xs">Documentation</dt><dd className="text-charcoal">{accommodations.documentation_status || '—'}</dd></div>
            {accommodations.details_text && <div className="col-span-2"><dt className="text-slate text-xs">Details</dt><dd className="text-charcoal">{accommodations.details_text}</dd></div>}
          </dl>
        )}
      </SectionCard>

      <SectionCard title="Scheduling" icon={CalendarClock} onEdit={() => setModal('scheduling')}>
        {!scheduling ? (
          <EmptyHint>Set your availability for interviews, advising, and visits.</EmptyHint>
        ) : (
          <dl className="grid grid-cols-2 gap-2 text-sm">
            <div><dt className="text-slate text-xs">Timezone</dt><dd className="text-charcoal">{scheduling.timezone || '—'}</dd></div>
            <div><dt className="text-slate text-xs">Preferred format</dt><dd className="text-charcoal">{scheduling.preferred_interview_format || '—'}</dd></div>
            <div><dt className="text-slate text-xs">Campus visit</dt><dd className="text-charcoal">{scheduling.campus_visit_interest ? 'Interested' : 'Not interested'}</dd></div>
            {scheduling.notes && <div className="col-span-2"><dt className="text-slate text-xs">Notes</dt><dd className="text-charcoal">{scheduling.notes}</dd></div>}
          </dl>
        )}
      </SectionCard>

      <div>
        <div className="flex items-center gap-2 mb-2 px-1">
          <Users size={16} className="text-cobalt" />
          <h3 className="font-semibold text-charcoal">Recommenders</h3>
        </div>
        <RecommendationsPage />
      </div>

      <Modal isOpen={modal === 'accommodations'} onClose={() => setModal(null)} title="Accommodations">
        <AccommodationForm defaultValues={accommodations || {}} loading={accommMut.isPending} onSubmit={d => accommMut.mutate(d)} />
      </Modal>
      <Modal isOpen={modal === 'scheduling'} onClose={() => setModal(null)} title="Scheduling & availability">
        <SchedulingForm defaultValues={scheduling || {}} loading={schedMut.isPending} onSubmit={d => schedMut.mutate(d)} />
      </Modal>
    </div>
  )
}
