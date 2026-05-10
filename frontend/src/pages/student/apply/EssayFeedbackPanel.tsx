/**
 * Workshops → Essay feedback (FEEDBACK-ONLY).
 *
 * Student pastes their essay; backend returns rubric + structural issues +
 * missing-element prompts. There is no "rewrite my essay" button by design.
 */
import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'

import { requestEssayFeedback } from '../../../api/workshops-feedback'
import Badge from '../../../components/ui/Badge'
import Button from '../../../components/ui/Button'
import Card from '../../../components/ui/Card'
import { showToast } from '../../../stores/toast-store'
import type { IssueSeverity, WorkshopFeedbackRun } from '../../../types'

const SEVERITY_VARIANT: Record<IssueSeverity, 'danger' | 'warning' | 'neutral'> = {
  major: 'danger',
  moderate: 'warning',
  minor: 'neutral',
}

export default function EssayFeedbackPanel() {
  const [essay, setEssay] = useState('')
  const [prompt, setPrompt] = useState('')
  const [run, setRun] = useState<WorkshopFeedbackRun | null>(null)

  const feedbackMut = useMutation({
    mutationFn: () =>
      requestEssayFeedback({
        essay_text: essay,
        prompt_text: prompt.trim() || null,
      }),
    onSuccess: r => {
      setRun(r)
      showToast('Feedback ready.', 'success')
    },
    onError: (err: unknown) =>
      showToast((err as Error).message ?? 'Could not generate feedback.', 'error'),
  })

  const wordCount = essay.trim().split(/\s+/).filter(Boolean).length

  return (
    <div className="space-y-4">
      <Card className="space-y-3">
        <div>
          <label className="block text-sm font-medium text-student-ink mb-1">
            Prompt (optional)
          </label>
          <input
            className="w-full rounded border border-divider px-3 py-2 text-sm"
            value={prompt}
            onChange={e => setPrompt(e.target.value)}
            maxLength={4000}
            placeholder="e.g., Why this program?"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-student-ink mb-1">
            Your essay <span className="text-red-600">*</span>
          </label>
          <textarea
            className="w-full rounded border border-divider px-3 py-2 text-sm font-mono"
            rows={14}
            maxLength={20000}
            value={essay}
            onChange={e => setEssay(e.target.value)}
            placeholder="Paste your draft. Min 20 characters."
          />
          <div className="flex items-center justify-between mt-1 text-xs text-student-text">
            <span>{wordCount} words</span>
            <span>I'll critique structure + flag missing elements. I won't rewrite it.</span>
          </div>
        </div>
        <div className="flex justify-end">
          <Button
            onClick={() => feedbackMut.mutate()}
            loading={feedbackMut.isPending}
            disabled={essay.trim().length < 20}
          >
            Get feedback
          </Button>
        </div>
      </Card>

      {run && (
        <>
          <Card>
            <div className="text-xs uppercase tracking-wide text-student-text mb-2">Rubric</div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
              {Object.entries(run.rubric_scores).map(([k, v]) => (
                <div key={k} className="flex items-center justify-between text-sm">
                  <span className="text-student-ink capitalize">{k.replace(/_/g, ' ')}</span>
                  <span className="font-medium text-student-ink">
                    {Number(v).toFixed(1)} / 5
                  </span>
                </div>
              ))}
            </div>
          </Card>

          {run.structural_issues.length > 0 && (
            <Card>
              <div className="text-xs uppercase tracking-wide text-student-text mb-2">
                Structural issues · {run.structural_issues.length}
              </div>
              <ul className="space-y-2">
                {run.structural_issues.map((iss, i) => (
                  <li key={i} className="flex items-start gap-2 text-sm">
                    <Badge variant={SEVERITY_VARIANT[iss.severity]} size="sm">
                      {iss.severity}
                    </Badge>
                    <div className="flex-1">
                      <div className="text-student-ink">{iss.issue}</div>
                      {iss.location_ref && (
                        <div className="text-xs text-student-text mt-0.5">
                          {iss.location_ref}
                        </div>
                      )}
                    </div>
                  </li>
                ))}
              </ul>
            </Card>
          )}

          {run.missing_elements.length > 0 && (
            <Card>
              <div className="text-xs uppercase tracking-wide text-student-text mb-2">
                Missing elements · {run.missing_elements.length}
              </div>
              <ul className="space-y-2">
                {run.missing_elements.map((m, i) => (
                  <li key={i} className="flex items-start gap-2 text-sm">
                    <Badge
                      variant={
                        m.importance === 'required'
                          ? 'danger'
                          : m.importance === 'should_have'
                            ? 'warning'
                            : 'neutral'
                      }
                      size="sm"
                    >
                      {m.importance.replace(/_/g, ' ')}
                    </Badge>
                    <span className="text-student-ink flex-1">{m.element}</span>
                  </li>
                ))}
              </ul>
            </Card>
          )}
        </>
      )}
    </div>
  )
}
