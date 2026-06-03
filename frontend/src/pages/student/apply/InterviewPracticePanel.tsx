/**
 * Workshops → Interview (NO MODEL ANSWERS).
 *
 * Two sub-modes (Spec/14-workshops.md §4):
 *  - Practice questions: returns questions to rehearse. Generating the
 *    *questions* is allowed — they're coach prompts, not student answers.
 *  - Score a response: paste a question + your answer and get a rubric +
 *    structural issues + missing elements + follow-up questions. No model
 *    answer is ever returned — the response schema forbids it.
 */
import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'

import { requestInterviewPractice } from '../../../api/workshops-feedback'
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

type InterviewType = 'behavioral' | 'technical' | 'general'

const TYPES: { key: InterviewType; label: string }[] = [
  { key: 'general', label: 'General' },
  { key: 'behavioral', label: 'Behavioral' },
  { key: 'technical', label: 'Technical' },
]

export default function InterviewPracticePanel() {
  const [interviewType, setInterviewType] = useState<InterviewType>('general')
  const [focus, setFocus] = useState('')
  const [questionText, setQuestionText] = useState('')
  const [responseText, setResponseText] = useState('')
  const [mode, setMode] = useState<WorkshopMode>('general')
  const [program, setProgram] = useState<ProgramOption | null>(null)
  const [run, setRun] = useState<WorkshopFeedbackRun | null>(null)

  const hasResponse = responseText.trim().length > 0

  const practiceMut = useMutation({
    mutationFn: () =>
      requestInterviewPractice({
        interview_type: interviewType,
        focus_area: focus.trim() || null,
        response_text: responseText.trim() || null,
        question_text: questionText.trim() || null,
        target_program_id: mode === 'program_specific' ? program?.programId ?? null : null,
      }),
    onSuccess: r => {
      setRun(r)
      showToast(hasResponse ? 'Coaching ready.' : 'Practice questions ready.', 'success')
    },
    onError: (err: unknown) =>
      showToast((err as Error).message ?? 'Could not get feedback.', 'error'),
  })

  // Score mode produces a non-zero rubric; practice mode returns an all-zero
  // placeholder rubric (we hide that).
  const scored = run ? Object.values(run.rubric_scores ?? {}).some(v => Number(v) > 0) : false
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
          <label className="mb-1 block text-sm font-medium text-foreground">Type</label>
          <div className="flex gap-1">
            {TYPES.map(t => (
              <button
                key={t.key}
                type="button"
                onClick={() => setInterviewType(t.key)}
                className={`rounded-lg border px-3 py-1.5 text-sm transition-colors ${
                  interviewType === t.key
                    ? 'border-primary bg-primary/5 text-foreground'
                    : 'border-border text-foreground hover:border-foreground'
                }`}
              >
                {t.label}
              </button>
            ))}
          </div>
        </div>

        <div>
          <label className="mb-1 block text-sm font-medium text-foreground">
            Focus area (optional)
          </label>
          <input
            className="w-full rounded-md border border-border px-3 py-2 text-sm"
            value={focus}
            onChange={e => setFocus(e.target.value)}
            maxLength={200}
            placeholder="e.g., research fit, leadership in ambiguity, your senior thesis"
          />
        </div>

        <details className="text-sm">
          <summary className="cursor-pointer text-foreground hover:text-foreground">
            Or — coach a response you've drafted
          </summary>
          <div className="mt-3 space-y-3 border-t border-border pt-3">
            <div>
              <label className="mb-1 block text-xs font-medium text-foreground">Question</label>
              <input
                className="w-full rounded-md border border-border px-3 py-2 text-sm"
                value={questionText}
                onChange={e => setQuestionText(e.target.value)}
                maxLength={4000}
                placeholder="The question you're answering"
              />
            </div>
            <div>
              <label className="mb-1 block text-xs font-medium text-foreground">Your response</label>
              <textarea
                className="w-full rounded-md border border-border px-3 py-2 font-mono text-sm"
                rows={6}
                maxLength={20000}
                value={responseText}
                onChange={e => setResponseText(e.target.value)}
                placeholder="Paste your answer. I'll coach delivery, structure, and specificity — no rewrite."
              />
            </div>
          </div>
        </details>

        <div className="text-xs text-foreground">
          {hasResponse ? (
            <>
              I'll coach your response — <strong>no model answer</strong> in return.
            </>
          ) : (
            <>
              You'll get questions to rehearse.{' '}
              <strong>These are practice questions, not answers.</strong>
            </>
          )}
        </div>

        <div className="flex justify-end">
          <Button
            variant="secondary"
            onClick={() => practiceMut.mutate()}
            loading={practiceMut.isPending}
          >
            {hasResponse ? 'Get feedback' : 'Get practice questions'}
          </Button>
        </div>
      </Card>

      {!run && !practiceMut.isPending && !practiceMut.isError && (
        <EmptyHint>
          Pick a type for questions to rehearse — or paste a response below for coaching.
        </EmptyHint>
      )}

      {practiceMut.isError && !run && <ErrorNote onRetry={() => practiceMut.mutate()} />}

      {run && (
        <>
          {readiness && program && (
            <ReadinessCard programName={program.programName} summary={readiness} />
          )}

          {scored && (
            <Card>
              <div className="mb-3 flex items-center justify-between">
                <div className="text-eyebrow uppercase text-foreground">Rubric scores</div>
                {run.is_stub && <StubNote />}
              </div>
              <RubricScores scores={run.rubric_scores} />
            </Card>
          )}

          {run.structural_issues.length > 0 && (
            <Card>
              <div className="mb-2 text-eyebrow uppercase text-foreground">
                Response issues · {run.structural_issues.length}
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

          {run.suggested_questions.length > 0 && (
            <Card>
              <div className="mb-3 text-eyebrow uppercase text-foreground">
                {hasResponse ? 'Questions to practice next' : 'Practice questions'} ·{' '}
                {run.suggested_questions.length}
              </div>
              <ol className="space-y-3">
                {run.suggested_questions.map((q, i) => (
                  <li key={i} className="text-sm">
                    <div className="font-medium text-foreground">
                      {i + 1}. {q.question}
                    </div>
                    {q.why && <div className="mt-0.5 text-xs italic text-foreground">{q.why}</div>}
                  </li>
                ))}
              </ol>
            </Card>
          )}
        </>
      )}
    </div>
  )
}
