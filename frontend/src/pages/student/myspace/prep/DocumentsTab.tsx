/**
 * My Space › Prep › Documents (Spec 2026-06-10 §5) — the documents repo,
 * moved from Profile › Preparation. Transcripts, certificates, and other
 * uploads that back applications.
 */
import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Trash2 } from 'lucide-react'

import Badge from '../../../../components/ui/Badge'
import Button from '../../../../components/ui/Button'
import Select from '../../../../components/ui/Select'
import Skeleton from '../../../../components/ui/Skeleton'
import QueryError from '../../../../components/ui/QueryError'
import { deleteDocument, listDocuments } from '../../../../api/documents'
import { confirmDialog } from '../../../../stores/confirm-store'
import { showToast } from '../../../../stores/toast-store'
import { formatFileSize } from '../../../../utils/format'
import { DOCUMENT_TYPES } from '../../../../utils/constants'
import { SectionHeader } from '../../profile/shared'
import FileDropzone from '../../profile/FileDropzone'

export default function DocumentsTab() {
  const qc = useQueryClient()
  const { data: documents, isLoading, isError, refetch } = useQuery({ queryKey: ['documents'], queryFn: listDocuments })
  const [docType, setDocType] = useState('transcript')

  const docDelete = useMutation({
    mutationFn: deleteDocument,
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['documents'] }); showToast('Document removed', 'success') },
    onError: () => showToast("We couldn't remove the document. Please try again.", 'error'),
  })

  const documentsList: any[] = Array.isArray(documents) ? documents : []

  return (
    <div className="mx-auto w-full max-w-5xl px-4 sm:px-6 py-6">
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
    </div>
  )
}
