/**
 * Workshops → Interview (NO MODEL ANSWERS).
 *
 * Two sub-modes (Spec/14-workshops.md §4):
 *  - Practice questions: returns questions to rehearse. Generating the
 *    *questions* is allowed — they're coach prompts, not student answers.
 *  - Score a response: paste a question + your answer and get a rubric +
 *    structural issues + missing elements + follow-up questions. No model
 *    answer is ever returned — the response schema forbids it.
 *
 * Ship D — input preservation: the drafted question/response (plus type,
 * focus, and program selection) persists to localStorage keyed per program
 * and is restored on mount. Cleared on successful submit.
 */
import { useEffect, useRef, useState } from 'react'
import { useMutation } from '@tanstack/react-query'

import { requestInterviewPractice } from '../../../api/workshops-feedback'
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
import { clearWorkshopDraft, loadLastWorkshopDraft, saveWorkshopDraft } from './workshopDrafts'
import {
  IMPORTANCE_LABEL,
  IMPORTANCE_VARIANT,
  SEVERITY_LABEL,
  SEVERITY_VARIANT,
  readinessSummary,
} from './workshopReadiness'

type InterviewType = 'behavioral' | 'technical' | 'general'

const TYPES: { key: InterviewType; label: string }[] = [
  { key: 'general', label: 'General' },
  { key: 'behavioral', label: 'Behavioral' },
  { key: 'technical', label: 'Technical' },
]

const DRAFT_PREFIX = 'up-interview-draft'

interface InterviewDraft {
  interviewType: InterviewType
  focus: string
  questionText: string
  responseText: string
  mode: WorkshopMode
  program: ProgramOption | null
}

/** The text the student actually typed — what's worth preserving. */
const draftText = (d: InterviewDraft) => `${d.focus}\n${d.questionText}\n${d.responseText}`

/** Save the draft when it holds real text; clear it otherwise (or once submitted). */
function persistInterviewDraft(d: InterviewDraft, lastSubmitted: string | null): void {
  const programId = d.mode === 'program_specific' ? d.program?.programId ?? null : null
  if (draftText(d).trim() && draftText(d) !== lastSubmitted) {
    saveWorkshopDraft(DRAFT_PREFIX, programId, d)
  } else {
    clearWorkshopDraft(DRAFT_PREFIX, programId)
  }
}

