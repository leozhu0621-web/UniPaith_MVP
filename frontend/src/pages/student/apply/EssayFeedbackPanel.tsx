/**
 * Workshops → Essay feedback (FEEDBACK-ONLY).
 *
 * The student pastes an essay they wrote; the backend returns a rubric +
 * structural issues + missing-element prompts. There is, by design, no
 * "rewrite my essay" path — the response schema mechanically excludes it and
 * a CI test (test_workshop_no_generation_contract.py) enforces it.
 */
import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'

import { requestEssayFeedback } from '../../../api/workshops-feedback'
import Badge from '../../../components/ui/Badge'
import Button from '../../../components/ui/Button'
import Card from '../../../components/ui/Card'
import { showToast } from '../../../stores/toast-store'
import type { WorkshopFeedbackRun } from '../../../types'

import AIBadge from '../../../components/ui/AIBadge'
import { RubricScores } from './RubricDots'
import { EmptyHint, ErrorNote, ReadinessCard } from './WorkshopShared'
import WorkshopProgramPicker, {
  type ProgramOption,
  type WorkshopMode,
} from './WorkshopProgramPicker'
import {
  IMPORTANCE_LABEL,
  IMPORTANCE_VARIANT,
  SEVERITY_LABEL,
  SEVERITY_VARIANT,
  readinessSummary,
} from './workshopReadiness'

export default function EssayFeedbackPanel() {
  const [essay, setEssay] = useState('')
  const [prompt, setPrompt] = useState('')
  const [mode, setMode] = useState<WorkshopMode>('general')
  const [program, setProgram] = useState<ProgramOption | null>(null)
  const [run, setRun] = useState<WorkshopFeedbackRun | null>(null)
  // The program the displayed run was generated for — snapshotted at request
  // time so switching the picker afterwards never relabels a stale run.
  const [runProgram, setRunProgram] = useState<ProgramOption | null>(null)

  const feedbackMut = useMutation({
    mutationFn: (target: ProgramOption | null) =>
      requestEssayFeedback({
        essay_text: essay,
        prompt_text: prompt.trim() || null,
        target_program_id: target?.programId ?? null,
      }),
    onSuccess: (r, target) => {
      setRun(r)
      setRunProgram(target)
      showToast('Feedback ready.', 'success')
    },
    onError: (err: unknown) =>
      showToast((err as Error).message ?? 'Could not get feedback.', 'error'),
  })

  const targetProgram = mode === 'program_specific' ? program : null
  const wordCount = essay.trim().split(/\s+/).filter(Boolean).length
  const tooShort = essay.trim().length < 20
  const readiness = run && runProgram ? readinessSummary(run, runProgram.programName) : null

  return (
    <div className="space-y-4">
      <Card className="space-y-3">
        <WorkshopProgramPicker
          mode={mode}
          onModeChange={setMode}
          program={program}
          onProgramChange={setProgram}
        />

        <div>
          <label className="mb-1 block text-sm font-medium text-foreground">Prompt (optional)</label>
          <input
            className="w-full rounded-md border border-border px-3 py-2 text-sm"
            value={prompt}
            onChange={e => setPrompt(e.target.value)}
            maxLength={4000}
            placeholder="e.g., Tell us about a time you led a team"
          />
        </div>

        <div>
          <label className="mb-1 block text-sm font-medium text-foreground">
            Your essay <span className="text-error">*</span>
          </label>
          <textarea
            className="w-full rounded-md border border-border px-3 py-2 text-sm"
            rows={14}
            maxLength={20000}
            value={essay}
            onChange={e => setEssay(e.target.value)}
            placeholder="Paste your draft. Minimum 20 characters."
          />
          <div className="mt-1 flex items-center justify-between text-xs text-muted-foreground">
            <span>{wordCount} words</span>
            <span>We score structure and flag missing elements — we never rewrite your essay.</span>
          </div>
        </div>

        <div className="flex justify-end">
          <Button
            variant="secondary"
            onClick={() => feedbackMut.mutate(targetProgram)}
            loading={feedbackMut.isPending}
            disabled={tooShort}
          >
            Get feedback
          </Button>
        </div>
      </Card>

      {!run && !feedbackMut.isPending && !feedbackMut.isError && (
        <EmptyHint>Drop in an essay draft to get structured feedback.</EmptyHint>
      )}

      {feedbackMut.isError && !run && <ErrorNote onRetry={() => feedbackMut.mutate(targetProgram)} />}

      {run && (
        <>
          {readiness && runProgram && (
            <ReadinessCard programName={runProgram.programName} summary={readiness} />
          )}

          <Card>
            <div className="mb-3 flex items-center justify-between">
              <div className="text-eyebrow uppercase text-muted-foreground">Rubric scores</div>
              <AIBadge fallback={run.is_stub} />
            </div>
            <RubricScores scores={run.rubric_scores} />
          </Card>

          {(run.structural_issues?.length ?? 0) > 0 && (
            <Card>
              <div className="mb-2 text-eyebrow uppercase text-muted-foreground">
                Structural issues · {run.structural_issues.length}
              </div>
              <ul className="space-y-2">
                {run.structural_issues.map((iss, i) => (
                  <li key={i} className="flex items-start gap-2 text-sm">
                    <Badge variant={SEVERITY_VARIANT[iss.severity]} size="sm">
                      {SEVERITY_LABEL[iss.severity]}
                    </Badge>
                    <div className="flex-1">
                      <div className="text-foreground">{iss.issue}</div>
                      {iss.location_ref && (
                        <div className="mt-0.5 text-xs text-muted-foreground">{iss.location_ref}</div>
                      )}
                    </div>
                  </li>
                ))}
              </ul>
            </Card>
          )}

          {(run.missing_elements?.length ?? 0) > 0 && (
            <Card>
              <div className="mb-2 text-eyebrow uppercase text-muted-foreground">
                Missing elements · {run.missing_elements.length}
              </div>
              <ul className="space-y-2">
                {run.missing_elements.map((m, i) => (
                  <li key={i} className="flex items-start gap-2 text-sm">
                    <Badge variant={IMPORTANCE_VARIANT[m.importance]} size="sm">
                      {IMPORTANCE_LABEL[m.importance]}
                    </Badge>
                    <span className="flex-1 text-foreground">{m.element}</span>
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
