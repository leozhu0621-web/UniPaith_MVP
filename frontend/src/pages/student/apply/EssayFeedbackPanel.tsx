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

import { RubricScores } from './RubricDots'
import { EmptyHint, ErrorNote, ReadinessCard, StubNote } from './WorkshopShared'
import WorkshopProgramPicker, {
  type ProgramOption,
  type WorkshopMode,
} from './WorkshopProgramPicker'
import { IMPORTANCE_VARIANT, SEVERITY_VARIANT, readinessSummary } from './workshopReadiness'

export default function EssayFeedbackPanel() {
  const [essay, setEssay] = useState('')
  const [prompt, setPrompt] = useState('')
  const [mode, setMode] = useState<WorkshopMode>('general')
  const [program, setProgram] = useState<ProgramOption | null>(null)
  const [run, setRun] = useState<WorkshopFeedbackRun | null>(null)

  const feedbackMut = useMutation({
    mutationFn: () =>
      requestEssayFeedback({
        essay_text: essay,
        prompt_text: prompt.trim() || null,
        target_program_id: mode === 'program_specific' ? program?.programId ?? null : null,
      }),
    onSuccess: r => {
      setRun(r)
      showToast('Feedback ready.', 'success')
    },
    onError: (err: unknown) =>
      showToast((err as Error).message ?? 'Could not get feedback.', 'error'),
  })

  const wordCount = essay.trim().split(/\s+/).filter(Boolean).length
  const tooShort = essay.trim().length < 20
  const readiness =
    run && mode === 'program_specific' && program
      ? readinessSummary(run, program.programName)
      : null

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
            className="w-full rounded-md border border-border px-3 py-2 font-mono text-sm"
            rows={14}
            maxLength={20000}
            value={essay}
            onChange={e => setEssay(e.target.value)}
            placeholder="Paste your draft. Minimum 20 characters."
          />
          <div className="mt-1 flex items-center justify-between text-xs text-foreground">
            <span>{wordCount} words</span>
            <span>I'll critique structure and flag missing elements. I won't rewrite it.</span>
          </div>
        </div>

        <div className="flex justify-end">
          <Button
            variant="secondary"
            onClick={() => feedbackMut.mutate()}
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

      {feedbackMut.isError && !run && <ErrorNote onRetry={() => feedbackMut.mutate()} />}

      {run && (
        <>
          {readiness && program && (
            <ReadinessCard programName={program.programName} summary={readiness} />
          )}

          <Card>
            <div className="mb-3 flex items-center justify-between">
              <div className="text-eyebrow uppercase text-foreground">Rubric scores</div>
              {run.is_stub && <StubNote />}
            </div>
            <RubricScores scores={run.rubric_scores} />
          </Card>

          {run.structural_issues.length > 0 && (
            <Card>
              <div className="mb-2 text-eyebrow uppercase text-foreground">
                Structural issues · {run.structural_issues.length}
              </div>
              <ul className="space-y-2">
                {run.structural_issues.map((iss, i) => (
                  <li key={i} className="flex items-start gap-2 text-sm">
                    <Badge variant={SEVERITY_VARIANT[iss.severity]} size="sm">
                      {iss.severity}
                    </Badge>
                    <div className="flex-1">
                      <div className="text-foreground">{iss.issue}</div>
                      {iss.location_ref && (
                        <div className="mt-0.5 text-xs text-foreground">{iss.location_ref}</div>
                      )}
                    </div>
                  </li>
                ))}
              </ul>
            </Card>
          )}

          {run.missing_elements.length > 0 && (
            <Card>
              <div className="mb-2 text-eyebrow uppercase text-foreground">
                Missing elements · {run.missing_elements.length}
              </div>
              <ul className="space-y-2">
                {run.missing_elements.map((m, i) => (
                  <li key={i} className="flex items-start gap-2 text-sm">
                    <Badge variant={IMPORTANCE_VARIANT[m.importance]} size="sm">
                      {m.importance.replace(/_/g, ' ')}
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
