/**
 * Workshops → Interview practice (NO MODEL ANSWERS).
 *
 * Returns suggested questions only. Each question item is exactly
 * `{question, why}` — there is no `model_answer` / `sample_response` /
 * `revised_text` field. The schema test (test_workshop_no_generation_contract.py)
 * enforces this on every commit.
 */
import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'

import { requestInterviewPractice } from '../../../api/workshops-feedback'
import Button from '../../../components/ui/Button'
import Card from '../../../components/ui/Card'
import { showToast } from '../../../stores/toast-store'
import type { WorkshopFeedbackRun } from '../../../types'

type InterviewType = 'behavioral' | 'technical' | 'general'

const TYPES: { key: InterviewType; label: string }[] = [
  { key: 'general', label: 'General' },
  { key: 'behavioral', label: 'Behavioral' },
  { key: 'technical', label: 'Technical' },
]

export default function InterviewPracticePanel() {
  const [interviewType, setInterviewType] = useState<InterviewType>('general')
  const [focus, setFocus] = useState('')
  // Optional — when filled in, the backend coaches the response instead
  // of returning canned practice questions.
  const [questionText, setQuestionText] = useState('')
  const [responseText, setResponseText] = useState('')
  const [run, setRun] = useState<WorkshopFeedbackRun | null>(null)

  const hasResponse = responseText.trim().length > 0
  const practiceMut = useMutation({
    mutationFn: () =>
      requestInterviewPractice({
        interview_type: interviewType,
        focus_area: focus.trim() || null,
        response_text: responseText.trim() || null,
        question_text: questionText.trim() || null,
      }),
    onSuccess: r => {
      setRun(r)
      showToast(hasResponse ? 'Coaching ready.' : 'Practice questions ready.', 'success')
    },
    onError: (err: unknown) =>
      showToast((err as Error).message ?? 'Could not generate questions.', 'error'),
  })

  return (
    <div className="space-y-4">
      <Card className="space-y-3">
        <div>
          <label className="block text-sm font-medium text-student-ink mb-1">Type</label>
          <div className="flex gap-1">
            {TYPES.map(t => (
              <button
                key={t.key}
                onClick={() => setInterviewType(t.key)}
                className={`px-3 py-1.5 text-sm rounded-lg border transition-colors ${
                  interviewType === t.key
                    ? 'border-student bg-student/5 text-student-ink'
                    : 'border-divider text-student-text hover:border-student-text'
                }`}
              >
                {t.label}
              </button>
            ))}
          </div>
        </div>
        <div>
          <label className="block text-sm font-medium text-student-ink mb-1">
            Focus area (optional)
          </label>
          <input
            className="w-full rounded border border-divider px-3 py-2 text-sm"
            value={focus}
            onChange={e => setFocus(e.target.value)}
            maxLength={200}
            placeholder="e.g., research fit, leadership in ambiguity, your senior thesis"
          />
        </div>
        {/* Optional — paste a question + your answer to get coached on
            your response instead of canned practice questions. */}
        <details className="text-sm">
          <summary className="cursor-pointer text-student-text hover:text-student-ink">
            Or — coach a response you've drafted
          </summary>
          <div className="mt-3 space-y-3 pt-1 border-t border-divider">
            <div>
              <label className="block text-xs font-medium text-student-ink mb-1">
                Question
              </label>
              <input
                className="w-full rounded border border-divider px-3 py-2 text-sm"
                value={questionText}
                onChange={e => setQuestionText(e.target.value)}
                maxLength={4000}
                placeholder="The question you're answering"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-student-ink mb-1">
                Your response
              </label>
              <textarea
                className="w-full rounded border border-divider px-3 py-2 text-sm font-mono"
                rows={6}
                maxLength={20000}
                value={responseText}
                onChange={e => setResponseText(e.target.value)}
                placeholder="Paste your answer. I'll coach delivery / structure / specificity. No rewrite."
              />
            </div>
          </div>
        </details>
        <div className="text-xs text-student-text">
          {hasResponse ? (
            <>I'll coach your response — <strong>no model answer</strong> in return.</>
          ) : (
            <>
              You'll get 5+ questions to practice. <strong>No model answers</strong> —
              practicing your own response is the point.
            </>
          )}
        </div>
        <div className="flex justify-end">
          <Button onClick={() => practiceMut.mutate()} loading={practiceMut.isPending}>
            {hasResponse ? 'Coach my response' : 'Generate questions'}
          </Button>
        </div>
      </Card>

      {run && run.suggested_questions.length > 0 && (
        <Card>
          <div className="text-xs uppercase tracking-wide text-student-text mb-3">
            Practice questions · {run.suggested_questions.length}
          </div>
          <ol className="space-y-3">
            {run.suggested_questions.map((q, i) => (
              <li key={i} className="text-sm">
                <div className="text-student-ink font-medium">
                  {i + 1}. {q.question}
                </div>
                <div className="text-xs text-student-text italic mt-0.5">{q.why}</div>
              </li>
            ))}
          </ol>
        </Card>
      )}
    </div>
  )
}