export default function InterviewPracticePanel() {
  // Restore the last draft synchronously on mount (program selection included).
  const [restored] = useState(() => loadLastWorkshopDraft<Partial<InterviewDraft>>(DRAFT_PREFIX))
  const [interviewType, setInterviewType] = useState<InterviewType>(
    restored?.interviewType === 'behavioral' || restored?.interviewType === 'technical'
      ? restored.interviewType
      : 'general',
  )
  const [focus, setFocus] = useState(typeof restored?.focus === 'string' ? restored.focus : '')
  const [questionText, setQuestionText] = useState(
    typeof restored?.questionText === 'string' ? restored.questionText : '',
  )
  const [responseText, setResponseText] = useState(
    typeof restored?.responseText === 'string' ? restored.responseText : '',
  )
  const [mode, setMode] = useState<WorkshopMode>(
    restored?.mode === 'program_specific' ? 'program_specific' : 'general',
  )
  const [program, setProgram] = useState<ProgramOption | null>(
    restored?.program && typeof restored.program.programId === 'string' ? restored.program : null,
  )
  const [draftRestored, setDraftRestored] = useState(
    Boolean(
      (typeof restored?.responseText === 'string' && restored.responseText.trim()) ||
        (typeof restored?.questionText === 'string' && restored.questionText.trim()),
    ),
  )
  // Initial-render constant: open the collapsed coach section when a draft was
  // restored into it (constant so the user's own toggling is never fought).
  const [coachInitiallyOpen] = useState(
    () =>
      Boolean(
        (typeof restored?.responseText === 'string' && restored.responseText.trim()) ||
          (typeof restored?.questionText === 'string' && restored.questionText.trim()),
      ),
  )
  const [run, setRun] = useState<WorkshopFeedbackRun | null>(null)
  // The program the displayed run was generated for — snapshotted at request
  // time so switching the picker afterwards never relabels a stale run.
  const [runProgram, setRunProgram] = useState<ProgramOption | null>(null)

  const hasResponse = responseText.trim().length > 0

  // Last successfully submitted text — once submitted, the stored draft is
  // cleared and not re-saved unless the text changes again.
  const lastSubmittedRef = useRef<string | null>(null)
  const draftRef = useRef<InterviewDraft>({ interviewType, focus, questionText, responseText, mode, program })
  draftRef.current = { interviewType, focus, questionText, responseText, mode, program }

  // Debounced persist while typing + flush on unmount.
  useEffect(() => {
    const t = setTimeout(() => persistInterviewDraft(draftRef.current, lastSubmittedRef.current), 600)
    return () => clearTimeout(t)
  }, [interviewType, focus, questionText, responseText, mode, program])
  useEffect(() => () => persistInterviewDraft(draftRef.current, lastSubmittedRef.current), [])

  const practiceMut = useMutation({
    mutationFn: (target: ProgramOption | null) =>
      requestInterviewPractice({
        interview_type: interviewType,
        focus_area: focus.trim() || null,
        response_text: responseText.trim() || null,
        question_text: questionText.trim() || null,
        target_program_id: target?.programId ?? null,
      }),
    onSuccess: (r, target) => {
      setRun(r)
      setRunProgram(target)
      lastSubmittedRef.current = draftText(draftRef.current)
      clearWorkshopDraft(DRAFT_PREFIX, target?.programId ?? null)
      setDraftRestored(false)
      showToast(hasResponse ? 'Coaching ready.' : 'Practice questions ready.', 'success')
    },
    onError: (err: unknown) =>
      showToast((err as Error).message ?? 'Could not get feedback.', 'error'),
  })

  const targetProgram = mode === 'program_specific' ? program : null
  // Score mode produces a non-zero rubric; practice mode returns an all-zero
  // placeholder rubric (we hide that).
  const scored = run ? Object.values(run.rubric_scores ?? {}).some(v => Number(v) > 0) : false
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

        <details className="text-sm" open={coachInitiallyOpen}>
          <summary className="cursor-pointer text-foreground hover:text-foreground">
            Or — coach a response you've drafted
          </summary>
          <div className="mt-3 space-y-3 border-t border-border pt-3">
            <div>
              <div className="mb-1 flex items-center justify-between">
                <label className="block text-xs font-medium text-foreground">Question</label>
                {draftRestored && (
                  <span className="text-[11px] text-muted-foreground">Draft restored</span>
                )}
              </div>
              <input
                className="w-full rounded-md border border-border px-3 py-2 text-sm"
                value={questionText}
                onChange={e => {
                  setQuestionText(e.target.value)
                  if (draftRestored) setDraftRestored(false)
                }}
                maxLength={4000}
                placeholder="The question you're answering"
              />
            </div>
            <div>
              <label className="mb-1 block text-xs font-medium text-foreground">Your response</label>
              <textarea
                className="w-full rounded-md border border-border px-3 py-2 text-sm"
                rows={6}
                maxLength={20000}
                value={responseText}
                onChange={e => {
                  setResponseText(e.target.value)
                  if (draftRestored) setDraftRestored(false)
                }}
                placeholder="Paste your answer. We'll coach delivery, structure, and specificity — no rewrite."
              />
            </div>
          </div>
        </details>

        <div className="text-xs text-muted-foreground">
          {hasResponse ? (
            <>
              We'll coach your response — <strong>no model answer</strong> in return.
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
            onClick={() => practiceMut.mutate(targetProgram)}
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

      {practiceMut.isError && !run && <ErrorNote onRetry={() => practiceMut.mutate(targetProgram)} />}

      {run && (
        <>
          {readiness && runProgram && (
            <ReadinessCard programName={runProgram.programName} summary={readiness} />
          )}

          {scored && (
            <Card>
              <div className="mb-3 flex items-center justify-between">
                <div className="text-eyebrow uppercase text-muted-foreground">Rubric scores</div>
                <AIBadge fallback={run.is_stub} />
              </div>
              <RubricScores scores={run.rubric_scores} />
            </Card>
          )}

          {(run.structural_issues?.length ?? 0) > 0 && (
            <Card>
              <div className="mb-2 text-eyebrow uppercase text-muted-foreground">
                Response issues · {run.structural_issues.length}
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

          {(run.suggested_questions?.length ?? 0) > 0 && (
            <Card>
              <div className="mb-3 text-eyebrow uppercase text-muted-foreground">
                {hasResponse ? 'Questions to practice next' : 'Practice questions'} ·{' '}
                {run.suggested_questions.length}
              </div>
              <ol className="space-y-3">
                {run.suggested_questions.map((q, i) => (
                  <li key={i} className="text-sm">
                    <div className="font-medium text-foreground">
                      {i + 1}. {q.question}
                    </div>
                    {q.why && <div className="mt-0.5 text-xs text-muted-foreground">{q.why}</div>}
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
