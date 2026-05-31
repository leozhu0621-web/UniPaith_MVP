/**
 * Phase C — Rationale popover.
 *
 * Triggers POST /me/matches/{program_id}/explain on open. Phase A returns a
 * deterministic stub built from breakdown columns; Plan 2's A5 rationale
 * agent returns real LLM-written prose. Follows the AI Rationale Popover
 * anatomy (Spec/02 §6) and the AI-surface conventions (§15): visible AI
 * attribution, confidence shown, graceful rule-based fallback, refresh.
 */
import { useEffect, useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { Sparkles, X, RefreshCw } from 'lucide-react'

import { explainMatch } from '../../../api/matching'
import { AIBadge } from '../../../components/ui/AIRationalePopover'
import { showToast } from '../../../stores/toast-store'
import type { ExplainMatchResponse } from '../../../types'

export interface RationalePopoverProps {
  programId: string
  fitnessBreakdown?: Record<string, unknown> | null
  confidenceBreakdown?: Record<string, unknown> | null
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
  // Spec 06 §5.5 — these come back already redacted to the student-safe view.
  const [resp, setResp] = useState<ExplainMatchResponse | null>(null)

  const explainMut = useMutation({
    mutationFn: () => explainMatch(programId),
    onSuccess: (r: ExplainMatchResponse) => {
      setRationale(r.rationale_text)
      setIsStub(r.is_stub)
      setResp(r)
    },
    onError: (err: unknown) =>
      showToast((err as Error).message ?? 'Could not load rationale.', 'error'),
  })

  // Prefer the server's redacted breakdowns/citations; fall back to props
  // (passed from the match list) only until the call returns.
  const fitness = (resp?.fitness_breakdown as Record<string, unknown> | null) ?? fitnessBreakdown
  const confidence =
    (resp?.confidence_breakdown as Record<string, unknown> | null) ?? confidenceBreakdown
  const studentCitations = resp?.cited_student_fields ?? []

  useEffect(() => {
    if (!cachedRationale) explainMut.mutate()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  return (
    <div
      className="fixed inset-0 z-50 flex items-end sm:items-center justify-center sm:p-4"
      style={{ background: 'rgba(10, 20, 40, 0.45)' }}
      onClick={onClose}
    >
      <div
        className="bg-card text-foreground rounded-t-2xl sm:rounded-xl elev-raised max-w-lg w-full max-h-[85vh] overflow-y-auto animate-slide-up-fade sm:animate-scale-in"
        onClick={e => e.stopPropagation()}
      >
        <header className="flex items-center justify-between gap-2 px-5 py-3 border-b border-border">
          <div className="flex items-center gap-2">
            <Sparkles size={16} className="text-primary" />
            <h3 className="text-sm font-semibold text-foreground">Why this score?</h3>
            <AIBadge />
          </div>
          <button aria-label="Close" onClick={onClose} className="text-muted-foreground hover:text-foreground">
            <X size={16} />
          </button>
        </header>

        <div className="p-5 space-y-4">
          {explainMut.isPending && !rationale ? (
            <div className="text-sm text-muted-foreground">Analyzing the match…</div>
          ) : (
            rationale && <p className="text-sm leading-relaxed text-foreground whitespace-pre-line">{rationale}</p>
          )}

          {studentCitations.length > 0 && (
            <div className="border-t border-border pt-3">
              <div className="text-eyebrow text-muted-foreground mb-2">Based on your profile</div>
              <div className="flex flex-wrap gap-1.5">
                {studentCitations.map(path => (
                  <span
                    key={path}
                    className="inline-flex items-center gap-1 rounded-pill border border-student bg-student/10 px-2 py-0.5 text-xs text-student-ink"
                  >
                    {prettyField(path)}
                  </span>
                ))}
              </div>
            </div>
          )}

          {fitness && Object.keys(fitness).length > 0 && (
            <BreakdownBlock title="Based on — fitness drivers" data={fitness} />
          )}
          {confidence && Object.keys(confidence).length > 0 && (
            <BreakdownBlock title="Based on — confidence drivers" data={confidence} />
          )}

          {isStub && <p className="text-xs text-muted-foreground italic">Showing rule-based result.</p>}

          <div className="flex justify-end pt-1">
            {!explainMut.isPending && (
              <button
                onClick={() => explainMut.mutate()}
                className="inline-flex items-center gap-1.5 text-xs font-semibold text-secondary hover:underline"
              >
                <RefreshCw size={12} /> Regenerate
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

// "sparse.research_experience" → "Research experience"
function prettyField(path: string): string {
  const last = path.split('.').pop() ?? path
  const words = last.replace(/_/g, ' ').trim()
  return words.charAt(0).toUpperCase() + words.slice(1)
}

function BreakdownBlock({ title, data }: { title: string; data: Record<string, unknown> }) {
  return (
    <div className="border-t border-border pt-3">
      <div className="text-eyebrow text-muted-foreground mb-2">{title}</div>
      <div className="flex flex-wrap gap-1.5">
        {Object.entries(data).map(([k, v]) => (
          <span
            key={k}
            className="inline-flex items-center gap-1 rounded-pill border border-cobalt px-2 py-0.5 text-xs text-cobalt"
          >
            <span className="font-semibold">{k}</span>
            <span className="text-cobalt/60">·</span>
            <span>{String(v)}</span>
          </span>
        ))}
      </div>
    </div>
  )
}
