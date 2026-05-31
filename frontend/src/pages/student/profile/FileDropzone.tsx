/**
 * Drag-drop upload zone (Spec/08 §6.1 transcript upload, §11.1 documents repo).
 * Presigned S3 flow: request-upload → PUT to S3 → confirm. Token-only styling.
 */
import { useRef, useState } from 'react'
import clsx from 'clsx'
import { Upload } from 'lucide-react'

import { confirmUpload, requestUpload, uploadToS3 } from '../../../api/documents'
import { showToast } from '../../../stores/toast-store'

type Status = 'idle' | 'uploading' | 'parsing' | 'done' | 'error'

export default function FileDropzone({
  documentType,
  label,
  accept = '.pdf,.png,.jpg,.jpeg,.doc,.docx',
  onUploaded,
}: {
  documentType: string
  label: string
  accept?: string
  onUploaded?: () => void
}) {
  const inputRef = useRef<HTMLInputElement>(null)
  const [status, setStatus] = useState<Status>('idle')
  const [progress, setProgress] = useState(0)
  const [dragging, setDragging] = useState(false)

  const handleFile = async (file: File) => {
    if (!file) return
    setStatus('uploading')
    setProgress(0)
    try {
      const { upload_url, document_id } = await requestUpload({
        document_type: documentType,
        file_name: file.name,
        content_type: file.type || 'application/octet-stream',
        file_size_bytes: file.size,
      })
      await uploadToS3(upload_url, file, pct => setProgress(pct))
      setStatus('parsing')
      await confirmUpload(document_id)
      setStatus('done')
      showToast('Uploaded', 'success')
      onUploaded?.()
      setTimeout(() => setStatus('idle'), 2000)
    } catch {
      setStatus('error')
      showToast("Upload didn't work. Try again.", 'error')
    }
  }

  return (
    <div
      onDragOver={e => {
        e.preventDefault()
        setDragging(true)
      }}
      onDragLeave={() => setDragging(false)}
      onDrop={e => {
        e.preventDefault()
        setDragging(false)
        if (e.dataTransfer.files?.[0]) handleFile(e.dataTransfer.files[0])
      }}
      onClick={() => inputRef.current?.click()}
      role="button"
      tabIndex={0}
      onKeyDown={e => {
        if (e.key === 'Enter' || e.key === ' ') inputRef.current?.click()
      }}
      className={clsx(
        'flex flex-col items-center justify-center gap-2 rounded-lg border-2 border-dashed px-4 py-8 text-center cursor-pointer transition-colors',
        dragging ? 'border-secondary bg-muted' : 'border-border hover:border-charcoal/30',
      )}
    >
      <input
        ref={inputRef}
        type="file"
        accept={accept}
        className="hidden"
        onChange={e => e.target.files?.[0] && handleFile(e.target.files[0])}
      />
      <Upload size={20} className="text-muted-foreground" />
      {status === 'idle' && (
        <p className="text-sm text-muted-foreground">
          {label} — drag a file here or <span className="text-secondary font-semibold">browse</span>
        </p>
      )}
      {status === 'uploading' && (
        <div className="w-full max-w-xs">
          <p className="text-sm text-muted-foreground mb-1">Uploading… {progress}%</p>
          <div className="h-1.5 w-full rounded-pill bg-border overflow-hidden">
            <div className="h-full bg-secondary transition-all" style={{ width: `${progress}%` }} />
          </div>
        </div>
      )}
      {status === 'parsing' && <p className="text-sm text-muted-foreground">Processing…</p>}
      {status === 'done' && <p className="text-sm text-success">Uploaded</p>}
      {status === 'error' && <p className="text-sm text-error">Upload failed — try again.</p>}
    </div>
  )
}
