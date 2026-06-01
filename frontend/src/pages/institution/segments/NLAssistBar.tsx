import { useState } from 'react'
import { Sparkles } from 'lucide-react'
import { useMutation } from '@tanstack/react-query'
import { segmentNlBridge } from '../../../api/institutions'
import { showToast } from '../../../stores/toast-store'
import type { NLBridgeResult } from '../../../types'

interface Props {
  onApply: (result: NLBridgeResult) => void
}

/** Spec 26 §6 — "Try AI assist": natural-language → structured rules via the
 *  SegmentBuilderNLBridge agent (with keyword fallback). Confidence + ambiguity
 *  notes are surfaced; the user edits the resulting chips before saving. */
export default function NLAssistBar({ onApply }: Props) {
  const [text, setText] = useState('')
  const [notes, setNotes] = useState<string[]>([])
  const [confidence, setConfidence] = useState<number | null>(null)

  const mut = useMutation({
    mutationFn: () => segmentNlBridge(text.trim()),
    onSuccess: (res) => {
      setNotes(res.ambiguity_notes ?? [])
      setConfidence(res.confidence_overall)
      if (!res.rules.length) {
        showToast('No rules could be derived — try rephrasing or build manually.', 'warning')
        return
      }
      onApply(res)
      showToast(
        `Drafted ${res.rules.length} rule${res.rules.length === 1 ? '' : 's'} — review and edit.`,
        'success',
      )
    },
    onError: () => showToast('AI assist failed. Build the segment manually.', 'error'),
  })

  return (
    <div className="rounded-lg border border-cobalt/30 bg-cobalt/5 p-4">
      <div className="mb-2 flex items-center gap-2 text-sm font-semibold text-cobalt">
        <Sparkles size={15} /> Try AI assist: type what audience you want →
      </div>
      <div className="flex gap-2">
        <input
          type="text"
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && text.trim()) mut.mutate()
          }}
          placeholder="e.g. high-fit master's students who saved our programs but haven't applied"
          className="flex-1 rounded-md border-border text-sm focus:border-cobalt focus:ring-cobalt"
        />
        <button
          type="button"
          disabled={!text.trim() || mut.isPending}
          onClick={() => mut.mutate()}
          className="shrink-0 rounded-md bg-secondary px-4 py-2 text-sm font-medium text-secondary-foreground hover:brightness-110 disabled:opacity-50"
        >
          {mut.isPending ? 'Drafting…' : 'Draft rules'}
        </button>
      </div>

      {confidence != null && (
        <div className="mt-2 space-y-1">
          <p className="text-xs text-muted-foreground">
            AI confidence: <span className="font-semibold text-foreground">{confidence}%</span> —
            review the suggested rules below before saving.
          </p>
          {notes.map((n, i) => (
            <p key={i} className="text-xs text-warning">
              • {n}
            </p>
          ))}
        </div>
      )}
    </div>
  )
}
