/**
 * Material upload flow — pick a file → Uni reads it → review → confirm → My Space.
 *
 * Self-contained: handles upload, the review card, and apply. Used in two places
 * (the Uni chat and the My Space profile import card) via the same backend.
 */
import { useRef, useState } from 'react'
import { Loader2, Sparkles, Upload } from 'lucide-react'

import {
  type ApplyResult,
  type MaterialIngest,
  type ProposedProfile,
  applyMaterial,
  uploadMaterial,
} from '../../api/materials'
import Button from '../ui/Button'
import MaterialReviewCard from './MaterialReviewCard'

const ACCEPT = '.pdf,.doc,.docx,.png,.jpg,.jpeg,.txt,.md'

type Phase =
  | { t: 'idle' }
  | { t: 'uploading' }
  | { t: 'review'; ingest: MaterialIngest }
  | { t: 'applying'; ingest: MaterialIngest }
  | { t: 'done'; result: ApplyResult }
  | { t: 'error'; message: string }

export default function MaterialUpload({
  onApplied,
  compact = false,
}: {
  onApplied?: (result: ApplyResult) => void
  compact?: boolean
}) {
  const inputRef = useRef<HTMLInputElement>(null)
  const [phase, setPhase] = useState<Phase>({ t: 'idle' })

  const pick = () => inputRef.current?.click()

  const onFile = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    e.target.value = '' // allow re-picking the same file
    if (!file) return
    setPhase({ t: 'uploading' })
    try {
      const ingest = await uploadMaterial(file)
      if (ingest.status === 'parsed' && ingest.proposed) {
        setPhase({ t: 'review', ingest })
      } else {
        setPhase({ t: 'error', message: ingest.error || 'Could not read this file. Add the details by hand.' })
      }
    } catch {
      setPhase({ t: 'error', message: 'Upload failed — please try again.' })
    }
  }

  const confirm = async (selection: Partial<ProposedProfile>) => {
    if (phase.t !== 'review') return
    const ingest = phase.ingest
    setPhase({ t: 'applying', ingest })
    try {
      const result = await applyMaterial(ingest.id, selection)
      setPhase({ t: 'done', result })
      onApplied?.(result)
    } catch {
      setPhase({ t: 'error', message: 'Could not save — please try again.' })
    }
  }

  const reset = () => setPhase({ t: 'idle' })
  const totalAdded = (r: ApplyResult) => Object.values(r.counts || {}).reduce((a, b) => a + b, 0)

  return (
    <div className={compact ? '' : 'space-y-3'}>
      <input ref={inputRef} type="file" accept={ACCEPT} onChange={onFile} className="hidden" />

      {(phase.t === 'idle' || phase.t === 'error' || phase.t === 'done') && (
        <div className={compact ? 'flex items-center gap-2' : ''}>
          <Button
            variant={compact ? 'ghost' : 'secondary'}
            size="sm"
            onClick={pick}
            aria-label="Upload a file for Uni to read"
          >
            <Upload size={14} className={compact ? '' : 'mr-1'} />
            {compact ? '' : 'Upload a resume, transcript, or CV'}
          </Button>
          {phase.t === 'done' && (
            <span className="text-xs text-secondary">
              Added {totalAdded(phase.result)} items to My Space.
            </span>
          )}
          {phase.t === 'error' && <span className="text-xs text-destructive">{phase.message}</span>}
        </div>
      )}

      {phase.t === 'uploading' && (
        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <Loader2 size={14} className="animate-spin" />
          <Sparkles size={14} className="text-secondary" /> Uni is reading your file…
        </div>
      )}

      {(phase.t === 'review' || phase.t === 'applying') && phase.ingest.proposed && (
        <MaterialReviewCard
          proposed={phase.ingest.proposed}
          onConfirm={confirm}
          onCancel={reset}
          applying={phase.t === 'applying'}
        />
      )}
    </div>
  )
}
