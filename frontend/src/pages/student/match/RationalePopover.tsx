/**
 * Phase C — Rationale popover.
 *
 * Triggers POST /me/matches/{program_id}/explain on open. Phase A returns a
 * deterministic stub built from breakdown columns; Plan 2's A5 rationale
 * agent (PR #124) returns real LLM-written prose. The popover renders both
 * the rationale text and the structured breakdown side-by-side so power
 * users can verify the explanation matches the underlying signals.
 */
import { useEffect, useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { Sparkles, X } from 'lucide-react'

import { explainMatch } from '../../../api/matching'
import Button from '../../../components/ui/Button'
import { showToast } from '../../../stores/toast-store'
import type { ExplainMatchResponse } from '../../../types'

export interface RationalePopoverProps {
  programId: string
  fitnessBreakdown?: Record<string, unknown> | null
  confidenceBreakdown?: Record<string, unknown> | null
  /** Existing rationale_text from the match row, if cached. Saves an API
   *  call when the popover opens. */
  cachedRationale?: string | null
  onClose: () => void
}

export default function RationalePopover({
  programId,
  fitnessBreakdown,
  confidenceBreakdown,
  cachedRationale,
  onClose,
}: RationalePopoverProps) {
  const [rationale, setRationale] = useState<string | null>(cachedRationale ?? null)
  const [isStub, setIsStub] = useState(false)

  const explainMut = useMutation({
    mutationFn: () => explainMatch(programId),
    onSuccess: (resp: ExplainMatchResponse) => {
      setRationale(resp.rationale_text)
      setIsStub(resp.is_stub)
    },
    onError: (err: unknown) =>
      showToast((err as Error).message ?? 'Could not load rationale.', 'error'),
  })

  // Auto-fetch on mount if we don't have a cached rationale.
  useEffect(() => {
    if (!cachedRationale) explainMut.mutate()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4"
      onClick={onClose}
    >
      <div
        className="bg-white rounded-xl shadow-xl max-w-lg w-full max-h-[85vh] overflow-y-auto"
        onClick={e => e.stopPropagation()}
      >
        <header className="flex items-center justify-between px-5 py-3 border-b border-divider">
          <div className="flex items-center gap-2">
            <Sparkles size={16} className="text-gold" />
            <h3 className="text-sm font-semibold text-student-ink">
              Why this score?
            </h3>
            {isStub && (
              <span className="text-[10px] uppercase tracking-wide px-1.5 py-0.5 rounded bg-amber-100 text-amber-800">
                preview
              </span>
            )}
          </div>
          <button
            aria-label="Close"
            onClick={onClose}
            className="text-student-text hover:text-student-ink"
          >
            <X size={16} />
          </button>
        </header>

        <div className="p-5 space-y-4">
          {explainMut.isPending && !rationale ? (
            <div className="text-sm text-student-text">
              Analyzing the match…
            </div>
          ) : (
            rationale && (
              <p className="text-sm text-student-ink whitespace-pre-line">{rationale}</p>
            )
          )}

          {fitnessBreakdown && Object.keys(fitnessBreakdown).length > 0 && (
            <BreakdownBlock title="Fitness drivers" data={fitnessBreakdown} />
          )}
          {confidenceBreakdown && Object.keys(confidenceBreakdown).length > 0 && (
            <BreakdownBlock title="Confidence drivers" data={confidenceBreakdown} />
          )}

          <div className="flex justify-end pt-2">
            {!explainMut.isPending && (
              <Button size="sm" variant="ghost" onClick={() => explainMut.mutate()}>
                Regenerate
              </Button>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

function BreakdownBlock({
  title,
  data,
}: {
  title: string
  data: Record<string, unknown>
}) {
  return (
    <div>
      <div className="text-[10px] uppercase tracking-wide text-student-text mb-1.5">
        {title}
      </div>
      <ul className="space-y-1">
        {Object.entries(data).map(([k, v]) => (
          <li key={k} className="text-xs text-student-ink flex items-start gap-1.5">
            <span className="text-student-text shrink-0">{k}</span>
            <span className="text-student-text">·</span>
            <span className="break-all">{String(v)}</span>
          </li>
        ))}
      </ul>
    </div>
  )
}
