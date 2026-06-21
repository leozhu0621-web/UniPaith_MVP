/**
 * Phase C — Rationale popover.
 *
 * Triggers POST /me/matches/{program_id}/explain on open. Phase A returns a
 * deterministic stub built from breakdown columns; Plan 2's A5 rationale
 * agent returns real LLM-written prose. Follows the AI Rationale Popover
 * anatomy (Spec/02 §6) and the AI-surface conventions (§15): visible AI
 * attribution, confidence shown, graceful rule-based fallback, refresh.
 */
import { useEffect, useRef, useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { Sparkles, X, RefreshCw } from 'lucide-react'

import { explainMatch } from '../../../api/matching'
import { AIBadge } from '../../../components/ui/AIRationalePopover'
import QueryError from '../../../components/ui/QueryError'
import { showToast } from '../../../stores/toast-store'
import type { DecisionBrief, ExplainMatchResponse } from '../../../types'

export interface RationalePopoverProps {
  programId: string
  fitnessBreakdown?: Record<string, unknown> | null
  confidenceBreakdown?: Record<string, unknown> | null
  cachedRationale?: string | null
  onClose: () => void
}

export default function RationalePopover({
  programId,
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
    onError: () => {
      // Regenerate failed with prose still on screen → toast; a first-load
      // failure renders the in-modal error state below instead (Ship D §4).
      if (rationale) showToast("We couldn't regenerate the reasoning. Please try again.", 'error')
    },
  })

  const studentCitations = resp?.cited_student_fields ?? []
  const decisionBrief = resp?.decision_brief ?? null
  const panelRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    explainMut.mutate()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  // Modal behavior: move focus into the dialog on open; Escape closes it.
  useEffect(() => {
    panelRef.current?.focus()
    const onKey = (e: KeyboardEvent) => { if (e.key === 'Escape') onClose() }
    document.addEventListener('keydown', onKey)
    return () => document.removeEventListener('keydown', onKey)
  }, [onClose])

  return (
    <div
      className="fixed inset-0 z-50 flex items-end sm:items-center justify-center sm:p-4 bg-scrim"
      onClick={onClose}
    >
      <div
        ref={panelRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby="rationale-title"
        tabIndex={-1}
        className="bg-card text-foreground rounded-t-2xl sm:rounded-xl elev-raised max-w-lg w-full max-h-[85vh] overflow-y-auto animate-slide-up-fade sm:animate-scale-in focus-visible:outline-none"
        onClick={e => e.stopPropagation()}
      >
        <header className="flex items-center justify-between gap-2 px-5 py-3 border-b border-border">
          <div className="flex items-center gap-2">
            <Sparkles size={16} className="text-primary" />
            <h3 id="rationale-title" className="text-sm font-semibold text-foreground">Why this match</h3>
            <AIBadge />
          </div>
          <button aria-label="Close" onClick={onClose} className="text-muted-foreground hover:text-foreground">
            <X size={16} />
          </button>
        </header>

        <div className="p-5 space-y-4">
          {explainMut.isPending && !rationale ? (
            <div className="text-sm text-muted-foreground">Analyzing the match…</div>
          ) : explainMut.isError && !rationale ? (
            // Real error state, not a near-empty modal (Ship D §4).
            <QueryError
              variant="inline"
              detail="We couldn't load the reasoning."
              onRetry={() => explainMut.mutate()}
            />
          ) : (
            rationale && <p className="text-sm leading-relaxed text-foreground whitespace-pre-line">{rationale}</p>
          )}

          {decisionBrief && <DecisionBriefBlock brief={decisionBrief} />}

          {studentCitations.length > 0 && (
            <div className="border-t border-border pt-3">
              <div className="text-eyebrow text-muted-foreground mb-2">Based on your profile</div>
              <div className="flex flex-wrap gap-1.5">
                {studentCitations.map(path => (
                  <span
                    key={path}
                    className="inline-flex items-center gap-1 rounded-pill border border-border px-2 py-0.5 text-xs text-foreground"
                  >
                    {prettyField(path)}
                  </span>
                ))}
              </div>
            </div>
          )}

          {isStub && <p className="text-xs text-muted-foreground italic">Showing rule-based result.</p>}

          <div className="flex justify-end pt-1">
            {/* The error state owns the retry control until something loads. */}
            {!explainMut.isPending && !(explainMut.isError && !rationale) && (
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

const BRIEF_ORDER = [
  'fit',
  'conflicts',
  'academic_gaps',
  'career_alignment',
  'cost_aid',
  'feasibility',
  'timeline',
  'support_compatibility',
  'application_readiness',
  'alternatives',
  'next_actions',
]

const BRIEF_LABELS: Record<string, string> = {
  fit: 'Fit',
  conflicts: 'Conflicts',
  academic_gaps: 'Academic gaps',
  career_alignment: 'Career alignment',
  cost_aid: 'Cost and aid',
  feasibility: 'Feasibility',
  timeline: 'Timeline',
  support_compatibility: 'Support fit',
  application_readiness: 'Application readiness',
  alternatives: 'Comparable alternatives',
  next_actions: 'Next actions',
}

function DecisionBriefBlock({ brief }: { brief: DecisionBrief }) {
  const keys = [
    ...BRIEF_ORDER.filter((key) => brief.sections[key]?.length),
    ...Object.keys(brief.sections).filter((key) => !BRIEF_ORDER.includes(key) && brief.sections[key]?.length),
  ]
  if (keys.length === 0) return null
  return (
    <div className="border-t border-border pt-4 space-y-4">
      {keys.map((key) => (
        <section key={key} className="space-y-2">
          <h4 className="text-xs font-semibold uppercase text-muted-foreground">
            {BRIEF_LABELS[key] ?? prettyField(key)}
          </h4>
          <div className="space-y-3">
            {brief.sections[key].map((item, index) => (
              <article key={`${key}-${index}`} className="space-y-1">
                <p className="text-sm leading-6 text-foreground">{item.statement}</p>
                {item.uncertainty && (
                  <p className="text-xs leading-5 text-muted-foreground">{item.uncertainty}</p>
                )}
                {item.evidence.length > 0 && (
                  <div className="flex flex-wrap gap-1.5 text-xs text-muted-foreground">
                    {item.evidence.slice(0, 3).map((evidence) => (
                      evidence.url ? (
                        <a
                          key={`${evidence.side}-${evidence.path}-${evidence.label}`}
                          href={evidence.url}
                          target="_blank"
                          rel="noreferrer"
                          className="underline underline-offset-2 hover:text-foreground"
                        >
                          {evidence.label}
                        </a>
                      ) : (
                        <span key={`${evidence.side}-${evidence.path}-${evidence.label}`}>
                          {evidence.label}
                        </span>
                      )
                    ))}
                  </div>
                )}
              </article>
            ))}
          </div>
        </section>
      ))}
      {Boolean(brief.omissions?.length) && (
        <section className="space-y-2">
          <h4 className="text-xs font-semibold uppercase text-muted-foreground">Unknowns</h4>
          <ul className="space-y-1 text-xs leading-5 text-muted-foreground">
            {brief.omissions?.slice(0, 4).map((item) => (
              <li key={`${item.section}-${item.reason}`}>{item.reason}</li>
            ))}
          </ul>
        </section>
      )}
    </div>
  )
}

// "sparse.research_experience" → "Research experience"
function prettyField(path: string): string {
  const last = path.split('.').pop() ?? path
  const words = last.replace(/_/g, ' ').trim()
  return words.charAt(0).toUpperCase() + words.slice(1)
}
