/**
 * My Space › Prep › Documents (Spec 2026-06-10 §5) — the documents repo,
 * moved from Profile › Preparation. Transcripts, certificates, and other
 * uploads that back applications.
 */
import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Download, FileText, Trash2 } from 'lucide-react'

import Badge from '../../../../components/ui/Badge'
import Button from '../../../../components/ui/Button'
import Select from '../../../../components/ui/Select'
import Skeleton from '../../../../components/ui/Skeleton'
import QueryError from '../../../../components/ui/QueryError'
import EmptyState from '../../../../components/ui/EmptyState'
import { deleteDocument, getDocument, listDocuments } from '../../../../api/documents'
import { confirmDialog } from '../../../../stores/confirm-store'
import { showToast } from '../../../../stores/toast-store'
import { formatDate, formatFileSize } from '../../../../utils/format'
import { DOCUMENT_TYPES } from '../../../../utils/constants'
import { SectionHeader } from '../../profile/shared'
import FileDropzone from '../../profile/FileDropzone'

export default function DocumentsTab() {
  const qc = useQueryClient()
  const { data: documents, isLoading, isError, refetch } = useQuery({ queryKey: ['documents'], queryFn: listDocuments })
  const [docType, setDocType] = useState('transcript')
  const [openingId, setOpeningId] = useState<string | null>(null)

  const docDelete = useMutation({
    mutationFn: deleteDocument,
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['documents'] }); showToast('Document removed', 'success') },
    onError: () => showToast("We couldn't remove the document. Please try again.", 'error'),
  })

  const openDocument = async (docId: string) => {
    if (openingId) return
    setOpeningId(docId)
    try {
      const doc = await getDocument(docId)
      const url: string | null = doc?.download_url ?? null
      if (url) {
        window.open(url, '_blank', 'noopener,noreferrer')
      } else {
        showToast("We couldn't open that file. Please try again.", 'error')
      }
    } catch {
      showToast("We couldn't open that file. Please try again.", 'error')
    } finally {
      setOpeningId(null)
    }
  }

  const documentsList: any[] = Array.isArray(documents) ? documents : []

  return (
    <div className="w-full px-4 sm:px-6 py-6">
      <SectionHeader
        title="Documents"
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
        <div className="mt-3">
          <EmptyState
            icon={<FileText size={40} />}
            title="No documents yet"
          />
        </div>
      ) : (
        <div className="stagger-list mt-3 space-y-2">
          {documentsList.map((doc: any) => (
            <div key={doc.id} className="flex items-center justify-between rounded-lg border border-border bg-card px-3 py-2">
              <div className="min-w-0">
                <p className="text-sm font-medium text-foreground truncate">{doc.file_name}</p>
                <p className="text-xs text-muted-foreground">
                  {formatFileSize(doc.file_size_bytes)}
                  {doc.uploaded_at ? ` · ${formatDate(doc.uploaded_at)}` : ''}
                </p>
              </div>
              <div className="flex items-center gap-2">
                <Badge variant="neutral">{DOCUMENT_TYPES.find(d => d.value === doc.document_type)?.label ?? doc.document_type}</Badge>
                {doc.verification_status === 'verified' && <Badge variant="success">verified</Badge>}
                <Button
                  size="sm"
                  variant="ghost"
                  aria-label={`Download ${doc.file_name}`}
                  disabled={openingId === doc.id}
                  onClick={() => openDocument(doc.id)}
                >
                  <Download size={14} />
                </Button>
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
      )}
    </div>
  )
}
