/**
 * Profile → Preparation tab (Spec/08 §11).
 * Documents repo · Accommodations · Scheduling · Recommenders.
 */
import { lazy, Suspense, useEffect, useRef, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useSearchParams } from 'react-router-dom'
import { Accessibility, Clock, Pencil, Trash2 } from 'lucide-react'

import Badge from '../../../components/ui/Badge'
import Button from '../../../components/ui/Button'
import Card from '../../../components/ui/Card'
import Modal from '../../../components/ui/Modal'
import Select from '../../../components/ui/Select'
import Skeleton from '../../../components/ui/Skeleton'
import { getAccommodations, getScheduling, upsertAccommodations, upsertScheduling } from '../../../api/students'
import { deleteDocument, listDocuments } from '../../../api/documents'
import { confirmDialog } from '../../../stores/confirm-store'
import { showToast } from '../../../stores/toast-store'
import { formatFileSize } from '../../../utils/format'
import { DOCUMENT_TYPES } from '../../../utils/constants'
import { AccommodationForm, SchedulingForm } from '../components/ProfileForms'
import { SectionHeader } from './shared'
import FileDropzone from './FileDropzone'

const RecommendationsPage = lazy(() => import('../RecommendationsPage'))

export default function PreparationTab() {
  const qc = useQueryClient()
  const [searchParams] = useSearchParams()
  const recommendersRef = useRef<HTMLDivElement>(null)
  const { data: documents, isLoading: documentsLoading } = useQuery({ queryKey: ['documents'], queryFn: listDocuments })
  const { data: accommodations } = useQuery({ queryKey: ['accommodations'], queryFn: getAccommodations, retry: false })
  const { data: scheduling } = useQuery({ queryKey: ['scheduling'], queryFn: getScheduling, retry: false })
  const [modal, setModal] = useState<null | 'accommodations' | 'scheduling'>(null)
  const [docType, setDocType] = useState('transcript')

  useEffect(() => {
    if (searchParams.get('section') === 'recommenders') {
      recommendersRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' })
    }
  }, [searchParams])

  const docDelete = useMutation({
    mutationFn: deleteDocument,
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['documents'] }); showToast('Document removed', 'success') },
    onError: () => showToast("We couldn't remove the document. Please try again.", 'error'),
  })
  const accommMut = useMutation({
    mutationFn: upsertAccommodations,
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['accommodations'] }); setModal(null); showToast('Saved', 'success') },
    onError: () => showToast("Something didn't work. Try again.", 'error'),
  })
  const schedMut = useMutation({
    mutationFn: upsertScheduling,
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['scheduling'] }); setModal(null); showToast('Saved', 'success') },
    onError: () => showToast("Something didn't work. Try again.", 'error'),
  })

  const documentsList: any[] = Array.isArray(documents) ? documents : []

  return (
    <div className="space-y-10">
      {/* Documents */}
      <section>
        <SectionHeader
          title="Documents"
          description="Transcripts, certificates, and other uploads."
          action={
            <div className="w-44">
              <Select
                uiSize="sm"
                options={DOCUMENT_TYPES}
                value={docType}
                onChange={e => setDocType(e.target.value)}
                aria-label="Document type"
              />
            </div>
          }
        />
        <FileDropzone documentType={docType} label={`Upload a ${DOCUMENT_TYPES.find(d => d.value === docType)?.label.toLowerCase() ?? 'document'}`} onUploaded={() => qc.invalidateQueries({ queryKey: ['documents'] })} />
        {documentsLoading ? (
          <div className="mt-3 space-y-2">
            {Array.from({ length: 3 }).map((_, i) => (
              <div key={i} className="flex items-center justify-between rounded-lg border border-border bg-card px-3 py-2">
                <div className="min-w-0 space-y-1.5">
                  <Skeleton className="h-4 w-48" />
                  <Skeleton className="h-3 w-20" />
                </div>
                <Skeleton className="h-5 w-16" />
              </div>
            ))}
          </div>
        ) : documentsList.length === 0 ? (
          <p className="mt-3 text-sm text-muted-foreground">No documents uploaded yet.</p>
        ) : (
          <div className="mt-3 space-y-2">
            {documentsList.map((doc: any) => (
              <div key={doc.id} className="flex items-center justify-between rounded-lg border border-border bg-card px-3 py-2">
                <div className="min-w-0">
                  <p className="text-sm font-medium text-foreground truncate">{doc.file_name}</p>
                  <p className="text-xs text-muted-foreground">{formatFileSize(doc.file_size_bytes)}</p>
                </div>
                <div className="flex items-center gap-2">
                  <Badge variant="neutral">{doc.document_type}</Badge>
                  {doc.verification_status === 'verified' && <Badge variant="success">verified</Badge>}
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={async () => {
                      const ok = await confirmDialog({
                        title: 'Delete document?',
                        body: "This can't be undone.",
                        confirmLabel: 'Delete',
                        destructive: true,
                      })
                      if (!ok) return
                      docDelete.mutate(doc.id)
                    }}
                  >
                    <Trash2 size={14} />
                  </Button>
                </div>
              </div>
            ))}
          </div>
        )}
      </section>

      {/* Accommodations */}
      <section>
        <SectionHeader
          title="Accommodations"
          description="Private to you — used only to support your experience."
          action={<Button size="sm" variant="tertiary" onClick={() => setModal('accommodations')}><Pencil size={14} /> Edit</Button>}
        />
        <Card className="p-5">
          {!accommodations?.accommodations_needed ? (
            <div className="flex items-center gap-2.5 text-sm text-muted-foreground">
              <Accessibility size={16} /> No accommodations specified (optional).
            </div>
          ) : (
            <dl className="grid sm:grid-cols-2 gap-3 text-sm">
              <div><dt className="text-muted-foreground">Category</dt><dd className="text-foreground">{accommodations.category || '—'}</dd></div>
              <div><dt className="text-muted-foreground">Documentation</dt><dd className="text-foreground">{accommodations.documentation_status || '—'}</dd></div>
              {accommodations.details_text && <div className="sm:col-span-2"><dt className="text-muted-foreground">Details</dt><dd className="text-foreground">{accommodations.details_text}</dd></div>}
            </dl>
          )}
        </Card>
      </section>

      {/* Scheduling */}
      <section>
        <SectionHeader
          title="Scheduling"
          description="When you're available for interviews, advising, or visits."
          action={<Button size="sm" variant="tertiary" onClick={() => setModal('scheduling')}><Pencil size={14} /> Edit</Button>}
        />
        <Card className="p-5">
          {!scheduling ? (
            <div className="flex items-center gap-2.5 text-sm text-muted-foreground">
              <Clock size={16} /> No scheduling preferences set.
            </div>
          ) : (
            <dl className="grid sm:grid-cols-2 gap-3 text-sm">
              <div><dt className="text-muted-foreground">Timezone</dt><dd className="text-foreground">{scheduling.timezone || '—'}</dd></div>
              <div><dt className="text-muted-foreground">Preferred format</dt><dd className="text-foreground">{scheduling.preferred_interview_format || '—'}</dd></div>
              <div><dt className="text-muted-foreground">Campus visit</dt><dd className="text-foreground">{scheduling.campus_visit_interest ? 'Interested' : 'Not interested'}</dd></div>
              {scheduling.notes && <div className="sm:col-span-2"><dt className="text-muted-foreground">Notes</dt><dd className="text-foreground">{scheduling.notes}</dd></div>}
            </dl>
          )}
        </Card>
      </section>

      {/* Recommenders */}
      <section ref={recommendersRef} id="section-recommenders">
        <SectionHeader title="Recommenders" description="Request and track recommendation letters." />
        <Suspense fallback={<p className="text-sm text-muted-foreground">Loading recommenders…</p>}>
          <RecommendationsPage />
        </Suspense>
      </section>

      <Modal isOpen={modal === 'accommodations'} onClose={() => setModal(null)} title="Accommodations">
        <AccommodationForm defaultValues={accommodations || {}} loading={accommMut.isPending} onSubmit={(d: any) => accommMut.mutate(d)} />
      </Modal>
      <Modal isOpen={modal === 'scheduling'} onClose={() => setModal(null)} title="Scheduling & availability">
        <SchedulingForm defaultValues={scheduling || {}} loading={schedMut.isPending} onSubmit={(d: any) => schedMut.mutate(d)} />
      </Modal>
    </div>
  )
}
