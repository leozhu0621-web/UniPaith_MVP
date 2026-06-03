import { useQuery } from '@tanstack/react-query'
import { FileText, Link2 } from 'lucide-react'
import { listDocuments } from '../../../api/documents'
import type { InboxAttachment } from '../../../types'

// Spec 17 §6 — attach a document from existing student materials (or a link).
export default function AttachmentPicker({
  selected,
  onAdd,
}: {
  selected: InboxAttachment[]
  onAdd: (a: InboxAttachment) => void
}) {
  const { data } = useQuery({ queryKey: ['my-documents'], queryFn: listDocuments })
  const docs: Array<{ id?: string; file_name?: string; name?: string }> = Array.isArray(data) ? data : []
  const has = (id?: string, name?: string) =>
    selected.some(s => (id && s.id === id) || s.name === name)

  return (
    <div className="mb-2 max-h-40 overflow-y-auto rounded-lg border border-border bg-muted/40 p-2">
      <p className="mb-1 px-1 text-[11px] font-medium text-muted-foreground">
        Attach from your materials
      </p>
      {docs.length === 0 ? (
        <p className="px-1 py-1 text-xs text-muted-foreground">No documents uploaded yet.</p>
      ) : (
        docs.slice(0, 12).map((doc, i) => {
          const name = doc.file_name || doc.name || 'Document'
          const added = has(doc.id, name)
          return (
            <button
              key={doc.id || i}
              disabled={added}
              onClick={() => onAdd({ id: doc.id, name, kind: 'document' })}
              className="flex w-full items-center gap-2 rounded px-2 py-1.5 text-left text-xs text-foreground hover:bg-card disabled:opacity-40"
            >
              <FileText size={12} className="shrink-0 text-secondary" />
              <span className="truncate">{name}</span>
              {added && <span className="ml-auto text-[10px] text-muted-foreground">Added</span>}
            </button>
          )
        })
      )}
      <div className="mt-1 flex items-center gap-1.5 border-t border-border px-1 pt-1.5 text-[11px] text-muted-foreground">
        <Link2 size={11} /> Paste a portfolio link directly in your reply.
      </div>
    </div>
  )
}
