/**
 * My Space › Prep › Documents (Spec 2026-06-10 §5) — the documents repo,
 * moved from Profile › Preparation. Transcripts, certificates, and other
 * uploads that back applications.
 */
import { useMemo, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { ArrowRight, FileText, Trash2 } from 'lucide-react'

import Badge from '../../../../components/ui/Badge'
import Button from '../../../../components/ui/Button'
import Select from '../../../../components/ui/Select'
import Skeleton from '../../../../components/ui/Skeleton'
import QueryError from '../../../../components/ui/QueryError'
import EmptyState from '../../../../components/ui/EmptyState'
import { deleteDocument, listDocuments } from '../../../../api/documents'
import { confirmDialog } from '../../../../stores/confirm-store'
import { showToast } from '../../../../stores/toast-store'
import { formatDate, formatFileSize, formatRelative } from '../../../../utils/format'
import { DOCUMENT_TYPES } from '../../../../utils/constants'
import { SectionHeader } from '../../profile/shared'
import FileDropzone from '../../profile/FileDropzone'
import type { StudentDocument } from '../../../../types'

type DocumentRecord = StudentDocument & {
  verification_status?: 'verified' | 'pending' | 'rejected' | 'none' | null
}

const CORE_DOCUMENT_TYPES = ['transcript', 'resume'] as const

function documentTypeLabel(type: string): string {
  return DOCUMENT_TYPES.find(d => d.value === type)?.label ?? type.replace(/_/g, ' ')
}

function uploadedTime(doc: DocumentRecord): number {
  const time = new Date(doc.uploaded_at).getTime()
  return Number.isNaN(time) ? 0 : time
}

function summarizeDocuments(documents: DocumentRecord[]) {
  const types = new Set(documents.map(doc => doc.document_type))
  const missingCore = CORE_DOCUMENT_TYPES.filter(type => !types.has(type))
  const verified = documents.filter(doc => doc.verification_status === 'verified').length
  const latest = [...documents].sort((a, b) => uploadedTime(b) - uploadedTime(a))[0] ?? null

  return {
    missingCore,
    verified,
    latest,
    uniqueTypeCount: types.size,
  }
}

function MaterialsLedger({
  documents,
  onChooseType,
}: {
  documents: DocumentRecord[]
  onChooseType: (type: string) => void
}) {
  const summary = summarizeDocuments(documents)
  const nextType = summary.missingCore[0] ?? 'certificate'
  const nextLabel = summary.missingCore.length > 0
    ? `Upload ${documentTypeLabel(nextType).toLowerCase()}`
    : 'Add another material'
  const latestLabel = summary.latest ? formatRelative(summary.latest.uploaded_at) : 'No arrivals yet'
  const latestDetail = summary.latest
    ? `${documentTypeLabel(summary.latest.document_type)} · ${formatDate(summary.latest.uploaded_at)}`
    : 'Uploaded materials appear here as soon as they arrive.'

  return (
    <section aria-label="Materials ledger" className="mt-4 border-y border-border bg-muted/30 px-4 py-4">
      <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            <p className="text-eyebrow uppercase text-muted-foreground">Materials ledger</p>
            {summary.missingCore.length > 0 ? (
              <Badge variant="warning">{summary.missingCore.length} core missing</Badge>
            ) : (
              <Badge variant="success">Core packet ready</Badge>
            )}
          </div>
          <h2 className="mt-1 text-lg font-semibold text-foreground">Know what has arrived before an application blocks</h2>
          <p className="mt-1 max-w-3xl text-sm text-muted-foreground">
            Track the uploaded evidence that supports applications. Keep transcript and resume current, then add essays, portfolios, recommendations, and certificates as programs ask for them.
          </p>
        </div>
        <Button size="sm" variant={summary.missingCore.length > 0 ? 'secondary' : 'tertiary'} onClick={() => onChooseType(nextType)}>
          {nextLabel}
          <ArrowRight size={14} />
        </Button>
      </div>

      <div className="mt-4 grid gap-2 md:grid-cols-4">
        <div className="rounded-lg border border-border bg-card p-3">
          <p className="text-xs font-medium text-muted-foreground">Core packet</p>
          <p className="mt-1 text-sm font-semibold text-foreground">{CORE_DOCUMENT_TYPES.length - summary.missingCore.length}/{CORE_DOCUMENT_TYPES.length} core files</p>
          <p className="mt-1 text-xs text-muted-foreground">
            {summary.missingCore.length > 0
              ? `Missing ${summary.missingCore.map(documentTypeLabel).join(', ')}.`
              : 'Transcript and resume are uploaded.'}
          </p>
        </div>
        <div className="rounded-lg border border-border bg-card p-3">
          <p className="text-xs font-medium text-muted-foreground">Evidence breadth</p>
          <p className="mt-1 text-sm font-semibold text-foreground">{summary.uniqueTypeCount} type{summary.uniqueTypeCount === 1 ? '' : 's'}</p>
          <p className="mt-1 text-xs text-muted-foreground">Different programs ask for different proof.</p>
        </div>
        <div className="rounded-lg border border-border bg-card p-3">
          <p className="text-xs font-medium text-muted-foreground">Latest arrival</p>
          <p className="mt-1 text-sm font-semibold text-foreground">{latestLabel}</p>
          <p className="mt-1 text-xs text-muted-foreground">{latestDetail}</p>
        </div>
        <div className="rounded-lg border border-border bg-card p-3">
          <p className="text-xs font-medium text-muted-foreground">Review status</p>
          <p className="mt-1 text-sm font-semibold text-foreground">{summary.verified}/{documents.length} verified</p>
          <p className="mt-1 text-xs text-muted-foreground">Recorded files still need student review before submission.</p>
        </div>
      </div>
    </section>
  )
}

export default function DocumentsTab() {
  const qc = useQueryClient()
  const { data: documents, isLoading, isError, refetch } = useQuery({ queryKey: ['documents'], queryFn: listDocuments })
  const [docType, setDocType] = useState('transcript')

  const docDelete = useMutation({
    mutationFn: deleteDocument,
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['documents'] }); showToast('Document removed', 'success') },
    onError: () => showToast("We couldn't remove the document. Please try again.", 'error'),
  })

  const documentsList: DocumentRecord[] = useMemo(
    () => (Array.isArray(documents) ? [...documents].sort((a, b) => uploadedTime(b) - uploadedTime(a)) : []),
    [documents],
  )
  const currentTypeLabel = DOCUMENT_TYPES.find(d => d.value === docType)?.label.toLowerCase() ?? 'document'

  return (
    <div className="w-full px-4 sm:px-6 py-6">
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
      <FileDropzone documentType={docType} label={`Upload a ${currentTypeLabel}`} onUploaded={() => qc.invalidateQueries({ queryKey: ['documents'] })} />
      {isLoading ? (
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
      ) : isError ? (
        <div className="mt-3">
          <QueryError variant="inline" detail="We couldn't load your documents." onRetry={() => refetch()} />
        </div>
      ) : documentsList.length === 0 ? (
        <div className="mt-3">
          <EmptyState
            icon={<FileText size={40} />}
            title="No documents yet"
            description="Start with a transcript and resume, then add essays, portfolios, recommendations, and certificates as programs ask for them."
            action={{ label: 'Upload transcript', onClick: () => setDocType('transcript') }}
          />
        </div>
      ) : (
        <>
          <MaterialsLedger documents={documentsList} onChooseType={setDocType} />
          <div className="stagger-list mt-3 space-y-2">
            {documentsList.map(doc => (
              <div key={doc.id} className="flex items-center justify-between gap-3 rounded-lg border border-border bg-card px-3 py-2">
                <div className="min-w-0">
                  <p className="text-sm font-medium text-foreground truncate">{doc.file_name}</p>
                  <p className="text-xs text-muted-foreground">
                    {documentTypeLabel(doc.document_type)} · {formatFileSize(doc.file_size_bytes)} · Uploaded {formatDate(doc.uploaded_at)}
                  </p>
                </div>
                <div className="flex shrink-0 items-center gap-2">
                  <Badge variant="neutral">{documentTypeLabel(doc.document_type)}</Badge>
                  {doc.verification_status === 'verified' ? <Badge variant="success">verified</Badge> : <Badge variant="info">recorded</Badge>}
                  <Button
                    size="sm"
                    variant="ghost"
                    aria-label={`Delete ${doc.file_name}`}
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
        </>
      )}
    </div>
  )
}
